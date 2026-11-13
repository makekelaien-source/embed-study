import unittest

from .human_intent import parse_motion_intent
from .supervisor import SafetyConfig, Supervisor, host_vision_payload
from .wire import Message

BOOT, HOST, LINK = '2' * 32, '3' * 32, '1' * 32


def message(seq, kind, **payload):
    return Message(LINK, seq, kind, payload)


def fixture(duration=300, start=True, local_input_ms=400):
    # Isolate the 200ms vision lease in these fixtures; hardware values are TBD.
    config = SafetyConfig(True, True, frozenset(('FORWARD',)), local_input_ms=local_input_ms)
    unit = Supervisor(BOOT, config)
    assert unit.begin_session(LINK, HOST, BOOT, 0)
    unit.set_local_inputs(0, physical_stop=False, power_ok=True, driver_ok=True,
                          direction_ok={'FORWARD': True})
    unit.issue_poll(0)
    unit.receive(message(1, 'heartbeat', token=1), 10)
    unit.receive(message(2, 'vision', token=1, frame_id=1, state='CLEAR', remaining_ms=200), 20)
    assert unit.arm(20)
    if start:
        assert unit.receive(message(3, 'move', token=1, command_id=1, action='FORWARD',
                                    speed_mm_s=20, duration_ms=duration), 30)['status'] == 'accepted'
    return unit


