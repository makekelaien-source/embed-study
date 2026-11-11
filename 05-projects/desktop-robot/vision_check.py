"""Compare stationary camera frames with a calibrated tabletop reference."""

import argparse
import sys
from pathlib import Path

import numpy as np


def _tiles(corridor):
    return [np.array_split(band, 4, axis=1) for band in np.array_split(corridor, 4)]


def _gray(tile):
    return tile.mean(axis=2) if tile.ndim == 3 else tile


def _exposure_ok(gray):
    return ((gray > 15) & (gray < 245)).mean() >= 0.90


def _detail(gray):
    return (np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()) / 2


def classify_corridor(reference, frame, roi):
    """Return CLEAR, EDGE or UNKNOWN for a fixed ROI with farther pixels at the top."""
    if reference is None or frame is None or reference.shape != frame.shape:
        return "UNKNOWN"
    if reference.dtype != np.uint8 or frame.dtype != np.uint8:
        return "UNKNOWN"
    if reference.ndim != 2 and (reference.ndim != 3 or reference.shape[2] != 3):
        return "UNKNOWN"
    x, y, width, height = roi
    rows, columns = reference.shape[:2]
    if min(x, y) < 0 or min(width, height) < 32 or x + width > columns or y + height > rows:
        return "UNKNOWN"

    reference_tiles = _tiles(reference[y:y + height, x:x + width].astype(np.float32))
    frame_tiles = _tiles(frame[y:y + height, x:x + width].astype(np.float32))
    supported = []
    changed = []
    for reference_band, frame_band in zip(reference_tiles, frame_tiles):
        band_supported = []
        band_changed = []
        for reference_tile, frame_tile in zip(reference_band, frame_band):
            reference_gray = _gray(reference_tile)
            frame_gray = _gray(frame_tile)
            reference_detail = _detail(reference_gray)
            if reference_detail < 4 or not (_exposure_ok(reference_gray) and _exposure_ok(frame_gray)):
                return "UNKNOWN"

            difference = np.abs(reference_tile - frame_tile)
            if difference.ndim == 3:
                difference = difference.max(axis=2)
            matching_fraction = (difference <= 24).mean()
            band_supported.append(matching_fraction >= 0.85 and _detail(frame_gray) >= reference_detail * 0.55)
            band_changed.append(matching_fraction <= 0.30)

        supported.append(all(band_supported))
        changed.append(all(band_changed))

    if all(supported):
        return "CLEAR"
    if changed[0] and all(supported[2:]):
        return "EDGE"
    return "UNKNOWN"


def _load_image(cv2, path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def _check_camera(cv2, device, count, reference, roi):
    source = int(device) if device.isdecimal() else device
    backend = cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY
    camera = cv2.VideoCapture(source, backend)
    try:
        if not camera.isOpened():
            print(f"{device}: UNKNOWN (camera did not open)")
            return 1
        rows, columns = reference.shape[:2]
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, columns)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, rows)
        for index in range(1, count + 1):
            ok, frame = camera.read()
            if not ok or frame is None:
                print(f"frame {index}: UNKNOWN (camera read failed)")
                return 1
            if frame.shape != reference.shape:
                print(f"frame {index}: UNKNOWN (camera size differs from reference)")
                return 1
            print(f"frame {index}: {classify_corridor(reference, frame, roi)}", flush=True)
        return 0
    finally:
        camera.release()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stationary tabletop vision diagnostic. Classifications are candidates.")
    parser.add_argument("--reference", type=Path, required=True, help="image with the entire corridor on the tabletop")
    parser.add_argument("--roi", type=int, nargs=4, required=True, metavar=("X", "Y", "WIDTH", "HEIGHT"))
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--image", type=Path, nargs="+", metavar="FILE", help="replay one or more image files")
    sources.add_argument("--camera", metavar="DEVICE", help="camera index or Linux V4L2 device path")
    parser.add_argument("--frames", type=int, default=20, help="number of camera samples, from 1 to 300")
    args = parser.parse_args(argv)
    if not 1 <= args.frames <= 300:
        parser.error("--frames must be from 1 to 300")
    try:
        import cv2
    except ImportError:
        parser.exit(2, "OpenCV is required to read image files or use a camera. Install opencv-python-headless.\n")

    reference = _load_image(cv2, args.reference)
    if classify_corridor(reference, reference, args.roi) != "CLEAR":
        print(f"{args.reference}: UNKNOWN (unreadable or unsuitable reference/ROI)")
        return 1
    if args.camera is not None:
        return _check_camera(cv2, args.camera, args.frames, reference, args.roi)

    input_error = False
    for path in args.image:
        frame = _load_image(cv2, path)
        input_error |= frame is None or frame.shape != reference.shape
        print(f"{path}: {classify_corridor(reference, frame, args.roi)}")
    return int(input_error)


if __name__ == "__main__":
    raise SystemExit(main())
