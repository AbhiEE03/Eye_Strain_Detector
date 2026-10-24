# Eye Strain Detection System — Real-Time Computer Vision Desktop App

A real-time desktop application that monitors eye-strain indicators using your webcam — counting blinks, tracking blinks per minute, and checking screen proximity using MediaPipe's face landmark model (478 points: 468 face-mesh + 10 iris).

🔗 **GitHub:** [Eye_Strain_Detector](https://github.com/AbhiEE03/Eye_Strain_Detector)

> Built in a single day, learning MediaPipe from scratch.

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
- Runs in real time at the camera's rate (~30 FPS; see Performance below)

### Dynamic Personal Calibration

Fixed thresholds don't generalize — everyone's eyes open differently.

**Press `C`** → hold eyes open for 3 seconds → system records your personal open-eye baseline → sets detection threshold at **70% of your baseline**.

One interaction. Reduces false blinks caused by differences in eye shape between people (it does not fix head pose, glasses glare or low light).

### 3-Frame Consecutive State Machine

A single low-EAR frame isn't a blink — it could be a lighting change or head tilt.

A blink is only registered when EAR stays below threshold for **3+ consecutive frames**. This filters noise without missing real blinks.

### Low Blink-Rate Alert

Blinks per minute are computed over a rolling 60-second window and shown on the HUD. If the rate stays below **10/min for 2 minutes**, a "LOW BLINK RATE - TAKE A BREAK" banner appears. No alert in the first 60 s, during calibration, or while no face is visible.

The 10/min threshold is a configurable heuristic (normal is often quoted as ~15–20/min and drops during screen use), **not a medical standard**. Logic lives in `blink_rate.py` and is unit-tested.

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
| MediaPipe   | 478-point face landmark detection   |
| NumPy       | EAR mathematical computations       |
| PyInstaller | Packaging into standalone .exe      |

**Performance** (measured with `tools/measure_live.py`, 60 s live webcam, AMD Ryzen 5 5600H, 12 threads; no face in frame during this run):

| Metric | Value |
| --- | --- |
| Camera (from `cap.get`) | 640×480 @ 30 FPS |
| Full-loop FPS (capture → process → draw → display) | 29.7 (camera-limited) |
| App CPU | ~57% of one core ≈ 4.8% of total CPU |
| Model file | `face_landmarker.task`, 3.6 MB |

Numbers depend on your hardware and camera; re-run the script to measure yours.

---

## Engineering Challenges Solved

### 1. MediaPipe 0.10.30+ Breaking Change

MediaPipe removed the entire `mp.solutions` interface in v0.10.30+. Most tutorials online are now broken.

**Solution:** `try/except` version fallback — auto-detects the API version and switches to the Tasks API automatically (tested on MediaPipe 0.10.35, which has no `mp.solutions`).

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

MediaPipe loads native libraries and data files by path at runtime, so PyInstaller's import analysis misses them.

**Solution:** `main.spec` builds a one-file exe with `collect_all('mediapipe')` and bundles `face_landmarker.task`, so the exe runs offline from any folder. Build with:

```bash
python -m PyInstaller main.spec
```

(Equivalent CLI, which would overwrite `main.spec`: `pyinstaller --onefile --collect-all mediapipe --add-data "face_landmarker.task;." main.py`)

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
├── main.py                  ← App: capture, EAR, calibration, HUD
├── blink_rate.py            ← Rolling blinks/min + low-rate alert (pure logic)
├── tests/                   ← Unit tests (no camera needed)
├── tools/measure_live.py    ← Live FPS/CPU measurement
├── main.spec                ← PyInstaller one-file build (bundles the model)
├── face_landmarker.task     ← MediaPipe model (gitignored; auto-downloaded on first source run)
└── *.pdf                    ← Project reports
```

**Tests:** `python -m unittest discover -s tests -v`

---

## Demo

## https://drive.google.com/file/d/10Yf9vRVdlOZmBLfGuulfcUSph2n3WeCb/view?usp=sharing

## What I Learned

- MediaPipe's landmark detection pipeline and EAR formula implementation
- Why fixed thresholds fail in production and how dynamic calibration solves it
- Noise filtering with state machines in real-time signal processing
- Handling breaking API changes gracefully with version fallbacks
- Packaging Python applications as standalone executables
