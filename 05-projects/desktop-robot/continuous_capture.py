"""Persistent, bounded microphone capture independent of ASR/response work.

Timestamps are monotonic estimates of ADC frame end, never acoustic truth.
No full-duplex echo cancellation is claimed: discard_playback() must follow TTS.
"""
from dataclasses import dataclass
import queue
import threading
import time
import numpy as np
from audio_capture import UtteranceGate

class CaptureFailure(RuntimeError): pass
class ClippedUtteranceError(CaptureFailure): pass

@dataclass(frozen=True)
class AudioFrame:
    samples: object
    end_time: float

class ContinuousCapture:
    def __init__(self, device=None, *, rate=None, channels=1, max_buffer_seconds=20,
                 clock=time.perf_counter, stream_factory=None):
        if max_buffer_seconds <= 0: raise ValueError('buffer must be positive')
        self.device=device;self.rate=rate;self.channels=channels;self.clock=clock
        self.stream_factory=stream_factory;self.max_buffer_seconds=max_buffer_seconds
        self._frames=queue.Queue(maxsize=max(1,int(max_buffer_seconds/.02)))
        self._error=None;self._stream=None;self._lock=threading.Lock()
        self._discard_before=float('-inf');self._last_detector=None;self._suspended=False
        self._adc_to_monotonic=None
        self._last_callback_time=None;self._last_adc_end=None
        self._stats={'callbacks':0,'frames':0,'max_callback_interval_s':0.,
                     'max_adc_gap_s':0.,'first_status':None}

    def diagnostics(self):
        """Low-volume startup diagnostics; no PCM or recognized private speech."""
        return dict(self._stats, sample_rate=self.rate, channels=self.channels,
                    queue_frames=self._frames.qsize(),
                    stream_latency=getattr(self._stream,'latency',None),
                    stream_cpu_load=getattr(self._stream,'cpu_load',None),
                    error=None if self._error is None else str(self._error))

    def __enter__(self):
        from robot import device_format, resample_audio
        import sounddevice as sd
        if self.rate is None:self.rate,self.channels=device_format(self.device,'input',16000)
        # Import scipy and exercise the actual conversion before a live callback
        # can compete for the GIL during expensive first-use imports.
        warm_started=self.clock()
        resample_audio(np.zeros(round(self.rate*.02),dtype='float32'),self.rate,16000)
        self._stats['resample_warmup_s']=self.clock()-warm_started
        factory=self.stream_factory or sd.InputStream
        self._adc_to_monotonic=None
        self._stream=factory(samplerate=self.rate,channels=self.channels,dtype='float32',
             blocksize=round(self.rate*.02),device=self.device,callback=self._callback,
             finished_callback=self._finished)
        self._stream.start()
        return self

    def __exit__(self,*args):
        stream=self._stream;self._stream=None
        if stream is not None:
            try:stream.stop()
            finally:stream.close()

    def _finished(self):
        if self._stream is not None:self.fail('microphone stream stopped unexpectedly')

    def fail(self,message):
        with self._lock:self._error=CaptureFailure(str(message))

    def _callback(self,data,frames,info,status):
        arrived=self.clock()
        self._stats['callbacks']+=1;self._stats['frames']+=frames
        if self._last_callback_time is not None:
            self._stats['max_callback_interval_s']=max(self._stats['max_callback_interval_s'],arrived-self._last_callback_time)
        self._last_callback_time=arrived
        adc_start=float(info.inputBufferAdcTime)
        if self._last_adc_end is not None:
            self._stats['max_adc_gap_s']=max(self._stats['max_adc_gap_s'],adc_start-self._last_adc_end)
        self._last_adc_end=adc_start+frames/self.rate
        if status:
            if self._stats['first_status'] is None:self._stats['first_status']=str(status)
            self.fail('microphone callback: '+str(status));return
        # PortAudio times share a clock with each other, not perf_counter.
        # Anchor once per stream; recalibrating per callback would inject scheduler jitter.
        try:
            if self._adc_to_monotonic is None:
                self._adc_to_monotonic=arrived-float(info.currentTime)
            end=self._adc_to_monotonic+float(info.inputBufferAdcTime)+frames/self.rate
            self.push_frame(data,end)
        except Exception as error:self.fail(error)

    def push_frame(self,samples,end_time):
        """Inject PCM and its capture time. Useful for deterministic fake-device tests."""
        a=np.asarray(samples,dtype='float32')
        if a.ndim==2:a=a.mean(axis=1)
        if a.ndim!=1 or not len(a) or not np.isfinite(a).all() or not np.isfinite(end_time):
            raise ValueError('finite nonempty mono/multichannel PCM and timestamp required')
        if not self.rate:raise ValueError('sample rate required')
        with self._lock:
            if self._error is not None or self._suspended:return
            start=end_time-len(a)/self.rate
            trim=0 if self._discard_before <= start else int(np.ceil((self._discard_before-start)*self.rate))
            if trim>=len(a):return
            a=a[trim:].copy()
            try:self._frames.put_nowait(AudioFrame(a,float(end_time)))
            except queue.Full:self._error=CaptureFailure('capture queue overflow; utterance is unreliable')

    def suspend_playback(self):
        """Drop PCM while a confirmed nonempty turn generates/plays a reply.

        Hardware failures remain fatal. Suspension never clears a prior overflow.
        This is half-duplex; user interruption during robot output is not supported.
        """
        with self._lock:
            self._suspended=True
            while True:
                try:self._frames.get_nowait()
                except queue.Empty:break

    def discard_playback(self):
        """Drop queued own speech and reset VAD before the next user turn."""
        with self._lock:
            self._discard_before=self.clock()
            self._suspended=False
            while True:
                try:self._frames.get_nowait()
                except queue.Empty:break
        if self._last_detector is not None:self._last_detector.reset()

    def listen(self,threshold,silence_seconds=.7,detector=None,min_voice_ms=120,
               idle_seconds=15,preroll_ms=None,max_seconds=12):
        from robot import resample_audio
        if not self.rate:raise ValueError('capture must have a sample rate')
        if detector is not None:detector.reset()
        self._last_detector=detector
        gate=UtteranceGate(threshold,min_voice_ms,
             (500 if detector is not None else 200) if preroll_ms is None else preroll_ms,
             silence_seconds,idle_seconds,max_seconds=max_seconds,reject_long=True,sample_rate=self.rate)
        first_start=None;last_end=None;deadline=self.clock()+idle_seconds
        while True:
            if self._error is not None:raise self._error
            try:frame=self._frames.get(timeout=min(.1,max(.001,deadline-self.clock())))
            except queue.Empty:
                if self._error is not None:raise self._error
                if self.clock()>=deadline:return None,None
                continue
            if first_start is None:first_start=frame.end_time-len(frame.samples)/self.rate
            if last_end is not None and frame.end_time < last_end:
                raise CaptureFailure('capture timestamps moved backwards')
            if last_end is not None and frame.end_time-len(frame.samples)/self.rate-last_end > .01:
                raise CaptureFailure('capture timestamp gap; missing PCM cannot be submitted')
            last_end=frame.end_time
            voiced=detector.feed(resample_audio(frame.samples,self.rate,16000)) if detector is not None else True
            result=gate.feed(frame.samples,speech_detected=voiced,
                             elapsed=frame.end_time-first_start)
            if gate.first_voice_s is not None:deadline=self.clock()+max_seconds+silence_seconds
            if result is None:continue
            if result.state=='blocked':
                raise ClippedUtteranceError('utterance exceeded capture limit; incomplete speech was not submitted')
            if result.state=='idle':return None,None
            if result.state=='done':
                end=frame.end_time-(result.end_sample-result.last_voice_sample)/self.rate
                return resample_audio(result.samples,self.rate,16000),end
