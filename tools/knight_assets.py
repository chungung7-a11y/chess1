#!/usr/bin/env python3
"""Deterministic knight-sheet packer and observable asset validator."""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
WHITE = ROOT / "assets/pieces/white-knight.png"
BLACK = ROOT / "assets/pieces/black-knight.png"
SOURCE = ROOT / ".superpowers/sdd/2026-09-08-flat-pixel-battle-implementation/knight-source-checker.png"
CELL, COLS, ROWS = 128, 8, 6
SIZE = (CELL * COLS, CELL * ROWS)
FOOT = (64, 120)
GUTTER = 8
STATES = {
    "idle": (0, 4), "walk": (4, 6), "hit": (10, 3),
    "recover": (13, 3), "cheer": (16, 4),
    "anticipation": (20, 3), "attackA": (23, 6),
    "attackB": (29, 6), "finisher": (35, 8),
    "deathEntry": (43, 5),
}
STANDING = tuple(range(10)) + tuple(range(13, 20))
EXPECTED_BOTTOM = {frame: 119 for frame in range(48)}
EXPECTED_BOTTOM.update({36: 105, 37: 98, 38: 98, 39: 105})


def is_checker(pixel: tuple[int, int, int]) -> bool:
    return min(pixel) >= 178 and max(pixel) - min(pixel) <= 22


def connected_foreground(source: Image.Image) -> np.ndarray:
    """Remove only checker-like pixels connected to an outer image edge."""
    rgb = np.asarray(source, dtype=np.int16)
    checker = (rgb.min(axis=2) >= 178) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= 22)
    flood = Image.fromarray((checker * 255).astype(np.uint8)).copy()
    ImageDraw.floodfill(flood, (0, 0), 128)
    connected_background = np.asarray(flood) == 128
    return ~connected_background


def geodesic_split(runs: list[tuple[int, int, int]], group: list[int],
                   width: int, height: int, columns: list[int], row: int) -> dict[int, list[int]]:
    left = min(runs[index][1] for index in group)
    right = max(runs[index][2] for index in group)
    top = min(runs[index][0] for index in group)
    bottom = max(runs[index][0] for index in group) + 1
    local = np.zeros((bottom - top, right - left), dtype=np.bool_)
    for index in group:
        y, start, end = runs[index]
        local[y - top, start - left:end - left] = True

    ys, xs = np.nonzero(local)
    owners = np.full(local.shape, -1, dtype=np.int8)
    queue: deque[tuple[int, int]] = deque()
    source_cell, source_row = width / COLS, height / ROWS
    for label, column in enumerate(columns):
        cx, cy = (column + .5) * source_cell - left, (row + .5) * source_row - top
        seed_at = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
        sy, sx = int(ys[seed_at]), int(xs[seed_at])
        owners[sy, sx] = label
        queue.append((sy, sx))
    while queue:
        y, x = queue.popleft()
        for ny in range(max(0, y - 1), min(local.shape[0], y + 2)):
            for nx in range(max(0, x - 1), min(local.shape[1], x + 2)):
                if local[ny, nx] and owners[ny, nx] < 0:
                    owners[ny, nx] = owners[y, x]
                    queue.append((ny, nx))

    split = {column: [] for column in columns}
    for label, column in enumerate(columns):
        owned_y, owned_x = np.nonzero(owners == label)
        split[column] = ((owned_y + top) * width + owned_x + left).tolist()
    return split


