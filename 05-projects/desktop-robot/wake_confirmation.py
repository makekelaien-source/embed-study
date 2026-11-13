"""Experimental bounded wake confirmation; never records or saves audio.

Multiple views come from the same waveform. Votes measure consistency, not a
statistical confidence or independent acoustic evidence. The caller supplies
the existing whole-utterance matcher without expanding its accepted names.
"""
from numbers import Integral
import time
import unicodedata

import numpy as np


CONFIRMATION_MODES = ('none', 'auto-consensus')
TAILS_MS = (160, 200, 240)
RETRY_TEXTS = frozenset(('なるほ', 'なるほど'))


def _normalized(text):
    return ''.join(char for char in unicodedata.normalize('NFKC', text).casefold()
                   if char.isalnum())


def _error(error):
    return (type(error).__name__ + ': ' + str(error))[:240]


def confirm_candidate(primary_text, audio, relative_last_voice, decode, accepts,
                      confirmation='none', sample_rate=16000):
    """Return a JSON-safe decision with at most three sequential decode calls.

    ``relative_last_voice`` is the last voiced frame's exclusive end index in
    ``audio``. Only rejected exact near-name transcripts may use the optional
    auto-language decoder. Invalid capture bounds or a failed decoder reject
    the entire retry, including any votes accumulated before the failure.
    """
    decision = dict(accepted=False, method='none', votes=0, views=[])
    if confirmation not in CONFIRMATION_MODES:
        decision.update(method='invalid', error='Unsupported confirmation mode')
        return decision
    if not isinstance(primary_text, str):
        decision.update(method='invalid', error='Primary transcript must be text')
        return decision
    try:
        if accepts(primary_text):
            decision.update(accepted=True, method='primary')
            return decision
    except Exception as error:
        decision.update(method='invalid', error=_error(error))
        return decision
    if confirmation == 'none':
        return decision
    if _normalized(primary_text) not in RETRY_TEXTS:
        decision['method'] = 'not-eligible'
        return decision
    decision['method'] = 'auto-consensus'
    try:
        samples = np.asarray(audio, dtype='float32')
        if samples.ndim != 1 or not len(samples) or not np.isfinite(samples).all():
            raise ValueError('Confirmation requires non-empty finite mono PCM')
        if (isinstance(sample_rate, bool) or not isinstance(sample_rate, Integral)
                or sample_rate <= 0):
            raise ValueError('Sample rate must be a positive integer')
        if (isinstance(relative_last_voice, bool)
                or not isinstance(relative_last_voice, Integral)
                or not 0 < relative_last_voice <= len(samples)):
            raise ValueError('Last voiced sample is outside the captured PCM')
        ends = [int(relative_last_voice) + round(sample_rate * tail / 1000)
                for tail in TAILS_MS]
        if len(set(ends)) != len(ends) or ends[-1] > len(samples):
            raise ValueError('Capture lacks distinct complete 160/200/240ms tails')
        if not callable(decode):
            raise ValueError('Confirmation decoder is unavailable')
        for tail, end in zip(TAILS_MS, ends):
            started = time.perf_counter()
            try:
                text = decode(samples[:end])
                if not isinstance(text, str):
                    raise TypeError('Confirmation decoder must return text')
                matched = bool(accepts(text))
            except Exception as error:
                decision['views'].append(dict(tail_ms=tail, accepted=False,
                    decode_s=time.perf_counter() - started, error=_error(error)))
                decision['error'] = _error(error)
                return decision
            decision['views'].append(dict(tail_ms=tail, text=text,
                accepted=matched, decode_s=time.perf_counter() - started))
            decision['votes'] += int(matched)
        decision['accepted'] = decision['votes'] >= 2
    except Exception as error:
        decision['error'] = _error(error)
    return decision
