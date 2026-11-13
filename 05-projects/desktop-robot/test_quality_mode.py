"""Quality mode preserves content boundaries; no model or hardware is invoked."""
import unittest
from unittest.mock import Mock

from robot import COMPACT_PROMPTS, PROMPTS, QUALITY_PROMPTS, Dialogue, LocalChat, select_prompt


class QualityModeTests(unittest.TestCase):
    def chunks(self, text, language='zh', mode='quality', **options):
        dialogue = Dialogue(Mock(side_effect=AssertionError('stream expected')),
                            language=language, prompt_mode=mode,
                            reply_stream=lambda messages: iter(text), **options)
        kind, stream = dialogue.turn_stream('解释电路' if language == 'zh' else 'Explain this circuit')
        self.assertEqual(kind, 'chat')
        return dialogue, list(stream)

    def test_select_prompt_routes_each_language_without_legacy_restriction(self):
        for language in ('zh', 'en'):
            self.assertEqual(select_prompt('quality', language), QUALITY_PROMPTS[language])
            self.assertEqual(select_prompt('original', language), PROMPTS[language])
            self.assertEqual(select_prompt('compact', language), COMPACT_PROMPTS[language])
            dialogue = Dialogue(lambda m: '', language=language, prompt_mode='quality')
            self.assertIn(QUALITY_PROMPTS[language], dialogue.prompt)
            for restriction in ('30字', '30 个字', '16 words', 'ONE short spoken sentence'):
                self.assertNotIn(restriction, dialogue.prompt)

    def test_chinese_first_sentence_keeps_late_negation_and_comma(self):
        first = '即使电源指示灯已经完全熄灭，电容也不一定放电完成。'
        rest = '测量确认后再操作。'
        for prefix in ('original', 'guarded'):
            with self.subTest(prefix=prefix):
                dialogue, chunks = self.chunks(first + rest, answer_prefix_policy=prefix)
                self.assertEqual(chunks, [first, rest])
                self.assertGreater(len(chunks[0]), 16)
                self.assertIn('不一定', chunks[0])
                self.assertEqual(dialogue.last_answer, first + rest)
                self.assertEqual(dialogue.first_clause_chars, 0)

    def test_english_first_sentence_keeps_qualification_and_comma(self):
        first = 'Even when the power indicator goes dark, the capacitor is not necessarily discharged.'
        rest = ' Measure it before touching the circuit.'
        for prefix in ('original', 'guarded'):
            with self.subTest(prefix=prefix):
                _, chunks = self.chunks(first + rest, language='en', answer_prefix_policy=prefix)
                self.assertEqual(chunks, [first, rest])
                self.assertIn('not necessarily', chunks[0])

    def test_quality_overrides_requested_first_chunk_limit(self):
        text = '接触线路之前必须先检查所有电容的残余电压，不可以仅凭电灯熄灭判断安全。'
        _, chunks = self.chunks(text, first_clause_chars=8)
        self.assertEqual(chunks, [text])

    def test_quality_decimal_and_protected_span_stay_intact(self):
        text = 'A voltage of 12.5 V is not safe in every situation, so assess the circuit first.'
        _, chunks = self.chunks(text, language='en')
        self.assertEqual(chunks, [text])

    def test_legacy_chinese_still_uses_character_limit(self):
        text = '整理桌面的时候先把不用的物品收起来然后再擦桌子。'
        for mode in ('original', 'compact'):
            with self.subTest(mode=mode):
                dialogue, chunks = self.chunks(text, mode=mode)
                self.assertLessEqual(len(chunks[0]), 16)
                self.assertEqual(''.join(chunks), text)
                self.assertEqual(dialogue.first_clause_chars, 16)

    def test_legacy_english_still_splits_at_commas(self):
        _, chunks = self.chunks('Keep it dry, and disconnect power.', language='en', mode='original')
        self.assertEqual(chunks, ['Keep it dry,', ' and disconnect power.'])

    def test_quality_truncation_withholds_residual_and_reports_explicit_error(self):
        class TruncatedChat:
            def __init__(self, answer):
                self.answer = answer
                self.metrics = {}
                self.closed = False

            def reply_stream(self, messages):
                try:
                    yield from self.answer
                    self.metrics['finish_reason'] = 'length'
                finally:
                    self.closed = True

        for language, complete, tail in (
                ('zh', '电容可能储存电荷。', '接触前不应该'),
                ('en', 'Capacitors can store charge.', ' You must not')):
            for prefix in ('original', 'guarded'):
                for buffered in (False, True):
                    with self.subTest(language=language, prefix=prefix, buffered=buffered):
                        chat = TruncatedChat(complete + tail)
                        dialogue = Dialogue(lambda m: '', language=language, prompt_mode='quality',
                                            reply_stream=chat.reply_stream,
                                            answer_prefix_policy=prefix, quality_guard=buffered)
                        _, stream = dialogue.turn_stream('解释电路' if language == 'zh' else 'Explain this circuit')
                        emitted = []
                        with self.assertRaisesRegex(RuntimeError, 'exceeded token budget.*unfinished sentence withheld'):
                            for clause in stream:
                                emitted.append(clause)
                        self.assertEqual(emitted, [] if buffered else [complete])
                        self.assertNotIn(tail, ''.join(emitted))
                        self.assertIn('generation_truncated', dialogue.quality_issues)
                        self.assertEqual(dialogue.last_answer, '')
                        self.assertEqual(len(dialogue.history), 0)
                        self.assertTrue(chat.closed)

    def test_quality_truncation_before_first_sentence_emits_nothing(self):
        class Chat:
            metrics = {}
            def reply_stream(self, messages):
                yield '仅当电路已经完全'
                self.metrics = {'finish_reason': 'length'}
        dialogue = Dialogue(lambda m: '', prompt_mode='quality', reply_stream=Chat().reply_stream)
        _, stream = dialogue.turn_stream('解释电路')
        with self.assertRaisesRegex(RuntimeError, 'unfinished sentence withheld'):
            next(stream)
        self.assertIn('generation_truncated', dialogue.quality_issues)

    def test_legacy_truncation_behavior_is_unchanged(self):
        class Chat:
            metrics = {}
            def reply_stream(self, messages):
                yield '尚未完成'
                self.metrics = {'finish_reason': 'length'}
        for mode in ('original', 'compact'):
            dialogue = Dialogue(lambda m: '', prompt_mode=mode, reply_stream=Chat().reply_stream)
            self.assertEqual(dialogue.turn('解释电路'), ('chat', '尚未完成'))
            self.assertNotIn('generation_truncated', dialogue.quality_issues)

    def test_local_chat_token_budget_is_configurable_without_changing_other_fields(self):
        chat = LocalChat(8080)
        messages = [{'role': 'user', 'content': 'Explain arrays'}]
        baseline = chat.chat_body(messages)
        self.assertEqual(baseline['max_tokens'], 48)
        chat.max_tokens = 160
        custom = chat.chat_body(messages)
        self.assertEqual(custom, {**baseline, 'max_tokens': 160})
        self.assertEqual(chat.chat_body(messages, stream=True), {**custom, 'stream': True})
        chat.max_tokens = 512
        self.assertEqual(chat.chat_body(messages)['max_tokens'], 512)


if __name__ == '__main__':
    unittest.main()
