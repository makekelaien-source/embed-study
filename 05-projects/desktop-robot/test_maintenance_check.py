import json
from pathlib import Path
import tempfile
import unittest

from maintenance_check import (collect_sample, filtered_audio_parameters, observe,
                               parse_service_show, summarize, thermal_stop_reasons)


class BoardFixture:
    def __init__(self, directory):
        self.root = Path(directory) / 'board'
        self.project = Path(directory) / 'robot'
        for name, text in {
            'sys/class/thermal/thermal_zone0/type': 'cpu-thermal\n',
            'sys/class/thermal/thermal_zone0/temp': '51000\n',
            'sys/class/thermal/thermal_zone7/type': 'skin_zone\n',
            'sys/class/thermal/thermal_zone7/temp': '34000\n',
            'sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq': '1716000\n',
            'sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq': '1200000\n',
            'proc/meminfo': 'MemTotal: 8192000 kB\nMemAvailable: 5123000 kB\n',
            'proc/123/status': 'Name: python\n',
            'proc/456/cmdline': '/venv/bin/python\0/home/orangepi/desktop-robot/robot.py\0'
                                '--threshold\0.005\0--min-voice-ms\0' '200\0'
                                '--preroll-ms=500\0--vad\0rms\0'
                                '--api-key\0VERY_SECRET_KEY\0--ssid\0SECRET_NETWORK\0',
            'service-show.txt': 'ActiveState=active\nSubState=running\nNRestarts=0\nMainPID=123\n'
                                'Environment=SECRET_ENV\n',
        }.items():
            self.write(name, text)
        ready = self.project / '.local/service-ready.json'
        ready.parent.mkdir(parents=True)
        ready.write_text(json.dumps({'state': 'ready', 'pid': 456, 'extra_secret': 'SECRET_READY'}), encoding='utf8')

    def write(self, relative, text):
        destination = self.root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding='utf8')

    def sample(self):
        return collect_sample(self.root, self.project, service_reader=lambda:
                              parse_service_show((self.root / 'service-show.txt').read_text(encoding='utf8')))


class FakeClock:
    def __init__(self):
        self.now = 0.
        self.delays = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.delays.append(seconds)
        self.now += seconds


