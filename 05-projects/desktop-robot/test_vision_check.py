import unittest

import numpy as np

from vision_check import classify_corridor


class CorridorTests(unittest.TestCase):
    def setUp(self):
        row, column = np.indices((96, 128))
        self.reference = (115 + 45 * ((row // 4 + column // 4) % 2)).astype(np.uint8)
        self.roi = (16, 16, 96, 64)

    def test_supported_full_corridor_with_minor_exposure_change(self):
        frame = self.reference + 5
        frame[:16] = 0
        self.assertEqual(classify_corridor(self.reference, frame, self.roi), "CLEAR")

    def test_consistent_loss_of_support_ahead_with_near_table_in_view(self):
        frame = self.reference.copy()
        frame[16:42] = 45
        self.assertEqual(classify_corridor(self.reference, frame, self.roi), "EDGE")

    def test_localized_or_ambiguous_change_does_not_clear_corridor(self):
        frame = self.reference.copy()
        frame[16:42, 16:40] = 45
        self.assertEqual(classify_corridor(self.reference, frame, self.roi), "UNKNOWN")

    def test_obscured_near_table_does_not_look_like_an_edge(self):
        frame = self.reference.copy()
        frame[16:42] = 45
        frame[62:80] = 45
        self.assertEqual(classify_corridor(self.reference, frame, self.roi), "UNKNOWN")

    def test_unreliable_images_do_not_clear_corridor(self):
        dark = np.full_like(self.reference, 12)
        white = np.full_like(self.reference, 255)
        blurred = np.full_like(self.reference, 137)
        for frame in (None, dark, white, blurred, self.reference[1:]):
            with self.subTest(shape=getattr(frame, "shape", None)):
                self.assertEqual(classify_corridor(self.reference, frame, self.roi), "UNKNOWN")

    def test_textureless_reference_does_not_clear_corridor(self):
        flat = np.full_like(self.reference, 138)
        self.assertEqual(classify_corridor(flat, flat, self.roi), "UNKNOWN")

    def test_invalid_region_does_not_clear_corridor(self):
        for roi in ((-1, 16, 96, 64), (16, 16, 999, 64), (16, 16, 8, 8)):
            with self.subTest(roi=roi):
                self.assertEqual(classify_corridor(self.reference, self.reference, roi), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
