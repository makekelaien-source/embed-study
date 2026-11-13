import unittest
from itertools import product

from quality_policy import reply_policy, requested_transform, guard_first_content


class PolicyTests(unittest.TestCase):
    def test_knowledge_receives_room_for_conclusion_and_reason(self):
        for text, language in [('什么是单片机？', 'zh'), ('Why is the sky blue?', 'en')]:
            with self.subTest(text=text):
                policy = reply_policy(text, language)
                self.assertEqual(policy.intent, 'knowledge')
                self.assertGreater(policy.max_tokens, 48)
                self.assertLessEqual(policy.max_tokens, 96)
                self.assertNotIn('30', policy.prompt)
                self.assertNotIn('16 words', policy.prompt)

    def test_a_followup_keeps_history_and_requests_new_information(self):
        policy = reply_policy('那能举个例子吗？', history=[{'role': 'assistant', 'content': 'previous'}])
        self.assertEqual(policy.intent, 'followup')
        self.assertIn('不重复上一回答', policy.prompt)
        self.assertEqual(reply_policy('How does it work?', 'en', ['previous']).intent, 'followup')
        self.assertEqual(reply_policy('Can you give a concrete example?', 'en', ['previous']).intent, 'followup')
        self.assertEqual(reply_policy('举个例子。', 'zh', ['previous']).intent, 'followup')

    def test_requested_transform_is_not_accidental_word_mention(self):
        for text in ['请重复 hello', '翻译这句话', 'Please repeat hello', 'Translate this into Chinese']:
            self.assertTrue(requested_transform(text), text)
            self.assertEqual(reply_policy(text).intent, 'transform')
        self.assertFalse(requested_transform('What does repeat mean?'))
        self.assertFalse(requested_transform('解释重复的意思'))
        self.assertTrue(requested_transform('请帮我翻译 hello'))
        self.assertTrue(requested_transform('Could you repeat hello?'))

    def test_smalltalk_keeps_existing_short_budget(self):
        self.assertEqual(reply_policy('你好').max_tokens, 48)
        self.assertEqual(reply_policy('Good morning', 'en').intent, 'chat')

    def test_no_future_or_unexecuted_operation_promises_in_policy(self):
        self.assertIn('不承诺稍后回答', reply_policy('你好').prompt)
        self.assertIn('unperformed operation', reply_policy('Hello', 'en').prompt)

    def test_invalid_language_and_empty_text_are_rejected(self):
        for text, language in [('', 'zh'), ('   ', 'en'), ('hello', 'ja')]:
            with self.assertRaises(ValueError):
                reply_policy(text, language)


