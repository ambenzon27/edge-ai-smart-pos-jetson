"""
Configuration settings for YOLO POS system.
Optimized for Jetson Orin (FPS, stability, detection reliability).
"""

from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / "logs"
MODEL_DIR = BASE_DIR / "model"

LOG_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Default model (override in code if using TensorRT .engine)
# Use .pt file for macOS/non-Jetson platforms, .engine for Jetson with TensorRT
import platform
if platform.system() == "Darwin":  # macOS
    DEFAULT_MODEL_PATH = BASE_DIR / "best.pt"
else:  # Linux/Jetson
    DEFAULT_MODEL_PATH = MODEL_DIR / "yolov8n.engine"
    # Fallback to .pt if .engine not found
    if not DEFAULT_MODEL_PATH.exists():
        DEFAULT_MODEL_PATH = BASE_DIR / "best.pt"

# ============================================================================
# LOGGING
# ============================================================================
LOG_FILE = LOG_DIR / "detections.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

# ============================================================================
# CAMERA SETTINGS (JETSON-OPTIMIZED)
# ============================================================================
# Note: On macOS, camera index 1 works better than 0
# On Jetson, use 0 (default USB camera)
CAMERA_DEVICE_INDEX = 1 if platform.system() == "Darwin" else 0

# Recommended resolutions:
# - 416x416 → fastest YOLO inference
# - 640x480 → better readability
CAMERA_WIDTH = 416
CAMERA_HEIGHT = 416

CAMERA_FPS = 30

# MJPEG is cheaper to decode than YUYV on Jetson
USE_MJPEG = True

# ============================================================================
# YOLO / INFERENCE SETTINGS
# ============================================================================
# Run inference every N frames (FPS boost)
INFERENCE_INTERVAL = 3   # 3–4 is the sweet spot

# Global confidence threshold
CONFIDENCE_THRESHOLD = 0.45

# IOU threshold for NMS
IOU_THRESHOLD = 0.5

# Temporal confirmation
TEMPORAL_CONFIRMATION_FRAMES = 3   # must appear 3×
TEMPORAL_WINDOW_SECONDS = 1.0      # within 1 second

# Cooldown after confirmed detection (per class)
COOLDOWN_SECONDS = 1.0

# Detection queue size (FastAPI polling safe)
DETECTION_QUEUE_MAX_SIZE = 100

# ============================================================================
# PER-CLASS CONFIDENCE OVERRIDES
# ============================================================================
# NOTE:
# - Values override CONFIDENCE_THRESHOLD
# - 0.95 is used to effectively DISABLE detection of unwanted classes
PER_CLASS_CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "coffee_nescafe": 0.50,
    "coffee_kopiko": 0.60,
    "lucky-me-pancit-canton": 0.50,
    "Coke-in-can": 0.65,
    "alaska_milk": 0.60,
    "Century-Tuna": 0.65,
    "VCut-Spicy-Barbeque": 0.60,
    "Selecta-Cornetto": 0.60,
    "nestleyogurt": 0.50,
    "Femme-Bathroom-Tissue": 0.60,
    "maya-champorado": 0.65,
    "jnj-potato-chips": 0.60,
    "Nivea-Deodorant": 0.65,
    "UFC-Canned-Mushroom": 0.60,
    "Libbys-Vienna-Sausage-can": 0.65,
    "Stik-O": 0.60,
    "nissin_cup_noodles": 0.65,
    "dewberry-strawberry": 0.60,
    "Smart-C": 0.60,
    "pineapple-juice-can": 0.50,
    "nestle_chuckie": 0.50,
    "Delight-Probiotic-Drink": 0.60,
    "Summit-Drinking-Water": 0.50,
    "almond_milk": 0.65,
    "Piknik": 0.60,
    "Bactidol": 0.95,               # effectively disabled
    "head&shoulders_shampoo": 0.50,
    "irish-spring-soap": 0.50,
    "c2_na_green": 0.50,
    "colgate_toothpaste": 0.50,
    "555-sardines-tomato": 0.60,
    "meadows_truffle_chips": 0.65,
    "double-black": 0.95,            # effectively disabled
    "NongshimCupNoodles": 0.65,
}