class SupervisorTests(unittest.TestCase):
    def test_default_is_disabled_but_optional_motion_does_not_break_face(self):
        unit = Supervisor(BOOT)
        unit.begin_session(LINK, HOST, BOOT, 0)
        unit.receive(message(1, 'face', state='listening'), 1)
        self.assertFalse(unit.arm(1))
        self.assertEqual(unit.state, 'DISARMED')
        self.assertEqual(unit.face, 'listening')

    def test_heartbeat_cannot_renew_vision_and_expiry_latches(self):
        unit = fixture()
        unit.issue_poll(100)
        unit.receive(message(4, 'heartbeat', token=2), 110)
        self.assertEqual(unit.tick(199), 'DRIVING')
        self.assertEqual(unit.tick(200), 'BLOCKED')
        self.assertEqual(unit.reason, 'vision_expired')
        self.assertIsNone(unit.active)
        self.assertFalse(unit.arm(201))
        self.assertTrue(unit.recover(201))
        self.assertEqual(unit.state, 'DISARMED')

    def test_delayed_response_with_fresh_reported_ttl_cannot_revive_old_poll(self):
        unit = fixture(start=False)
        result = unit.receive(message(3, 'vision', token=1, frame_id=2,
                                      state='CLEAR', remaining_ms=200), 201)
        self.assertEqual(result['reason'], 'token_expired')
        self.assertLessEqual(unit.vision_until_ms, 200)
        result = unit.receive(message(4, 'move', token=1, command_id=1, action='FORWARD',
                                      speed_mm_s=20, duration_ms=50), 202)
        self.assertEqual(result['status'], 'rejected')

    def test_new_token_cannot_renew_an_old_camera_frame(self):
        unit = fixture()
        unit.issue_poll(100)
        unit.receive(message(4, 'vision', token=2, frame_id=1, state='CLEAR', remaining_ms=200), 110)
        self.assertEqual(unit.vision_until_ms, 200)
        self.assertEqual(unit.tick(200), 'BLOCKED')

    def test_revoke_for_same_frame_is_not_dropped_as_a_duplicate_clear(self):
        unit = fixture()
        unit.receive(message(4, 'vision', token=1, frame_id=1, state='UNKNOWN', remaining_ms=0), 40)
        self.assertEqual(unit.state, 'BLOCKED')
        self.assertIsNone(unit.active)

    def test_same_command_id_returns_status_without_extending_or_reexecuting(self):
        unit = fixture(duration=50)
        original_end = unit.active['until_ms']
        payload = dict(token=1, command_id=1, action='FORWARD', speed_mm_s=20, duration_ms=50)
        result = unit.receive(message(4, 'move', **payload), 40)
        self.assertTrue(result['cached'])
        self.assertEqual(unit.active['until_ms'], original_end)
        unit.tick(80)
        self.assertEqual(unit.state, 'ARMED')
        result = unit.receive(message(5, 'move', **payload), 90)
        self.assertEqual(result['status'], 'simulated_stopped')
        self.assertFalse(result['physical_verified'])
        self.assertIsNone(unit.active)
        result = unit.receive(message(6, 'move', **dict(payload, speed_mm_s=10)), 91)
        self.assertEqual(result['reason'], 'duplicate_mismatch')

    def test_unverified_direction_and_rejected_id_need_a_new_human_command(self):
        unit = fixture(start=False)
        result = unit.receive(message(3, 'move', token=1, command_id=1, action='REVERSE',
                                      speed_mm_s=20, duration_ms=50), 30)
        self.assertEqual(result['reason'], 'direction_not_verified')
        result = unit.receive(message(4, 'move', token=1, command_id=1, action='FORWARD',
                                      speed_mm_s=20, duration_ms=50), 40)
        self.assertEqual(result['reason'], 'duplicate_mismatch')
        self.assertIsNone(unit.active)

    def test_stop_needs_no_token_and_never_arms_a_disabled_unit(self):
        unit = Supervisor(BOOT)
        unit.begin_session(LINK, HOST, BOOT, 0)
        unit.receive(message(1, 'stop', command_id=1), 10)
        self.assertEqual(unit.state, 'DISARMED')
        unit = fixture()
        unit.receive(message(4, 'stop', command_id=2), 40)
        self.assertIsNone(unit.active)

    def test_stop_id_is_consumed_and_cannot_be_reused_as_a_move(self):
        unit = fixture(start=False)
        unit.receive(message(3, 'stop', command_id=1), 30)
        result = unit.receive(message(4, 'move', token=1, command_id=1, action='FORWARD',
                                      speed_mm_s=20, duration_ms=50), 40)
        self.assertEqual(result['reason'], 'duplicate_mismatch')
        self.assertIsNone(unit.active)
        unit = fixture()
        unit.receive(message(4, 'stop', command_id=2), 40)
        result = unit.receive(message(5, 'move', token=1, command_id=2, action='FORWARD',
                                      speed_mm_s=20, duration_ms=50), 41)
        self.assertEqual(result['status'], 'rejected')
        self.assertIsNone(unit.active)
        unit = fixture()
        unit.receive(message(4, 'stop', command_id=1), 40)
        result = unit.receive(message(5, 'move', token=1, command_id=1, action='FORWARD',
                                      speed_mm_s=20, duration_ms=300), 41)
        self.assertEqual(result['status'], 'simulated_stopped')
        self.assertIsNone(unit.active)

    def test_physical_veto_dominates_display_and_does_not_auto_resume(self):
        unit = fixture()
        unit.receive(message(4, 'face', state='speaking'), 31)
        unit.set_local_inputs(40, physical_stop=True, power_ok=True, driver_ok=True,
                              direction_ok={'FORWARD': True})
        self.assertEqual(unit.face, 'blocked')
        self.assertIsNone(unit.active)
        self.assertFalse(unit.recover(41))
        self.assertFalse(unit.arm(42))
        unit.set_local_inputs(43, physical_stop=False, power_ok=True, driver_ok=True,
                              direction_ok={'FORWARD': True})
        self.assertEqual(unit.state, 'BLOCKED')

    def test_bad_sensor_snapshot_cannot_recover_using_cached_good_values(self):
        unit = fixture()
        with self.assertRaises(ValueError):
            unit.set_local_inputs(40, physical_stop=False, power_ok=True, driver_ok=True,
                                  direction_ok={'FORWARD': 1})
        self.assertFalse(unit.recover(41))
        self.assertFalse(unit.arm(42))
        unit.set_local_inputs(43, physical_stop=False, power_ok=True, driver_ok=True,
                              direction_ok={'FORWARD': True})
        self.assertTrue(unit.recover(44))
        self.assertEqual(unit.state, 'DISARMED')

    def test_local_sensor_expiry_is_not_renewed_by_host_heartbeat_or_vision(self):
        unit = fixture(local_input_ms=150)
        unit.issue_poll(100)
        unit.receive(message(4, 'heartbeat', token=2), 101)
        unit.receive(message(5, 'vision', token=2, frame_id=2,
                              state='CLEAR', remaining_ms=200), 102)
        self.assertEqual(unit.tick(149), 'DRIVING')
        self.assertEqual(unit.tick(150), 'BLOCKED')
        self.assertEqual(unit.reason, 'local_inputs_stale')

    def test_clock_regression_and_invalid_sensor_validity_stop_first(self):
        unit = fixture()
        with self.assertRaises(ValueError):
            unit.tick(29)
        self.assertIsNone(unit.active)
        self.assertEqual(unit.state, 'BLOCKED')
        self.assertFalse(unit.recover(40))
        unit.set_local_inputs(41, physical_stop=False, power_ok=True, driver_ok=True,
                              direction_ok={'FORWARD': True})
        self.assertFalse(unit.recover(42))
        self.assertTrue(unit.begin_session('4' * 32, HOST, BOOT, 43))
        self.assertFalse(unit.arm(44))
        unit = fixture()
        with self.assertRaises(ValueError):
            unit.set_local_inputs(40, physical_stop=False, power_ok=True, driver_ok=True,
                                  direction_ok={'FORWARD': 1})
        self.assertIsNone(unit.active)

    def test_new_session_clears_permits_and_old_boot_echo_rejects(self):
        unit = fixture()
        self.assertFalse(unit.begin_session('4' * 32, HOST, '5' * 32, 40))
        self.assertTrue(unit.begin_session('4' * 32, '6' * 32, BOOT, 41))
        self.assertEqual(unit.state, 'DISARMED')
        self.assertIsNone(unit.active)
        result = unit.receive(message(999, 'heartbeat', token=1), 42)
        self.assertEqual(result['reason'], 'wrong_link')

    def test_poll_lifecycle_does_not_depend_on_the_faster_control_tick(self):
        unit = fixture(start=False)
        with self.assertRaises(ValueError):
            unit.issue_poll(50)
        self.assertEqual(unit.issue_poll(100)['token'], 2)
        self.assertEqual(len(unit.tokens), 2)

    def test_link_nonce_cannot_be_reused_after_an_intermediate_session(self):
        unit = fixture(start=False)
        self.assertTrue(unit.begin_session('4' * 32, HOST, BOOT, 30))
        self.assertFalse(unit.begin_session(LINK, HOST, BOOT, 31))
        self.assertEqual(unit.link, '4' * 32)

    def test_fresh_poll_token_cannot_bless_a_buffered_old_frame(self):
        payload = host_vision_payload(2, 2, 'CLEAR', 100, 90, 110)
        self.assertEqual(payload['state'], 'UNKNOWN')
        self.assertEqual(payload['remaining_ms'], 0)
        payload = host_vision_payload(2, 2, 'CLEAR', 100, 105, 110)
        self.assertEqual(payload['state'], 'CLEAR')

    def test_human_intent_rejects_questions_quotes_conditions_and_model_origin(self):
        self.assertEqual(parse_motion_intent('前进。', origin='asr'), 'FORWARD')
        self.assertEqual(parse_motion_intent('Stop moving!', origin='asr'), 'STOP')
        for text in ('前进？', '不要前进', '如果前进会怎样', '请解释“前进”', '他说前进'):
            self.assertIsNone(parse_motion_intent(text, origin='asr'))
        self.assertIsNone(parse_motion_intent('前进', origin='llm'))


if __name__ == '__main__':
    unittest.main()
