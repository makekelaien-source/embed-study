"""Strict human motion-intent adapter for the FUTURE integration path."""
import re

COMMANDS = {
    '前进': 'FORWARD', '后退': 'REVERSE', '左转': 'LEFT', '右转': 'RIGHT', '停止': 'STOP',
    'move forward': 'FORWARD', 'move backward': 'REVERSE',
    'turn left': 'LEFT', 'turn right': 'RIGHT', 'stop moving': 'STOP',
}


def parse_motion_intent(text, *, origin):
    """Only trusted ASR/button orchestration may supply origin, never the LLM.

    This is an application routing contract, not cryptographic authentication.
    Question marks, quotations, extra words and unsupported sources reject.
    The current robot.py movement logger is NOT a real motor adapter.
    """
    if origin not in ('asr', 'button') or not isinstance(text, str):
        return None
    if re.search(r'[?？"“”‘’「」『』\']', text):
        return None
    command = re.sub(r'[。！!.]+$', '', text.strip().casefold())
    command = ' '.join(command.split())
    return COMMANDS.get(command)
