"""Local allowlisted voice tools and digital audio level helpers (no shell)."""
import math
import re
from dataclasses import dataclass


def dbfs_threshold(value):
    value = float(value)
    if not math.isfinite(value) or not -80 <= value <= 0:
        raise ValueError('minimum input level must be between -80 and 0 dBFS')
    return 10 ** (value / 20)


def volume_clarification(text, language):
    """Clarify an unmatched direct volume request without guessing an action.

    Call only after the exact tool allowlist returns no match. Questions,
    negations, conditionals and discussion/quotation of a command continue
    through normal chat. This helper never changes volume or repairs text.
    """
    command = re.sub(r'\s+', ' ', text.strip().casefold())
    if re.search(r'[?？"“”‘’「」『』\']', command):
        return None
    if re.search(r'不|别|勿|无需|无须|如果|假如|假设|要是|的话|'
                 r'为什么|为何|怎么|怎样|如何|是否|能否|可否|吗|么|呢|什么|'
                 r'解释|意思|含义|原理|教程|区别|例如|比如|示例|例子|'
                 r'说过|说了|刚才|他说|她说|我说|你说|复述|重复|'
                 r'听到|听见|提到|台词|这句|讨论|介绍|分析|模式', command):
        return None
    if re.search(r"\b(?:not|never|dont|don't|why|what|how|if|unless|whether|"
                 r"explain|meaning|said|say|quote|quoted|example|mode)\b", command):
        return None
    chinese = (re.match(r'^(?:请|麻烦|帮我|给我|把|将|调|提高|降低|增大|减小|'
                        r'放大|缩小|音量|声音|静音|取消静音|恢复声音|大声|小声)', command)
               and re.search(r'音量|声音|静音|大声|小声', command)
               and re.search(r'调高|调低|提高|降低|大一点|小一点|大点|小点|'
                             r'静音|恢复声音|调到|调至|设置为|设为|增大|减小|'
                             r'放大|缩小|大声|小声', command))
    english = (re.match(r'^(?:please\b|turn\b|set\b|lower\b|raise\b|increase\b|'
                        r'decrease\b|mute\b|unmute\b|volume\b|louder\b|quieter\b)', command)
               and re.search(r'\b(?:volume|sound|louder|quieter|mute|unmute)\b', command)
               and re.search(r'\b(?:up|down|set|lower|raise|increase|decrease|'
                             r'louder|quieter|mute|unmute)\b', command))
    if not (chinese or english):
        return None
    return ('没能确认调节指令，请再说一次。' if language == 'zh'
            else "I couldn't confirm the volume command. Please say it again.")


def capability_clarification(text, language):
    """Ask what an ambiguous bare open/close directive means; never execute it.

    The caller checks supported end/tool/movement commands first. Entire
    utterances must match, so discussion, questions, quotations, negations
    and conditional phrases cannot be mistaken for these bare directives.
    """
    volume = volume_clarification(text, language)
    if volume is not None:
        return volume
    command = re.sub(r'[。！!.,，]+$', '', ' '.join(text.strip().casefold().split()))
    polite = r'(?:请帮我|麻烦你帮我|麻烦你|麻烦|帮我|帮忙|请)?'
    suffix = r'(?:一下|下)?(?:吧|呀|啊)?'
    close = (re.fullmatch(polite + r'(?:关闭|关掉|关上|关了|关机|关)' + suffix, command)
             or re.fullmatch(r'(?:please )?(?:close(?: it)?|turn (?:it )?off|shut (?:it )?off)', command))
    opened = (re.fullmatch(polite + r'(?:打开|开启|开机|开)' + suffix, command)
              or re.fullmatch(r'(?:please )?(?:open(?: it)?|turn (?:it )?on)', command))
    if close:
        return ('你是想结束对话，还是静音？' if language == 'zh'
                else 'Do you want to end our chat or mute?')
    if opened:
        return ('你是想恢复声音，还是开始聊天？' if language == 'zh'
                else 'Do you want to unmute, or start chatting?')
    return None


@dataclass
class VolumeControl:
    # Percentage of application signal amplitude, independent of ALSA volume.
    percent: int = 100
    previous: int = 100

    def execute(self, text, language):
        command = re.sub(r'[。！!.,，？?]+$', '', text.strip().casefold())
        command = re.sub(r'\s+', ' ', command)
        down = {'声音小一点', '声音小点', '小声一点', '小声点', '音量小一点',
                '调低音量', '降低音量', '把音量调低', '把声音调小一点',
                '请小声一点', '太吵了', 'turn down the volume', 'lower your volume',
                'speak more quietly', 'quieter please', 'please turn down the volume'}
        up = {'声音大一点', '大声一点', '调高音量', '提高音量', '把音量调高',
              'turn up the volume', 'louder please'}
        mute = {'静音', '请静音', 'mute', 'mute yourself'}
        unmute = {'取消静音', '恢复声音', 'unmute'}
        absolute = re.fullmatch(r'(?:把)?音量(?:设置为|设为|调到|调至)(100|[1-9]?\d)(?:%|％|百分比)?', command)
        english = re.fullmatch(r'(?:set (?:your |the )?volume to) (100|[1-9]?\d)(?: percent|%)?', command)
        target = None
        if command in down:
            target = max(0, self.percent - 20)
        elif command in up:
            target = min(100, self.percent + 20)
        elif command in mute:
            target = 0
        elif command in unmute:
            target = self.previous if self.percent == 0 else self.percent
        elif absolute or english:
            target = int((absolute or english).group(1))
        if target is None:
            return None
        before = self.percent
        if before > 0:
            self.previous = before
        self.percent = target
        answer = ('音量已调整。' if language == 'zh' else 'Volume adjusted.')
        return {'tool': 'set_volume', 'before': before, 'percent': target,
                'ok': True, 'answer': answer}

    @property
    def gain(self):
        return self.percent / 100
