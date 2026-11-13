"""In-memory scenarios only: no serial, GPIO, camera, motor or service access."""
import argparse
import json
from pathlib import Path

from .supervisor import SafetyConfig, Supervisor, host_vision_payload
from .wire import LineFramer, Message, encode


def scenario(enable=False, name='lease-expiry'):
    link, boot, host = '1' * 32, '2' * 32, '3' * 32
    config = SafetyConfig(motion_enabled=enable, calibrated=enable,
                          safe_actions=frozenset(('FORWARD',)) if enable else frozenset())
    unit = Supervisor(boot, config)
    framer = LineFramer()
    rows = []
    sequence = 0

    def record(event, now, result=None):
        rows.append({'event': event, 'mcu_ms': now, 'motion_state': unit.state,
                     'face': unit.face, 'active_command': unit.active['command_id'] if unit.active else None,
                     'result': result, 'hardware_action': False, 'physical_verified': False})

    def send(kind, payload, now):
        nonlocal sequence
        sequence += 1
        frame = encode(Message(link, sequence, kind, payload))
        # Exercise transport fragmentation rather than calling receive directly.
        decoded = framer.feed(frame[:11]) + framer.feed(frame[11:])
        assert len(decoded) == 1
        result = unit.receive(decoded[0], now)
        record(kind, now, result)

    unit.begin_session(link, host, boot, 0)
    unit.set_local_inputs(0, physical_stop=False, power_ok=True, driver_ok=True,
                          direction_ok={'FORWARD': True})
    poll = unit.issue_poll(0)
    record('poll', 0, poll)
    send('face', {'state': 'listening'}, 1)
    send('heartbeat', {'token': poll['token']}, 10)
    # Host and MCU clocks deliberately have different origins.
    payload = host_vision_payload(poll['token'], 1, 'CLEAR',
                                 poll_received_ms=100005, captured_ms=100010,
                                 evaluated_ms=100015)
    send('vision', payload, 20)
    record('explicit_simulated_arm', 20, unit.arm(20))
    send('move', {'token': 1, 'command_id': 1, 'action': 'FORWARD',
                  'speed_mm_s': 20, 'duration_ms': 300}, 30)
    if name == 'stop':
        send('stop', {'command_id': 2}, 40)
    elif name == 'reconnect':
        unit.begin_session('4' * 32, '5' * 32, boot, 40)
        record('new_session_requires_rearm', 40)
    else:
        unit.set_local_inputs(90, physical_stop=False, power_ok=True, driver_ok=True,
                              direction_ok={'FORWARD': True})
        poll = unit.issue_poll(100)
        record('poll', 100, poll)
        send('heartbeat', {'token': poll['token']}, 110)
        unit.set_local_inputs(180, physical_stop=False, power_ok=True, driver_ok=True,
                              direction_ok={'FORWARD': True})
        unit.tick(199)
        record('vision_still_fresh', 199)
        unit.tick(200)
        record('vision_deadline', 200)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=('lease-expiry', 'stop', 'reconnect'), default='lease-expiry')
    parser.add_argument('--enable-simulated-motion', action='store_true',
                        help='Enable only the IN-MEMORY fixture; no physical backend exists')
    parser.add_argument('--output', type=Path, help='Optional NEW JSONL evidence file')
    args = parser.parse_args()
    rows = scenario(args.enable_simulated_motion, args.scenario)
    text = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf8') as output:
            output.write(text)
    print(text, end='')


if __name__ == '__main__':
    main()
