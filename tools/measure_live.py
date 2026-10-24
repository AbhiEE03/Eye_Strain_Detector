"""Measure the real app loop (EyeStrainDetector.run) with the live webcam.

Usage:  venv\\Scripts\\python tools\\measure_live.py [seconds]   (default 60)
Needs psutil (pip install psutil). It's a dev-only tool, not needed by the app.

It does not copy the loop: it wraps draw_hud (to count frames) and cv2.waitKey
(to press ESC after the duration), so the numbers are for the unmodified run().
"""
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2      # noqa: E402
import psutil   # noqa: E402
import main     # noqa: E402

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
stats = {"start": None, "frames": 0, "face": 0, "hud_fps": [], "proc": [], "total": []}
real_wait_key = cv2.waitKey
real_draw_hud = main.EyeStrainDetector.draw_hud


def draw_hud(self, frame, avg_ear, prox, fps, bpm, low_blink):
    if stats["start"] is None:
        stats["start"] = time.perf_counter()
    stats["frames"] += 1
    stats["face"] += prox != "NO FACE"
    stats["hud_fps"].append(fps)
    return real_draw_hud(self, frame, avg_ear, prox, fps, bpm, low_blink)


def wait_key(delay):
    key = real_wait_key(delay)
    if stats["start"] is not None and time.perf_counter() - stats["start"] >= DURATION:
        return 27
    return key


def sample_cpu(stop):
    proc = psutil.Process()
    proc.cpu_percent(None)
    psutil.cpu_percent(None)
    while not stop.wait(1.0):
        if stats["start"] is not None:
            stats["proc"].append(proc.cpu_percent(None))
            stats["total"].append(psutil.cpu_percent(None))


def cpu_name():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-c", "(Get-CimInstance Win32_Processor).Name"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


if __name__ == "__main__":
    main.EyeStrainDetector.draw_hud = draw_hud
    cv2.waitKey = wait_key
    stop = threading.Event()
    threading.Thread(target=sample_cpu, args=(stop,), daemon=True).start()
    main.EyeStrainDetector(camera_index=0).run()
    elapsed = time.perf_counter() - stats["start"]
    stop.set()
    cores = psutil.cpu_count()
    steady = stats["hud_fps"][len(stats["hud_fps"]) // 10:]   # skip first 10% (window filling)
    print("\n===== measure_live results =====")
    print(f"CPU model             : {cpu_name()} ({cores} logical cores)")
    print(f"Duration              : {elapsed:.1f} s, {stats['frames']} frames, face in {100 * stats['face'] / max(1, stats['frames']):.0f}% of frames")
    print(f"Full-loop FPS (wall)  : {stats['frames'] / elapsed:.1f}")
    print(f"HUD FPS (mean, steady): {mean(steady):.1f}")
    print(f"Process CPU           : {mean(stats['proc']):.0f}% of one core = {mean(stats['proc']) / cores:.1f}% of total machine")
    print(f"Whole-machine CPU     : {mean(stats['total']):.1f}% (all processes)")
