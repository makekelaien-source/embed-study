import unittest
import numpy as np
from continuous_capture import ContinuousCapture,CaptureFailure,ClippedUtteranceError
class ContinuousTests(unittest.TestCase):
 def make(self,seconds=20):return ContinuousCapture(rate=16000,max_buffer_seconds=seconds,clock=lambda:100.)
 def feed(self,c,start,voice=.4,quiet=.6):
  t=start
  for n,value in [(int(voice/.02),.1),(int(quiet/.02),0)]:
   for _ in range(n):
    t+=.02;c.push_frame(np.full(320,value,dtype='float32'),t)
  return t
 def test_keeps_second_utterance_during_recognition(self):
  c=self.make();t=self.feed(c,10);self.feed(c,t)
  a,end=c.listen(.01,.3);b,end2=c.listen(.01,.3)
  self.assertIsNotNone(a);self.assertIsNotNone(b);self.assertGreater(end2,end)
  self.assertAlmostEqual(end,10.4,places=4)
 def test_buffer_clock_not_consumer_clock(self):
  c=self.make();self.feed(c,10)
  _,end=c.listen(.01,.3);self.assertLess(end,11);self.assertNotEqual(end,100)
 def test_overflow_fails_closed(self):
  c=self.make(.04);self.feed(c,10)
  with self.assertRaisesRegex(CaptureFailure,'overflow'):c.listen(.01)
 def test_disconnect_fails_closed(self):
  c=self.make();c.fail('disconnected')
  with self.assertRaisesRegex(CaptureFailure,'disconnected'):c.listen(.01)
 def test_discards_own_playback(self):
  c=self.make();self.feed(c,90);c.discard_playback();self.feed(c,101)
  _,end=c.listen(.01,.3);self.assertGreater(end,101)
 def test_discards_late_callback_from_before_boundary(self):
  c=self.make();c.discard_playback();c.push_frame(np.ones(320),99)
  self.assertTrue(c._frames.empty())
 def test_overlength_is_not_submitted(self):
  c=self.make();self.feed(c,10,voice=2,quiet=.6)
  with self.assertRaises(ClippedUtteranceError):c.listen(.01,.3,max_seconds=.5)
 def test_timestamp_regression_is_error(self):
  c=self.make();c.push_frame(np.ones(320)*.1,10);c.push_frame(np.ones(320)*.1,9)
  with self.assertRaises(CaptureFailure):c.listen(.01)
if __name__=='__main__':unittest.main()

class LifecycleTests(unittest.TestCase):
 def test_context_closes_stream_and_maps_adc_time(self):
  from types import SimpleNamespace
  class Stream:
   def __init__(self,**kw):self.kw=kw;self.started=False;self.closed=False
   def start(self):self.started=True
   def stop(self):self.kw['finished_callback']()
   def close(self):self.closed=True
  c=ContinuousCapture(rate=16000,stream_factory=Stream,clock=lambda:100)
  with c:
   stream=c._stream;self.assertTrue(stream.started)
   c._callback(np.ones((320,1))*.1,320,SimpleNamespace(currentTime=20,inputBufferAdcTime=19.98),False)
   self.assertAlmostEqual(c._frames.get().end_time,100)
  self.assertTrue(stream.closed);self.assertIsNone(c._error)
 def test_vad_resets_after_discard(self):
  class Detector:
   def __init__(self):self.count=0
   def reset(self):self.count+=1
  c=ContinuousCapture(rate=16000);d=Detector();c._last_detector=d;c.discard_playback()
  self.assertEqual(d.count,1)
 def test_timestamp_gap_fails(self):
  c=ContinuousCapture(rate=16000,clock=lambda:100)
  c.push_frame(np.ones(320)*.1,10);c.push_frame(np.ones(320)*.1,10.5)
  with self.assertRaisesRegex(CaptureFailure,'gap'):c.listen(.01)

class PlaybackSuspensionTests(unittest.TestCase):
 def test_thirty_second_output_does_not_overflow(self):
  c=ContinuousCapture(rate=16000,max_buffer_seconds=.04,clock=lambda:100)
  c.push_frame(np.ones(320),10);c.suspend_playback()
  for i in range(1500):c.push_frame(np.ones(320),11+i*.02)
  self.assertTrue(c._frames.empty());self.assertIsNone(c._error)
  c.discard_playback();c.push_frame(np.ones(320),101)
  self.assertEqual(c._frames.qsize(),1)
 def test_prior_overflow_not_erased_by_suspend(self):
  c=ContinuousCapture(rate=16000,max_buffer_seconds=.02,clock=lambda:100)
  c.push_frame(np.ones(320),10);c.push_frame(np.ones(320),10.02)
  c.suspend_playback();c.discard_playback()
  with self.assertRaisesRegex(CaptureFailure,'overflow'):c.listen(.01)
 def test_hardware_error_during_playback_not_erased(self):
  c=ContinuousCapture(rate=16000,clock=lambda:100);c.suspend_playback()
  c.fail('device unplugged');c.discard_playback()
  with self.assertRaisesRegex(CaptureFailure,'unplugged'):c.listen(.01)

class AdcClockTests(unittest.TestCase):
 def test_callback_scheduling_jitter_keeps_adc_sequence(self):
  from types import SimpleNamespace
  now=[100.]
  c=ContinuousCapture(rate=16000,clock=lambda:now[0])
  for i in range(50):
   now[0]=100+i*.02+(.08 if i%2 else 0)
   pcm=np.full((320,1),.1 if i<20 else 0,dtype='float32')
   c._callback(pcm,320,SimpleNamespace(currentTime=20+i*.02,inputBufferAdcTime=19.98+i*.02),False)
  _,end=c.listen(.01,.3)
  self.assertAlmostEqual(end,100.38,places=5)
 def test_real_adc_gap_still_rejected(self):
  from types import SimpleNamespace
  c=ContinuousCapture(rate=16000,clock=lambda:100.)
  for t in (20.,20.5):
   c._callback(np.ones((320,1))*.1,320,SimpleNamespace(currentTime=t,inputBufferAdcTime=t-.02),False)
  with self.assertRaisesRegex(CaptureFailure,'gap'):c.listen(.01)

class StartupTests(unittest.TestCase):
 def test_resample_is_warm_before_stream_creation(self):
  from unittest.mock import patch
  events=[]
  class Stream:
   def __init__(self,**kw):events.append('create')
   def start(self):events.append('start')
   def stop(self):pass
   def close(self):pass
  with patch('robot.resample_audio',side_effect=lambda a,r,t:events.append(('warm',r,t))):
   with ContinuousCapture(rate=48000,stream_factory=Stream):pass
  self.assertEqual(events,[('warm',48000,16000),'create','start'])
 def test_diagnostics_capture_overflow_status_and_timing(self):
  from types import SimpleNamespace
  now=[100.]
  c=ContinuousCapture(rate=48000,clock=lambda:now[0])
  c._callback(np.zeros((960,1)),960,SimpleNamespace(currentTime=20,inputBufferAdcTime=19.98),False)
  now[0]=100.3
  c._callback(np.zeros((960,1)),960,SimpleNamespace(currentTime=20.3,inputBufferAdcTime=20.28),'input overflow')
  d=c.diagnostics()
  self.assertEqual(d['callbacks'],2);self.assertEqual(d['first_status'],'input overflow')
  self.assertAlmostEqual(d['max_callback_interval_s'],.3)
  self.assertAlmostEqual(d['max_adc_gap_s'],.28)
