"""
Camera helpers for streaming frames from a USB device.
Optimized for Jetson Orin: FPS-safe, duplicate-safe, production-ready.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque, defaultdict
from pathlib import Path
from typing import Optional
import queue
import os
import platform

import cv2
import mediapipe as mp
import torch
from ultralytics import YOLO

from . import config

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
config.LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[logging.FileHandler(config.LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

logger.info("CUDA available: %s", torch.cuda.is_available())
if torch.cuda.is_available():
    logger.info("GPU: %s", torch.cuda.get_device_name(0))


# ─────────────────────────────────────────────────────────────
# Optional audio
# ─────────────────────────────────────────────────────────────
try:
    import winsound
except Exception:
    winsound = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


def espeak_say(text: str, speed: int = 150) -> None:
    """Fast, non-blocking TTS for Jetson/Linux/macOS."""
    if platform.system() == "Darwin":  # macOS
        # Use macOS 'say' command
        os.system(f'say -r {int(speed * 1.2)} "{text}" &')
    elif platform.system() == "Linux":
        # Use Linux espeak
        os.system(f'espeak -s {speed} "{text}" >/dev/null 2>&1 &')
    # Windows/other: silently skip


# ─────────────────────────────────────────────────────────────
# TTS Worker
# ─────────────────────────────────────────────────────────────
class TTSAnnouncer:
    def __init__(self):
        self._q: queue.Queue[str] = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._engine = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        try:
            self._q.put_nowait("")
        except Exception:
            pass

    def speak(self, text: str):
        if text:
            try:
                self._q.put_nowait(text)
            except Exception:
                pass

    def _worker(self):
        if pyttsx3:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", 150)
            except Exception:
                self._engine = None

        while self._running:
            try:
                text = self._q.get(timeout=0.5)
            except Exception:
                continue

            if not text or not self._engine:
                continue

            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                self._engine = None


# ─────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────
class CameraNotReadyError(Exception):
    pass


# ─────────────────────────────────────────────────────────────
# Main Camera + Detection Class
# ─────────────────────────────────────────────────────────────
class USBCameraStream:
    def __init__(
        self,
        device_index: int = config.CAMERA_DEVICE_INDEX,
        width: int = config.CAMERA_WIDTH,
        height: int = config.CAMERA_HEIGHT,
        fps: int = config.CAMERA_FPS,
        model_path: Optional[str] = None,
        inference_interval: int = config.INFERENCE_INTERVAL,
        confidence_threshold: float = config.CONFIDENCE_THRESHOLD,
        cooldown_seconds: float = config.COOLDOWN_SECONDS,
        per_class_thresholds: Optional[dict[str, float]] = None,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.device_index = device_index

        self.inference_interval = max(1, inference_interval)
        self.confidence_threshold = confidence_threshold
        self.cooldown_seconds = cooldown_seconds
        self.per_class_thresholds = per_class_thresholds or {}

        self._capture: Optional[cv2.VideoCapture] = None
        self._frame_lock = threading.Lock()
        self._latest_frame: Optional[bytes] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_count = 0

        # Detection state
        self._model: Optional[YOLO] = None
        self._detection_lock = threading.Lock()
        self._detections: deque[dict] = deque(maxlen=config.DETECTION_QUEUE_MAX_SIZE)
        self._last_seen: dict[str, float] = {}
        self._temporal_hits: defaultdict[str, deque] = defaultdict(deque)
        self._last_added: Optional[str] = None

        # Transaction
        self._recording = False
        self._total = 0
        self._items: list[dict] = []

        # YOLO load
        if model_path:
            path = Path(model_path)
            if not path.exists():
                raise FileNotFoundError(path)
            self._model = YOLO(str(path))
            if torch.cuda.is_available():
                self._model.to("cuda")
            logger.info("YOLO loaded: %s", path)

        # Hand tracking
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=config.GESTURE_MAX_NUM_HANDS,
            min_detection_confidence=config.GESTURE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.GESTURE_MIN_TRACKING_CONFIDENCE,
        )

        self._last_gesture = None
        self._gesture_time = None

        self._tts = TTSAnnouncer()

    # ─────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────
    def start(self):
        if self._running:
            return

        # Use platform-appropriate camera backend
        if platform.system() == "Darwin":  # macOS
            cap = cv2.VideoCapture(self.device_index, cv2.CAP_AVFOUNDATION)
        elif platform.system() == "Linux":  # Jetson/Linux
            cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
        else:  # Windows or other
            cap = cv2.VideoCapture(self.device_index)

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)

        # MJPEG optimization (may not work on all platforms)
        if config.USE_MJPEG and platform.system() == "Linux":
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        if not cap.isOpened():
            raise RuntimeError("Camera open failed")

        self._capture = cap
        self._running = True
        self._tts.start()

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        espeak_say("Welcome sa AMB Store. Buksan ang kamay para magsimula.", 160)

    def stop(self):
        self._running = False
        if self._capture:
            self._capture.release()
        self._tts.stop()

    # ─────────────────────────────────────────────
    # Frame Loop
    # ─────────────────────────────────────────────
    def _loop(self):
        wait = 1.0 / max(self.fps, 1)

        while self._running:
            ok, frame = self._capture.read()
            if not ok:
                time.sleep(0.1)
                continue

            self._frame_count += 1

            gesture = self._detect_gesture(frame)
            self._handle_gesture(gesture)

            # Run detection and draw bounding boxes
            if self._model and self._frame_count % self.inference_interval == 0:
                frame = self._run_detection_with_viz(frame)

            ret, buf = cv2.imencode(".jpg", frame)
            if ret:
                with self._frame_lock:
                    self._latest_frame = buf.tobytes()

            time.sleep(wait)

    # ─────────────────────────────────────────────
    # Detection Logic (STABILIZED)
    # ─────────────────────────────────────────────
    def _run_detection_with_viz(self, frame):
        """Run detection and draw bounding boxes on frame"""
        results = self._model(frame, verbose=False)[0]
        now = time.time()
        annotated_frame = frame.copy()

        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = results.names[cls]

            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            threshold = self.per_class_thresholds.get(name, self.confidence_threshold)

            # Determine box color based on state
            if conf < threshold:
                color = (128, 128, 128)  # Gray - Low confidence
                label = f"{name} {conf:.2f}"
            elif not self._recording:
                color = (255, 255, 0)  # Yellow - Paused
                label = f"{name} {conf:.2f} (PAUSED)"
            elif now - self._last_seen.get(name, 0) < self.cooldown_seconds:
                color = (0, 200, 255)  # Orange - Cooldown
                label = f"{name} {conf:.2f} (COOLDOWN)"
            else:
                color = (0, 255, 0)  # Green - Ready to add
                label = f"{name} {conf:.2f}"

            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)

            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), color, -1)

            # Draw label text
            cv2.putText(annotated_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

            # Handle detection confirmation logic (same as before)
            if conf < threshold or not self._recording:
                continue

            # cooldown
            if now - self._last_seen.get(name, 0) < self.cooldown_seconds:
                continue

            # temporal confirmation
            hits = self._temporal_hits[name]
            hits.append(now)
            while hits and now - hits[0] > 1.0:
                hits.popleft()

            if len(hits) < 3:
                continue

            # confirmed - add to queue
            hits.clear()
            self._last_seen[name] = now
            price = config.ITEM_PRICES.get(name, 50)

            with self._detection_lock:
                self._detections.append(
                    {
                        "class_name": name,
                        "confidence": conf,
                        "price": price,
                        "timestamp": now,
                    }
                )
                self._total += int(price)
                self._items.append({"class_name": name, "price": price})

            logger.info("Detected %s ₱%s", name, price)

        return annotated_frame

    def _run_detection(self, frame):
        results = self._model(frame, verbose=False)[0]
        now = time.time()

        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = results.names[cls]

            threshold = self.per_class_thresholds.get(name, self.confidence_threshold)
            if conf < threshold or not self._recording:
                continue

            # cooldown
            if now - self._last_seen.get(name, 0) < self.cooldown_seconds:
                continue

            # temporal confirmation
            hits = self._temporal_hits[name]
            hits.append(now)
            while hits and now - hits[0] > 1.0:
                hits.popleft()

            if len(hits) < 3:
                continue

            # confirmed
            hits.clear()
            self._last_seen[name] = now
            price = config.ITEM_PRICES.get(name, 50)

            with self._detection_lock:
                self._detections.append(
                    {
                        "class_name": name,
                        "confidence": conf,
                        "price": price,
                        "timestamp": now,
                    }
                )
                self._total += int(price)
                self._items.append({"class_name": name, "price": price})

            logger.info("Detected %s ₱%s", name, price)

    # ─────────────────────────────────────────────
    # Gesture Logic
    # ─────────────────────────────────────────────
    def _detect_gesture(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self._hands.process(rgb)
        if not res.multi_hand_landmarks:
            return None

        lm = res.multi_hand_landmarks[0].landmark
        fingers = sum(lm[t].y < lm[b].y for t, b in [(8, 6), (12, 10), (16, 14), (20, 18)])

        if fingers >= 4:
            return "palm"
        if fingers <= 1:
            return "fist"
        return None

    def _handle_gesture(self, gesture):
        now = time.time()
        if gesture != self._last_gesture:
            self._last_gesture = gesture
            self._gesture_time = now
            return

        if not gesture or now - self._gesture_time < config.GESTURE_CONFIRMATION_TIME:
            return

        if gesture == "palm" and not self._recording:
            self._recording = True
            espeak_say("Nagsimula na ang session.", 160)

        elif gesture == "fist" and self._recording:
            self._recording = False
            espeak_say(f"Total ay {self._total} pesos. Salamat!", 160)
            self._total = 0
            self._items.clear()

        self._last_gesture = None
        self._gesture_time = None

    # ─────────────────────────────────────────────
    # API Helpers
    # ─────────────────────────────────────────────
    def get_frame(self) -> bytes:
        with self._frame_lock:
            if not self._latest_frame:
                raise CameraNotReadyError()
            return self._latest_frame

    def get_detections(self) -> list[dict]:
        with self._detection_lock:
            out = list(self._detections)
            self._detections.clear()
        return out

    def is_recording(self) -> bool:
        return self._recording