def assign_components(mask: np.ndarray, size: tuple[int, int]) -> list[list[int]]:
    """Assign complete connected poses to the nearest source-cell center."""
    width, height = size
    runs: list[tuple[int, int, int]] = []
    parents: list[int] = []

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(a: int, b: int) -> None:
        a, b = find(a), find(b)
        if a != b:
            parents[b] = a

    previous: list[int] = []
    for y in range(height):
        padded = np.pad(mask[y], (1, 1))
        changes = np.diff(padded.astype(np.int8))
        starts = np.flatnonzero(changes == 1)
        ends = np.flatnonzero(changes == -1)
        current: list[int] = []
        cursor = 0
        for start, end in zip(starts.tolist(), ends.tolist()):
            index = len(runs)
            runs.append((y, start, end))
            parents.append(index)
            current.append(index)
            while cursor < len(previous) and runs[previous[cursor]][2] < start - 1:
                cursor += 1
            probe = cursor
            while probe < len(previous) and runs[previous[probe]][1] <= end:
                union(index, previous[probe])
                probe += 1
        previous = current

    groups: dict[int, list[int]] = {}
    for index in range(len(runs)):
        groups.setdefault(find(index), []).append(index)

    poses: list[list[int]] = [[] for _ in range(48)]
    source_cell, source_row = width / COLS, height / ROWS
    for group in groups.values():
        area = sum(runs[index][2] - runs[index][1] for index in group)
        if area < 8:
            continue
        left = min(runs[index][1] for index in group)
        right = max(runs[index][2] for index in group)
        top = min(runs[index][0] for index in group)
        bottom = max(runs[index][0] for index in group) + 1
        x_total = sum((start + end - 1) * (end - start) / 2
                      for _, start, end in (runs[index] for index in group))
        y_total = sum(y * (end - start)
                      for y, start, end in (runs[index] for index in group))
        column = max(0, min(COLS - 1, int((x_total / area) / source_cell)))
        row = max(0, min(ROWS - 1, int((y_total / area) / source_row)))
        columns = [candidate for candidate in range(COLS)
                   if left <= (candidate + .5) * source_cell < right]
        if len(columns) > 1 and right - left > source_cell * 1.35:
            split = geodesic_split(runs, group, width, height, columns, row)
            for owner, offsets in split.items():
                poses[row * COLS + owner].extend(offsets)
            continue
        for run_index in group:
            y, start, end = runs[run_index]
            poses[row * COLS + column].extend(range(y * width + start, y * width + end))
    return poses


