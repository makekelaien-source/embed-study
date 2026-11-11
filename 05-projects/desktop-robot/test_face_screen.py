import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from PIL import Image
except ImportError:
    Image = None


def export_face(state, target, *options):
    script = Path(__file__).with_name("face_screen.py")
    result = subprocess.run([sys.executable, str(script), state, str(target), *options],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return target.read_bytes()


class FaceScreenTests(unittest.TestCase):
    def test_all_states_export_distinct_ssd1306_frames(self):
        states = ("idle", "listening", "thinking", "speaking", "blocked")
        with tempfile.TemporaryDirectory() as folder:
            frames = [export_face(state, Path(folder) / f"{state}.bin") for state in states]

        self.assertEqual(len(set(frames)), len(states))
        for frame in frames:
            self.assertEqual(len(frame), 1024)
            self.assertGreater(sum(byte.bit_count() for byte in frame), 128)
            self.assertEqual(frame[:128], bytes(128))
            self.assertEqual(frame[-128:], bytes(128))

    def test_pbm_preview_matches_display_pixels(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            preview = export_face("listening", target / "face.pbm")
            frame = export_face("listening", target / "face.bin")

        magic, size, raster = preview.split(b"\n", maxsplit=2)
        self.assertEqual((magic, size), (b"P4", b"128 64"))
        self.assertEqual(len(raster), 1024)
        self.assertEqual(frame[128 + 24], 0xF0)
        preview_white = [not byte & (0x80 >> bit) for byte in raster for bit in range(8)]
        screen_lit = [
            bool(frame[y // 8 * 128 + x] & (1 << (y % 8)))
            for y in range(64)
            for x in range(128)
        ]
        self.assertEqual(preview_white, screen_lit)


@unittest.skipUnless(Image is not None, "color face export needs Pillow")
class ColorFaceScreenTests(unittest.TestCase):
    def test_builtin_color_states_export_distinct_portrait_previews_and_frames(self):
        states = ("idle", "listening", "thinking", "speaking", "blocked")
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            frames = [export_face(state, target / f"{state}.rgb565") for state in states]
            previews = [export_face(state, target / f"{state}.png") for state in states]

        self.assertEqual(len(set(frames)), len(states))
        self.assertEqual(len(set(previews)), len(states))
        for frame, preview in zip(frames, previews):
            self.assertEqual(len(frame), 153600)
            with Image.open(io.BytesIO(preview)) as image:
                self.assertEqual((image.size, image.mode), ((240, 320), "RGB"))

    def test_rgb565_red_green_blue_order_and_portrait_row_stride(self):
        image = Image.new("RGB", (240, 320))
        image.putpixel((0, 0), (255, 0, 0))
        image.putpixel((1, 0), (0, 255, 0))
        image.putpixel((0, 1), (0, 0, 255))
        image.putpixel((239, 319), (255, 255, 255))
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            source = target / "colors.png"
            image.save(source)
            frame = export_face("idle", target / "colors.rgb565", "--artwork", str(source))

        self.assertEqual(frame[:4], b"\xf8\x00\x07\xe0")
        self.assertEqual(frame[480:482], b"\x00\x1f")
        self.assertEqual(frame[-2:], b"\xff\xff")

    def test_custom_art_is_letterboxed_with_transparency_flattened(self):
        image = Image.new("RGBA", (120, 40), (255, 0, 0, 255))
        image.paste((0, 255, 0, 128), (40, 0, 80, 40))
        image.paste((0, 0, 255, 0), (80, 0, 120, 40))
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            source = target / "wide.png"
            image.save(source)
            preview = export_face("idle", target / "custom.png", "--artwork", str(source))
            builtin = export_face("idle", target / "builtin.png")

        with Image.open(io.BytesIO(preview)) as custom, Image.open(io.BytesIO(builtin)) as base:
            background = base.getpixel((0, 0))
            self.assertEqual(custom.getpixel((30, 119)), background)
            self.assertEqual(custom.getpixel((30, 120)), (255, 0, 0))
            self.assertEqual(custom.getpixel((30, 199)), (255, 0, 0))
            self.assertEqual(custom.getpixel((30, 200)), background)
            self.assertEqual(custom.getpixel((200, 160)), background)
            half_green = custom.getpixel((120, 160))
            self.assertEqual(half_green, (background[0] // 2, (background[1] + 256) // 2, background[2] // 2))
