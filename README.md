# Edge-AI Smart POS for Jetson Orin

A real-time, self-checkout Point-of-Sale system built for the NVIDIA Jetson Orin.
A USB camera streams into a YOLOv8 detector that recognizes grocery items on the
fly, MediaPipe hand gestures start and stop a shopping session, and a FastAPI
server drives a full-screen browser kiosk that shows the live feed and an
auto-updating cart. The model can be exported to TensorRT for low-latency
inference on the Orin GPU.

## Highlights

- **Real-time object detection** — YOLOv8 (Ultralytics) over an MJPEG camera
  stream, with temporal confirmation and per-class confidence thresholds to
  suppress false positives.
- **Hand-gesture control** — MediaPipe Hands: an open palm starts a recording
  session, a closed fist ends it. No touchscreen required.
- **TensorRT optimization** — export the trained `.pt` weights to a `.engine`
  file for FP16 inference on Jetson; the app auto-selects the engine when present.
- **FastAPI kiosk backend** — camera boots in a background thread so the UI loads
  instantly; REST endpoints expose detections, prices, health, and recording
  state.
- **Browser kiosk UI** — a lightweight HTML/JS front end that renders the live
  stream, running cart, and checkout receipt in full-screen Chromium.
- **Cross-platform dev** — runs on macOS for development (`best.pt`) and on
  Jetson for deployment (`.engine`), selected automatically in `app/config.py`.

## Architecture

```
start_amb_store.py         # Launcher: pre-flight checks + uvicorn
│
├── app/
│   ├── main.py            # FastAPI app: routes, MJPEG stream, lifecycle
│   ├── camera.py          # USB capture, YOLO inference, MediaPipe gestures
│   └── config.py          # Camera, inference, gesture, price & threshold config
│
├── web/
│   ├── index.html         # Kiosk UI
│   └── static/            # app.js, styles.css
│
├── scripts/
│   ├── start_server.sh    # Start uvicorn (with optional .venv)
│   └── start_kiosk.sh     # Wait for /health, launch Chromium in kiosk mode
│
├── convert_to_tensorrt.py # Export best.pt -> TensorRT .engine
├── check_gpu.py           # Verify CUDA / GPU availability
├── best.pt                # Trained YOLOv8 weights (33 grocery classes)
└── model/best.pt          # Same weights, resolved via config on Jetson
```

The camera capture loop runs YOLOv8 every `INFERENCE_INTERVAL` frames and only
emits a detection after it appears in `TEMPORAL_CONFIRMATION_FRAMES` consecutive
inferences within a short window, followed by a per-class cooldown. Confirmed
detections are queued and polled by the front end via `/detections`.

## HTTP API

| Method | Endpoint           | Description                                        |
|--------|--------------------|----------------------------------------------------|
| GET    | `/`                | Kiosk UI (`web/index.html`)                        |
| GET    | `/video-stream`    | Live MJPEG stream (`multipart/x-mixed-replace`)    |
| GET    | `/detections`      | Newly confirmed detections (queue cleared on read) |
| GET    | `/recording-state` | Current gesture-controlled recording state         |
| GET    | `/prices`          | Item price table (PHP)                             |
| GET    | `/health`          | Startup / camera health for the kiosk launcher     |

## Requirements

### Hardware
- NVIDIA Jetson Orin (Nano / NX / AGX)
- USB (UVC) camera
- Optional speakers for audio/TTS feedback

### Software
- JetPack 5.x / 6.x (Ubuntu 20.04 / 22.04) for deployment, or macOS for development
- Python 3.8+
- Chromium (for kiosk mode on Jetson)

### Python dependencies
```
fastapi
uvicorn[standard]
opencv-python
ultralytics
mediapipe
pyttsx3
```
Pinned versions are in [`requirements.txt`](requirements.txt).

## Quick start

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Verify GPU (optional, Jetson)
python3 check_gpu.py

# 3. (Jetson) export TensorRT engine for faster inference
python3 convert_to_tensorrt.py

# 4. Launch the server + pre-flight checks
python3 start_amb_store.py
```

Then open `http://<device-ip>:8000` in a browser, or run the kiosk launcher on
the Jetson:

```bash
./scripts/start_kiosk.sh
```

To run the server directly without the launcher:

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# or
./scripts/start_server.sh
```

## Using the system

1. **Start a session** — show an open palm to the camera and hold briefly.
2. **Scan items** — present grocery items one at a time; confirmed detections are
   added to the cart automatically with prices from `app/config.py`.
3. **End a session** — show a closed fist to stop recording and review the receipt.

## Configuration

All tunables live in [`app/config.py`](app/config.py):

- **Camera** — device index, resolution (default 416×416), FPS, MJPEG toggle.
- **Inference** — `INFERENCE_INTERVAL`, global `CONFIDENCE_THRESHOLD`,
  `IOU_THRESHOLD`, and per-class overrides in
  `PER_CLASS_CONFIDENCE_THRESHOLDS` (set to `0.95` to effectively disable a class).
- **Temporal filtering** — confirmation frames, window, and per-class cooldown.
- **Gestures** — MediaPipe confidence, finger-extension threshold, and hold time.
- **Prices** — `ITEM_PRICES` maps each class label to its price in PHP.

The model path is resolved automatically: `best.pt` on macOS, and
`model/yolov8n.engine` on Jetson with a fallback to `best.pt` when the engine is
absent.

## Deployment on Jetson Orin

Deployment notes and checklists are included in the repo:

- [`RUN_ON_JETSON.md`](RUN_ON_JETSON.md)
- [`JETSON_SETUP.md`](JETSON_SETUP.md)
- [`DEPLOY_TO_JETSON_ORIN.md`](DEPLOY_TO_JETSON_ORIN.md)
- [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md)
- [`ME7_READY_FOR_DEPLOYMENT.md`](ME7_READY_FOR_DEPLOYMENT.md)

For a run-through of the design and testing approach, see
[`AMB_STORE_DESIGN_README.md`](AMB_STORE_DESIGN_README.md),
[`ARCHITECTURE.md`](ARCHITECTURE.md), and
[`TESTING_GUIDE.md`](TESTING_GUIDE.md).

## License

Released under the [MIT License](LICENSE).

## Author

Anna Marie Benzon
