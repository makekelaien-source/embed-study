import tempfile
from pathlib import Path
import unittest

from robot import Dialogue, Endpoint, audio_format, resample_audio, resolve_voice, split_clauses


class VoiceSelectionTests(unittest.TestCase):
    def test_each_language_has_its_own_default(self):
        with tempfile.TemporaryDirectory() as folder:
            assets = Path(folder)
            self.assertEqual(resolve_voice(assets, "zh"), "melo")
            self.assertEqual(resolve_voice(assets, "en"), "lessac")

    def test_saved_choices_are_independent_and_can_be_overridden(self):
        with tempfile.TemporaryDirectory() as folder:
            assets = Path(folder)
            (assets / "voices.json").write_text('{"zh":"zh-ll-2","en":"ryan"}', encoding="utf8")
            self.assertEqual(resolve_voice(assets, "zh"), "zh-ll-2")
            self.assertEqual(resolve_voice(assets, "en"), "ryan")
            self.assertEqual(resolve_voice(assets, "en", "lessac"), "lessac")
            self.assertEqual(resolve_voice(assets, "en"), "ryan")

    def test_an_english_voice_cannot_be_used_for_chinese(self):
        with self.assertRaisesRegex(ValueError, "ryan"):
            resolve_voice(Path("."), "zh", "ryan")


class AudioTests(unittest.TestCase):
    def test_fixed_rate_stereo_device_uses_supported_format(self):
        def check(rate, channels):
            return (rate, channels) == (48000, 2)

        self.assertEqual(audio_format(16000, 48000, 2, check), (48000, 2))

    def test_resampling_preserves_duration_and_audible_tone(self):
        import numpy as np

        source = np.sin(2 * np.pi * 1000 * np.arange(4800) / 48000).astype("float32")
        result = resample_audio(source, 48000, 16000)
        self.assertEqual(result.shape, (1600,))
        expected = np.sin(2 * np.pi * 1000 * np.arange(1600) / 16000)
        self.assertLess(np.max(np.abs(result[16:-16] - expected[16:-16])), 0.01)


class DialogueTests(unittest.TestCase):
    def test_english_uses_english_prompt_and_retains_context(self):
        def reply(messages):
            self.assertIn("Reply in English", messages[0]["content"])
            return messages[1]["content"]

        dialogue = Dialogue(reply, language="en")
        dialogue.turn("The robot is named Willow.")
        self.assertEqual(dialogue.turn("What is its name?"), ("chat", "The robot is named Willow."))
        self.assertEqual(dialogue.turn(" END   CHAT! "), ("end", ""))
        self.assertEqual(dialogue.turn("New topic."), ("chat", "New topic."))

    def test_english_commands_require_the_entire_utterance(self):
        dialogue = Dialogue(lambda messages: "move forward", language="en")
        self.assertEqual(dialogue.turn("Move forward."), ("command", "FORWARD"))
        self.assertEqual(dialogue.turn("Should I move forward?"), ("chat", "move forward"))
        self.assertEqual(dialogue.turn("stop moving"), ("command", "STOP"))

    def test_followup_gets_context_until_session_ends(self):
        def reply(messages):
            if messages[-1]["content"] == "它叫什么？":
                return messages[-2]["content"] if len(messages) > 2 else "我不知道。"
            return "叫小蓝。"

        dialogue = Dialogue(reply)
        dialogue.turn("给机器人取个名字。")
        self.assertEqual(dialogue.turn("它叫什么？"), ("chat", "叫小蓝。"))
        self.assertEqual(dialogue.turn("结束对话。"), ("end", ""))
        self.assertEqual(dialogue.turn("它叫什么？"), ("chat", "我不知道。"))

    def test_movement_requires_an_entire_user_utterance(self):
        dialogue = Dialogue(lambda messages: "前进")
        self.assertEqual(dialogue.turn("前进。"), ("command", "FORWARD"))
        self.assertEqual(dialogue.turn("解释一下怎么前进。"), ("chat", "前进"))
        self.assertEqual(dialogue.turn("前进，右转"), ("chat", "前进"))


class StreamingTests(unittest.TestCase):
    def test_clauses_split_on_commas_and_stop_punctuation(self):
        deltas = iter(["你好，", "今天", "天气", "不错。", "我们", "出门吧！"])
        self.assertEqual(list(split_clauses(deltas, "，。！？；")),
                         ["你好，", "今天天气不错。", "我们出门吧！"])

    def test_english_clauses_keep_the_spaces_between_them(self):
        deltas = iter(["Hello, ", "the robot is named ", "Willow."])
        self.assertEqual(list(split_clauses(deltas, ",.!?;")),
                         ["Hello,", " the robot is named Willow."])

    def test_turn_stream_feeds_clauses_then_saves_the_full_answer(self):
        def reply_stream(messages):
            yield "好的，"
            yield "它叫小蓝。"

        dialogue = Dialogue(lambda messages: "", language="zh", reply_stream=reply_stream)
        kind, stream = dialogue.turn_stream("它叫什么？")
        self.assertEqual(kind, "chat")
        self.assertEqual(list(stream), ["好的，", "它叫小蓝。"])
        self.assertEqual(dialogue.last_answer, "好的，它叫小蓝。")
        self.assertEqual(dialogue.history[-1]["content"], "好的，它叫小蓝。")

    def test_turn_falls_back_to_the_plain_reply_when_no_stream_exists(self):
        dialogue = Dialogue(lambda messages: "好的。它叫小蓝。")
        self.assertEqual(dialogue.turn("它叫什么？"), ("chat", "好的。它叫小蓝。"))


class EndpointTests(unittest.TestCase):
    def test_initial_silence_and_trailing_silence_are_distinct(self):
        endpoint = Endpoint()
        self.assertEqual(endpoint.feed(False, 14.9), "listen")
        self.assertEqual(endpoint.feed(False, 15), "idle")
        endpoint = Endpoint()
        self.assertEqual(endpoint.feed(True, 14.9), "listen")
        self.assertEqual(endpoint.feed(False, 15.1), "listen")
        self.assertEqual(endpoint.feed(False, 15.7), "done")

    def test_continuous_speech_has_a_length_limit(self):
        endpoint = Endpoint()
        self.assertEqual(endpoint.feed(True, 1), "listen")
        self.assertEqual(endpoint.feed(True, 13), "done")

    def test_speech_after_idle_deadline_does_not_reopen_session(self):
        endpoint = Endpoint()
        self.assertEqual(endpoint.feed(False, 14.9), "listen")
        self.assertEqual(endpoint.feed(True, 15.1), "idle")
