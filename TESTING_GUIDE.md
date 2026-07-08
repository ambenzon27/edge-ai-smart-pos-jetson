# Testing and Optimization Guide

This guide helps you test and optimize the POS system for maximum accuracy during grading.

## Pre-Testing Checklist

### Hardware Setup
- [ ] Camera is securely mounted
- [ ] Camera is at appropriate height (chest level)
- [ ] Lighting is adequate and even
- [ ] No backlighting (light should be in front, not behind)
- [ ] Speakers are connected and working
- [ ] Jetson Orin is in MAX performance mode

### Software Setup
- [ ] All dependencies installed
- [ ] Model file (best.pt) is present
- [ ] Products.json is configured
- [ ] Camera permissions are granted
- [ ] Audio is working

### Jetson Performance Mode

```bash
# Set to maximum performance
sudo nvpmodel -m 0
sudo jetson_clocks

# Verify settings
sudo nvpmodel -q
```

## Testing Procedure

### 1. System Startup Test

```bash
# Run the system
python3 pos_system.py

# Expected output:
# - "Loading model..."
# - "Warming up model..."
# - "Model ready!"
# - "Camera initialized successfully!"
# - "POS SYSTEM RUNNING"
```

**Pass Criteria:**
- System starts without errors
- Camera feed appears
- FPS > 20

### 2. Object Detection Test

**Test Items:** Prepare 3-5 grocery items from your training set

**Procedure:**
1. Start a session (open hand gesture)
2. Present each item to the camera
3. Hold item steady for 1 second
4. Wait for beep before removing
5. Verify item appears on receipt

**Pass Criteria:**
- Detection latency < 1 second
- Correct item identified
- No duplicate scans
- Bounding box appears around item
- Beep sound plays

**Common Issues:**

| Issue | Solution |
|-------|----------|
| No detection | Move item closer (30-50cm) |
| Wrong item detected | Improve lighting, hold item steady |
| Multiple detections | Wait for cooldown period |
| Low confidence | Ensure good lighting, clear view |

### 3. Gesture Recognition Test

**Test Gestures:**
- Open hand (5 fingers extended)
- Closed fist (0 fingers extended)

**Procedure:**
1. Show open hand to camera
2. Hold for 1 second (watch progress bar)
3. Wait for "Session started" message
4. Show closed fist to camera
5. Hold for 1 second
6. Wait for "Session ended" message

**Pass Criteria:**
- Gesture detected within 1 second
- Visual progress bar appears
- Audio feedback plays
- Session state changes correctly
- No false triggers

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Hand not detected | Ensure hand is fully visible |
| Gesture not triggering | Hold for full 1 second |
| False triggers | Adjust gesture_hold_time in config |
| Progress bar jerky | Improve lighting on hand |

### 4. Full Workflow Test

**Complete Transaction:**

1. **Prepare:**
   - 5 different grocery items
   - Notebook to record results

2. **Execute:**
   ```
   START → Open hand gesture (hold 1s)
   ↓
   SCAN → Present item 1 (wait for beep)
   ↓
   SCAN → Present item 2 (wait for beep)
   ↓
   SCAN → Present item 3 (wait for beep)
   ↓
   SCAN → Present item 4 (wait for beep)
   ↓
   SCAN → Present item 5 (wait for beep)
   ↓
   END → Closed fist gesture (hold 1s)
   ```

3. **Verify:**
   - All 5 items on receipt
   - Correct prices
   - Total calculated correctly
   - All audio cues played

**Pass Criteria:**
- 100% item recognition accuracy
- 100% gesture recognition accuracy
- Total amount correct
- No system lag or freezing

## Optimization for Grading

### 1. Camera Setup

**Optimal Setup:**
- Distance: 30-50cm from items
- Angle: Perpendicular to items (90°)
- Lighting: 500-1000 lux (office lighting)
- Background: Plain, contrasting with items

**Camera Settings:**
```python
# In pos_system.py, adjust if needed:
self.camera.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # Default
self.camera.set(cv2.CAP_PROP_CONTRAST, 32)     # Default
self.camera.set(cv2.CAP_PROP_SATURATION, 64)   # Default
```

### 2. Detection Confidence

**If getting false positives:**
```python
# In object_detector.py, increase threshold:
ObjectDetector(conf_threshold=0.6)  # Default: 0.5
```

**If missing detections:**
```python
# Decrease threshold:
ObjectDetector(conf_threshold=0.4)  # Default: 0.5
```

### 3. Timing Adjustments

**If items scan too quickly (duplicates):**
```python
# In object_detector.py:
self.detection_cooldown = 1.0  # Default: 0.5
```

**If gestures trigger accidentally:**
```python
# In gesture_detector.py:
self.gesture_hold_time = 1.5  # Default: 1.0
```

### 4. Performance Tuning

