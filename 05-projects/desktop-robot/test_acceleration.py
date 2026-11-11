import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from robot import Endpoint, Voice
from acceleration import split_first_clause, server_options, warmup_pipeline
from summarize_speed import stats


class AccelerationTests(unittest.TestCase):
    def test_frequency_restore_never_exceeds_the_hardware_advertised_limit(self):
        from restore_frequency import rated_maximum
        self.assertEqual(rated_maximum("2002000","416000 1716000 2002000 2200000"),2002000)
        self.assertEqual(rated_maximum("1794000","416000 1716000 1794000"),1794000)
        with self.assertRaises(ValueError):rated_maximum("100","200 300")
    def test_profile_keeps_language_speeds_independent_and_bench_has_no_mic(self):
        from run_fast import profile_arguments
        profile={"common":{"threads":2},"language_overrides":{"zh":{"speed":.9},"en":{"speed":1}},
                 "microphone":{"input_device":0}}
        zh=profile_arguments(profile,"zh",False)
        en=profile_arguments(profile,"en",True)
        self.assertEqual(zh[zh.index("--speed")+1],"0.9")
        self.assertEqual(en[en.index("--speed")+1],"1")
        self.assertIn("--input-device",zh)
        self.assertNotIn("--input-device",en)
    def test_benchmark_reuses_identical_pcm_without_resynthesizing(self):
        import numpy as np
        from acceleration import cached_input
        create=Mock(return_value=np.linspace(-.1,.1,1600,dtype="float32"))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"input.wav"
            first=cached_input(path,create)
            second=cached_input(path,create)
            np.testing.assert_array_equal(first,second)
            create.assert_called_once()
    def test_theresa_archive_model_name_is_accepted(self):
        from acceleration import tts_model_path
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"theresa.onnx").touch()
            self.assertEqual(tts_model_path(root),root/"theresa.onnx")
    def test_report_uses_nearest_rank_p90_and_does_not_claim_quality(self):
        result=stats([{"response_s":i} for i in range(1,16)])
        self.assertEqual(result["median_s"],8)
        self.assertEqual(result["p90_s"],14)
        self.assertEqual(result["content_quality"],"not_scored")
    def test_first_clause_is_available_before_a_late_punctuation(self):
        text = "整理桌面的时候先把不用的物品收起来然后再擦桌子。"
        source = iter(text)
        chunks = split_first_clause(source, "，。！？；", 16)
        first = next(chunks)
        self.assertLessEqual(len(first), 16)
        self.assertEqual(first + "".join(chunks), text)

    def test_numbers_words_and_pairs_are_not_split(self):
        for text in ["建议先把温度设置为123456789.25度然后观察。",
                     "你可以先使用OpenSourceRobot工具来试一试。",
                     "建议先把这个（蓝色的圆形打印外壳）放在桌上。",
                     "他说“先整理桌面，然后再休息”比较合适。",
                     "你可以先看看《离线桌面机器人制作手册》然后再装配。"]:
            chunks = list(split_first_clause(iter(text), "，。！？；", 16))
            self.assertEqual("".join(chunks), text)
            for protected in ["123456789.25", "OpenSourceRobot", "（蓝色的圆形打印外壳）", "“先整理桌面，然后再休息”", "《离线桌面机器人制作手册》"]:
                if protected in text:
                    self.assertTrue(any(protected in chunk for chunk in chunks), chunks)

    def test_english_remains_punctuation_based(self):
        text = "Please keep the OpenSourceRobot on your desk. Then rest."
        self.assertEqual(list(split_first_clause(iter(text), ",.!?;", 0)),
                         ["Please keep the OpenSourceRobot on your desk.", " Then rest."])

    def test_streaming_decimal_is_not_mistaken_for_a_sentence_end(self):
        text = "Use 12.5 grams. Then wait."
        chunks = list(split_first_clause(iter(text), ",.!?;", 0))
        self.assertEqual(chunks, ["Use 12.5 grams.", " Then wait."])

    def test_long_protected_token_is_released_when_the_token_ends(self):
        text="12345678901234567.8然后再观察温度变化。"
        chunks=split_first_clause(iter(text),"，。！？；",16)
        self.assertEqual(next(chunks),"12345678901234567.8")

    def test_endpoint_has_configurable_silence(self):
        ep = Endpoint(silence_seconds=0.45)
        ep.feed(True, 1)
        self.assertEqual(ep.feed(False, 1.44), "listen")
        self.assertEqual(ep.feed(False, 1.46), "done")

    def test_batch_threads_have_separate_affinity(self):
        flags = server_options(2, 8, "6-7", "0-7")
        self.assertEqual(flags[flags.index("--threads-batch")+1], "8")
        self.assertEqual(flags[flags.index("--cpu-range-batch")+1], "0-7")
        self.assertEqual(flags[flags.index("--cpu-range")+1], "6-7")

    def test_warmup_does_not_create_a_user_dialogue(self):
        import numpy as np
        speech = Mock()
        audio = Mock(samples=np.zeros(1600, dtype="float32"), sample_rate=16000)
        speech.synthesize.return_value = [audio]
        chat = Mock()
        result = warmup_pipeline(speech, chat, "zh", "固定系统提示")
        self.assertGreaterEqual(result["total_s"], 0)
        self.assertEqual(chat.request.call_args.args[1]["messages"][0],
                         {"role": "system", "content": "固定系统提示"})
        speech.recognize.assert_called_once()

    def test_speed_reaches_the_actual_chinese_tts_engine(self):
        voice = Voice.__new__(Voice)
        voice.language, voice.speaker_id, voice.speed = "zh", 0, 0.9
        voice.tts = Mock()
        list(voice.synthesize("你好。"))
        self.assertEqual(voice.tts.generate.call_args.kwargs["speed"], 0.9)
