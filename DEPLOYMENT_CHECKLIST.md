# ME7 POS System - Deployment Checklist

**Last Updated:** December 13, 2025
**Model Version:** YOLOv8n trained on dataset_complete_v4 (34 product classes)
**Target Hardware:** NVIDIA Jetson Orin Nano

---

## Training Summary

### Model Performance
- **Model:** YOLOv8n (6MB)
- **Training Dataset:** dataset_complete_v4 with 34 grocery product classes
- **Training Platform:** Google Colab A100 GPU (40GB)
- **Batch Size:** 128
- **Epochs:** 100 (with early stopping, patience=5)
- **Expected mAP@0.5:** >85% (target for 34 classes)
- **Model File:** `best.pt` (5.4MB)

### 34 Product Classes
1. coffee_nescafe
2. coffee_kopiko
3. Lucky-Me-Pancit-Canton
4. Coke-in-can
5. Alaska-Milk
6. Century-Tuna
7. VCut-Spicy-Barbeque
8. Selecta-Cornetto
9. Nestle-Yogurt
10. Femme-Bathroom-Tissue
11. Maya-Champorado
12. JnJ-Potato-Chips
13. Nivea-Deodorant
14. UFC-Canned-Mushroom
15. Libbys-Vienna-Sausage-can
16. Stik-O
17. NissinCupNoodles
18. Dewberry-Strawberry
19. Smart-C
20. Pineapple-juice-can
21. Nestle-Chuckie
22. Delight-Probiotic-Drink
23. Summit-Drinking-Water
24. almond_milk
25. Piknik
26. Bactidol
27. HS-Shampoo
28. irish-spring-soap
29. c2_na_green
30. colgate_toothpaste
31. 555-sardines
32. meadows-truffle
33. double-black
34. NongshimCupNoodles

---

## Pre-Deployment Checklist

### 1. Files Verification
- [x] `best.pt` - Trained YOLOv8n model (5.4MB)
- [x] `products.json` - All 34 products with prices
- [x] `pos_system.py` - Main application
- [x] `object_detector.py` - YOLO object detection module
- [x] `gesture_detector.py` - MediaPipe hand gesture module
- [x] `audio_manager.py` - Audio and TTS module
- [x] `pos_ui.py` - UI and receipt management
- [x] `requirements.txt` - Python dependencies
- [x] `README.md` - Documentation

### 2. Hardware Requirements
- [ ] NVIDIA Jetson Orin Nano (or NX/AGX)
- [ ] USB Camera or CSI Camera
- [ ] Speakers for audio feedback
- [ ] Internet connection (for initial setup)
- [ ] Power supply (5V/4A for Orin Nano)

### 3. Software Requirements
- [ ] JetPack 5.0+ installed
- [ ] Python 3.8+
- [ ] CUDA 11.4+
- [ ] cuDNN 8.6+

---

## Installation Steps (On Jetson Orin)

### Step 1: System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libportaudio2 portaudio19-dev
sudo apt-get install -y espeak ffmpeg libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y libjpeg-dev libpng-dev libtiff-dev
```

### Step 2: PyTorch for Jetson
```bash
# For JetPack 5.x
wget https://nvidia.box.com/shared/static/mp164asf3sceb570wvjsrezk1p4ftj8t.whl -O torch-2.0.0-cp38-cp38-linux_aarch64.whl
pip3 install torch-2.0.0-cp38-cp38-linux_aarch64.whl

# Install torchvision
sudo apt-get install -y libjpeg-dev zlib1g-dev
git clone --branch v0.15.0 https://github.com/pytorch/vision torchvision
cd torchvision
python3 setup.py install --user
cd ..
```

### Step 3: Python Dependencies
```bash
cd /path/to/me7
pip3 install -r requirements.txt
```

### Step 4: Verify Files
```bash
# Check model file
ls -lh best.pt  # Should show ~5.4MB

# Check products database
cat products.json | grep -c "\"name\"" # Should show 34

# Check Python modules
python3 -c "import cv2, ultralytics, mediapipe, pygame, pyttsx3; print('All imports successful!')"
```

---

## Testing & Validation

### 1. Test Object Detection
```bash
python3 -c "
from object_detector import ObjectDetector
detector = ObjectDetector('best.pt', use_tensorrt=False)
print('Object detector initialized successfully!')
"
```

### 2. Test Gesture Detection
```bash
python3 -c "
from gesture_detector import GestureDetector
detector = GestureDetector()
print('Gesture detector initialized successfully!')
detector.release()
"
```

### 3. Test Audio System
```bash
python3 -c "
from audio_manager import AudioManager
audio = AudioManager(enable_tts=True)
audio.play_session_start()
import time; time.sleep(3)
audio.stop()
print('Audio system working!')
"
```

### 4. Test Complete System
```bash
# Test without TensorRT first
python3 pos_system.py --no-tensorrt --camera 0

