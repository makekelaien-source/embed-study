"""Deterministic PCM segmentation shared by microphone capture and replay.

Indices address the input PCM, including the pre-roll and trailing silence.
No recording device, ASR model or background recording is opened here.
"""
from collections import deque
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class CaptureResult:
    state: str
    samples: object
    start_sample: int
    end_sample: int
    first_voice_sample: object
    last_voice_sample: object
    first_voice_s: object
    last_voice_s: object


class UtteranceGate:
    """Confirm consecutive audible frames and preserve a bounded pre-roll.

    ``elapsed`` is optional wall time for live endpoint/idle semantics. Replay
    omits it and uses PCM duration. A completed event rearms the gate. A long
    rejected wake command instead remains blocked until a full quiet tail.
    First/last voice indices mark ends of accepted frames (onset confirmation
    is therefore distinct from the beginning of the returned pre-roll).
    """
    def __init__(self, threshold, min_voice_ms=120, preroll_ms=200,
                 silence_seconds=.55, idle_seconds=15, max_seconds=12,
                 reject_long=False, sample_rate=16000):
        if not math.isfinite(threshold) or not 0 < threshold <= 1:
            raise ValueError('threshold must be finite and in (0, 1]')
        if not math.isfinite(min_voice_ms) or not 60 <= min_voice_ms <= 500:
            raise ValueError('min_voice_ms must be 60-500')
        if not math.isfinite(preroll_ms) or not 20 <= preroll_ms <= 2000:
            raise ValueError('preroll_ms must be 20-2000')
        if not math.isfinite(silence_seconds) or not .2 <= silence_seconds <= 1.5:
            raise ValueError('silence_seconds must be .2-1.5')
        if not math.isfinite(idle_seconds) or idle_seconds <= 0:
            raise ValueError('idle_seconds must be positive and finite')
        if not math.isfinite(max_seconds) or max_seconds <= 0:
            raise ValueError('max_seconds must be positive and finite')
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValueError('sample_rate must be a positive integer')
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.min_voice_samples = math.ceil(sample_rate * min_voice_ms / 1000)
        self.preroll_samples = math.ceil(sample_rate * preroll_ms / 1000)
        self.silence_seconds = silence_seconds
        self.idle_seconds = idle_seconds
        self.max_seconds = max_seconds
        self.reject_long = reject_long
        self.position = 0
        self.elapsed = 0.
        self.preroll = deque()
        self.preroll_length = 0
        self.chunks = []
        self.loud_samples = 0
        self.first_voice_sample = self.last_voice_sample = None
        self.first_voice_s = self.last_voice_s = None
        self.start_sample = 0
        self.blocked = False
        self.quiet_since = None

    def _clear_phrase(self):
        self.preroll.clear()
        self.preroll_length = 0
        self.chunks = []
        self.loud_samples = 0
        self.first_voice_sample = self.last_voice_sample = None
        self.first_voice_s = self.last_voice_s = None

    def _remember(self, audio):
        self.preroll.append(audio)
        self.preroll_length += len(audio)
        while self.preroll_length > self.preroll_samples:
            excess = self.preroll_length - self.preroll_samples
            oldest = self.preroll.popleft()
            removed = min(excess, len(oldest))
            if removed < len(oldest):
                self.preroll.appendleft(oldest[removed:])
            self.preroll_length -= removed

    def _result(self, state, samples=None):
        return CaptureResult(state, samples, self.start_sample, self.position,
                             self.first_voice_sample, self.last_voice_sample,
                             self.first_voice_s, self.last_voice_s)

    def feed(self, audio, speech_detected=True, elapsed=None, level=None):
        audio = np.asarray(audio, dtype='float32')
        if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
            raise ValueError('audio must be non-empty, finite mono PCM')
        # Live capture may preserve a multichannel energy measurement even
        # though the stored/recognized PCM is the same downmixed mono signal.
        measured_level = float(np.sqrt(np.mean(audio ** 2))) if level is None else float(level)
        if not math.isfinite(measured_level) or measured_level < 0:
            raise ValueError('level must be a finite nonnegative RMS value')
        now = (self.position + len(audio)) / self.sample_rate if elapsed is None else elapsed
        if not math.isfinite(now) or now < self.elapsed:
            raise ValueError('elapsed must be finite and monotonic')
        self.elapsed = now
        self.position += len(audio)
        voiced = bool(speech_detected) and measured_level >= self.threshold
        self.loud_samples = self.loud_samples + len(audio) if voiced else 0

        if self.blocked:
            if voiced:
                self.quiet_since = None
            elif self.quiet_since is None:
                self.quiet_since = now - len(audio) / self.sample_rate
            if self.quiet_since is not None and now - self.quiet_since + 1e-9 >= self.silence_seconds:
                self.blocked = False
                self.quiet_since = None
                self._clear_phrase()
            return None

        if self.first_voice_s is None:
            # Preserve Endpoint's rule: an expired idle period cannot reopen.
            if now >= self.idle_seconds:
                self.start_sample = self.position
                return self._result('idle')
            self._remember(audio.copy())
            if self.loud_samples < self.min_voice_samples:
                return None
            self.chunks = list(self.preroll)
            self.start_sample = self.position - self.preroll_length
            self.first_voice_sample = self.last_voice_sample = self.position
            self.first_voice_s = self.last_voice_s = now
            self.preroll.clear()
            self.preroll_length = 0
            return None

        self.chunks.append(audio.copy())
        if voiced:
            self.last_voice_sample = self.position
            self.last_voice_s = now
        # Duration starts at confirmed onset, never at the pre-roll boundary.
        too_long = now - self.first_voice_s + 1e-9 >= self.max_seconds
        quiet = now - self.last_voice_s + 1e-9 >= self.silence_seconds
        if too_long and self.reject_long:
            result = self._result('blocked')
            self._clear_phrase()
            self.blocked = True
            self.quiet_since = None if voiced else now - len(audio) / self.sample_rate
            return result
        if quiet or too_long:
            result = self._result('done', np.concatenate(self.chunks))
            self._clear_phrase()
            return result
        return None
