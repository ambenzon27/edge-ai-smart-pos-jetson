# System Architecture

Detailed architecture documentation for the POS system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      POS SYSTEM                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Camera     │  │   Display    │  │   Audio      │      │
│  │   Input      │  │   Output     │  │   Output     │      │
│  └──────┬───────┘  └──────▲───────┘  └──────▲───────┘      │
│         │                  │                  │              │
│         ▼                  │                  │              │
│  ┌──────────────────────────────────────────────────┐       │
│  │          Main Application (pos_system.py)        │       │
│  │                                                   │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐│       │
│  │  │   Frame     │  │   Session   │  │   UI     ││       │
│  │  │   Capture   │  │   Control   │  │  Render  ││       │
│  │  └─────────────┘  └─────────────┘  └──────────┘│       │
│  └──────────────────────────────────────────────────┘       │
│         │                  │                  │              │
│    ┌────┴────┐        ┌────┴────┐       ┌────┴────┐        │
│    ▼         ▼        ▼         ▼       ▼         ▼        │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐     │
│  │ Obj │  │ Ges │  │Audio│  │ UI  │  │Prod │  │Queue│     │
│  │ Det │  │ Det │  │ Mgr │  │ Mgr │  │ DB  │  │ Mgr │     │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Main Application (pos_system.py)

```
┌───────────────────────────────────────────────────────┐
│              POSSystem Class                          │
├───────────────────────────────────────────────────────┤
│                                                        │
│  Main Thread:                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Camera Capture (30 FPS)                  │    │
│  │  2. Frame Distribution                       │    │
│  │  3. Result Collection                        │    │
│  │  4. UI Rendering                             │    │
│  │  5. User Input Handling                      │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Detection Thread:                                    │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Get frame from queue                     │    │
│  │  2. Run object detection                     │    │
│  │  3. Put results in queue                     │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Gesture Thread:                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Get frame from queue                     │    │
│  │  2. Run gesture detection                    │    │
│  │  3. Trigger session events                   │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Audio Thread:                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Get audio event from queue               │    │
│  │  2. Play beep or TTS                         │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

### 2. Object Detection (object_detector.py)

```
┌───────────────────────────────────────────────────────┐
│           ObjectDetector Class                        │
├───────────────────────────────────────────────────────┤
│                                                        │
│  Initialization:                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Load YOLOv8 model                        │    │
│  │  2. Export to TensorRT (optional)            │    │
│  │  3. Warm up model                            │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Detection Pipeline:                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │  Frame → Preprocess → Inference → NMS        │    │
│  │         → Filter by conf → Return results    │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Optimization:                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │  • FP16 precision                            │    │
│  │  • TensorRT engine                           │    │
│  │  • GPU execution                             │    │
│  │  • Duplicate prevention                      │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

### 3. Gesture Detection (gesture_detector.py)

```
┌───────────────────────────────────────────────────────┐
│         GestureDetector Class                         │
├───────────────────────────────────────────────────────┤
│                                                        │
│  Initialization:                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Initialize MediaPipe Hands               │    │
│  │  2. Set confidence thresholds                │    │
│  │  3. Configure tracking                       │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Detection Pipeline:                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │  Frame → RGB Convert → MediaPipe             │    │
│  │       → Landmark Detection → Classify        │    │
│  │       → Temporal Filter → Trigger            │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Gesture Classification:                              │
│  ┌──────────────────────────────────────────────┐    │
│  │  • Count extended fingers                    │    │
│  │  • 4-5 fingers = Open hand                   │    │
│  │  • 0-1 fingers = Closed fist                 │    │
│  │  • 1 second hold = Trigger                   │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

### 4. Audio Manager (audio_manager.py)

```
┌───────────────────────────────────────────────────────┐
│          AudioManager Class                           │
├───────────────────────────────────────────────────────┤
│                                                        │
│  Initialization:                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Initialize pygame mixer                  │    │
│  │  2. Initialize pyttsx3 engine                │    │
│  │  3. Generate beep sounds                     │    │
│  │  4. Start audio worker thread                │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Audio Queue:                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │  Event → Queue → Worker Thread → Playback    │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Beep Types:                                          │
│  ┌──────────────────────────────────────────────┐    │
│  │  • Item scanned: 1000Hz, 100ms               │    │
│  │  • Session start: 800Hz, 150ms               │    │
│  │  • Session end: 600Hz, 200ms                 │    │
│  │  • Error: 400Hz, 300ms                       │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

