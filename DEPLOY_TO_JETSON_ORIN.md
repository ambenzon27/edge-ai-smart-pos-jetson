# Deploying to Jetson Orin - Performance Optimized

This guide ensures your POS system runs smoothly on Jetson Orin with good FPS.

## Prerequisites

1. Jetson Orin with JetPack 6.0 or later installed
2. USB camera connected
3. Speaker connected to monitor (audio output)

## Step 1: Transfer Files to Jetson Orin

### Option A: Using SCP (from your Mac)
```bash
cd "/Users/annamariebenzon/Documents/PhD in AI/SECOND YEAR/First Sem/AI231/MLOps Assignment/me7"
scp -r me7_2 jetson@<JETSON_IP>:~/
```

### Option B: Using USB drive or Git
Copy the `me7_2` folder to the Jetson Orin

## Step 2: Install Dependencies on Jetson Orin

```bash
cd ~/me7_2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install ultralytics opencv-python mediapipe fastapi uvicorn pyttsx3

# Install espeak for TTS
sudo apt-get update
sudo apt-get install -y espeak
```

## Step 3: Convert Model to TensorRT (CRITICAL for Performance!)

This step is **essential** for good FPS on Jetson Orin. TensorRT provides 3-5x speedup!

```bash
cd ~/me7_2
source venv/bin/activate

python3 convert_to_tensorrt.py
```

This will create `model/best.engine` which is optimized for Jetson Orin.

## Step 4: Test Camera

```bash
python3 test_camera_jetson.py
```

Expected output:
- Camera opens successfully
- Real frames (not black)
- ~30 FPS capture rate

## Step 5: Run Performance Test

```bash
python3 performance_test_jetson.py
```

This will show:
- Model inference time
- FPS with YOLO detection
- Memory usage
- GPU utilization

## Step 6: Start the POS System

```bash
python3 start_amb_store.py
```

Access from browser:
- On Jetson: `http://localhost:8000`
- From network: `http://<JETSON_IP>:8000`

## Performance Expectations on Jetson Orin

With TensorRT optimization:
- **FPS**: 15-25 FPS with YOLO detection
- **Inference time**: 30-50ms per frame
- **Detection latency**: < 1 second

Without TensorRT (using .pt model):
- **FPS**: 3-8 FPS (slow and laggy)
- **Inference time**: 150-300ms per frame
- Not recommended for production

## Troubleshooting

### Low FPS / Lag
1. Make sure you converted to TensorRT (Step 3)
2. Check GPU is being used: `nvidia-smi`
3. Lower camera resolution in `app/config.py`:
   ```python
   CAMERA_WIDTH = 416
   CAMERA_HEIGHT = 416
   ```

### Camera Not Working
1. Check camera is detected: `ls /dev/video*`
2. Test with: `v4l2-ctl --list-devices`
3. Try different camera index (0, 1, 2)

### Model Not Loading
1. Check `best.pt` exists in project root
2. For TensorRT: check `model/best.engine` exists
3. Check CUDA is available: `python3 -c "import torch; print(torch.cuda.is_available())"`

### Audio Not Working
1. Check speaker connection
2. Test audio: `speaker-test -t wav`
3. Test espeak: `espeak "Hello from AMB Store"`

## Advanced Optimizations

### 1. Max Performance Mode
```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 2. Reduce Resolution Further
Edit `app/config.py`:
```python
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 320
INFERENCE_INTERVAL = 4  # Process every 4th frame
```

### 3. Disable Hand Tracking (if not needed)
Comment out gesture detection in `app/camera.py` line 254

### 4. Monitor Performance
```bash
# Terminal 1: Watch GPU usage
watch -n 1 nvidia-smi

# Terminal 2: Run the app
python3 start_amb_store.py
```

## Expected Performance Metrics

| Configuration | FPS | Inference Time | CPU % | GPU % |
|--------------|-----|----------------|-------|-------|
| TensorRT + 640x480 | 20-25 | 40ms | 30% | 60% |
| TensorRT + 416x416 | 25-30 | 30ms | 25% | 50% |
| PyTorch .pt + 640x480 | 5-8 | 200ms | 60% | 80% |

## Deployment Checklist

- [ ] Jetson Orin powered on and connected to network
- [ ] USB camera connected and detected
- [ ] Speaker/monitor audio working
- [ ] Python dependencies installed
- [ ] Model converted to TensorRT (.engine file exists)
- [ ] Camera test passes
- [ ] Performance test shows good FPS (>15)
- [ ] Web interface accessible from browser
- [ ] Gesture detection working (open/close hand)
- [ ] Item detection working with bounding boxes
- [ ] Audio announcements working

## Support

If you encounter issues:
1. Check the logs in `logs/detections.log`
2. Run the diagnostic scripts
3. Verify all prerequisites are met
