import unittest

try:
    from .motion_math import TrackGeometry, mix_twist
except ImportError:
    from motion_math import TrackGeometry, mix_twist


class MotionMathTests(unittest.TestCase):
    # Synthetic geometry only; these values are not measured robot settings.
    geometry = TrackGeometry(.18, .20, .30)

    def test_unit_translation_and_rotation_have_explicit_units_and_signs(self):
        unconstrained = TrackGeometry(.18, .20, 2.)
        forward = mix_twist(1., 0., unconstrained)
        self.assertEqual((forward.left_m_s, forward.right_m_s, forward.scale), (1., 1., 1.))
        rotation = mix_twist(0., 1., unconstrained)
        self.assertAlmostEqual(rotation.left_m_s, -.1)
        self.assertAlmostEqual(rotation.right_m_s, .1)

    def test_reverse_spin_and_curved_reverse_preserve_requested_signs(self):
        reverse = mix_twist(-.1, 0., self.geometry)
        self.assertEqual((reverse.left_m_s, reverse.right_m_s), (-.1, -.1))
        left_spin = mix_twist(0., 2., self.geometry)
        self.assertEqual((left_spin.left_m_s, left_spin.right_m_s), (-.2, .2))
        right_spin = mix_twist(0., -2., self.geometry)
        self.assertEqual((right_spin.left_m_s, right_spin.right_m_s), (.2, -.2))
        curved_reverse = mix_twist(-.1, .5, self.geometry)
        self.assertAlmostEqual(curved_reverse.left_m_s, -.15)
        self.assertAlmostEqual(curved_reverse.right_m_s, -.05)

    def test_stop_is_zero_on_both_tracks(self):
        stop = mix_twist(0., 0., self.geometry)
        self.assertEqual((stop.left_m_s, stop.right_m_s, stop.scale), (0., 0., 1.))

    def test_combined_speed_saturation_uses_one_scale_and_preserves_curvature(self):
        limited = TrackGeometry(.18, .20, .15)
        result = mix_twist(.20, 1., limited)  # raw left .10, right .30
        self.assertAlmostEqual(result.scale, .5)
        self.assertAlmostEqual(result.left_m_s, .05)
        self.assertAlmostEqual(result.right_m_s, .15)
        self.assertAlmostEqual(result.left_m_s / result.right_m_s, 1 / 3)
        linear = (result.left_m_s + result.right_m_s) / 2
        angular = (result.right_m_s - result.left_m_s) / limited.effective_gauge_m
        self.assertAlmostEqual(linear, .20 * result.scale)
        self.assertAlmostEqual(angular, 1. * result.scale)

    def test_saturation_preserves_opposite_track_directions(self):
        limited = TrackGeometry(.18, .20, .05)
        result = mix_twist(.01, 2., limited)
        self.assertLess(result.left_m_s, 0)
        self.assertGreater(result.right_m_s, 0)
        self.assertLessEqual(abs(result.left_m_s), .05)
        self.assertLessEqual(abs(result.right_m_s), .05)
        self.assertAlmostEqual(result.left_m_s / result.right_m_s, -.19 / .21)

    def test_effective_gauge_is_separate_from_measured_physical_spacing(self):
        physical_model = TrackGeometry(.18, .18, 1.)
        scrub_model = TrackGeometry(.18, .24, 1.)
        a, b = mix_twist(0., 1., physical_model), mix_twist(0., 1., scrub_model)
        self.assertAlmostEqual(a.right_m_s, .09)
        self.assertAlmostEqual(b.right_m_s, .12)
        self.assertEqual(physical_model.track_center_spacing_m, scrub_model.track_center_spacing_m)

    def test_pending_nonfinite_or_nonpositive_geometry_is_rejected(self):
        for invalid in (None, 'pending', '', True, 0, -.1, float('nan'), float('inf')):
            for index in range(3):
                values = [.18, .20, .30]
                values[index] = invalid
                with self.subTest(index=index, invalid=invalid), self.assertRaises(ValueError):
                    TrackGeometry(*values)
        with self.assertRaises(ValueError):
            mix_twist(.1, 0., {'effective_gauge_m': .20})

    def test_invalid_twists_and_arithmetic_overflow_are_rejected(self):
        for invalid in (None, '0.1', False, float('nan'), float('inf')):
            for pair in ((invalid, 0.), (0., invalid)):
                with self.subTest(pair=pair), self.assertRaises(ValueError):
                    mix_twist(*pair, self.geometry)
        with self.assertRaises(ValueError):
            mix_twist(1e308, 1e308, TrackGeometry(.18, 4., .3))


if __name__ == '__main__':
    unittest.main()