### 5. POS UI (pos_ui.py)

```
┌───────────────────────────────────────────────────────┐
│              POSUI Class                              │
├───────────────────────────────────────────────────────┤
│                                                        │
│  Display Layout (1280x720):                           │
│  ┌──────────────────────────────────────────────┐    │
│  │ ┌────────────┬─────────────────────────┐     │    │
│  │ │            │  PUREGOLD POS           │     │    │
│  │ │            ├─────────────────────────┤     │    │
│  │ │  Camera    │  SESSION ACTIVE         │     │    │
│  │ │  Feed      ├─────────────────────────┤     │    │
│  │ │  832x720   │  ITEMS:                 │     │    │
│  │ │            │  1x Apple      P25.00   │     │    │
│  │ │  [Live     │  2x Banana     P30.00   │     │    │
│  │ │   Video]   │  1x Orange     P20.00   │     │    │
│  │ │            ├─────────────────────────┤     │    │
│  │ │            │  TOTAL:       P75.00    │     │    │
│  │ │            ├─────────────────────────┤     │    │
│  │ │            │  FPS: 28.5              │     │    │
│  │ └────────────┴─────────────────────────┘     │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
│  Receipt Management:                                  │
│  ┌──────────────────────────────────────────────┐    │
│  │  • Add items                                 │    │
│  │  • Update quantities                         │    │
│  │  • Calculate totals                          │    │
│  │  • Session control                           │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

## Data Flow

### Frame Processing Pipeline

```
Camera Capture (30 FPS)
    │
    ▼
┌─────────────────┐
│  Raw Frame      │
│  1280x720 BGR   │
└────────┬────────┘
         │
         ├──────────────────────┬──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
  ┌──────────┐          ┌──────────┐          ┌──────────┐
  │ Object   │          │ Gesture  │          │ Display  │
  │ Detection│          │ Detection│          │ Rendering│
  │ Queue    │          │ Queue    │          │          │
  └────┬─────┘          └────┬─────┘          └────┬─────┘
       │                     │                      │
       ▼                     ▼                      │
  ┌──────────┐          ┌──────────┐               │
  │ YOLOv8   │          │MediaPipe │               │
  │ Inference│          │  Hands   │               │
  └────┬─────┘          └────┬─────┘               │
       │                     │                      │
       ▼                     ▼                      │
  ┌──────────┐          ┌──────────┐               │
  │Detection │          │ Gesture  │               │
  │ Results  │          │ Results  │               │
  └────┬─────┘          └────┬─────┘               │
       │                     │                      │
       └──────────┬──────────┴──────────────────────┘
                  │
                  ▼
           ┌──────────────┐
           │  Combine &   │
           │   Render     │
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │   Display    │
           │   1280x720   │
           └──────────────┘
```

### Session State Machine

```
┌─────────────┐
│   IDLE      │
│  (No Session)│
└──────┬──────┘
       │
       │ Open Hand (1s)
       ▼
┌─────────────┐
│   ACTIVE    │──────┐
│  (Scanning) │      │ Item Detected
└──────┬──────┘      │
       │             ▼
       │      ┌─────────────┐
       │      │  Add Item   │
       │      │  to Receipt │
       │      └─────────────┘
       │
       │ Closed Fist (1s)
       ▼
┌─────────────┐
│   ENDED     │
│(Show Total) │
└──────┬──────┘
       │
       │ Auto-reset
       ▼