class PrefixGuardTests(unittest.TestCase):
    def test_impossible_placeholder_initial_streams_before_next_delta_or_punctuation(self):
        for prefix, question, language in [('单片机把CPU和存储器', '什么是单片机？', 'zh'),
                                            ('电压是两个点之间的', '什么是电压？', 'zh'),
                                            ('A microcontroller integrates', 'What is a microcontroller?', 'en'),
                                            ('Current is the flow of', 'What is current?', 'en')]:
            with self.subTest(prefix=prefix):
                events = []
                def model():
                    events.append('prefix')
                    yield prefix
                    events.append('tail')
                    yield '。' if language == 'zh' else '.'
                stream = guard_first_content(model(), question, language)
                self.assertEqual(next(stream), prefix)
                self.assertEqual(events, ['prefix'])
                self.assertEqual(''.join(stream), '。' if language == 'zh' else '.')

    def test_ambiguous_initials_remain_held_until_a_complete_clause(self):
        for prefix, end, question, language in [('我认为电压是', '电势差。', '电压是什么？', 'zh'),
                                                ('这个芯片集成了', '处理器。', '单片机是什么？', 'zh'),
                                                ('The chip integrates', ' a processor.', 'What is an MCU?', 'en')]:
            with self.subTest(prefix=prefix):
                events = []
                def model():
                    events.append('prefix')
                    yield prefix
                    events.append('end')
                    yield end
                stream = guard_first_content(model(), question, language)
                self.assertEqual(next(stream), prefix + end)
                self.assertEqual(events, ['prefix', 'end'])
                self.assertEqual(list(stream), [])

    def test_every_current_placeholder_atom_initial_is_covered_and_never_leaks(self):
        from answer_quality import normalize
        from quality_policy import _placeholder, _PLACEHOLDER_INITIALS, _ENGLISH_PLACEHOLDERS
        atoms = {'好的', '好', '嗯', '这个问题很有趣', '这是个好问题', '这是一个好问题',
                 '这个问题很重要', '请稍等', '稍等', '等一下', '正在思考', '正在查询',
                 '我需要一点时间思考'}
        atoms.update(''.join(parts) for parts in product(
            ('', '这个问题', '关于这个问题', '对于这个问题'),
            ('', '我', '我需要', '我要', '我会', '让我'), ('', '先'),
            ('思考一下', '想一想', '想想', '考虑一下', '查一下', '查询一下', '查一查')))
        atoms.update(''.join(parts) for parts in product(
            ('我会', '我将', '稍后', '一会儿', '等会儿', '然后'), ('', '再'),
            ('回答你', '答复你', '告诉你', '给你答复')))
        atoms.update('我会' + ''.join(parts) + '你' for parts in product(
            ('', '认真'), ('思考', '考虑'), ('', '一下'), ('后', '之后'),
            ('', '再'), ('告诉', '回答', '答复')))
        atoms.update(_ENGLISH_PLACEHOLDERS)
        # Also exercise the Chinese regex's outer concatenation closure.
        atoms.update(atom + '请稍等' for atom in tuple(atoms) if not atom.isascii())
        for atom in atoms:
            with self.subTest(atom=atom):
                self.assertTrue(_placeholder(atom))
                self.assertIn(normalize(atom)[0], _PLACEHOLDER_INITIALS)
                issues = []
                result = ''.join(guard_first_content(list(atom) + ['。'], '什么是单片机？', issues=issues))
                self.assertEqual(result, '这次没有给出有效回答，请换一种问法。')
                self.assertTrue(set(issues) & {'placeholder_prefix', 'placeholder_only'})

    def test_punctuation_leading_chunks_normalize_before_early_initial_test(self):
        from answer_quality import normalize
        source = [' “', '让我想', '想。”', '电压是电势差。']
        issues = []
        result = ''.join(guard_first_content(source, '什么是电压？', issues=issues))
        self.assertEqual(normalize(result), '电压是电势差')
        self.assertNotIn('让我想想', result)
        self.assertIn('placeholder_prefix', issues)

    def test_question_prefix_split_across_deltas_and_clauses_is_never_released_early(self):
        for source, question in [(['电', '压', '是', '什', '么', '？'], '电压是什么？'),
                                 (['电压，', '是', '什', '么', '？'], '电压是什么？'),
                                 (['A ', 'microcontroller', '？'], 'A microcontroller?')]:
            with self.subTest(source=source):
                issues = []
                result = ''.join(guard_first_content(source, question, issues=issues))
                self.assertIn('没有给出有效回答', result)
                self.assertIn('exact_echo', issues)

    def test_placeholder_prefix_is_not_released_as_first_content(self):
        issues = []
        output = ''.join(guard_first_content(['让我想', '想。单片机是', '集成处理器和存储器的芯片。'],
                                            '什么是单片机？', issues=issues))
        self.assertEqual(output, '单片机是集成处理器和存储器的芯片。')
        self.assertIn('placeholder_prefix', issues)

    def test_only_placeholder_or_empty_has_an_explicit_end(self):
        for deltas in [[], [''], ['好的，', '请稍等。'], ['这个问题我需要思考一下。']]:
            output = ''.join(guard_first_content(deltas, '什么是单片机？'))
            self.assertIn('没有给出有效回答', output)

    def test_prefix_gate_streams_following_deltas_before_generation_finishes(self):
        events = []
        def model():
            events.append('first')
            yield '电压是电势差。'
            events.append('second')
            yield '电流是电荷流率。'
        output = guard_first_content(model(), '电压是什么？')
        self.assertEqual(next(output), '电压是电势差。')
        self.assertEqual(events, ['first'])
        self.assertEqual(next(output), '电流是电荷流率。')
        self.assertEqual(events, ['first', 'second'])
        self.assertEqual(list(output), [])

    def test_normal_example_and_decimal_are_preserved(self):
        source = ['电压为3.', '3伏。', '这是一个例子。']
        self.assertEqual(''.join(guard_first_content(source, '举一个例子')), ''.join(source))

    def test_exact_echo_is_suppressed_but_requested_repetition_is_preserved(self):
        issues = []
        output = ''.join(guard_first_content(['什么是单片机。'], '什么是单片机？', issues=issues))
        self.assertIn('没有给出有效回答', output)
        self.assertIn('exact_echo', issues)
        for question in ['请重复让我想想。', '请帮我翻译这句话', 'Please repeat let me think.']:
            self.assertEqual(''.join(guard_first_content(['让我想想。'], question)), '让我想想。')

    def test_echo_with_following_answer_keeps_the_answer(self):
        output = ''.join(guard_first_content(['什么是单片机？', '单片机在一颗芯片上集成CPU和存储器。'], '什么是单片机？'))
        self.assertEqual(output, '单片机在一颗芯片上集成CPU和存储器。')

    def test_placeholder_words_inside_an_explanation_are_not_removed(self):
        text = '让我想想的意思是需要一点考虑时间。'
        self.assertEqual(''.join(guard_first_content([text], '这句话是什么意思？')), text)

    def test_conversational_acknowledgement_is_not_a_failed_knowledge_answer(self):
        for question, answer in [('谢谢', '好的。'), ('Thank you', 'Okay.'), ('是的', '好的。'),
                                 ('嗯', '嗯。'), ('是的', '是的。'), ('谢谢', '谢谢。')]:
            self.assertEqual(''.join(guard_first_content([answer], question)), answer)
        self.assertIn('没有给出有效回答', ''.join(guard_first_content(['让我想想。'], '谢谢')))

    def test_prefix_limit_does_not_count_tail_after_a_valid_first_clause(self):
        text = '电压是电势差。' + '后续内容。' * 100
        self.assertEqual(''.join(guard_first_content([text], '电压是什么？', max_prefix_chars=20)), text)

    def test_english_placeholder_prefix_and_explicit_end(self):
        issues = []
        output = ''.join(guard_first_content(['Okay, ', 'let me think. ', 'A microcontroller integrates a processor and memory.'],
                                            'What is a microcontroller?', 'en', issues))
        self.assertEqual(output, ' A microcontroller integrates a processor and memory.')
        self.assertIn('placeholder_prefix', issues)
        self.assertIn('did not produce', ''.join(guard_first_content(["I'll get back to you."], 'What is PWM?', 'en')))

    def test_repeated_placeholder_work_is_bounded_and_closes_source(self):
        events = []
        def model():
            try:
                while True:
                    events.append('next')
                    yield '让我想想。'
            finally:
                events.append('closed')
        issues = []
        output = ''.join(guard_first_content(model(), '什么是单片机？', issues=issues, max_prefix_chars=20))
        self.assertIn('没有给出有效回答', output)
        self.assertEqual(events[-1], 'closed')
        self.assertLess(len(events), 10)
        self.assertIn('prefix_limit', issues)


if __name__ == '__main__':
    unittest.main()