class MaintenanceTests(unittest.TestCase):
    def test_linux_fixture_reads_actual_files_and_excludes_private_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            row = BoardFixture(directory).sample()
        self.assertEqual(row['errors'], [])
        self.assertEqual(row['thermal'][0], {'zone': 0, 'name': 'cpu-thermal', 'temperature_c': 51.})
        self.assertEqual(row['thermal'][1]['temperature_c'], 34.)
        self.assertEqual(row['policy6'], {'max_khz': 1716000, 'current_khz': 1200000})
        self.assertEqual(row['mem_available_kib'], 5123000)
        self.assertTrue(row['service']['main_pid_exists'])
        self.assertTrue(row['ready']['pid_exists'])
        self.assertTrue(row['ready']['robot_process'])
        self.assertEqual(row['ready']['audio_parameters']['preroll_ms'], 500.)
        self.assertEqual(row['ready']['audio_parameters']['min_voice_ms'], 200.)
        self.assertEqual(row['ready']['audio_parameters']['vad'], 'rms')
        self.assertNotIn('SECRET', json.dumps(row))
        self.assertNotIn('Environment', row['service'])

    def test_missing_or_invalid_facts_never_become_zero_or_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            board = BoardFixture(directory)
            board.write('sys/class/thermal/thermal_zone0/temp', 'nan')
            board.write('sys/class/thermal/thermal_zone7/type', 'other_zone')
            board.write('proc/meminfo', 'MemTotal: 8192000 kB')
            (board.root / 'sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq').unlink()
            (board.root / 'proc/456/cmdline').unlink()
            row = board.sample()
        self.assertIsNone(row['thermal'][0]['temperature_c'])
        self.assertIsNone(row['policy6']['current_khz'])
        self.assertIsNone(row['mem_available_kib'])
        self.assertFalse(row['ready']['robot_process'])
        self.assertGreater(len(row['errors']), 0)
        self.assertIsNone(summarize([row])['skin_max_c'])

    def test_stale_ready_pid_and_wrong_process_are_not_confirmed(self):
        with tempfile.TemporaryDirectory() as directory:
            board = BoardFixture(directory)
            board.write('proc/456/cmdline', '/usr/bin/unrelated\0--threshold\0.01\0')
            row = board.sample()
            self.assertTrue(row['ready']['pid_exists'])
            self.assertFalse(row['ready']['robot_process'])
            self.assertTrue(row['errors'])
            (board.project / '.local/service-ready.json').write_text('{"state":"ready","pid":999}', encoding='utf8')
            row = board.sample()
            self.assertFalse(row['ready']['pid_exists'])
            self.assertFalse(row['ready']['robot_process'])

    def test_default_one_sample_and_exclusive_output_preserve_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            board = BoardFixture(directory)
            output = Path(directory) / 'observation.jsonl'
            clock = FakeClock()
            code, summary = observe(output, collector=board.sample, clock=clock.clock, sleep=clock.sleep)
            records = [json.loads(line) for line in output.read_text(encoding='utf8').splitlines()]
            self.assertEqual(code, 0)
            self.assertEqual([row['event'] for row in records], ['sample', 'summary'])
            self.assertEqual(summary['sample_count'], 1)
            self.assertEqual(clock.delays, [])
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                observe(output, collector=board.sample)
            self.assertEqual(output.read_bytes(), original)

    def test_duration_and_count_budgets_are_bounded_and_do_not_load_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            board = BoardFixture(directory)
            for options, expected_count, expected_time in [
                ({'duration_seconds': 300, 'interval_seconds': 5}, 61, 300),
                ({'samples': 3, 'interval_seconds': 2}, 3, 4),
            ]:
                with self.subTest(options=options):
                    clock = FakeClock()
                    output = Path(directory) / f"run-{expected_count}.jsonl"
                    code, summary = observe(output, collector=board.sample, clock=clock.clock,
                                            sleep=clock.sleep, **options)
                    self.assertEqual(code, 0)
                    self.assertEqual(summary['sample_count'], expected_count)
                    self.assertEqual(summary['elapsed_seconds'], expected_time)
                    self.assertEqual(summary['monitor_kind'], 'idle-health-observation')
                    self.assertIn('no acoustic', summary['scope'])
                    self.assertLessEqual(max(clock.delays), 60)

    def test_thermal_limit_records_stop_without_mutating_board_or_service(self):
        for sensor, value in [('thermal_zone0', '70000'), ('thermal_zone7', '43000')]:
            with self.subTest(sensor=sensor), tempfile.TemporaryDirectory() as directory:
                board = BoardFixture(directory)
                board.write(f'sys/class/thermal/{sensor}/temp', value)
                before = {p.relative_to(board.root): p.read_bytes() for p in board.root.rglob('*') if p.is_file()}
                clock = FakeClock()
                output = Path(directory) / 'thermal.jsonl'
                code, summary = observe(output, samples=10, collector=board.sample,
                                        clock=clock.clock, sleep=clock.sleep)
                records = [json.loads(line) for line in output.read_text(encoding='utf8').splitlines()]
                self.assertEqual(code, 2)
                self.assertEqual([row['event'] for row in records], ['sample', 'stop', 'summary'])
                self.assertTrue(summary['stopped_for_temperature'])
                self.assertEqual(summary['sample_count'], 1)
                self.assertEqual(clock.delays, [])
                self.assertEqual(before, {p.relative_to(board.root): p.read_bytes() for p in board.root.rglob('*') if p.is_file()})

    def test_summary_reports_state_changes_and_restart_counter_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            board = BoardFixture(directory)
            rows = [board.sample()]
            board.write('sys/class/thermal/thermal_zone0/temp', '62000')
            board.write('service-show.txt', 'ActiveState=activating\nSubState=auto-restart\nNRestarts=2\nMainPID=123')
            rows.append(board.sample())
            board.write('service-show.txt', 'ActiveState=active\nSubState=running\nNRestarts=0\nMainPID=123')
            rows.append(board.sample())
        result = summarize(rows)
        self.assertEqual(result['cpu_max_c'], 62.)
        self.assertEqual(result['skin_max_c'], 34.)
        self.assertEqual(result['active_state_changes'], 2)
        self.assertEqual(result['sub_state_changes'], 2)
        self.assertEqual(result['restart_count_first'], 0)
        self.assertEqual(result['restart_count_last'], 0)
        self.assertEqual(result['restart_count_max'], 2)
        self.assertEqual(result['restart_count_increases'], 2)
        self.assertEqual(result['restart_counter_resets'], 1)
        self.assertEqual(result['non_active_samples'], 1)

    def test_unavailable_service_and_inactive_service_have_nonzero_observation_status(self):
        with tempfile.TemporaryDirectory() as directory:
            board = BoardFixture(directory)
            board.write('service-show.txt', 'ActiveState=inactive\nSubState=dead\nNRestarts=0\nMainPID=0')
            code, summary = observe(Path(directory) / 'inactive.jsonl', collector=board.sample)
            self.assertEqual(code, 1)
            self.assertEqual(summary['non_active_samples'], 1)
            def unavailable():
                raise OSError('systemctl missing')
            row = collect_sample(board.root, board.project, service_reader=unavailable)
            self.assertIsNone(row['service']['ActiveState'])
            self.assertTrue(row['errors'])

    def test_parameter_validation_and_numeric_argument_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            for kwargs in [{'duration_seconds': float('nan')}, {'duration_seconds': -1},
                           {'duration_seconds': 86401}, {'interval_seconds': float('inf')},
                           {'interval_seconds': 0}, {'interval_seconds': 61},
                           {'samples': 0}, {'samples': 10001}, {'samples': True},
                           {'samples': 5, 'duration_seconds': 5}]:
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    observe(Path(directory) / 'never-created.jsonl', **kwargs)
            self.assertFalse((Path(directory) / 'never-created.jsonl').exists())
        filtered = filtered_audio_parameters(['python', 'robot.py', '--threshold=SECRET',
                                              '--wake-threshold', 'nan', '--vad=SECRET',
                                              '--silence', '.55', '--api-key', 'SECRET'])
        self.assertEqual(filtered, {'silence': .55})
        self.assertEqual(thermal_stop_reasons({'thermal': []}), [])


if __name__ == '__main__':
    unittest.main()