┌─────────────┐
│   IDLE      │
└─────────────┘
```

## Threading Model

### Thread Synchronization

```
Main Thread
┌────────────────────────────────────────┐
│                                        │
│  Camera Capture                        │
│  ┌──────────────────────────────┐     │
│  │  while running:              │     │
│  │    frame = camera.read()     │     │
│  │    frame_queue.put(frame)    │     │
│  │    gesture_queue.put(frame)  │     │
│  │    ...                       │     │
│  └──────────────────────────────┘     │
└────────────────────────────────────────┘
         │              │
         ▼              ▼
    Queue(2)       Queue(2)
         │              │
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│ Detection    │  │  Gesture     │
│ Thread       │  │  Thread      │
│              │  │              │
│  Get frame   │  │  Get frame   │
│  Process     │  │  Process     │
│  Put result  │  │  Trigger?    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
  Result Queue    Event Trigger
       │                 │
       └────────┬────────┘
                ▼
         ┌─────────────┐
         │ Audio Queue │
         └──────┬──────┘
                ▼
         ┌─────────────┐
         │Audio Thread │
         │  Play beep  │
         │  or TTS     │
         └─────────────┘
```

## Performance Optimization

### 1. GPU Utilization

```
┌─────────────────────────────────────┐
│          Jetson Orin GPU            │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────┐     │
│  │  YOLOv8 Inference         │ 60% │
│  └───────────────────────────┘     │
│                                     │
│  ┌──────────────┐                  │
│  │  MediaPipe   │ 15%              │
│  └──────────────┘                  │
│                                     │
│  ┌─────────┐                       │
│  │ OpenCV  │ 5%                    │
│  └─────────┘                       │
│                                     │
│  Idle: 20%                          │
│                                     │
└─────────────────────────────────────┘
```

### 2. Memory Management

```
Total Memory: ~2GB

┌─────────────────────────────────────┐
│  Model Weights (YOLO)       800 MB  │
├─────────────────────────────────────┤
│  Frame Buffers              200 MB  │
├─────────────────────────────────────┤
│  MediaPipe Models           300 MB  │
├─────────────────────────────────────┤
│  UI Buffers                 100 MB  │
├─────────────────────────────────────┤
│  Python Runtime             400 MB  │
├─────────────────────────────────────┤
│  System/Other               200 MB  │
└─────────────────────────────────────┘
```

### 3. Latency Breakdown

```
Total System Latency: ~500ms

┌─────────────────────────────────────┐
│  Camera Capture          33ms (30Hz)│
├─────────────────────────────────────┤
│  Queue Transfer          5ms        │
├─────────────────────────────────────┤
│  Object Detection        100-200ms  │
├─────────────────────────────────────┤
│  Gesture Detection       50-100ms   │
├─────────────────────────────────────┤
│  UI Rendering           20ms        │
├─────────────────────────────────────┤
│  Display Update         16ms (60Hz) │
└─────────────────────────────────────┘
```

## Scalability

### Current Capacity
- **Throughput**: 30 FPS camera, 20-30 FPS processing
- **Concurrent Users**: 1 (single camera)
- **Items per Session**: Unlimited
- **Session Duration**: Unlimited

### Extension Points
- Multiple camera support (multi-threading)
- Database integration (SQLite/PostgreSQL)
- Network communication (REST API)
- Cloud synchronization
- Multiple product categories
- Multi-language support

## Security Considerations

1. **Local Processing**: All data processed locally
2. **No Network**: No external network access required
3. **No Storage**: No persistent storage of images
4. **Privacy**: No personal data collection

## Reliability

### Error Handling
- Camera failure → Graceful shutdown with error message
- Model loading failure → Fallback to non-TensorRT
- Detection failure → Continue processing
- Audio failure → Silent mode, continue processing
- Queue overflow → Drop oldest frames

### Recovery Mechanisms
- Thread restart on crash
- Automatic resource cleanup
- Graceful degradation
- User notification

## Monitoring and Debugging

### Built-in Monitoring
- Real-time FPS counter
- Inference time display
- Queue size monitoring
- GPU utilization (tegrastats)

### Debug Output
- Detection results logging
- Gesture events logging
- Session state changes
- Performance metrics

---

This architecture is designed for:
- ✅ High performance (<1s latency)
- ✅ Reliability (error handling)
- ✅ Maintainability (modular design)
- ✅ Extensibility (clear interfaces)
- ✅ Efficiency (optimized for Jetson)
