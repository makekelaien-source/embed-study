"""Bounded, checksummed JSONL framing for a trusted local USB link.

CRC detects accidental corruption; it is not authentication. No serial port or
hardware is opened by this module. Boot negotiation remains an adapter duty.
"""
from dataclasses import dataclass
import json
import re
from types import MappingProxyType
import zlib

MAX_FRAME_BYTES = 512
MAX_COUNTER = 2 ** 31 - 1
ACTIONS = frozenset(('FORWARD', 'REVERSE', 'LEFT', 'RIGHT'))
FACES = frozenset(('boot', 'idle', 'listening', 'thinking', 'speaking',
                   'blocked', 'fault', 'offline', 'low_power'))
SCHEMAS = {
    'hello': {'boot': 'id', 'role': ('host', 'mcu')},
    'hello_ack': {'host_boot': 'id', 'mcu_boot': 'id'},
    'poll': {'token': (1, MAX_COUNTER), 'budget_ms': (1, 200)},
    'heartbeat': {'token': (1, MAX_COUNTER)},
    'vision': {'token': (1, MAX_COUNTER), 'frame_id': (1, MAX_COUNTER),
               'state': ('CLEAR', 'EDGE', 'UNKNOWN'), 'remaining_ms': (0, 200)},
    'move': {'token': (1, MAX_COUNTER), 'command_id': (1, MAX_COUNTER),
             'action': tuple(sorted(ACTIONS)), 'speed_mm_s': (1, 100), 'duration_ms': (1, 300)},
    'stop': {'command_id': (1, MAX_COUNTER)},
    'face': {'state': tuple(sorted(FACES))},
    'ack': {'command_id': (1, MAX_COUNTER),
            'status': ('accepted', 'rejected', 'output_applied', 'simulated_stopped',
                       'completed', 'aborted', 'failed'),
            'reason': 'reason', 'physical_verified': 'bool'},
}


def identifier(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[0-9a-f]{32}', value)) and value != '0' * 32


def _integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def _payload(kind, payload):
    if kind not in SCHEMAS or type(payload) is not dict or set(payload) != set(SCHEMAS[kind]):
        raise ValueError('Unknown kind or incorrect payload fields')
    for key, rule in SCHEMAS[kind].items():
        value = payload[key]
        if rule == 'id':
            valid = identifier(value)
        elif rule == 'reason':
            valid = isinstance(value, str) and bool(re.fullmatch(r'[a-z0-9_]{1,40}', value))
        elif rule == 'bool':
            valid = type(value) is bool
        elif type(rule[0]) is int:
            valid = _integer(value, *rule)
        else:
            valid = isinstance(value, str) and value in rule
        if not valid:
            raise ValueError('Invalid payload field: ' + key)
    if kind == 'ack' and payload['status'] == 'completed' and not payload['physical_verified']:
        raise ValueError('Completed requires physical verification; simulation cannot claim it')
    if kind == 'ack' and payload['status'] == 'simulated_stopped' and payload['physical_verified']:
        raise ValueError('A simulated stop is never physical verification')
    return dict(payload)


@dataclass(frozen=True)
class Message:
    link: str
    seq: int
    kind: str
    payload: object

    def __post_init__(self):
        if not identifier(self.link) or not _integer(self.seq, 1, MAX_COUNTER):
            raise ValueError('Invalid link or sequence')
        if not isinstance(self.kind, str):
            raise ValueError('Invalid message kind')
        object.__setattr__(self, 'payload', MappingProxyType(_payload(self.kind, self.payload)))


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def encode(message):
    body = {'v': 1, 'link': message.link, 'seq': message.seq,
            'kind': message.kind, 'payload': dict(message.payload)}
    body['crc32'] = f'{zlib.crc32(_canonical(body)) & 0xffffffff:08x}'
    line = _canonical(body) + b'\n'
    if len(line) > MAX_FRAME_BYTES:
        raise ValueError('Frame is too long')
    return line


def command_ack(link, seq, receipt):
    """Only command receipts become wire ACKs; local drops never emit null IDs."""
    if not isinstance(receipt, dict) or receipt.get('local_only') or receipt.get('command_id') is None:
        raise ValueError('Local diagnostic/drop is not a command ACK')
    try:
        payload = {key: receipt[key] for key in SCHEMAS['ack']}
    except (KeyError, TypeError) as error:
        raise ValueError('Incomplete command receipt') from error
    return Message(link, seq, 'ack', payload)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def decode(line):
    if not isinstance(line, bytes) or not line.endswith(b'\n') or len(line) > MAX_FRAME_BYTES:
        raise ValueError('Require one bounded newline-terminated frame')
    try:
        body = json.loads(line, object_pairs_hook=_unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ValueError('Invalid JSON frame') from error
    if type(body) is not dict or set(body) != {'v', 'link', 'seq', 'kind', 'payload', 'crc32'}:
        raise ValueError('Incorrect frame fields')
    if type(body['v']) is not int or body['v'] != 1:
        raise ValueError('Unsupported protocol version')
    checksum = body.pop('crc32')
    expected = f'{zlib.crc32(_canonical(body)) & 0xffffffff:08x}'
    if checksum != expected:
        raise ValueError('CRC mismatch')
    return Message(body['link'], body['seq'], body['kind'], body['payload'])


class LineFramer:
    """Recover after malformed/oversize lines without an unbounded RX buffer."""
    def __init__(self):
        self.buffer = bytearray()
        self.dropping = False
        self.errors = 0

    def feed(self, chunk):
        if not isinstance(chunk, (bytes, bytearray)):
            raise TypeError('Transport must provide bytes')
        messages = []
        for byte in chunk:
            if self.dropping:
                if byte == 10:
                    self.dropping = False
                continue
            self.buffer.append(byte)
            if len(self.buffer) > MAX_FRAME_BYTES:
                self.errors += 1
                self.buffer.clear()
                self.dropping = byte != 10
                continue
            if byte == 10:
                try:
                    messages.append(decode(bytes(self.buffer)))
                except ValueError:
                    self.errors += 1
                self.buffer.clear()
        return messages
