import unittest
from datetime import datetime, timezone
from pathlib import Path
from device_status import DeviceStatus, is_cpu_temperature_request


class DeviceStatusTests(unittest.TestCase):
    def make(self, data):
        root = Path('/fake')
        def read(path):
            value = data[str(path).replace('\\', '/')]
            if isinstance(value, Exception):
                raise value
            return value
        return DeviceStatus(root=root, read_text=read,
                            list_zones=lambda _: [root / name for name in sorted({key.split('/')[2] for key in data})],
                            clock=lambda: datetime(2026, 11, 13, tzinfo=timezone.utc))

    def test_direct_queries(self):
        for text in ('CPU现在温度多少？', '当前CPU温度是多少', '现在CPU有多热',
                     '请帮我查一下处理器温度', '你的CPU温度是多少？', '香橙派温度多少',
                     'What is the current CPU temperature?', 'read cpu temperature',
                     'Please check the processor temperature now', 'CPU temperature', "What's the CPU temperature?", 'How hot is your CPU now?'):
            with self.subTest(text=text):
                self.assertTrue(is_cpu_temperature_request(text))

    def test_recorded_query_and_local_word_order_variants(self):
        for text in ('这块香橙派现在的CPU温度多少？',
                     '这块板子当前的处理器温度是多少',
                     '请告诉我这台机器人现在的 CPU 温度',
                     '现在这块开发板的CPU温度有几度',
                     '本机CPU目前的温度是多少度',
                     '请查看你的处理器当前的温度',
                     '此刻香橙派的芯片温度多少'):
            with self.subTest(text=text):
                self.assertTrue(is_cpu_temperature_request(text))
                # Missing sensors must return a tool failure, never call the LLM.
                result = self.make({}).execute(text)
                self.assertEqual(result['tool'], 'read_cpu_temperature')
                self.assertFalse(result['ok'])
        for text in ('这块香橙派现在的CPU温度多少才正常',
                     '请解释这块板子CPU温度的含义',
                     '如果这块香橙派现在的CPU温度太高怎么办'):
            self.assertIsNone(self.make({}).execute(text))

    def test_not_general_knowledge_or_quoted(self):
        for text in ('CPU温度是什么', 'CPU温度多少正常', '如何测CPU温度', 'CPU为什么发热',
                     '不要查CPU温度', '如果CPU温度太高怎么办', '请解释CPU温度',
                     '他说“CPU温度多少”', 'What is a safe CPU temperature?',
                     'Why does CPU temperature increase', 'How do I read CPU temperature',
                     'What should the CPU temperature be?', 'temperature of the sun',
                     'tell me CPU temperature and delete files'):
            with self.subTest(text=text):
                self.assertFalse(is_cpu_temperature_request(text))

    def test_two_real_cpu_zones_and_no_gpu(self):
        status = self.make({'/fake/thermal_zone0/type': 'cpul_thermal_zone',
                            '/fake/thermal_zone0/temp': '46234',
                            '/fake/thermal_zone1/type': 'cpub_thermal_zone',
                            '/fake/thermal_zone1/temp': '47891',
                            '/fake/thermal_zone2/type': 'gpu_thermal_zone',
                            '/fake/thermal_zone2/temp': '99000',
                            '/fake/thermal_zone3/type': 'cpul_idle_zone',
                            '/fake/thermal_zone3/temp': '100000'})
        result = status.execute('CPU温度')
        self.assertTrue(result['ok'])
        self.assertEqual(result['celsius'], 47.891)
        self.assertEqual(len(result['zones']), 2)
        self.assertEqual(result['unit'], 'celsius')
        self.assertEqual(result['read_at'], '2026-11-13T00:00:00+00:00')
        self.assertIn('47.9', result['answer'])

    def test_missing_sensors(self):
        result = self.make({}).execute('CPU temperature', 'en')
        self.assertFalse(result['ok'])
        self.assertNotIn('celsius', result)
        self.assertIn('unknown', result['answer'])

    def test_invalid_and_failed_reads(self):
        for bad in ('nan', '42.3', '999999', '', PermissionError('denied')):
            with self.subTest(bad=bad):
                result = self.make({'/fake/thermal_zone0/type': 'cpu-thermal',
                                    '/fake/thermal_zone0/temp': bad}).execute('CPU温度')
                self.assertFalse(result['ok'])
                self.assertNotIn('celsius', result)
                self.assertIn('无法确认', result['answer'])

    def test_unrelated_does_not_read(self):
        def fail(_):
            raise AssertionError('Unexpected read')
        self.assertIsNone(DeviceStatus(list_zones=fail).execute('What is a CPU?'))

    def test_fresh_read_every_request(self):
        data = {'/fake/thermal_zone0/type': 'cpu-thermal', '/fake/thermal_zone0/temp': '40000'}
        tool = self.make(data)
        self.assertEqual(tool.execute('CPU温度')['celsius'], 40)
        data['/fake/thermal_zone0/temp'] = '51000'
        self.assertEqual(tool.execute('CPU温度')['celsius'], 51)


if __name__ == '__main__':
    unittest.main()

