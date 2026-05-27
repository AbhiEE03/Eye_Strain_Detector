# 👁️ Digital Eye Strain Detection System

A real-time eye strain monitoring system using computer vision and facial landmark detection. Built with Python, OpenCV, and MediaPipe.

## Features

- 👁️ **Blink Rate Monitoring** — Counts blinks using Eye Aspect Ratio (EAR)
- 📏 **Proximity Detection** — Warns when you're too close to the screen
- 📊 **Live EAR Graph** — Real-time EAR trend visualization on screen
- 🎯 **Calibration** — Personalized blink threshold calibration
- ⚡ **FPS Display** — Live performance counter

## Demo

The HUD displays:

- Blink count
- EAR value vs. threshold
- Distance status (OK / TOO CLOSE)
- Live FPS
- Real-time EAR waveform graph

## Requirements

- Python 3.8+
- Webcam

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Eye_Strain_System.git
cd Eye_Strain_System

# Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

> **Note:** The MediaPipe face landmark model (`face_landmarker.task`, ~6 MB) will be **automatically downloaded** on first run if not present.

## Usage

```bash
python main.py
```

### Keyboard Controls

| Key   | Action                                                    |
| ----- | --------------------------------------------------------- |
| `C`   | Start calibration (keep eyes open normally for 3 seconds) |
| `ESC` | Quit                                                      |

## How It Works

1. **Face Detection** — Uses MediaPipe FaceLandmarker (or legacy `face_mesh` API) to detect 478 facial landmarks in real time.
2. **EAR Calculation** — Eye Aspect Ratio is computed from 6 key eye landmarks per eye. A drop below the threshold signals a blink.
3. **Proximity Estimation** — The horizontal distance between cheek landmarks is used to estimate how close the face is to the camera.
4. **Calibration** — Press `C` to sample your personal open-eye EAR baseline. The blink threshold is set to 70% of that baseline.

## Tech Stack

| Library         | Purpose                   |
| --------------- | ------------------------- |
| `opencv-python` | Video capture & rendering |
| `mediapipe`     | Face landmark detection   |
| `numpy`         | EAR computation           |

## Project Structure

```
Eye_Strain_System/
├── main.py            # Main application
├── main.spec          # PyInstaller build spec
├── requirements.txt   # Python dependencies
└── README.md
```

## License

This project was developed as an academic project for the 6th Semester Deep Learning course.
