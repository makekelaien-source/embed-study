"""Offline Naruto keyword gate. The fixed acknowledgement is a PCM WAV."""
from pathlib import Path
import re
import unicodedata

CAPTURE_POLL_SECONDS = .25
CAPTURE_NO_FRAME_SECONDS = 1.5


def is_naruto(text):
    """Whole-utterance matching; never accept partial names or ordinary phrases."""
    text = unicodedata.normalize('NFKC', text).casefold()
    text = ''.join(char for char in text if char.isalnum())
    # 'なるど' is the voiced-consonant spelling observed in the owner's sample.
    return bool(re.fullmatch(r'(?:naruto|なると|ナルト|なるど)+', text))


def microphone_frames(device):
    """Capture independently of inference; bound lag and flag discontinuities."""
    import queue
    import time
    import numpy as np
    import sounddevice as sd
    from robot import device_format, resample_audio, RATE
    rate, channels = device_format(device, 'input', RATE)
    block = round(rate * .04)
    resample_audio(np.zeros(block, dtype='float32'), rate, RATE)
    frames = queue.Queue(maxsize=25)
    state = dict(last_frame_at=None, finished=False, error=None)

    def capture(audio, count, timing, status):
        try:
            item = (audio.copy(), bool(status.input_overflow))
            try:
                frames.put_nowait(item)
            except queue.Full:
                try:
                    frames.get_nowait()
                except queue.Empty:
                    pass
                frames.put_nowait((item[0], True))
            # Silence is still a captured frame; this is producer liveness,
            # not a speech/utterance deadline.
            state['last_frame_at'] = time.monotonic()
        except Exception as error:
            # PortAudio does not propagate callback exceptions to this thread.
            state['error'] = (type(error).__name__ + ': ' + str(error))[:240]
            raise sd.CallbackAbort from error

    def finished():
        state['finished'] = True

    def ensure_live(stream):
        if state['error'] is not None:
            raise RuntimeError('Wake capture callback failed: ' + state['error'])
        if state['finished'] or stream.closed or not stream.active or stream.stopped:
            raise RuntimeError('Wake capture stream stopped or became inactive')
        last_frame_at = state['last_frame_at'] if state['last_frame_at'] is not None else opened_at
        if time.monotonic() - last_frame_at >= CAPTURE_NO_FRAME_SECONDS:
            raise RuntimeError('Wake capture watchdog: no microphone frames for '
                               f'{CAPTURE_NO_FRAME_SECONDS:.2f}s')

    with sd.InputStream(samplerate=rate, channels=channels, dtype='float32',
                        blocksize=block, device=device, latency=.2, callback=capture,
                        finished_callback=finished) as stream:
        opened_at = time.monotonic()
        while True:
            ensure_live(stream)
            try:
                audio, overflow = frames.get(timeout=CAPTURE_POLL_SECONDS)
            except queue.Empty:
                ensure_live(stream)
                continue
            ensure_live(stream)
            yield resample_audio(audio.mean(axis=1), rate, RATE), overflow


class WakeUtterances:
    """Gate short, audible utterances without continuous ASR computation."""
    def __init__(self, threshold, min_voice_ms=120, preroll_ms=200,
                 silence_seconds=.56):
        from audio_capture import UtteranceGate
        self.gate = UtteranceGate(threshold, min_voice_ms, preroll_ms,
                                 silence_seconds, idle_seconds=1e12,
                                 max_seconds=3, reject_long=True)
        self.last_result = None

    def feed(self, audio):
        # Metadata is valid only for the just-completed returned waveform.
        self.last_result = None
        result = self.gate.feed(audio)
        if result is not None and result.state == 'done':
            self.last_result = result
            return result.samples
        return None