def extract_pose(source: Image.Image, offsets: list[int]) -> Image.Image:
    width, _ = source.size
    xs = [offset % width for offset in offsets]
    ys = [offset // width for offset in offsets]
    left, top, right, bottom = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    pose = Image.new("RGBA", (right - left, bottom - top))
    source_pixels, pose_pixels = source.load(), pose.load()
    for offset in offsets:
        y, x = divmod(offset, width)
        pose_pixels[x - left, y - top] = (*source_pixels[x, y], 255)
    return pose


def pose_support_center(pose: Image.Image) -> float:
    alpha = pose.getchannel("A")
    bottom = alpha.getbbox()[3] - 1
    xs = [x for y in range(max(0, bottom - 3), bottom + 1)
          for x in range(pose.width) if alpha.getpixel((x, y))]
    xs.sort()
    middle = len(xs) // 2
    return float(xs[middle]) if len(xs) % 2 else (xs[middle - 1] + xs[middle]) / 2


def pack_pose(pose: Image.Image, index: int) -> Image.Image:
    pose = pose.crop(pose.getchannel("A").getbbox())
    if index == 34:
        pose = pose.rotate(-4, resample=Image.Resampling.NEAREST, expand=True)
        pose = pose.crop(pose.getchannel("A").getbbox())
    bottom = EXPECTED_BOTTOM[index]
    max_width = 104 if index in STANDING else 112
    max_height = bottom - GUTTER + 1
    scale = min(1.0, max_width / pose.width, max_height / pose.height)
    if index in STANDING:
        support = pose_support_center(pose)
        anchor_room = FOOT[0] - GUTTER
        scale = min(scale, anchor_room / max(support, pose.width - 1 - support))
    target = (max(1, round(pose.width * scale)), max(1, round(pose.height * scale)))
    if target != pose.size:
        pose = pose.resize(target, Image.Resampling.NEAREST)
    pose = pose.crop(pose.getchannel("A").getbbox())

    if index in STANDING:
        left = round(FOOT[0] - pose_support_center(pose))
    else:
        left = round(FOOT[0] - pose.width / 2)
    left = max(GUTTER, min(CELL - GUTTER - pose.width, left))
    top = bottom - pose.height + 1
    tile = Image.new("RGBA", (CELL, CELL))
    tile.alpha_composite(pose, (left, top))
    return tile


def black_palette(white: Image.Image) -> Image.Image:
    black = Image.new("RGBA", white.size)
    output = []
    for red, green, blue, alpha in white.get_flattened_data():
        if not alpha:
            output.append((0, 0, 0, 0))
            continue
        high, low = max(red, green, blue), min(red, green, blue)
        light = (red * 30 + green * 59 + blue * 11) // 100
        if blue > red * 1.15 and blue > green * 1.08 and blue - min(red, green) > 24:
            mapped = (min(225, 42 + high * 3 // 4), 10 + high // 8, 20 + high // 5)
        elif red > green * 1.08 and green > blue * 1.2 and blue < 58:
            mapped = (min(230, 35 + high * 3 // 4), 20 + high * 7 // 20, 10 + high // 7)
        elif high - low < 52 or (low > 145 and high - low < 86):
            mapped = (14 + light * 7 // 20, 17 + light * 3 // 8, 22 + light * 9 // 20)
        else:
            mapped = (red, green, blue)
        output.append((*mapped, alpha))
    black.putdata(output)
    return black


def pack(source_path: Path, white_path: Path, black_path: Path) -> int:
    source = Image.open(source_path).convert("RGB")
    if source.size != (1448, 1086):
        print(f"FAIL source size={source.size}, expected (1448, 1086)", file=sys.stderr)
        return 1
    mask = connected_foreground(source)
    poses = assign_components(mask, source.size)
    missing = [index for index, offsets in enumerate(poses) if not offsets]
    if missing:
        print(f"FAIL source poses missing for frames {missing}", file=sys.stderr)
        return 1

    # Frames 33-34 overlap into one connected attack pose in the generated source.
    # Keep every body/weapon pixel in both frames; frame 34 receives a deliberate
    # nearest-neighbor pose rotation in pack_pose so the motion remains distinct.
    shared_attack = sorted(set(poses[33]) | set(poses[34]))
    poses[33] = shared_attack
    poses[34] = shared_attack

    white = Image.new("RGBA", SIZE)
    for index, offsets in enumerate(poses):
        tile = pack_pose(extract_pose(source, offsets), index)
        white.alpha_composite(tile, (index % COLS * CELL, index // COLS * CELL))
    black = black_palette(white)
    white_path.parent.mkdir(parents=True, exist_ok=True)
    white.save(white_path, optimize=True, compress_level=9)
    black.save(black_path, optimize=True, compress_level=9)
    print(f"PACKED source_components={sum(bool(offsets) for offsets in poses)}")
    print(f"WROTE {white_path.relative_to(ROOT)} {white_path.stat().st_size} bytes")
    print(f"WROTE {black_path.relative_to(ROOT)} {black_path.stat().st_size} bytes")
    return validate(white_path, black_path)


def frame(image: Image.Image, index: int) -> Image.Image:
    x, y = index % COLS * CELL, index // COLS * CELL
    return image.crop((x, y, x + CELL, y + CELL))


def support_center(tile: Image.Image, bottom: int) -> float | None:
    alpha = tile.getchannel("A")
    xs = [x for y in range(max(0, bottom - 3), bottom + 1)
          for x in range(CELL) if alpha.getpixel((x, y))]
    if not xs:
        return None
    xs.sort()
    middle = len(xs) // 2
    return float(xs[middle]) if len(xs) % 2 else (xs[middle - 1] + xs[middle]) / 2


def load_final(path: Path, label: str, errors: list[str]) -> Image.Image | None:
    if not path.exists():
        errors.append(f"{label}: missing {path.relative_to(ROOT)}")
        return None
    image = Image.open(path)
    if image.mode != "RGBA":
        errors.append(f"{label}: mode={image.mode}, expected RGBA")
    if image.size != SIZE:
        errors.append(f"{label}: size={image.size}, expected {SIZE}")
        return None
    return image.convert("RGBA")


def validate_sheet(image: Image.Image, label: str, errors: list[str]) -> None:
    tiles = [frame(image, index) for index in range(48)]
    boxes = [tile.getchannel("A").getbbox() for tile in tiles]
    empty = [index for index, box in enumerate(boxes) if box is None]
    if empty:
        errors.append(f"{label}: empty frames {empty}")
        return

    occupancy = [sum(1 for value in tile.getchannel("A").get_flattened_data() if value)
                 for tile in tiles]
    fragments = [(index, count) for index, count in enumerate(occupancy) if count < 2000]
    if fragments:
        errors.append(f"{label}: weapon-only/fragment occupancy {fragments}")

    touching = [index for index, box in enumerate(boxes)
                if box[0] == 0 or box[1] == 0 or box[2] == CELL or box[3] == CELL]
    if touching:
        errors.append(f"{label}: cell-boundary contact in frames {touching}")

    tight = [index for index, box in enumerate(boxes)
             if min(box[0], box[1], CELL - box[2], CELL - box[3]) < GUTTER]
    if tight:
        errors.append(f"{label}: under-{GUTTER}px gutter in frames {tight}")

    baselines = [(index, boxes[index][3] - 1, expected)
                 for index, expected in EXPECTED_BOTTOM.items()
                 if abs((boxes[index][3] - 1) - expected) > 3]
    if baselines:
        errors.append(f"{label}: baseline mismatches {baselines}")

    feet = []
    for index in STANDING:
        center = support_center(tiles[index], boxes[index][3] - 1)
        if center is None or abs(center - FOOT[0]) > 3:
            feet.append((index, None if center is None else round(center, 1)))
    if feet:
        errors.append(f"{label}: unstable standing foot centers {feet}")

    identical = []
    for state, (start, count) in STATES.items():
        for index in range(start, start + count - 1):
            if tiles[index].tobytes() == tiles[index + 1].tobytes():
                identical.append(f"{state}:{index}-{index + 1}")
    if identical:
        errors.append(f"{label}: identical neighboring frames {identical}")


def validate(white_path: Path, black_path: Path) -> int:
    errors: list[str] = []
    white = load_final(white_path, "white", errors)
    black = load_final(black_path, "black", errors)
    if white is not None:
        validate_sheet(white, "white", errors)
    if black is not None:
        validate_sheet(black, "black", errors)
    if white is not None and black is not None:
        if white.getchannel("A").tobytes() != black.getchannel("A").tobytes():
            errors.append("white/black alpha masks differ")
        opaque = white.getchannel("A").point(lambda value: 255 if value else 0)
        white_rgb = Image.composite(white, Image.new("RGBA", SIZE), opaque).convert("RGB")
        black_rgb = Image.composite(black, Image.new("RGBA", SIZE), opaque).convert("RGB")
        if white_rgb.tobytes() == black_rgb.tobytes():
            errors.append("white/black opaque palettes are identical")

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        print(f"RESULT failed={len(errors)}", file=sys.stderr)
        return 1
    print("PASS 1024x768 RGBA, 8x6 cells, 48 nonempty contained frames")
    print("PASS gutters, explicit baselines, stable standing feet, distinct motion")
    print("PASS white/black exact alpha equality and distinct palettes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("pack", "validate"))
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--white", type=Path, default=WHITE)
    parser.add_argument("--black", type=Path, default=BLACK)
    args = parser.parse_args()
    white, black = args.white.resolve(), args.black.resolve()
    if args.command == "pack":
        return pack(args.source.resolve(), white, black)
    return validate(white, black)


if __name__ == "__main__":
    raise SystemExit(main())
