import unittest
import numpy as np
from replay_capture import replay,meaningful_transcript
class ReplayTests(unittest.TestCase):
    def test_reject_punctuation(self):
        self.assertFalse(meaningful_transcript(' 。！？ '));self.assertTrue(meaningful_transcript('停止'))
    def test_continues_after_empty(self):
        # Each pulse confirms onset; empty first recognition must not discard second.
        pcm=np.concatenate([np.zeros(16000),np.ones(8000)*.1,np.zeros(16000),np.ones(8000)*.1,np.zeros(16000)]).astype('float32')
        answers=iter(['。','你好']);rows=list(replay(pcm,16000,lambda p,r:next(answers)))
        self.assertEqual(len(rows),2);self.assertFalse(rows[0]['nonempty_text']);self.assertEqual(rows[1]['text'],'你好')
        self.assertGreater(rows[1]['start_s'],rows[0]['end_s'])
    def test_does_not_complete_trailing_partial(self):
        pcm=np.concatenate([np.zeros(16000),np.ones(8000)*.1]).astype('float32')
        self.assertEqual(list(replay(pcm,16000,lambda p,r:'x')),[])
    def test_detector_rejects_energy(self):
        pcm=np.concatenate([np.ones(8000)*.1,np.zeros(16000)]).astype('float32')
        self.assertEqual(list(replay(pcm,16000,lambda p,r:'x',detector=lambda p,r:False)),[])
if __name__=='__main__':unittest.main()