# Then test with TensorRT optimization
python3 pos_system.py --camera 0
```

---

## Operation Guide

### Starting the System
```bash
python3 pos_system.py
```

### Controls
- **Open Hand (hold 1s):** Start customer session
- **Closed Fist (hold 1s):** End customer session
- **Q Key:** Quit application

### Session Workflow
1. Customer shows **open hand** → Session starts → Beep sound
2. Present items one by one → Item detected → Beep + TTS announcement
3. Items automatically added to receipt
4. Customer shows **closed fist** → Session ends → Total announced

### Performance Expectations
- **Object Detection Latency:** <500ms
- **Gesture Detection Latency:** <1s (requires 1s hold)
- **FPS:** 28-32 FPS (with TensorRT)
- **Model Size:** 6MB (.pt), ~3MB (.engine)

---

## Grading Criteria (From ME7 Instructions)

### Maximum Points Strategy
1. **Item Recognition Accuracy:** Each error = -10 points
   - Ensure good lighting
   - Hold items steady for 0.5s
   - Keep items 30-50cm from camera
   - Use duplicate detection cooldown (500ms)

2. **Gesture Recognition Accuracy:** Each error = -10 points
   - Clear hand gestures (open palm or closed fist)
   - Hold gesture for full 1 second
   - Avoid partial hand visibility
   - Use gesture cooldown (2s between triggers)

3. **Latency Requirements:** <1 second for both
   - Object detection: <500ms (achieved with TensorRT)
   - Gesture detection: <1s (with 1s hold requirement)
   - Use FP16 inference for speed

4. **UI Requirements:**
   - [x] Live camera feed with bounding boxes
   - [x] Puregold-style receipt interface
   - [x] Real-time receipt updates
   - [x] Session status indicators

5. **Audio Requirements:**
   - [x] Audible beep on item scan
   - [x] Optional TTS for item names
   - [x] Session start/end announcements
   - [x] Total amount announcement

---

## Troubleshooting

### Camera Issues
```bash
# List available cameras
ls /dev/video*

# Test specific camera
python3 pos_system.py --camera 1
```

### Low FPS
1. Verify TensorRT is enabled
2. Check GPU utilization: `sudo tegrastats`
3. Reduce camera resolution if needed
4. Lower target FPS: `python3 pos_system.py --fps 20`

### Detection Errors
- Improve lighting conditions
- Clean camera lens
- Adjust confidence threshold in `object_detector.py`
- Check if item is in products.json
- Verify model has class in training data

### Audio Problems
```bash
# Test audio output
speaker-test -t wav -c 2

# List audio devices
aplay -l

# Disable TTS if causing issues
python3 pos_system.py --no-tts
```

---

## Optimization Tips for Demo Day

### Lighting Setup
- Use bright, even lighting
- Avoid shadows on products
- No backlighting from windows
- LED lights recommended

### Camera Positioning
- Mount camera at 45-degree angle
- Height: 30-40cm above surface
- Distance: Products at 30-50cm from camera
- Stable mount (no wobbling)

### Product Presentation
- Present items one at a time
- Hold steady for at least 0.5 seconds
- Show product label to camera
- Avoid hand covering product

### Practice Workflow
1. Start session with open hand (hold 1s, wait for beep)
2. Pick up first item, show to camera
3. Wait for beep + announcement
4. Set down item, pick up next
5. Repeat for all items
6. Show closed fist (hold 1s) to end session
7. Listen for total announcement

---

## Files Summary

### Core Files (Must Transfer to Jetson)
```
me7/
├── best.pt                 # 5.4MB - Trained YOLOv8n model
├── products.json           # 34 products with prices
├── pos_system.py           # Main application
├── object_detector.py      # YOLO detection module
├── gesture_detector.py     # Hand gesture module
├── audio_manager.py        # Audio and TTS
├── pos_ui.py              # UI and receipt
├── requirements.txt        # Python dependencies
└── README.md              # Documentation
```

### Optional Files
```
me7/
├── jetson_deployment/     # Backup deployment files
├── DEPLOYMENT_CHECKLIST.md # This file
└── TESTING_GUIDE.md       # Testing procedures
```

---

## Quick Reference Commands

```bash
# Basic run
python3 pos_system.py

# Custom camera
python3 pos_system.py --camera 1

# Without TTS
python3 pos_system.py --no-tts

# Without TensorRT (for debugging)
python3 pos_system.py --no-tensorrt

# Custom model path
python3 pos_system.py --model /path/to/best.pt

# Lower FPS
python3 pos_system.py --fps 20

# Full options
python3 pos_system.py --model best.pt --products products.json --camera 0 --fps 30
```

---

## Success Indicators

### Before Demo
- [ ] System boots without errors
- [ ] Camera feed displays correctly
- [ ] Model loads successfully
- [ ] TensorRT optimization completes
- [ ] FPS shows 25-32
- [ ] Audio feedback works
- [ ] TTS announcements clear

### During Demo
- [ ] Session starts with open hand
- [ ] Items detected with <1s latency
- [ ] Receipt updates in real-time
- [ ] No duplicate detections
- [ ] Session ends with closed fist
- [ ] Total announced correctly

### Quality Metrics
- [ ] Object detection: >90% accuracy
- [ ] Gesture recognition: >90% accuracy
- [ ] Latency: <1s for both
- [ ] No crashes or freezes
- [ ] Audio clear and synchronized

---

## Contact & Support

**Instructor:** Check ME7 instructions PDF
**Documentation:** README.md in this directory
**Model Training:** See ME4_4_ME7.ipynb notebook

**Last Validation:** December 13, 2025
**Status:** Ready for deployment
**Version:** 1.0 (34 products, YOLOv8n)

---

## Final Checklist Before Demo

- [ ] Charged Jetson Orin (or power adapter ready)
- [ ] Camera connected and tested
- [ ] Speakers connected and tested
- [ ] All 34 products available for demo
- [ ] Lighting setup tested
- [ ] Camera position optimized
- [ ] Practice run completed successfully
- [ ] Backup plan ready (no-tensorrt mode)
- [ ] Confidence threshold tested
- [ ] Gesture hold time tested (1 second)

**Good luck with your demo! 🎉**
