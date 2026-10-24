from collections import deque

# A normal resting blink rate is often quoted as roughly 15-20 blinks/min, and it
# drops noticeably during focused screen use. 10/min is a configurable heuristic
# for "noticeably below normal", NOT a medical or clinical standard.
LOW_BLINK_RATE_PER_MIN = 10
# The rate must stay low this long before alerting, so one quiet minute doesn't nag.
LOW_RATE_SUSTAIN_SEC = 120
# Rolling window for blinks/min. Also the warm-up: no alert until it has filled once.
RATE_WINDOW_SEC = 60


class BlinkRateMonitor:
    """Rolling blinks-per-minute and a sustained-low-rate alert.

    Pure logic: every method takes `now` (seconds), so it can be tested with fake time.
    """

    def __init__(self, start_time, window_sec=RATE_WINDOW_SEC,
                 low_rate_per_min=LOW_BLINK_RATE_PER_MIN, sustain_sec=LOW_RATE_SUSTAIN_SEC):
        self.start_time = start_time
        self.window_sec = window_sec
        self.low_rate_per_min = low_rate_per_min
        self.sustain_sec = sustain_sec
        self.blink_times = deque()
        self.low_since = None

    def add_blink(self, now):
        self.blink_times.append(now)

    def rate(self, now):
        while self.blink_times and now - self.blink_times[0] > self.window_sec:
            self.blink_times.popleft()
        return len(self.blink_times) * 60.0 / self.window_sec

    def warming_up(self, now):
        return now - self.start_time < self.window_sec

    def update(self, now, paused=False):
        """Returns True when the low-blink-rate alert should be shown."""
        rate = self.rate(now)
        if paused or self.warming_up(now) or rate >= self.low_rate_per_min:
            self.low_since = None
            return False
        if self.low_since is None:
            self.low_since = now
        return now - self.low_since >= self.sustain_sec