# ============================================================================
# HAND GESTURE SETTINGS (MEDIAPIPE)
# ============================================================================
GESTURE_STATIC_IMAGE_MODE = False
GESTURE_MAX_NUM_HANDS = 1

# Lowered for better real-world lighting
GESTURE_MIN_DETECTION_CONFIDENCE = 0.5
GESTURE_MIN_TRACKING_CONFIDENCE = 0.3

# Gesture confirmation buffer
GESTURE_HISTORY_MAX_SIZE = 2

# Gesture classification thresholds
GESTURE_FINGER_EXTENSION_THRESHOLD = 0.05
GESTURE_PALM_MIN_FINGERS = 4
GESTURE_FIST_MAX_FINGERS = 1   # ≤1 finger = fist

# Hold gesture for this long to confirm
GESTURE_CONFIRMATION_TIME = 1.0

# Draw landmarks (disable for max FPS)
SHOW_HAND_LANDMARKS = True

# ============================================================================
# AUDIO / TTS
# ============================================================================
# espeak is faster and more reliable on Jetson than pyttsx3
USE_ESPEAK_TTS = True

# ============================================================================
# UI OVERLAY SETTINGS
# ============================================================================
STATUS_TEXT_RECORDING = "REC"
STATUS_TEXT_PAUSED = "PAUSED"

STATUS_COLOR_RECORDING = (0, 0, 255)     # Red (BGR)
STATUS_COLOR_PAUSED = (128, 128, 128)    # Gray

STATUS_POSITION = (10, 30)
STATUS_FONT = 0                          # cv2.FONT_HERSHEY_SIMPLEX
STATUS_FONT_SCALE = 0.8
STATUS_FONT_THICKNESS = 2

# Bounding boxes
BBOX_COLOR_READY = (0, 255, 0)
BBOX_COLOR_COOLDOWN = (0, 200, 255)
BBOX_COLOR_DUPLICATE = (128, 128, 128)
BBOX_COLOR_LOW_CONFIDENCE = (128, 128, 128)
BBOX_THICKNESS = 2

# Labels
LABEL_FONT = 0
LABEL_FONT_SCALE = 0.5
LABEL_FONT_THICKNESS = 2
LABEL_TEXT_COLOR = (0, 0, 0)
LABEL_PADDING = 10

# ============================================================================
# ITEM PRICES (PHP)
# ============================================================================
ITEM_PRICES = {
    "coffee_nescafe": 10,
    "coffee_kopiko": 10,
    "lucky-me-pancit-canton": 14,
    "Coke-in-can": 30,
    "alaska_milk": 28,
    "Century-Tuna": 38,
    "VCut-Spicy-Barbeque": 20,
    "Selecta-Cornetto": 35,
    "nestleyogurt": 25,
    "Femme-Bathroom-Tissue": 20,
    "maya-champorado": 94,
    "jnj-potato-chips": 20,
    "Nivea-Deodorant": 100,
    "UFC-Canned-Mushroom": 35,
    "Libbys-Vienna-Sausage-can": 23,
    "Stik-O": 12,
    "nissin_cup_noodles": 22,
    "dewberry-strawberry": 18,
    "Smart-C": 22,
    "pineapple-juice-can": 30,
    "nestle_chuckie": 15,
    "Delight-Probiotic-Drink": 12,
    "Summit-Drinking-Water": 15,
    "almond_milk": 90,
    "Piknik": 25,
    "Bactidol": 85,
    "head&shoulders_shampoo": 210,
    "irish-spring-soap": 40,
    "c2_na_green": 20,
    "colgate_toothpaste": 70,
    "555-sardines-tomato": 26,
    "meadows_truffle_chips": 90,
    "double-black": 1000,
    "NongshimCupNoodles": 50,
}
