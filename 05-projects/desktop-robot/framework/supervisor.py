"""Receiver-side safety STATE SIMULATION; this contains no actuator backend.

All motion is disabled by default. Test inputs are not sensor evidence. A real
MCU implementation must run independently of the SBC, voice and LCD tasks.
"""
from collections import deque
from dataclasses import dataclass, field

from .wire import ACTIONS, MAX_COUNTER, Message, identifier


@dataclass(frozen=True)
class SafetyConfig:
    motion_enabled: bool = False
    calibrated: bool = False
    safe_actions: frozenset = field(default_factory=frozenset)
    max_speed_mm_s: int = 20
    heartbeat_ms: int = 500
    lease_ms: int = 200
    poll_period_ms: int = 100
    local_input_ms: int = 100

    def __post_init__(self):
        if type(self.motion_enabled) is not bool or type(self.calibrated) is not bool:
            raise ValueError('Enable/calibration flags must be booleans')
        if not isinstance(self.safe_actions, frozenset) or not self.safe_actions <= ACTIONS:
            raise ValueError('Safe directions must be an explicit frozenset')
        for value, lower, upper in ((self.max_speed_mm_s, 1, 100),
                                    (self.heartbeat_ms, 50, 1000), (self.lease_ms, 1, 200),
                                    (self.poll_period_ms, 1, 200), (self.local_input_ms, 10, 500)):
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError('Invalid simulation budget')
        if not self.poll_period_ms <= self.lease_ms <= 2 * self.poll_period_ms:
            raise ValueError('Two-token window requires poll_period >= half the lease')


def host_vision_payload(token, frame_id, state, poll_received_ms, captured_ms,
                        evaluated_ms, max_frame_age_ms=100, remaining_ms=200):
    """Host adapter contract: capture must be NEWER than receipt of this poll.

    These three times use only the SBC's monotonic clock. The MCU independently
    enforces its own issued-token deadline. A fresh token cannot bless an old
    buffered image. Real capture time must come from a validated camera clock.
    """
    values = (poll_received_ms, captured_ms, evaluated_ms, max_frame_age_ms, remaining_ms)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError('Host timestamps/budgets must be nonnegative integer milliseconds')
    if state not in ('CLEAR', 'EDGE', 'UNKNOWN') or remaining_ms > 200:
        raise ValueError('Invalid classification or budget')
    fresh = (poll_received_ms < captured_ms <= evaluated_ms
             and evaluated_ms - captured_ms <= max_frame_age_ms)
    return {'token': token, 'frame_id': frame_id,
            'state': state if fresh else 'UNKNOWN',
            'remaining_ms': remaining_ms if fresh and state == 'CLEAR' else 0}