**For Maximum Accuracy (lower FPS ok):**
```bash
python3 pos_system.py --fps 15
```

**For Maximum Speed:**
```bash
# Ensure TensorRT is enabled
python3 pos_system.py --fps 30
```

**Monitor Performance:**
```bash
# In another terminal, watch GPU usage:
watch -n 0.5 tegrastats
```

## Grading Day Checklist

### Before Testing
- [ ] Jetson in MAX performance mode
- [ ] All background processes closed
- [ ] Camera clean and focused
- [ ] Lighting optimal
- [ ] Audio volume appropriate
- [ ] Test run completed successfully

### During Testing
- [ ] Hold items steady for full 1 second
- [ ] Wait for beep before moving to next item
- [ ] Ensure hand is fully visible for gestures
- [ ] Hold gestures for full duration
- [ ] Watch for visual confirmations

### Emergency Troubleshooting

**System Running Slow:**
```bash
# Restart Jetson
sudo reboot

# Set max performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

**Camera Not Working:**
```bash
# Find camera
v4l2-ctl --list-devices

# Use correct ID
python3 pos_system.py --camera 1
```

**Model Not Loading:**
```bash
# Verify model
ls -lh best.pt

# Test without TensorRT
python3 pos_system.py --no-tensorrt
```

## Accuracy Improvement Tips

### Item Recognition

1. **Consistent Presentation:**
   - Always show same side of item
   - Keep item upright
   - Fill 50-70% of camera view
   - Avoid hand covering item

2. **Optimal Timing:**
   - Hold item for 1 full second
   - Keep item still during detection
   - Wait for beep before removing

3. **Environment:**
   - Remove clutter from background
   - Use consistent lighting
   - Avoid shadows on items
   - No reflective surfaces

### Gesture Recognition

1. **Clear Gestures:**
   - Fully open hand (spread fingers)
   - Fully closed fist (tight)
   - Hand perpendicular to camera
   - All fingers visible

2. **Positioning:**
   - Hand 30-40cm from camera
   - Center of frame
   - No obstruction
   - Good lighting on hand

3. **Timing:**
   - Hold gesture steady
   - Watch progress bar
   - Don't move until triggered

## Performance Benchmarks

### Target Metrics

| Metric | Target | Excellent |
|--------|--------|-----------|
| Item Recognition Accuracy | >90% | >95% |
| Gesture Recognition Accuracy | >90% | >95% |
| Detection Latency | <1s | <500ms |
| System FPS | >15 | >25 |
| False Positives | <5% | <2% |

### Measurement

**Record During Testing:**
```
Total Items Presented: ___
Correct Detections: ___
Incorrect Detections: ___
Missed Detections: ___
Accuracy: ___%

Total Gestures: ___
Correct Triggers: ___
False Triggers: ___
Missed Triggers: ___
Accuracy: ___%
```

## Common Failure Modes

### Object Detection Failures

1. **Item Not in Training Set**
   - Symptom: No detection or wrong item
   - Fix: Only test with trained items

2. **Poor Lighting**
   - Symptom: Low confidence, missed detections
   - Fix: Add more light, avoid shadows

3. **Item Too Far/Close**
   - Symptom: No detection
   - Fix: Maintain 30-50cm distance

4. **Motion Blur**
   - Symptom: Detections appear/disappear
   - Fix: Hold item perfectly still

### Gesture Failures

1. **Partial Hand Visible**
   - Symptom: No detection
   - Fix: Ensure entire hand is in frame

2. **Fingers Partially Closed**
   - Symptom: Gesture not recognized
   - Fix: Fully open or fully close hand

3. **Insufficient Hold Time**
   - Symptom: Progress bar doesn't fill
   - Fix: Hold for full duration

4. **Hand Too Close**
   - Symptom: Landmarks not detected
   - Fix: Move hand back 30-40cm

## Final Recommendations

1. **Practice First**
   - Do at least 3 complete test runs
   - Record accuracy for each run
   - Identify and fix weak points

2. **Have Backup Plan**
   - Know how to disable TensorRT
   - Know how to change camera
   - Know how to adjust thresholds

3. **Stay Calm During Grading**
   - If detection fails, adjust position
   - If gesture fails, try again
   - System is designed to be forgiving

4. **Maximum Points Strategy**
   - Accuracy is everything
   - Take your time with each item
   - Verify each detection before proceeding
   - Watch visual feedback constantly

## Quick Reference Commands

```bash
# Standard run
python3 pos_system.py

# Maximum accuracy mode
python3 pos_system.py --fps 15 --no-tensorrt

# Debug mode (no TTS, slower but more reliable)
python3 pos_system.py --no-tts --fps 20

# Quick start script
./run_pos.sh

# Check system status
sudo tegrastats

# Set max performance
sudo nvpmodel -m 0 && sudo jetson_clocks
```

Good luck with your grading! 🎯
