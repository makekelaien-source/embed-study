"""Read-only board health observation; never records audio or controls services.

This observes an otherwise idle voice service. It is not an acoustic,
accuracy, latency, model-load, or full stability acceptance test.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time


MONITOR_KIND = 'idle-health-observation'
CPU_LIMIT_C = 70.
SKIN_LIMIT_C = 43.
ROOT = Path(__file__).resolve().parent
SERVICE_FIELDS = ('ActiveState', 'SubState', 'NRestarts', 'MainPID')
AUDIO_NUMERIC_FLAGS = frozenset((
    '--input-device', '--output-device', '--threshold', '--min-input-dbfs',
    '--min-voice-ms', '--preroll-ms', '--silence', '--wake-threshold',
    '--wake-min-voice-ms', '--wake-preroll-ms', '--wake-silence',
))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def parse_service_show(text):
    result = {}
    for line in text.splitlines():
        key, separator, value = line.partition('=')
        if separator and key in SERVICE_FIELDS:
            result[key] = value.strip()
    return result


def system_service_state():
    result = subprocess.run(
        ['systemctl', 'show', 'desktop-robot.service',
         '--property=' + ','.join(SERVICE_FIELDS)],
        capture_output=True, text=True, timeout=5, check=False,
    )
    if result.returncode:
        raise RuntimeError(f'systemctl show exited {result.returncode}')
    return parse_service_show(result.stdout)


def filtered_audio_parameters(commandline):
    """Return known numeric/audio settings only, never raw process arguments."""
    result = {}
    args = commandline.split('\0') if isinstance(commandline, str) else list(commandline)
    for index, item in enumerate(args):
        flag, separator, inline = item.partition('=')
        value = inline if separator else (args[index + 1] if index + 1 < len(args) else '')
        if flag in AUDIO_NUMERIC_FLAGS and re.fullmatch(r'-?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?', value, re.I):
            number = float(value)
            if math.isfinite(number):
                result[flag[2:].replace('-', '_')] = number
        elif flag == '--vad' and value in ('rms', 'silero'):
            result['vad'] = value
        elif flag == '--wake-confirmation' and value in ('none', 'auto-consensus'):
            result['wake_confirmation'] = value
        elif flag == '--answer-prefix-policy' and value in ('original', 'guarded'):
            result['answer_prefix_policy'] = value
    return result


def collect_sample(root=Path('/'), project_root=ROOT, service_reader=system_service_state):
    """Read Linux sysfs/proc fixtures or the real board; return selected facts."""
    root, project_root = Path(root), Path(project_root)
    errors = []

    def read(relative, label):
        try:
            return (root / relative).read_text(encoding='utf8').strip()
        except (OSError, UnicodeError):
            errors.append(label + ': unreadable')
            return None

    def integer(text, label):
        try:
            value = int(text)
            if value < 0:
                raise ValueError
            return value
        except (ValueError, TypeError):
            errors.append(label + ': missing or invalid integer')
            return None

    thermal = []
    for zone in (0, 7):
        prefix = f'sys/class/thermal/thermal_zone{zone}/'
        name = read(prefix + 'type', f'thermal_zone{zone} type')
        raw = read(prefix + 'temp', f'thermal_zone{zone} temp')
        try:
            temperature = float(raw) / 1000
            if not math.isfinite(temperature) or not -50 <= temperature <= 200:
                raise ValueError
        except (ValueError, TypeError):
            temperature = None
            errors.append(f'thermal_zone{zone}: missing or invalid temperature')
        thermal.append({'zone': zone, 'name': name, 'temperature_c': temperature})
    if thermal[1]['name'] != 'skin_zone':
        errors.append('thermal_zone7: expected skin_zone; skin interpretation unconfirmed')

    frequency = {}
    for key, filename in (('max_khz', 'scaling_max_freq'), ('current_khz', 'scaling_cur_freq')):
        label = 'policy6 ' + filename
        frequency[key] = integer(read('sys/devices/system/cpu/cpufreq/policy6/' + filename, label), label)

    memory_text = read('proc/meminfo', 'meminfo')
    memory = None
    if memory_text is not None:
        found = re.search(r'^MemAvailable:\s+(\d+)\s+kB\s*$', memory_text, re.M)
        if found:
            memory = int(found.group(1))
    if memory is None:
        errors.append('MemAvailable: missing or invalid kB value')

    service = {key: None for key in SERVICE_FIELDS}
    try:
        observed = service_reader()
        for key in ('ActiveState', 'SubState'):
            value = observed.get(key)
            if isinstance(value, str) and re.fullmatch(r'[a-z-]{1,40}', value):
                service[key] = value
            else:
                errors.append('service ' + key + ': missing or invalid state')
        for key in ('NRestarts', 'MainPID'):
            service[key] = integer(observed.get(key), 'service ' + key)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError, AttributeError):
        errors.append('service state: unavailable')
    main_pid = service['MainPID']
    service['main_pid_exists'] = bool(main_pid and (root / 'proc' / str(main_pid)).is_dir())
    if service['ActiveState'] == 'active' and not service['main_pid_exists']:
        errors.append('active service: live MainPID not confirmed')

    ready = {'state': None, 'pid': None, 'pid_exists': False,
             'robot_process': False, 'audio_parameters': {}}
    try:
        document = json.loads((project_root / '.local/service-ready.json').read_text(encoding='utf8'))
        if not isinstance(document, dict):
            raise ValueError
        pid = document.get('pid')
        if type(pid) is not int or pid <= 0:
            raise ValueError
        ready['state'] = 'ready' if document.get('state') == 'ready' else 'other'
        ready['pid'] = pid
        ready['pid_exists'] = (root / 'proc' / str(pid)).is_dir()
        if ready['pid_exists']:
            commandline = read(f'proc/{pid}/cmdline', 'ready process cmdline')
            if commandline is not None:
                ready['robot_process'] = any(Path(arg).name == 'robot.py' for arg in commandline.split('\0'))
                ready['audio_parameters'] = filtered_audio_parameters(commandline)
        if ready['state'] != 'ready' or not ready['pid_exists'] or not ready['robot_process']:
            errors.append('ready file: live robot process not confirmed')
    except (OSError, UnicodeError, ValueError, TypeError):
        errors.append('ready file: missing, unreadable or invalid')

    return {'event': 'sample', 'monitor_kind': MONITOR_KIND, 'at_utc': utc_now(),
            'thermal': thermal, 'policy6': frequency, 'mem_available_kib': memory,
            'service': service, 'ready': ready, 'errors': errors}


def thermal_stop_reasons(sample):
    reasons = []
    for sensor in sample.get('thermal', []):
        temperature = sensor.get('temperature_c')
        if temperature is None:
            continue
        limit = CPU_LIMIT_C if sensor.get('zone') == 0 else (
            SKIN_LIMIT_C if sensor.get('name') == 'skin_zone' else None)
        if limit is not None and temperature >= limit:
            reasons.append({'zone': sensor['zone'], 'name': sensor.get('name'),
                            'temperature_c': temperature, 'limit_c': limit})
    return reasons


def summarize(samples, stopped=False):
    def maximum(predicate):
        values = [sensor['temperature_c'] for sample in samples for sensor in sample['thermal']
                  if predicate(sensor) and sensor.get('temperature_c') is not None]
        return max(values) if values else None
    active = [row['service'].get('ActiveState') for row in samples]
    substates = [row['service'].get('SubState') for row in samples]
    restarts = [row['service'].get('NRestarts') for row in samples]
    known_restarts = [number for number in restarts if number is not None]
    return {'event': 'summary', 'monitor_kind': MONITOR_KIND, 'at_utc': utc_now(),
            'sample_count': len(samples), 'cpu_max_c': maximum(lambda s: s['zone'] == 0),
            'skin_max_c': maximum(lambda s: s.get('name') == 'skin_zone'),
            'active_state_changes': sum(a != b for a, b in zip(active, active[1:])),
            'sub_state_changes': sum(a != b for a, b in zip(substates, substates[1:])),
            'restart_count_first': known_restarts[0] if known_restarts else None,
            'restart_count_last': known_restarts[-1] if known_restarts else None,
            'restart_count_max': max(known_restarts) if known_restarts else None,
            'restart_count_increases': sum(max(0, b - a) for a, b in zip(restarts, restarts[1:])
                                         if a is not None and b is not None),
            'restart_counter_resets': sum(b < a for a, b in zip(restarts, restarts[1:])
                                         if a is not None and b is not None),
            'samples_with_errors': sum(bool(row['errors']) for row in samples),
            'non_active_samples': sum(value != 'active' for value in active),
            'stopped_for_temperature': stopped,
            'scope': 'Idle observation only; no acoustic, accuracy, load or latency test.'}


def observe(output, duration_seconds=0, interval_seconds=5, samples=None,
            collector=collect_sample, clock=time.monotonic, sleep=time.sleep):
    if not math.isfinite(duration_seconds) or not 0 <= duration_seconds <= 86400:
        raise ValueError('duration_seconds must be finite and 0-86400')
    if not math.isfinite(interval_seconds) or not .25 <= interval_seconds <= 60:
        raise ValueError('interval_seconds must be finite and .25-60')
    if samples is not None and (type(samples) is not int or not 1 <= samples <= 10000):
        raise ValueError('samples must be an integer from 1 to 10000')
    if samples is not None and (duration_seconds or samples * interval_seconds > 86400):
        raise ValueError('choose samples or duration; maximum observation budget is one day')
    rows = []
    stopped = False
    started = clock()
    # Exclusive creation preserves every previous observation, including failures.
    with Path(output).open('x', encoding='utf8') as stream:
        def emit(row):
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
        while True:
            sample = collector()
            rows.append(sample)
            emit(sample)
            reasons = thermal_stop_reasons(sample)
            if reasons:
                stopped = True
                emit({'event': 'stop', 'monitor_kind': MONITOR_KIND,
                      'at_utc': utc_now(), 'reason': 'temperature_limit', 'sensors': reasons,
                      'action': 'Observation stopped; service and system left unchanged.'})
                break
            now = clock()
            if samples is not None:
                if len(rows) >= samples:
                    break
                delay = interval_seconds
            else:
                remaining = duration_seconds - (now - started)
                if remaining <= 0:
                    break
                delay = min(interval_seconds, remaining)
            sleep(delay)
        summary = summarize(rows, stopped)
        summary['elapsed_seconds'] = max(0, clock() - started)
        summary['requested_duration_seconds'] = duration_seconds
        summary['requested_samples'] = samples
        summary['interval_seconds'] = interval_seconds
        emit(summary)
    return (2 if stopped else 1 if summary['samples_with_errors'] or summary['non_active_samples'] else 0), summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New JSONL filename; existing files are never overwritten')
    parser.add_argument('--duration-seconds', type=float, default=0, help='Default 0 takes one sample; maximum 86400')
    parser.add_argument('--samples', type=int, help='Alternative sample-count budget, 1-10000')
    parser.add_argument('--interval-seconds', type=float, default=5)
    parser.add_argument('--root', type=Path, default=Path('/'), help='Linux filesystem root; tests may use a fixture root')
    parser.add_argument('--project-root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        code, summary = observe(args.output, args.duration_seconds, args.interval_seconds, args.samples,
                                collector=lambda: collect_sample(args.root, args.project_root))
    except (OSError, ValueError) as error:
        print(f'Observation failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