class Supervisor:
    def __init__(self, local_boot, config=None):
        if not identifier(local_boot):
            raise ValueError('Require a fresh local boot identifier')
        self.local_boot = local_boot
        self.config = config or SafetyConfig()
        self.link = None
        self.seen_links = set()
        self.host_boot = None
        self.state = 'DISARMED'
        self.clock_ms = 0
        self.last_rx_seq = 0
        self.poll_serial = 0
        self.last_poll_ms = None
        self.tokens = {}
        self.last_heartbeat_ms = None
        self.vision_until_ms = 0
        self.last_frame_id = 0
        self.highest_command_id = 0
        self.active = None
        self.receipts = {}
        self.events = deque(maxlen=256)
        self.physical_stop = False
        self.power_ok = self.driver_ok = False
        self.local_inputs_valid = False
        self.local_inputs_at_ms = None
        self.clock_fault = False
        self.direction_ok = {action: False for action in ACTIONS}
        self.requested_face = 'idle'
        self.reason = 'not_armed'

    def _time(self, now):
        if type(now) is not int or not 0 <= now <= 2 ** 64 - 1:
            self.clock_fault = True
            self._invalidate_inputs()
            self._halt('invalid_clock', blocked=True)
            raise ValueError('Require local uint64-style monotonic milliseconds')
        if now < self.clock_ms:
            self.clock_fault = True
            self._invalidate_inputs()
            self.tokens.clear()
            self.last_heartbeat_ms = None
            self._halt('clock_regression', blocked=True)
            raise ValueError('Clock regressed; movement inhibited')
        self.clock_ms = now

    def _receipt(self, command_id, status, reason):
        return {'command_id': command_id, 'status': status, 'reason': reason,
                'physical_verified': False, 'local_only': command_id is None}

    def _invalidate_inputs(self):
        self.local_inputs_valid = False
        self.local_inputs_at_ms = None
        self.power_ok = self.driver_ok = False
        self.direction_ok = {action: False for action in ACTIONS}

    def _cache(self, command_id, signature, receipt):
        self.receipts[command_id] = (signature, dict(receipt))
        while len(self.receipts) > 64:
            del self.receipts[next(iter(self.receipts))]

    def _halt(self, reason, blocked=False):
        previous = self.state
        if self.active is not None:
            command_id = self.active['command_id']
            signature = self.active['signature']
            receipt = self._receipt(command_id, 'simulated_stopped', reason)
            self._cache(command_id, signature, receipt)
            self.events.append(dict(receipt, at_ms=self.clock_ms, hardware_action=False))
        self.active = None
        self.reason = reason
        self.state = ('BLOCKED' if blocked or previous == 'BLOCKED' else
                      'ARMED' if previous in ('ARMED', 'DRIVING') else 'DISARMED')
        if blocked:
            self.vision_until_ms = 0

    def begin_session(self, link, host_boot, echoed_mcu_boot, now):
        """Trusted HELLO_ACK adapter hook, NOT an automatic remote arm command."""
        self._time(now)
        if not identifier(link) or not identifier(host_boot) or echoed_mcu_boot != self.local_boot:
            return False
        if link in self.seen_links:
            return False
        if len(self.seen_links) >= 256:
            self._halt('session_table_exhausted', blocked=True)
            return False
        self._halt('new_session', blocked=True)
        self.link, self.host_boot = link, host_boot
        self.seen_links.add(link)
        self.state = 'DISARMED'
        self.last_rx_seq = self.poll_serial = self.last_frame_id = self.highest_command_id = 0
        self.tokens.clear()
        self.clock_fault = False
        self._invalidate_inputs()
        self.last_poll_ms = self.last_heartbeat_ms = None
        self.vision_until_ms = 0
        self.receipts.clear()
        return True

    def issue_poll(self, now):
        self.tick(now)
        if self.link is None:
            raise ValueError('Poll requires validated boot/session negotiation')
        if self.last_poll_ms is not None and now - self.last_poll_ms < self.config.poll_period_ms:
            raise ValueError('Poll cadence is separate from the faster safety tick')
        if self.poll_serial == MAX_COUNTER:
            self._halt('counter_exhausted', blocked=True)
            raise ValueError('Renegotiate before counter wrap')
        self.poll_serial += 1
        self.last_poll_ms = now
        self.tokens = {token: expiry for token, expiry in self.tokens.items() if expiry > now}
        self.tokens[self.poll_serial] = now + self.config.lease_ms
        while len(self.tokens) > 2:
            del self.tokens[min(self.tokens)]
        return {'token': self.poll_serial, 'budget_ms': self.config.lease_ms}

    def _token(self, token, now):
        return self.tokens.get(token, 0) > now

    def set_local_inputs(self, now, *, physical_stop, power_ok, driver_ok, direction_ok):
        self._time(now)
        if any(type(flag) is not bool for flag in (physical_stop, power_ok, driver_ok)):
            self._invalidate_inputs()
            self._halt('invalid_local_inputs', blocked=True)
            raise ValueError('Local inputs need explicit validity, not truthy values')
        if not isinstance(direction_ok, dict) or set(direction_ok) - ACTIONS:
            self._invalidate_inputs()
            self._halt('invalid_local_inputs', blocked=True)
            raise ValueError('Unknown direction')
        if any(type(flag) is not bool for flag in direction_ok.values()):
            self._invalidate_inputs()
            self._halt('invalid_local_inputs', blocked=True)
            raise ValueError('Direction sensor validity must be boolean')
        self.physical_stop, self.power_ok, self.driver_ok = physical_stop, power_ok, driver_ok
        self.local_inputs_valid, self.local_inputs_at_ms = True, now
        self.direction_ok = {action: direction_ok.get(action, False) for action in ACTIONS}
        if physical_stop or not power_ok or not driver_ok:
            self._halt('physical_stop' if physical_stop else 'power_or_driver_fault', blocked=True)
        self.tick(now)

    def _base_reason(self, now):
        if not self.config.motion_enabled:
            return 'motion_disabled'
        if not self.config.calibrated:
            return 'calibration_missing'
        if self.link is None:
            return 'no_session'
        if self.clock_fault:
            return 'clock_fault'
        if not self.local_inputs_valid:
            return 'local_inputs_invalid'
        if now - self.local_inputs_at_ms >= self.config.local_input_ms:
            return 'local_inputs_stale'
        if self.physical_stop:
            return 'physical_stop'
        if not self.power_ok or not self.driver_ok:
            return 'power_or_driver_fault'
        if self.last_heartbeat_ms is None or now - self.last_heartbeat_ms >= self.config.heartbeat_ms:
            return 'heartbeat_expired'
        return None

    def arm(self, now):
        self.tick(now)
        if self.state in ('DRIVING', 'BLOCKED'):
            return False
        reason = self._base_reason(now)
        if reason or not any(self.direction_ok[action] for action in self.config.safe_actions):
            self.state = 'DISARMED'
            self.reason = reason or 'no_verified_direction'
            return False
        self.state, self.reason = 'ARMED', 'ok'
        return True

    def recover(self, now):
        self.tick(now)
        if self.state != 'BLOCKED' or self._base_reason(now):
            return False
        self.state, self.reason = 'DISARMED', 'await_rearm'
        self.vision_until_ms = 0
        return True

    def _move_reason(self, action, now):
        reason = self._base_reason(now)
        if reason:
            return reason
        if action not in self.config.safe_actions or not self.direction_ok[action]:
            return 'direction_not_verified'
        if action == 'FORWARD' and self.vision_until_ms <= now:
            return 'vision_expired'
        return None

    def tick(self, now):
        self._time(now)
        if self.state == 'DRIVING':
            reason = self._move_reason(self.active['action'], now)
            if reason:
                self._halt(reason, blocked=True)
            elif now >= self.active['until_ms']:
                self._halt('duration_elapsed')
        elif self.state == 'ARMED' and self._base_reason(now):
            self._halt(self._base_reason(now), blocked=True)
        return self.state

    def receive(self, message, now):
        self.tick(now)
        if not isinstance(message, Message):
            raise TypeError('Parse/validate framing before supervising')
        if message.link != self.link:
            return self._receipt(None, 'rejected', 'wrong_link')
        if message.seq <= self.last_rx_seq:
            return self._receipt(None, 'rejected', 'old_sequence')
        self.last_rx_seq = message.seq
        payload = message.payload
        if message.kind == 'stop':
            self._halt('remote_stop')
            command_id = payload['command_id']
            receipt = self._receipt(command_id, 'simulated_stopped', 'remote_stop')
            # STOP always halts, but its ID can never later become a MOVE.
            if command_id > self.highest_command_id:
                self.highest_command_id = command_id
                self._cache(command_id, (('kind', 'stop'), ('command_id', command_id)), receipt)
            return receipt
        if message.kind == 'face':
            self.requested_face = payload['state']
            return None
        if message.kind == 'vision' and payload['state'] != 'CLEAR':
            # New revoke sequence MUST work even when frame_id/token are old.
            self.vision_until_ms = 0
            self._halt('vision_' + payload['state'].lower(), blocked=True)
            return None
        if message.kind == 'move':
            command_id = payload['command_id']
            signature = tuple(sorted(payload.items()))
            if command_id in self.receipts:
                old_signature, receipt = self.receipts[command_id]
                return dict(receipt, cached=True) if signature == old_signature else self._receipt(
                    command_id, 'rejected', 'duplicate_mismatch')
            if command_id <= self.highest_command_id:
                return self._receipt(command_id, 'rejected', 'old_command')
            self.highest_command_id = command_id
            reason = ('unarmed' if self.state != 'ARMED' else
                      'token_expired' if not self._token(payload['token'], now) else
                      'speed_limit' if payload['speed_mm_s'] > self.config.max_speed_mm_s else
                      self._move_reason(payload['action'], now))
            receipt = self._receipt(command_id, 'rejected' if reason else 'accepted', reason or 'ok')
            self._cache(command_id, signature, receipt)
            if not reason:
                self.active = dict(payload, signature=signature, until_ms=now + payload['duration_ms'])
                self.state = 'DRIVING'
                self.events.append(dict(receipt, at_ms=now, hardware_action=False))
            return receipt
        if message.kind not in ('vision', 'heartbeat'):
            return self._receipt(None, 'rejected', 'unsupported_kind')
        if not self._token(payload['token'], now):
            return self._receipt(None, 'rejected', 'token_expired')
        if message.kind == 'heartbeat':
            self.last_heartbeat_ms = now
        elif payload['frame_id'] > self.last_frame_id:
            self.last_frame_id = payload['frame_id']
            self.vision_until_ms = min(self.tokens[payload['token']], now + payload['remaining_ms'])
        self.tick(now)
        return None

    @property
    def face(self):
        if self.physical_stop:
            return 'blocked'
        if self.link is None:
            return 'boot'
        if not self.config.motion_enabled:
            return self.requested_face
        if self.clock_fault or not self.local_inputs_valid:
            return 'fault'
        if not self.power_ok or not self.driver_ok:
            return 'fault'
        if self.reason == 'heartbeat_expired':
            return 'offline'
        if self.state == 'BLOCKED':
            return 'blocked'
        return self.requested_face
