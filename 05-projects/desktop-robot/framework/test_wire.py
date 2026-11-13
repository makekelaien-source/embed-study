import json
import unittest

from .wire import LineFramer, Message, MAX_FRAME_BYTES, command_ack, decode, encode

LINK = '1' * 32


class WireTests(unittest.TestCase):
    def test_roundtrip_and_fragmented_transport(self):
        msg = Message(LINK, 1, 'heartbeat', {'token': 7})
        line = encode(msg)
        framer = LineFramer()
        self.assertEqual(framer.feed(line[:9]), [])
        self.assertEqual(framer.feed(line[9:]), [msg])
        self.assertEqual(framer.errors, 0)

    def test_corruption_is_rejected_and_next_frame_recovers(self):
        line = encode(Message(LINK, 2, 'heartbeat', {'token': 7}))
        damaged = line.replace(b'"token":7', b'"token":8')
        framer = LineFramer()
        self.assertEqual(framer.feed(damaged + line), [decode(line)])
        self.assertEqual(framer.errors, 1)

    def test_oversize_line_never_accumulates_unbounded_state(self):
        line = encode(Message(LINK, 3, 'stop', {'command_id': 2}))
        framer = LineFramer()
        self.assertEqual(framer.feed(b'x' * (MAX_FRAME_BYTES * 20)), [])
        self.assertLessEqual(len(framer.buffer), MAX_FRAME_BYTES)
        self.assertEqual(framer.feed(b'\n' + line), [decode(line)])
        self.assertEqual(framer.errors, 1)

    def test_duplicate_fields_nonfinite_unknown_and_wrong_version_reject(self):
        line = encode(Message(LINK, 1, 'heartbeat', {'token': 7}))
        cases = [line.replace(b'"v":1', b'"v":1,"v":1'),
                 line.replace(b'"token":7', b'"token":NaN'),
                 line.replace(b'"v":1', b'"v":2')]
        body = json.loads(line)
        body['extra'] = 1
        cases.append(json.dumps(body).encode() + b'\n')
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode(data)

    def test_header_payload_and_actuation_bounds_are_strict(self):
        for seq in (True, 0, -1, 1.0, 2 ** 31):
            with self.subTest(seq=seq), self.assertRaises(ValueError):
                Message(LINK, seq, 'heartbeat', {'token': 1})
        payload = {'token': 1, 'command_id': 1, 'action': 'FORWARD',
                   'speed_mm_s': 20, 'duration_ms': 300}
        for key, value in [('duration_ms', 301), ('speed_mm_s', True),
                           ('action', 'SHELL'), ('token', 0)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                Message(LINK, 1, 'move', dict(payload, **{key: value}))

    def test_simulation_cannot_encode_completed_without_physical_evidence(self):
        with self.assertRaises(ValueError):
            Message(LINK, 1, 'ack', {'command_id': 1, 'status': 'completed',
                                    'reason': 'timer_ended', 'physical_verified': False})
        message = Message(LINK, 1, 'ack', {'command_id': 1, 'status': 'simulated_stopped',
                                         'reason': 'duration_elapsed', 'physical_verified': False})
        self.assertEqual(decode(encode(message)), message)
        with self.assertRaises(TypeError):
            message.payload['reason'] = 'changed'

    def test_local_drops_are_not_null_id_wire_acks(self):
        for receipt in (None, {}, {'command_id': None, 'local_only': True}):
            with self.subTest(receipt=receipt), self.assertRaises(ValueError):
                command_ack(LINK, 1, receipt)
        receipt = {'command_id': 1, 'status': 'accepted', 'reason': 'ok',
                   'physical_verified': False, 'cached': True, 'local_only': False}
        message = command_ack(LINK, 1, receipt)
        self.assertEqual(decode(encode(message)), message)
        self.assertNotIn('cached', message.payload)


if __name__ == '__main__':
    unittest.main()
