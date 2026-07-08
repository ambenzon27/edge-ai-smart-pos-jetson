from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Generator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .camera import USBCameraStream, CameraNotReadyError

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
INDEX_HTML = WEB_DIR / "index.html"

MODEL_PATH = config.DEFAULT_MODEL_PATH

# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title="Jetson YOLO POS Camera Server",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # kiosk / local-only usage
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CAMERA INSTANCE
# ============================================================================
camera = USBCameraStream(
    model_path=str(MODEL_PATH) if MODEL_PATH.exists() else None,
    per_class_thresholds=config.PER_CLASS_CONFIDENCE_THRESHOLDS,
)

# Camera state flags
_camera_initializing = True
_camera_failed = False


# ============================================================================
# CAMERA BACKGROUND STARTUP
# ============================================================================
def _start_camera_background() -> None:
    """Start camera + model in background thread (non-blocking)."""
    global _camera_initializing, _camera_failed

    print("🎥 Initializing camera and YOLO model in background…")
    try:
        camera.start()
        _camera_initializing = False
        print("✅ Camera and model ready")
    except Exception as exc:
        _camera_failed = True
        _camera_initializing = False
        print(f"❌ Camera initialization failed: {exc}")


@app.on_event("startup")
async def on_startup() -> None:
    """Start camera asynchronously so UI loads immediately."""
    thread = threading.Thread(
        target=_start_camera_background,
        daemon=True,
        name="camera-init-thread",
    )
    thread.start()
    print("🚀 FastAPI server started (camera initializing in background)")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Gracefully stop camera on shutdown."""
    try:
        camera.stop()
    except Exception as exc:
        print(f"⚠️ Camera stop error: {exc}")


# ============================================================================
# VIDEO STREAMING
# ============================================================================
def _frame_generator() -> Generator[bytes, None, None]:
    """
    MJPEG stream generator.
    Designed to be lightweight and non-blocking.
    """
    while True:
        try:
            frame = camera.get_frame()
        except CameraNotReadyError:
            time.sleep(0.1)
            continue
        except Exception:
            time.sleep(0.2)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n" +
            frame + b"\r\n"
        )

        # Small sleep to avoid CPU hogging
        time.sleep(0.01)


# ============================================================================
# ROUTES
# ============================================================================
@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    """Serve kiosk UI."""
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_HTML)


@app.get("/test", response_class=FileResponse)
async def test_page() -> FileResponse:
    """Diagnostic test page for camera stream."""
    test_html = BASE_DIR / "test_live_stream.html"
    if not test_html.exists():
        raise HTTPException(status_code=404, detail="Test page not found")
    return FileResponse(test_html)


@app.get("/test-prices", response_class=FileResponse)
async def test_prices_page() -> FileResponse:
    """Price debugging test page."""
    test_html = BASE_DIR / "test_prices.html"
    if not test_html.exists():
        raise HTTPException(status_code=404, detail="Price test page not found")
    return FileResponse(test_html)


@app.get("/video-stream")
async def video_stream() -> StreamingResponse:
    """Live MJPEG video stream."""
    return StreamingResponse(
        _frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/health")
async def health() -> JSONResponse:
    """Health endpoint used by kiosk + startup checks."""
    if _camera_failed:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Camera failed to initialize"},
        )

    if _camera_initializing:
        return JSONResponse(
            content={"status": "initializing", "message": "Camera and model loading"},
        )

    try:
        frame = camera.get_frame()
        frame_size = len(frame) if frame else 0
    except CameraNotReadyError:
        return JSONResponse(
            content={"status": "warming_up", "message": "Camera warming up"},
        )

    return JSONResponse(content={
        "status": "ok",
        "message": "Ready",
        "frame_size": frame_size,
        "frame_count": camera._frame_count
    })


@app.get("/detections")
async def get_detections() -> list[dict]:
    """
    Returns newly CONFIRMED detections only.
    Queue is cleared after each call.
    """
    return camera.get_detections()


@app.get("/recording-state")
async def recording_state() -> dict[str, bool]:
    """Current gesture-controlled recording state."""
    return {"recording": camera.is_recording()}


@app.get("/prices")
async def prices() -> dict[str, int]:
    """Expose item price list to frontend."""
    return config.ITEM_PRICES


# ============================================================================
# STATIC FILES
# ============================================================================
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
