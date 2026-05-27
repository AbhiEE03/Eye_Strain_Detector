# =============================================================================
# requirements.txt:
#   opencv-python>=4.8.0
#   mediapipe>=0.10.30
#   numpy>=1.24.0
# Run:  python main.py  |  C = calibrate  |  ESC = quit
# =============================================================================

# To remove the noisy messages

from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks import python as mp_python

import mediapipe as mp
from collections import deque
import time
import numpy as np
import cv2
import os
os.environ["GLOG_minloglevel"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


EAR_CONSEC_FRAMES = 3
CALIB_DURATION_SEC = 3
CALIB_THRESHOLD_PCT = 0.70
DIST_THRESHOLD = 0.28
FACE_W_LANDMARKS = (234, 454)
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
COL_GREEN = (0,   220,  80)
COL_YELLOW = (0,   220, 220)
COL_RED = (30,   30, 220)
COL_WHITE = (240, 240, 240)
COL_DARK = (20,   20,  20)


def _dist(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def compute_ear(landmarks, indices, w, h):
    pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices]
    p1, p2, p3, p4, p5, p6 = pts
    vert1 = _dist(p2, p6)
    vert2 = _dist(p3, p5)
    horiz = _dist(p1, p4)
    if horiz < 1e-6:
        return 0.0
    return (vert1 + vert2) / (2.0 * horiz)


class EyeStrainDetector:

    def __init__(self, camera_index=0):
        self._use_legacy = False
        try:
            fm = mp.solutions.face_mesh
            self.face_mesh = fm.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._use_legacy = True
            print("[INFO] Using legacy MediaPipe face_mesh API.")
        except AttributeError:
            print("[INFO] Legacy API unavailable — using Tasks API.")
            self._init_tasks_api()

        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.blink_count = 0
        self.consec_below = 0
        self.ear_history = deque(maxlen=90)
        self.ear_threshold = 0.21
        self.baseline_ear = None
        self.calibrating = False
        self.calib_samples = []
        self.calib_start_time = 0.0
        self.fps_counter = deque(maxlen=30)

    def _init_tasks_api(self):
        import urllib.request
        import os
        model_path = "face_landmarker.task"
        if not os.path.exists(model_path):
            print("[INFO] Downloading face_landmarker model (~6 MB) ...")
            urllib.request.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
                "face_landmarker/float16/1/face_landmarker.task",
                model_path,
            )
            print("[INFO] Download complete.")
        base_opts = mp_python.BaseOptions(model_asset_path=model_path)
        opts = FaceLandmarkerOptions(
            base_options=base_opts,
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.face_landmarker = FaceLandmarker.create_from_options(opts)

    def _get_landmarks(self, rgb, frame_idx):
        if self._use_legacy:
            rgb.flags.writeable = False
            res = self.face_mesh.process(rgb)
            rgb.flags.writeable = True
            if res.multi_face_landmarks:
                return res.multi_face_landmarks[0].landmark
        else:
            ts = int(frame_idx * (1000 / 30))
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = self.face_landmarker.detect_for_video(img, ts)
            if res.face_landmarks:
                return res.face_landmarks[0]
        return None

    def start_calibration(self):
        self.calibrating = True
        self.calib_samples = []
        self.calib_start_time = time.time()
        print("[CALIB] Keep eyes open normally ...")

    def update_calibration(self, ear):
        self.calib_samples.append(ear)
        if time.time() - self.calib_start_time >= CALIB_DURATION_SEC:
            if self.calib_samples:
                self.baseline_ear = float(np.mean(self.calib_samples))
                self.ear_threshold = self.baseline_ear * CALIB_THRESHOLD_PCT
                print(
                    f"[CALIB] Baseline={self.baseline_ear:.4f}  Threshold={self.ear_threshold:.4f}")
            self.calibrating = False

    @staticmethod
    def estimate_proximity(lm, fw, fh):
        lx = lm[FACE_W_LANDMARKS[0]].x * fw
        rx = lm[FACE_W_LANDMARKS[1]].x * fw
        return "TOO CLOSE" if abs(rx - lx) / fw > DIST_THRESHOLD else "OK"

    def draw_hud(self, frame, avg_ear, prox, fps):
        h, w = frame.shape[:2]
        ov = frame.copy()
        cv2.rectangle(ov, (0, 0), (320, 160), COL_DARK, -1)
        cv2.addWeighted(ov, 0.55, frame, 0.45, 0, frame)
        f, fb = cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, "EYE STRAIN DETECTOR", (10, 22),
                    fb, 0.55, COL_GREEN, 1, cv2.LINE_AA)
        cv2.putText(frame, f"Blinks : {self.blink_count}",
                    (10, 52), f, 0.55, COL_WHITE, 1, cv2.LINE_AA)
        ecol = COL_RED if avg_ear < self.ear_threshold else COL_WHITE
        cv2.putText(frame, f"EAR    : {avg_ear:.3f}  (thr {self.ear_threshold:.3f})", (
            10, 77), f, 0.50, ecol, 1, cv2.LINE_AA)
        pcol = COL_RED if prox == "TOO CLOSE" else COL_GREEN
        cv2.putText(frame, f"Dist   : {prox}",
                    (10, 102), f, 0.55, pcol, 1, cv2.LINE_AA)
        cv2.putText(frame, f"FPS    : {fps:.1f}",
                    (10, 127), f, 0.48, COL_YELLOW, 1, cv2.LINE_AA)
        if self.calibrating:
            rem = max(0, CALIB_DURATION_SEC -
                      (time.time() - self.calib_start_time))
            cv2.putText(
                frame, f"CALIBRATING ... {rem:.1f}s", (10, h - 40), fb, 0.65, COL_YELLOW, 2, cv2.LINE_AA)
        cv2.putText(frame, "[C] Calibrate  [ESC] Quit", (10,
                    h - 10), f, 0.40, (160, 160, 160), 1, cv2.LINE_AA)
        if prox == "TOO CLOSE":
            cv2.rectangle(frame, (0, h - 45), (w, h), (0, 0, 180), -1)
            cv2.putText(frame, "  MOVE BACK FROM SCREEN  ", (w //
                        2 - 195, h - 15), fb, 0.75, COL_WHITE, 2, cv2.LINE_AA)
        if len(self.ear_history) > 1:
            pts = list(self.ear_history)
            mn, mx = min(pts), max(pts)
            sx, sy, sw, sh = w - 170, 10, 160, 60
            cv2.rectangle(frame, (sx, sy), (sx + sw, sy + sh),
                          (40, 40, 40), -1)
            for i in range(1, len(pts)):
                def sc(v, _mn=mn, _mx=mx):
                    return sy + sh // 2 if _mx == _mn else int(sy + sh - (v - _mn) / (_mx - _mn) * sh)
                x1 = sx + int((i-1) / (len(pts)-1) * sw)
                x2 = sx + int(i / (len(pts)-1) * sw)
                cv2.line(
                    frame, (x1, sc(pts[i-1])), (x2, sc(pts[i])), COL_GREEN, 1, cv2.LINE_AA)
            if mx != mn:
                ty = int(sy + sh - (self.ear_threshold - mn) / (mx - mn) * sh)
                cv2.line(frame, (sx, ty), (sx + sw, ty),
                         COL_RED, 1, cv2.LINE_AA)
            cv2.putText(frame, "EAR", (sx + 2, sy + 10), f,
                        0.35, (180, 180, 180), 1, cv2.LINE_AA)

    def run(self):
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera.")
        print("Started.  C = Calibrate  |  ESC = Quit")
        cv2.namedWindow("Digital Eye Strain Detection System",
                        cv2.WINDOW_NORMAL)
        idx = 0
        try:
            while True:
                t0 = time.perf_counter()
                ret, frame = self.cap.read()
                if not ret:
                    continue
                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                lm = self._get_landmarks(rgb, idx)
                idx += 1
                avg_ear, prox = 0.0, "NO FACE"
                if lm:
                    l = compute_ear(lm, LEFT_EYE_IDX,  w, h)
                    r = compute_ear(lm, RIGHT_EYE_IDX, w, h)
                    avg_ear = (l + r) / 2.0
                    self.ear_history.append(avg_ear)
                    prox = self.estimate_proximity(lm, w, h)
                    if self.calibrating:
                        self.update_calibration(avg_ear)
                    else:
                        if avg_ear < self.ear_threshold:
                            self.consec_below += 1
                        else:
                            if self.consec_below >= EAR_CONSEC_FRAMES:
                                self.blink_count += 1
                            self.consec_below = 0
                self.fps_counter.append(time.perf_counter() - t0)
                fps = 1.0 / (sum(self.fps_counter) /
                             len(self.fps_counter) + 1e-9)
                self.draw_hud(frame, avg_ear, prox, fps)
                cv2.imshow("Digital Eye Strain Detection System", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break
                elif key in (ord('c'), ord('C')):
                    self.start_calibration()
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
            if self._use_legacy:
                self.face_mesh.close()
            else:
                self.face_landmarker.close()
            print("Resources released. Goodbye.")


if __name__ == "__main__":
    EyeStrainDetector(camera_index=0).run()
