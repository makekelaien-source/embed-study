"""Offline two-track differential mixing; no GPIO, serial or motor actions.

The no-slip model does not prove a tracked robot's actual path or safety.
All example geometry and speed values must remain separate from live setup.
"""
import argparse
from dataclasses import asdict, dataclass
import json
import math


def finite_number(name, value, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + ' must be a confirmed numeric value')
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise ValueError(name + ' must be finite') from None
    if not math.isfinite(number) or (positive and number <= 0):
        raise ValueError(name + (' must be finite and positive' if positive else ' must be finite'))
    return number


@dataclass(frozen=True)
class TrackGeometry:
    track_center_spacing_m: float
    effective_gauge_m: float
    max_track_speed_m_s: float

    def __post_init__(self):
        # No guessed fallback for a missing/pending dimension or speed limit.
        for field in ('track_center_spacing_m', 'effective_gauge_m', 'max_track_speed_m_s'):
            object.__setattr__(self, field, finite_number(field, getattr(self, field), positive=True))


@dataclass(frozen=True)
class TrackSpeeds:
    left_m_s: float
    right_m_s: float
    scale: float


def mix_twist(linear_m_s, angular_rad_s, geometry):
    """Map forward-positive / counterclockwise-positive twist to track speeds.

    Output signs refer to each track moving the chassis forward. A common
    saturation scale preserves their ratio; independent clipping would not.
    This only calculates target track linear speeds. It grants no permission
    to drive and does not implement acceleration, reversal or safe stopping.
    """
    if not isinstance(geometry, TrackGeometry):
        raise ValueError('geometry must be a validated TrackGeometry')
    linear = finite_number('linear_m_s', linear_m_s)
    angular = finite_number('angular_rad_s', angular_rad_s)
    turn = angular * (geometry.effective_gauge_m / 2)
    left, right = linear - turn, linear + turn
    if not all(math.isfinite(value) for value in (turn, left, right)):
        raise ValueError('requested twist exceeds finite arithmetic range')
    peak = max(abs(left), abs(right))
    if peak <= geometry.max_track_speed_m_s:
        return TrackSpeeds(left, right, 1.)
    scale = geometry.max_track_speed_m_s / peak
    if scale == 0:
        raise ValueError('requested normalization scale underflows')
    # Normalize before multiplying, so each result stays within its limit.
    return TrackSpeeds(left / peak * geometry.max_track_speed_m_s,
                       right / peak * geometry.max_track_speed_m_s, scale)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linear', type=float, required=True, help='Desired forward velocity, m/s')
    parser.add_argument('--angular', type=float, required=True, help='Desired CCW yaw rate, rad/s')
    parser.add_argument('--track-gauge', type=float, required=True, help='Measured physical track-center spacing, m')
    parser.add_argument('--effective-gauge', type=float, required=True, help='Explicit model/calibrated effective gauge, m')
    parser.add_argument('--max-track-speed', type=float, required=True, help='Explicit example/validated track speed limit, m/s')
    args = parser.parse_args(argv)
    try:
        geometry = TrackGeometry(args.track_gauge, args.effective_gauge, args.max_track_speed)
        result = mix_twist(args.linear, args.angular, geometry)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({'mode': 'math-only-dry-run', 'geometry': asdict(geometry),
                      'requested_twist': {'linear_m_s': args.linear, 'angular_rad_s': args.angular},
                      'target_tracks': asdict(result),
                      'hardware_action': False}, allow_nan=False))


if __name__ == '__main__':
    main()
