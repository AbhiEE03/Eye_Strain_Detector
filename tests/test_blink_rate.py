# Run:  python -m unittest discover -s tests -v
# Uses fake timestamps (seconds), so no camera or MediaPipe is needed.
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blink_rate import BlinkRateMonitor


def blinks_every(mon, start, end, interval):
    t = start
    while t < end:
        mon.add_blink(t)
        t += interval


class RollingWindowTests(unittest.TestCase):
    def test_rate_counts_only_last_60_seconds(self):
        mon = BlinkRateMonitor(start_time=0.0)
        blinks_every(mon, 0.0, 120.0, 4.0)          # 15 blinks/min for 2 min
        self.assertAlmostEqual(mon.rate(120.0), 15.0)

    def test_old_blinks_drop_out_of_window(self):
        mon = BlinkRateMonitor(start_time=0.0)
        blinks_every(mon, 0.0, 30.0, 2.0)           # 15 blinks in first 30 s
        self.assertAlmostEqual(mon.rate(30.0), 15.0)
        self.assertAlmostEqual(mon.rate(91.0), 0.0)  # all older than 60 s

    def test_no_blinks_is_zero(self):
        self.assertEqual(BlinkRateMonitor(start_time=0.0).rate(100.0), 0.0)


class AlertTests(unittest.TestCase):
    def test_no_alert_during_first_60_seconds(self):
        mon = BlinkRateMonitor(start_time=0.0)
        for t in range(0, 60):
            self.assertFalse(mon.update(float(t)))

    def test_alert_after_sustained_low_rate(self):
        mon = BlinkRateMonitor(start_time=0.0)      # zero blinks -> rate 0
        alerts = {t: mon.update(float(t)) for t in range(0, 200)}
        # warm-up ends at 60 s, low rate must then persist 120 s -> alert from 180 s
        self.assertFalse(alerts[179])
        self.assertTrue(alerts[180])

    def test_no_alert_when_rate_is_normal(self):
        mon = BlinkRateMonitor(start_time=0.0)
        for t in range(0, 400):                     # steady 15/min, added in real time
            if t % 4 == 0:
                mon.add_blink(float(t))
            self.assertFalse(mon.update(float(t)))

    def test_recovery_resets_sustain_timer(self):
        mon = BlinkRateMonitor(start_time=0.0)
        for t in range(0, 150):                     # low from 60 s onward
            mon.update(float(t))
        blinks_every(mon, 150.0, 151.0, 0.05)       # burst of 20 blinks -> rate 20/min
        self.assertFalse(mon.update(151.0))
        for t in range(152, 211):                   # burst still inside window
            self.assertFalse(mon.update(float(t)))
        # burst leaves the window at 210 s -> low again, needs another 120 s
        alerts = {t: mon.update(float(t)) for t in range(211, 340)}
        self.assertFalse(alerts[329])
        self.assertTrue(alerts[331])

    def test_paused_never_alerts_and_resets_timer(self):
        mon = BlinkRateMonitor(start_time=0.0)
        for t in range(0, 170):
            mon.update(float(t))
        self.assertFalse(mon.update(175.0, paused=True))   # e.g. calibrating
        alerts = {t: mon.update(float(t)) for t in range(176, 300)}
        self.assertFalse(alerts[180])               # would have alerted without the pause
        self.assertTrue(alerts[296])                # 176 + 120

    def test_thresholds_are_configurable(self):
        mon = BlinkRateMonitor(start_time=0.0, low_rate_per_min=5, sustain_sec=10)
        for t in range(0, 300):                     # 6 blinks/min, above 5
            if t % 10 == 0:
                mon.add_blink(float(t))
            self.assertFalse(mon.update(float(t)))
        mon2 = BlinkRateMonitor(start_time=0.0, low_rate_per_min=5, sustain_sec=10)
        alerts = {t: mon2.update(float(t)) for t in range(0, 80)}   # no blinks
        self.assertFalse(alerts[69])
        self.assertTrue(alerts[70])                 # 60 s warm-up + 10 s sustain


if __name__ == "__main__":
    unittest.main()