class SenseVoiceWake:
    """Reuse existing multilingual ASR for this Japanese proper name only."""
    def __init__(self, assets, threshold, min_voice_ms=120, preroll_ms=200,
                 silence_seconds=.56, confirmation='none'):
        import sherpa_onnx
        from robot import ASR
        from wake_confirmation import CONFIRMATION_MODES
        if confirmation not in CONFIRMATION_MODES:
            raise ValueError('Unsupported wake confirmation mode')
        folder = Path(assets) / ASR
        self.threshold = threshold
        self.min_voice_ms = min_voice_ms
        self.preroll_ms = preroll_ms
        self.silence_seconds = silence_seconds
        self.confirmation = confirmation
        self.confirmation_recognizer = None
        self.confirmation_error = None
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=str(folder / 'model.int8.onnx'), tokens=str(folder / 'tokens.txt'),
            language='ja', use_itn=True, num_threads=2,
        )
        if confirmation == 'auto-consensus':
            # Preload before ready/microphone capture, never on a first wake.
            try:
                self.confirmation_recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model=str(folder / 'model.int8.onnx'), tokens=str(folder / 'tokens.txt'),
                    language='auto', use_itn=True, num_threads=2,
                )
            except Exception as error:
                import json
                self.confirmation_error = (type(error).__name__ + ': ' + str(error))[:240]
                print('WAKE_CONFIRMATION ' + json.dumps(dict(mode=confirmation,
                      ready=False, error=self.confirmation_error)), flush=True)

    def recognize(self, audio):
        from robot import RATE
        stream = self.recognizer.create_stream()
        stream.accept_waveform(RATE, audio)
        self.recognizer.decode_stream(stream)
        return stream.result.text.strip()

    def recognize_confirmation(self, audio):
        from robot import RATE
        recognizer = getattr(self, 'confirmation_recognizer', None)
        if recognizer is None:
            raise RuntimeError(getattr(self, 'confirmation_error', None)
                               or 'Wake confirmation decoder is unavailable')
        stream = recognizer.create_stream()
        stream.accept_waveform(RATE, audio)
        recognizer.decode_stream(stream)
        return stream.result.text.strip()

    def confirm(self, text, audio, capture_result=None):
        from numbers import Integral
        from robot import RATE
        from wake_confirmation import confirm_candidate
        relative_last_voice = None
        if capture_result is not None and getattr(capture_result, 'state', None) == 'done':
            start = getattr(capture_result, 'start_sample', None)
            end = getattr(capture_result, 'end_sample', None)
            last = getattr(capture_result, 'last_voice_sample', None)
            try:
                audio_length = len(audio)
            except TypeError:
                audio_length = -1
            if (all(isinstance(value, Integral) and not isinstance(value, bool)
                    for value in (start, end, last))
                    and 0 <= start < last <= end and end - start == audio_length):
                relative_last_voice = last - start
        return confirm_candidate(text, audio, relative_last_voice,
            self.recognize_confirmation, is_naruto,
            confirmation=getattr(self, 'confirmation', 'none'), sample_rate=RATE)

    def wait(self, device):
        import json
        import time
        def new_gate():
            return WakeUtterances(self.threshold, getattr(self, 'min_voice_ms', 120),
                                  getattr(self, 'preroll_ms', 200),
                                  getattr(self, 'silence_seconds', .56))
        gate = new_gate()
        frames = microphone_frames(device)
        try:
            for audio, overflow in frames:
                if overflow:
                    gate = new_gate()
                    print('WAKE: input discontinuity; discarding partial word', flush=True)
                candidate = gate.feed(audio)
                if candidate is None:
                    continue
                start = time.monotonic()
                text = self.recognize(candidate)
                primary_decode_s = time.monotonic() - start
                confirmation = self.confirm(text, candidate, gate.last_result)
                accepted = confirmation['accepted']
                row = dict(text=text, accepted=accepted, decode_s=time.monotonic()-start)
                if getattr(self, 'confirmation', 'none') != 'none':
                    row.update(primary_decode_s=primary_decode_s, confirmation=confirmation)
                print('WAKE_CANDIDATE ' + json.dumps(row, ensure_ascii=False), flush=True)
                if accepted:
                    return 'Naruto'
        finally:
            frames.close()


class NarutoWake:
    def __init__(self, folder):
        import sherpa_onnx
        folder = Path(folder)

        def model(prefix, quantized=True):
            suffix = '.int8.onnx' if quantized else '.onnx'
            paths = list(folder.glob(prefix + '*chunk-8*' + suffix))
            if not quantized:
                paths = [p for p in paths if '.int8.' not in p.name]
            if len(paths) != 1:
                raise ValueError(f'Expected one {prefix} chunk-8 model in {folder}')
            return str(paths[0])

        self.kws = sherpa_onnx.KeywordSpotter(
            tokens=str(folder / 'tokens.txt'), encoder=model('encoder'),
            decoder=model('decoder', False), joiner=model('joiner'),
            keywords_file=str(folder / 'naruto-keywords.txt'),
            num_threads=1, provider='cpu', keywords_threshold=0.35,
        )

    def wait(self, device):
        from robot import RATE
        stream = self.kws.create_stream()
        frames = microphone_frames(device)
        try:
            for audio, overflow in frames:
                if overflow:
                    print('WAKE: input discontinuity; resetting detector', flush=True)
                    stream = self.kws.create_stream()
                stream.accept_waveform(RATE, audio)
                while self.kws.is_ready(stream):
                    self.kws.decode_stream(stream)
                    result = self.kws.get_result(stream)
                    if result:
                        self.kws.reset_stream(stream)
                        return result
        finally:
            frames.close()



def load_acknowledgement(path):
    import wave
    import numpy as np
    with wave.open(str(path), 'rb') as audio:
        if audio.getsampwidth() != 2 or audio.getnchannels() != 1:
            raise ValueError('Wake acknowledgement must be mono 16-bit PCM WAV')
        rate = audio.getframerate()
        samples = np.frombuffer(audio.readframes(audio.getnframes()), '<i2').astype('float32') / 32768
    if not len(samples):
        raise ValueError('Empty wake acknowledgement')
    return samples, rate
