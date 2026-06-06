# Eye Strain Detection System — Real-Time Computer Vision Desktop App

A real-time desktop application that monitors eye strain using your webcam — detecting blink rate, eye closure patterns, and screen proximity using MediaPipe's 468-point facial landmark model.

🔗 **GitHub:** [Eye_Strain_Detector](https://github.com/AbhiEE03/Eye_Strain_Detector)

> Built in a single day, learning MediaPipe from scratch. Tested across multiple systems — consistent accuracy.

---

## The Problem

Most developers stare at screens for hours without blinking normally. No tool existed that could run locally, adapt to your personal eye baseline, and alert you in real time — without requiring any setup.

---

## Key Features

### Real-Time EAR (Eye Aspect Ratio) Detection

```
EAR = (||p2−p6|| + ||p3−p5||) / (2 × ||p1−p4||)
```

- Uses 6 MediaPipe landmarks per eye
- Left eye: `[33, 160, 158, 133, 153, 144]`
- Right eye: `[362, 385, 387, 263, 373, 380]`
- Both eyes averaged for final EAR value
- Runs at **~40 FPS** on standard hardware

### Dynamic Personal Calibration

Fixed thresholds don't generalize — everyone's eyes open differently.

**Press `C`** → hold eyes open for 3 seconds → system records your personal open-eye baseline → sets detection threshold at **70% of your baseline**.

One interaction. Eliminates false positives entirely.

### 3-Frame Consecutive State Machine

A single low-EAR frame isn't a blink — it could be a lighting change or head tilt.

A blink is only registered when EAR stays below threshold for **3+ consecutive frames**. This filters noise without missing real blinks.

### Screen Proximity Alert

Estimates face-to-screen distance using face width relative to frame width. Triggers a **"TOO CLOSE"** banner when you sit dangerously close.

### Live EAR Sparkline

A real-time mini graph of your eye openness history, rendered directly on the HUD.

---

## Tech Stack

| Tool        | Purpose                             |
| ----------- | ----------------------------------- |
| Python 3.13 | Core language                       |
| OpenCV      | Webcam capture & HUD rendering      |
| MediaPipe   | 468-point facial landmark detection |
| NumPy       | EAR mathematical computations       |
| PyInstaller | Packaging into standalone .exe      |

**Performance:** ~40 FPS · <15% CPU · 6MB MediaPipe model

---

## Engineering Challenges Solved

### 1. MediaPipe 0.10.30+ Breaking Change

MediaPipe removed the entire `mp.solutions` interface in v0.10.30+. Most tutorials online are now broken.

**Solution:** `try/except` version fallback — auto-detects the API version and switches to the Tasks API automatically. Works on any MediaPipe version.

```python
try:
    # Legacy API
    import mediapipe as mp
    face_mesh = mp.solutions.face_mesh.FaceMesh(...)
except AttributeError:
    # Tasks API (v0.10.30+)
    from mediapipe.tasks.python import vision
    ...
```

### 2. PyInstaller + MediaPipe Packaging

MediaPipe's C extensions are not auto-detected by PyInstaller.

**Solution:**

```bash
pyinstaller --collect-all mediapipe main.py
```

### 3. Cross-System Accuracy

Tested across multiple machines with different lighting conditions, webcam qualities, and face structures. Dynamic calibration ensures consistent accuracy regardless of setup.

---

## Running the App

### Option 1: Standalone .exe (No Python Required)

1. Download the latest release
2. Extract the zip
3. Run `main.exe`

### Option 2: From Source

```bash
git clone https://github.com/AbhiEE03/Eye_Strain_Detector.git
cd Eye_Strain_Detector
pip install opencv-python mediapipe numpy
python main.py
```

**Controls:**

- `C` — Calibrate to your personal baseline
- `ESC` — Exit (camera always released cleanly via try/finally)

---

## Project Structure

```
Eye_Strain_System/
├── main.py                  ← Full source (296 lines)
├── face_landmarker.task     ← MediaPipe model file
├── dist/
│   └── main.exe             ← Standalone Windows app
└── report.pdf               ← Project report
```

---

## Demo

## https://drive.google.com/file/d/10Yf9vRVdlOZmBLfGuulfcUSph2n3WeCb/view?usp=sharing

## What I Learned

- MediaPipe's landmark detection pipeline and EAR formula implementation
- Why fixed thresholds fail in production and how dynamic calibration solves it
- Noise filtering with state machines in real-time signal processing
- Handling breaking API changes gracefully with version fallbacks
- Packaging Python applications as standalone executables
