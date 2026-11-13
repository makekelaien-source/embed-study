"""Read-only, offline device telemetry. No shell commands and no guessed values."""
from datetime import datetime, timezone
from pathlib import Path
import re


THERMAL_ROOT = Path('/sys/class/thermal')


def is_cpu_temperature_request(text):
    """Match direct local readings, never general advice or quoted commands."""
    value = re.sub(r'[。！!.,，？?]+$', '', ' '.join(text.strip().casefold().split()))
    if re.search(r'["“”‘’「」『』]', value):
        return False
    if re.search(r'为什么|为何|原理|意思|含义|解释|举例|例如|比如|正常|安全|应该|如果|假如|假设|他说|她说|复述|重复|如何|怎么降低|怎么测|如何测|不要|不用|别查', value):
        return False
    if re.search(r'\b(?:why|explain|meaning|example|normal|safe|should|would|if|unless|said|quote|repeat|not|never)\b', value):
        return False
    subject = r'(?:cpu|处理器|芯片|香橙派|你的cpu|你的处理器|本机cpu|板子cpu)'
    # Compose local ownership, time and sensor separately, so ordinary ASR
    # word-order variants route to telemetry without repairing the transcript.
    local = r'(?:这块(?:香橙派|板子|开发板)|这台(?:机器人|设备)|这(?:块板|台机器)|香橙派|板子|本机|你的|你)'
    now = r'(?:现在|当前|此刻|目前)'
    cpu = r'(?:cpu|处理器|芯片)'
    zh = (
        rf'(?:请|请问|帮我|请帮我)?(?:查一下|查询|查看|测一下|读一下|告诉我)?(?:{now})?(?:{local}(?:的)?(?:{now})?(?:的)?)?{cpu}(?:{now})?(?:的)?(?:温度|有多热)(?:{now})?(?:是|有)?(?:多少|几度|怎么样)?(?:度|摄氏度)?(?:了|呢|啊|呀)?',

        rf'(?:请|请问|帮我|请帮我)?(?:查一下|查询|查看|测一下|读一下|告诉我)?(?:现在|当前|此刻)?{subject}(?:现在|当前|的)?(?:温度|有多热)(?:现在|当前)?(?:是|有)?(?:多少|几度|怎么样)?(?:度|摄氏度)?(?:了|呢|啊|呀)?',
        rf'(?:现在|当前)?(?:你|这块板子|板子|香橙派)(?:的)?(?:cpu)?温度(?:是|有)?(?:多少|几度)(?:度|摄氏度)?(?:了|呢)?',
    )
    if any(re.fullmatch(pattern, re.sub(r"\s+", "", value)) for pattern in zh):
        return True
    return bool(re.fullmatch(
        r'(?:please )?(?:(?:what is|what\'s|tell me|read|check|show)(?: me)? )?'
        r'(?:the |your |this board\'s )?(?:current )?(?:cpu|processor) temperature'
        r'(?: (?:now|right now|currently))?', value)) or bool(re.fullmatch(
        r'how hot is (?:the |your )?(?:cpu|processor)(?: (?:now|right now))?', value))


def _cpu_zone(kind):
    # The A733 exposes cpul/cpub thermal zones plus separate idle and GPU zones.
    # Only actual CPU sensors qualify, not skin/GPU/NPU or idle-model sensors.
    return bool(re.fullmatch(r'(?:cpu[lb]?_thermal_zone|cpu-thermal|cpu_thermal|cpu|cpu[0-9]+|x86_pkg_temp|soc_cpu)', kind))


class DeviceStatus:
    def __init__(self, root=THERMAL_ROOT, read_text=None, list_zones=None, clock=None):
        self.root = Path(root)
        self.read_text = read_text or (lambda path: path.read_text(encoding='ascii'))
        self.list_zones = list_zones or (lambda root: sorted(root.glob('thermal_zone*')))
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(self, text, language='zh'):
        if not is_cpu_temperature_request(text):
            return None
        result = {'tool': 'read_cpu_temperature', 'ok': False, 'unit': 'celsius',
                  'read_at': self.clock().isoformat(), 'zones': []}
        try:
            for zone in self.list_zones(self.root):
                zone = Path(zone)
                kind = self.read_text(zone / 'type').strip()
                if not _cpu_zone(kind):
                    continue
                raw = self.read_text(zone / 'temp').strip()
                if not re.fullmatch(r'-?\d+', raw):
                    raise ValueError('invalid_temperature_format')
                milli = int(raw)
                if not -40000 <= milli <= 150000:
                    raise ValueError('temperature_out_of_range')
                result['zones'].append({'zone': zone.name, 'type': kind,
                                        'celsius': milli / 1000.0})
            if not result['zones']:
                raise ValueError('cpu_sensor_not_found')
            hottest = max(z['celsius'] for z in result['zones'])
            result.update(ok=True, celsius=hottest)
            result['answer'] = (f'刚读取的CPU最高温度是{hottest:.1f}摄氏度。' if language == 'zh'
                                else f'The CPU currently reads {hottest:.1f} degrees Celsius at its hottest sensor.')
        except (OSError, ValueError, UnicodeError) as error:
            result['error'] = type(error).__name__
            result['answer'] = ('CPU温度读取失败，现在无法确认温度。' if language == 'zh'
                                else 'I could not read the CPU temperature, so its current temperature is unknown.')
        return result


def execute(text, language='zh'):
    return DeviceStatus().execute(text, language)

