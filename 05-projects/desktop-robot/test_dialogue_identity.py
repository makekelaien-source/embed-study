import unittest

from robot import Dialogue


class DialogueIdentityIntegrationTests(unittest.TestCase):
    def test_identity_bypasses_generation_and_replaces_polluted_context(self):
        def fail(messages):
            self.fail('Identity must not call the model')
        dialogue = Dialogue(fail)
        dialogue.history.append({'role': 'assistant', 'content': '我叫小智。'})
        self.assertEqual(dialogue.turn('你是谁？'),
                         ('clarification', '我叫鸣人，是你的语音助手。'))
        self.assertEqual(dialogue.history[-1]['content'], '我叫鸣人，是你的语音助手。')

    def test_hardware_capability_bypasses_model_in_english(self):
        dialogue = Dialogue(lambda messages: self.fail('No invented hardware'), language='en')
        kind, answer = dialogue.turn('Can you control the tracks?')
        self.assertEqual(kind, 'clarification')
        self.assertIn('not connected', answer)

    def test_motion_question_and_quotation_do_not_dispatch_commands(self):
        for language, texts in [('zh', ['前进？', '“前进”']),
                                ('en', ['Move forward?', '"move forward"'])]:
            for text in texts:
                with self.subTest(text=text):
                    self.assertNotEqual(Dialogue(lambda m: 'Answer', language=language).turn(text)[0], 'command')

    def test_valid_commands_still_reach_simulation(self):
        self.assertEqual(Dialogue(lambda m: '').turn('前进。'), ('command', 'FORWARD'))

    def test_translation_is_forwarded_unchanged_with_authoritative_identity(self):
        def reply(messages):
            self.assertEqual(messages[-1]['content'], '翻译“你叫小智”')
            self.assertIn('鸣人', messages[0]['content'])
            self.assertIn('未接入', messages[0]['content'])
            return 'Your name is Xiaozhi.'
        for mode in ('original', 'compact'):
            self.assertEqual(Dialogue(reply, prompt_mode=mode).turn('翻译“你叫小智”'),
                             ('chat', 'Your name is Xiaozhi.'))
