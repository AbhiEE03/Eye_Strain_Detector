# Eye Strain Detection System

A real-time desktop app that watches for eye-strain indicators through your webcam. It counts blinks, tracks your blink rate, warns when that rate stays low, and warns when you sit too close to the screen. It runs locally with Python, OpenCV and MediaPipe's Face Landmarker (478 landmarks: 468 face-mesh points + 10 iris points), and the Windows exe works fully offline.

**GitHub:** [Eye_Strain_Detector](https://github.com/AbhiEE03/Eye_Strain_Detector) · **Demo video:** [Google Drive](https://drive.google.com/file/d/10Yf9vRVdlOZmBLfGuulfcUSph2n3WeCb/view?usp=sharing)

---

## Features

### Blink detection with the Eye Aspect Ratio (EAR)

```
EAR = (||p2 − p6|| + ||p3 − p5||) / (2 × ||p1 − p4||)
```

- 6 landmarks per eye. Left: `[33, 160, 158, 133, 153, 144]`, right: `[362, 385, 387, 263, 373, 380]`
- The EAR of both eyes is averaged every frame.

### 3-frame state machine

A single low-EAR frame might be noise, so it isn't counted. A blink is counted only when EAR stays below the threshold for **3 or more consecutive frames** and then rises above it again. At 30 FPS that is a closure of at least ~100 ms.

### Personal calibration (70% of baseline)

Press **`C`** and keep your eyes open normally for 3 seconds. The app averages your open-eye EAR and sets the blink threshold to **70% of that baseline**. Until you calibrate, the threshold is the default **0.210** (shown on the HUD as `thr 0.210`). The console prints `[CALIB] Baseline=… Threshold=…` when calibration finishes. Calibration adapts to individual eye shape. It does not compensate for head pose, glasses glare or poor lighting.

### Blink rate and low-blink alert

- The blink rate is counted over a **rolling 60-second window** and shown on the HUD.
- If it stays below **10 blinks/min for 2 minutes**, a "LOW BLINK RATE - TAKE A BREAK" banner appears.
- The alert is paused for the first 60 s, during calibration and whenever no face is visible.
- 10/min is a configurable heuristic (normal is often quoted as ~15–20/min). It is **not a medical standard**.
- The logic lives in [`blink_rate.py`](blink_rate.py) and is unit-tested.

### Proximity alert

When face width (landmarks 234 → 454) exceeds 28% of the frame width, a "MOVE BACK FROM SCREEN" banner appears. This is a relative heuristic, not a calibrated distance in cm.

### HUD

Blink count, EAR and threshold, distance status, FPS, blinks/min, and a live EAR sparkline with the threshold line.

---

## Measured results

From my own testing on an AMD Ryzen 5 5600H laptop. Numbers will differ on other hardware.

| What | Result |
| --- | --- |
| Camera (read back with `cap.get`) | 640×480 @ 30 FPS |
| Full-loop FPS (capture → process → draw → display), face in frame | ~30 (HUD showed 29.3–31.6), limited by the camera |
| Eye Aspect Ratio on the HUD | ~0.30–0.34 eyes open, ~0.07 eyes closed (shown in red) |
| Calibration (press `C`) | Threshold moved from the 0.210 default to 0.207 and 0.201 in separate runs |
| Natural blinking, 2-minute sessions vs. a person counting | Counts matched (9 vs 9, 6 vs 6) |
| Deliberate fast blinking | 62 blinks/min counted |
| Low-blink banner | Appears as designed (tested with the threshold temporarily raised to 30/min) |
| Exe startup (launch → window shown, one-file exe, empty folder) | ~7.5 s typical (6.6–10.6 s over 6 runs) |
| Exe offline | Works with Wi-Fi off, run from an empty folder |

The blink checks are a small manual sanity test with one person, not a formal accuracy evaluation.

---

## Run it

### From source

```bash
git clone https://github.com/AbhiEE03/Eye_Strain_Detector.git
cd Eye_Strain_Detector
pip install -r requirements.txt
python main.py
```

The model file `face_landmarker.task` (3.6 MB) isn't committed. A source run downloads it once from Google's MediaPipe model storage and saves it next to `main.py`.

**Controls:** `C` calibrate · `ESC` quit. The camera is always released (`try/finally`).

### Build the standalone exe (Windows)

```bash
pip install pyinstaller
python main.py                       # once, so face_landmarker.task exists locally
python -m PyInstaller main.spec
```

This produces `dist/main.exe`, a one-file build. [`main.spec`](main.spec) collects MediaPipe's native files (`collect_all('mediapipe')`) and bundles `face_landmarker.task`. At runtime the exe reads the model from PyInstaller's unpack folder (`sys._MEIPASS`), so it runs from any folder and never downloads the model.

### Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover the rolling window, warm-up, sustained-low alert, recovery, pause and configurable thresholds. They use fake timestamps, so they need no camera.

To measure FPS on your own machine, run `tools/measure_live.py`. It is a dev-only tool and needs `pip install psutil`.

---

## Implementation notes

- **MediaPipe API change.** `mp.solutions` (legacy FaceMesh) is gone in recent MediaPipe releases. The app uses legacy FaceMesh if it exists, otherwise the Tasks `FaceLandmarker` in VIDEO mode. `requirements.txt` asks for `mediapipe>=0.10.30`; tested on 0.10.35, which uses the Tasks path.
- **Windows startup.** OpenCV's Media Foundation backend can stall for several seconds while it sets up hardware transforms when the webcam opens. `main.py` sets `OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS=0` before importing `cv2`.
- **Honest FPS.** The HUD's FPS is the number of full loops in the last second (start-to-start), so drawing and display time are included.
- **Offline and privacy.** Frames are processed in memory and never saved or uploaded. The exe bundles the model and works fully offline (verified with Wi-Fi off). MediaPipe itself may still try to send usage telemetry; offline, that fails silently. The app's own code makes no network requests except the one-time model download in a source checkout.

---

## Project structure

```
main.py                ← capture, EAR, state machine, calibration, proximity, HUD
blink_rate.py          ← rolling blinks/min + sustained low-rate alert (pure logic)
tests/                 ← unit tests for blink_rate.py
tools/measure_live.py  ← live FPS measurement of the real loop
main.spec              ← PyInstaller one-file build (bundles the model)
*.pdf                  ← project reports
```

## Limitations

- EAR thresholds can misfire with strong head turns, glasses glare or low light.
- Proximity uses face width relative to the frame, so it isn't an absolute distance.
- Blink accuracy has only been sanity-checked by hand (see above), not evaluated on a labelled dataset.
