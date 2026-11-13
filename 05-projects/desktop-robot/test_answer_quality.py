import unittest
from unittest.mock import Mock, patch
from answer_quality import check_answer


class QualityTests(unittest.TestCase):
    def test_prefix_guard_holds_placeholder_but_streams_real_first_clause(self):
        from robot import Dialogue
        events = []
        def model(messages):
            for label, text in [('placeholder-start', '让我想'), ('placeholder-end', '想。'),
                                ('content', '电压是电势差。'), ('tail', '电流是电荷流率。')]:
                events.append(label)
                yield text
        reply = Mock(side_effect=AssertionError('no retries or nonstream request'))
        source = Mock(side_effect=model)
        dialogue = Dialogue(reply, reply_stream=source, answer_prefix_policy='guarded')
        kind, stream = dialogue.turn_stream('什么是电压？')
        self.assertEqual(kind, 'chat')
        with patch('robot.time.perf_counter', return_value=123.):
            self.assertEqual(next(stream), '电压是电势差。')
        self.assertEqual(events, ['placeholder-start', 'placeholder-end', 'content'])
        self.assertEqual(dialogue.first_token_at, 123.)  # raw model token, not release time
        self.assertEqual(''.join(stream), '电流是电荷流率。')
        self.assertEqual(dialogue.last_answer, '电压是电势差。电流是电荷流率。')
        self.assertEqual(dialogue.history[-1]['content'], dialogue.last_answer)
        self.assertEqual(dialogue.quality_issues, ['placeholder_prefix'])
        source.assert_called_once()
        reply.assert_not_called()

    def test_guarded_empty_placeholder_and_echo_finish_with_spoken_history(self):
        from robot import Dialogue
        for text, reason in [('', 'empty'), ('让我想想。', 'placeholder_only'),
                             ('什么是单片机？', 'exact_echo')]:
            with self.subTest(text=text):
                reply = Mock(return_value=text)
                dialogue = Dialogue(reply, answer_prefix_policy='guarded')
                kind, answer = dialogue.turn('什么是单片机？')
                self.assertEqual(kind, 'chat')
                self.assertEqual(answer, '这次没有给出有效回答，请换一种问法。')
                self.assertEqual(dialogue.last_answer, answer)
                self.assertEqual(dialogue.history[-1]['content'], answer)
                self.assertIn(reason, dialogue.quality_issues)
                reply.assert_called_once()

    def test_default_prefix_policy_leaves_original_stream_and_history_unchanged(self):
        from robot import Dialogue
        raw = '让我想想。电压是电势差。'
        dialogue = Dialogue(lambda _: raw)
        self.assertEqual(dialogue.answer_prefix_policy, 'original')
        self.assertEqual(dialogue.turn('什么是电压？'), ('chat', raw))
        self.assertEqual(dialogue.history[-1]['content'], raw)
        self.assertEqual(dialogue.quality_issues, [])
        self.assertIsNone(dialogue.quality_reason)

    def test_prefix_guard_preserves_transforms_and_phatic_acknowledgements(self):
        from robot import Dialogue
        for question, answer, language in [('请重复让我想想。', '让我想想。', 'zh'),
                                            ('请帮我翻译 hello', 'hello', 'zh'),
                                            ('谢谢', '好的。', 'zh'),
                                            ('Thank you', 'Okay.', 'en')]:
            for full_buffer in (False, True):
                with self.subTest(question=question, full_buffer=full_buffer):
                    dialogue = Dialogue(lambda _: answer, language=language,
                                        answer_prefix_policy='guarded', quality_guard=full_buffer)
                    self.assertEqual(dialogue.turn(question), ('chat', answer))
                    self.assertEqual(dialogue.history[-1]['content'], answer)
                    self.assertEqual(dialogue.quality_issues, [])

    def test_both_guards_keep_full_buffer_wait_without_second_censor(self):
        from robot import Dialogue
        events = []
        def model(_):
            events.append('first')
            yield '让我想想。电压是电势差。'
            events.append('tail')
            yield '电流是电荷流率。'
        dialogue = Dialogue(Mock(), reply_stream=model, quality_guard=True,
                            answer_prefix_policy='guarded')
        _, stream = dialogue.turn_stream('什么是电压？')
        self.assertEqual(next(stream), '电压是电势差。')
        self.assertEqual(events, ['first', 'tail'])
        self.assertEqual(''.join(stream), '电流是电荷流率。')
        self.assertEqual(dialogue.history[-1]['content'], '电压是电势差。电流是电荷流率。')

    def test_prefix_limit_closes_raw_model_generator_without_retry(self):
        from robot import Dialogue
        events = []
        def model(_):
            try:
                while True:
                    events.append('next')
                    yield '让我想想。'
            finally:
                events.append('closed')
        reply = Mock(side_effect=AssertionError('no retry'))
        dialogue = Dialogue(reply, reply_stream=model, answer_prefix_policy='guarded')
        _, answer = dialogue.turn('什么是单片机？')
        self.assertIn('没有给出有效回答', answer)
        self.assertEqual(events[-1], 'closed')
        self.assertIn('prefix_limit', dialogue.quality_issues)
        self.assertLess(len(events), 110)
        reply.assert_not_called()

    def test_quality_issues_do_not_leak_into_later_chat_or_tool(self):
        from robot import Dialogue
        reply = Mock(side_effect=['让我想想。', '单片机是一种芯片。'])
        dialogue = Dialogue(reply, answer_prefix_policy='guarded')
        dialogue.turn('什么是单片机？')
        self.assertTrue(dialogue.quality_issues)
        dialogue.turn('它是什么？')
        self.assertEqual(dialogue.quality_issues, [])
        self.assertIsNone(dialogue.quality_reason)
        self.assertEqual(dialogue.turn('声音小一点')[0], 'tool')
        self.assertEqual(dialogue.quality_issues, [])

    def test_guarded_turn_synthesizes_only_filtered_content_and_logs_finite_issues(self):
        import json
        from pathlib import Path
        import tempfile
        import time
        import numpy as np
        from robot import Dialogue, SpokenAudio, run_turn
        reply = Mock(side_effect=AssertionError('no nonstream retry'))
        dialogue = Dialogue(reply, reply_stream=lambda _: iter(['让我想想。', '电压是电势差。']),
                            answer_prefix_policy='guarded')
        speech = Mock()
        speech.recognize.return_value = '什么是电压？'
        speech.tool_audio = {'zh': [SpokenAudio(np.ones(32, dtype='float32'), 16000)]}
        speech.synthesize.return_value = [SpokenAudio(np.full(32, .2, dtype='float32'), 16000)]
        with tempfile.TemporaryDirectory() as directory, \
             patch('robot.play_audio', side_effect=lambda *args: time.perf_counter()) as play:
            target = Path(directory) / 'metrics.jsonl'
            self.assertEqual(run_turn(dialogue, speech, np.zeros(100), None, metrics_path=target), 'chat')
            speech.synthesize.assert_called_once_with('电压是电势差。')
            np.testing.assert_array_equal(play.call_args.args[0], np.full(32, .2, dtype='float32'))
            row = json.loads(target.read_text(encoding='utf8'))
            self.assertEqual(row['answer_prefix_policy'], 'guarded')
            self.assertEqual(row['quality_issues'], ['placeholder_prefix'])
            self.assertEqual(row['answer'], '电压是电势差。')
            self.assertEqual(dialogue.history[-1]['content'], row['answer'])
            self.assertIsNone(row['tool'])
        reply.assert_not_called()

    def test_placeholder_and_empty_have_explicit_completion(self):
        for text in ('', '让我想想。', '好的，请稍等。', '我需要思考一下。'):
            answer, reason = check_answer('什么是单片机？', text)
            self.assertIsNotNone(reason)
            self.assertIn('没有生成有效回答', answer)

    def test_exact_echo_is_rejected(self):
        self.assertEqual(check_answer('什么是单片机？', '什么是单片机。')[1], 'exact_echo')

    def test_real_answer_and_appropriate_repetition_are_preserved(self):
        for question, answer in [('什么是单片机？', '单片机把处理器、内存和外设集成在一颗芯片里。'),
                                 ('请重复 hello', 'hello'),
                                 ('让我想想是什么意思？', '它表示说话者需要时间考虑。'),
                                 ('什么是电流？', '让我想想。电流是电荷的定向移动。')]:
            self.assertEqual(check_answer(question, answer), (answer, None))

    def test_english_placeholder(self):
        self.assertEqual(check_answer('What is a MCU?', "I'll think about it.", 'en')[1], 'placeholder_only')

    def test_dialogue_history_matches_the_spoken_fallback(self):
        from robot import Dialogue
        dialogue = Dialogue(lambda _: '让我想想。', quality_guard=True)
        kind, answer = dialogue.turn('什么是单片机？')
        self.assertEqual(kind, 'chat')
        self.assertEqual(dialogue.quality_reason, 'placeholder_only')
        self.assertEqual(dialogue.history[-1]['content'], answer)
        self.assertIn('没有生成有效回答', answer)
