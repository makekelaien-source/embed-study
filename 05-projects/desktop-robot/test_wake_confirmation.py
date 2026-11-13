import json
import unittest
from unittest.mock import Mock

import numpy as np

from wake_confirmation import confirm_candidate
from wake_word import is_naruto


class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.audio = np.linspace(-.1, .1, 16000, dtype='float32')

    def check(self, text, decode, last=8000, audio=None, mode='auto-consensus'):
        return confirm_candidate(text, self.audio if audio is None else audio,
                                 last, decode, is_naruto, confirmation=mode)

    def test_default_none_keeps_primary_matcher_and_never_retries(self):
        decode = Mock(side_effect=AssertionError('must not decode'))
        for text in ['Naruto', 'ナルト', 'なるほど', 'なるほ', 'I like Naruto']:
            result = confirm_candidate(text, None, None, decode, is_naruto)
            self.assertEqual(result['accepted'], is_naruto(text))
        decode.assert_not_called()

    def test_primary_name_accepts_without_extra_audio_or_decoder(self):
        decode = Mock(side_effect=AssertionError('must not decode'))
        result = self.check('なると。', decode, last=None, audio=np.array([np.nan]))
        self.assertTrue(result['accepted'])
        self.assertEqual(result['method'], 'primary')
        decode.assert_not_called()

    def test_near_name_alone_is_never_an_acceptance(self):
        for text in ['なるほ。', 'なるほど！']:
            decode = Mock(side_effect=['なるほ', 'なるほど', 'Notto'])
            result = self.check(text, decode)
            self.assertFalse(result['accepted'])
            self.assertEqual(result['votes'], 0)
            self.assertEqual(decode.call_count, 3)

    def test_only_exact_normalized_near_name_can_retry(self):
        decode = Mock(return_value='Naruto')
        for text in ['', 'なるほどですね', 'なるほなるほ', 'naruho', '然后',
                     '南通', 'I like Naruto', 'ナルトについて教えて']:
            with self.subTest(text=text):
                self.assertFalse(self.check(text, decode)['accepted'])
        decode.assert_not_called()

    def test_two_of_three_strict_names_are_required_and_crops_are_exact(self):
        decode = Mock(side_effect=['なると', 'なるほど', 'Naruto!'])
        result = self.check('なるほ。', decode)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['votes'], 2)
        self.assertEqual([len(call.args[0]) for call in decode.call_args_list],
                         [10560, 11200, 11840])
        for call, end in zip(decode.call_args_list, [10560, 11200, 11840]):
            np.testing.assert_array_equal(call.args[0], self.audio[:end])
        self.assertEqual([view['tail_ms'] for view in result['views']], [160, 200, 240])
        self.assertTrue(all(view['decode_s'] >= 0 for view in result['views']))
        json.dumps(result)  # Metadata contains no waveform or NumPy values.

    def test_one_correct_view_does_not_accept(self):
        result = self.check('なるほど', Mock(side_effect=['Naruto', 'なるほ', 'なるほど']))
        self.assertFalse(result['accepted'])
        self.assertEqual(result['votes'], 1)

    def test_hard_negative_transcripts_cannot_vote_for_the_name(self):
        for text in ['なるほ', 'なるほど', '然后', '南通', 'Notto', 'Naruto是什么']:
            result = self.check('なるほど', Mock(return_value=text))
            self.assertFalse(result['accepted'], text)

    def test_invalid_indices_pcm_and_incomplete_tails_fail_before_decoding(self):
        for last in [None, -1, 0, 16001, 8000., True, float('nan')]:
            with self.subTest(last=last):
                decode = Mock(return_value='Naruto')
                result = self.check('なるほ', decode, last=last)
                self.assertFalse(result['accepted'])
                self.assertIn('error', result)
                decode.assert_not_called()
        for audio, last in [(np.ones((16000, 1)), 8000), (np.array([]), 1),
                            (np.array([np.nan]), 1), (np.array([np.inf]), 1),
                            (np.zeros(9000), 8000)]:
            with self.subTest(shape=audio.shape, last=last):
                decode = Mock(return_value='Naruto')
                result = self.check('なるほ', decode, last=last, audio=audio)
                self.assertFalse(result['accepted'])
                self.assertIn('error', result)
                decode.assert_not_called()

    def test_invalid_rate_and_unknown_mode_fail_closed(self):
        for rate in [0, -1, True, 16000., float('nan'), 1]:
            decode = Mock(return_value='Naruto')
            result = confirm_candidate('なるほ', self.audio, 8000, decode, is_naruto,
                                       'auto-consensus', rate)
            self.assertFalse(result['accepted'])
            decode.assert_not_called()
        result = self.check('Naruto', Mock(), mode='unknown')
        self.assertFalse(result['accepted'])

    def test_decoder_error_rejects_even_after_two_positive_votes(self):
        decode = Mock(side_effect=['Naruto', 'なると', RuntimeError('backend failed')])
        result = self.check('なるほ', decode)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['votes'], 2)
        self.assertIn('RuntimeError', result['error'])
        self.assertEqual(len(result['views']), 3)

    def test_missing_decoder_and_non_text_output_fail_closed(self):
        for decode in [None, Mock(return_value={'text': 'Naruto'})]:
            result = self.check('なるほど', decode)
            self.assertFalse(result['accepted'])
            self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
