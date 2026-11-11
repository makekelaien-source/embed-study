"""Export face assets for a 240-by-320 ST7789 or a 128-by-64 SSD1306."""

import argparse
from pathlib import Path


WIDTH = 128
HEIGHT = 64
SCALE = 4
COLOR_SIZE = (240, 320)
COLOR_BACKGROUND = (10, 18, 32)
FACE_COLORS = {
    "idle": (111, 220, 206),
    "listening": (100, 225, 253),
    "thinking": (182, 167, 247),
    "speaking": (148, 234, 178),
    "blocked": (253, 170, 103),
}

# Each expression contains a left eye, right eye, and mouth on a 32×16 grid.
FACES = {
    "idle": (
        ("..##..", ".####.", ".####.", ".####.", "..##.."),
        ("..##..", ".####.", ".####.", ".####.", "..##.."),
        ("........", "#......#", ".##..##.", "...##...", "........"),
    ),
    "listening": (
        (".####.", "##..##", "#.##.#", "##..##", ".####."),
        (".####.", "##..##", "#.##.#", "##..##", ".####."),
        ("........", "...##...", "..#..#..", "...##...", "........"),
    ),
    "thinking": (
        (".#####", "......", "...##.", "...##.", "......"),
        ("...##.", "...##.", "...##.", "......", "......"),
        ("........", "........", "....####", "........", "........"),
    ),
    "speaking": (
        ("..##..", ".#..#.", "#....#", "......", "......"),
        ("..##..", ".#..#.", "#....#", "......", "......"),
        (".######.", "#......#", "#......#", ".#....#.", "..####.."),
    ),
    "blocked": (
        ("##....", "..##..", "....##", "......", "......"),
        ("....##", "..##..", "##....", "......", "......"),
        ("........", "...##...", ".##..##.", "#......#", "........"),
    ),
}


def _lit_cells(state):
    for (left, top), glyph in zip(((5, 3), (21, 3), (12, 9)), FACES[state]):
        for row, line in enumerate(glyph):
            for column, mark in enumerate(line):
                if mark == "#":
                    yield left + column, top + row


def lit_pixels(state):
    for column, row in _lit_cells(state):
        for dy in range(SCALE):
            for dx in range(SCALE):
                yield column * SCALE + dx, row * SCALE + dy


def ssd1306_frame(pixels):
    frame = bytearray(WIDTH * HEIGHT // 8)
    for x, y in pixels:
        page, bit = divmod(y, 8)
        frame[page * WIDTH + x] |= 1 << bit
    return frame


def pbm_preview(pixels):
    # PBM packs rows with the left pixel in bit 7. A zero bit is white.
    row_bytes = WIDTH // 8
    raster = bytearray(b"\xff" * (row_bytes * HEIGHT))
    for x, y in pixels:
        column, bit = divmod(x, 8)
        raster[y * row_bytes + column] &= ~(0x80 >> bit)
    return f"P4\n{WIDTH} {HEIGHT}\n".encode("ascii") + raster


def _color_image(state, artwork):
    from PIL import Image, ImageDraw

    width, height = COLOR_SIZE
    image = Image.new("RGB", COLOR_SIZE, COLOR_BACKGROUND)
    if artwork is not None:
        with Image.open(artwork, formats=("PNG",)) as source:
            scale = min(width / source.width, height / source.height)
            size = (max(1, round(source.width * scale)), max(1, round(source.height * scale)))
            layer = source.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        image.paste(layer, ((width - layer.width) // 2, (height - layer.height) // 2), layer)
        return image

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 77, 223, 242), radius=45, fill=(18, 32, 50), outline=(30, 54, 74), width=2)
    scale = 7
    left = (width - 32 * scale) // 2
    top = (height - 16 * scale) // 2
    for column, row in _lit_cells(state):
        x = left + column * scale
        y = top + row * scale
        draw.rectangle((x, y, x + scale - 1, y + scale - 1), fill=FACE_COLORS[state])
    return image


def _rgb565(image):
    data = image.tobytes()
    frame = bytearray()
    for red, green, blue in zip(data[::3], data[1::3], data[2::3]):
        value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
        frame.extend(value.to_bytes(2, "big"))
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", choices=FACES)
    parser.add_argument("output", type=Path, help="Color .rgb565/.png or monochrome .bin/.pbm")
    parser.add_argument("--artwork", type=Path, metavar="PNG", help="Replace the builtin color face with a PNG")
    args = parser.parse_args()
    suffix = args.output.suffix.lower()

    if suffix in (".png", ".rgb565"):
        try:
            image = _color_image(args.state, args.artwork)
        except ImportError:
            parser.error("color export requires Pillow. See the installation command in vision-face-runbook.md")
        except (OSError, ValueError) as error:
            parser.error(str(error))
        if suffix == ".png":
            image.save(args.output, format="PNG")
        else:
            args.output.write_bytes(_rgb565(image))
        return

    if args.artwork is not None:
        parser.error("--artwork requires .png or .rgb565 output")
    pixels = lit_pixels(args.state)
    if suffix == ".bin":
        args.output.write_bytes(ssd1306_frame(pixels))
    elif suffix == ".pbm":
        args.output.write_bytes(pbm_preview(pixels))
    else:
        parser.error("output must end in .rgb565, .png, .bin or .pbm")


if __name__ == "__main__":
    main()
