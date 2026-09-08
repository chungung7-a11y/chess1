#!/usr/bin/env python3
"""Turn the six coherent character cells into lightweight animated sheets."""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sprites-web.png"
OUT = ROOT / "assets/pieces"
CELL = 128
COLS, ROWS = 8, 6
PIECES = "KQRBNP"
STATES = {
    "idle": (0, 4, 8, True), "walk": (4, 6, 12, True),
    "hit": (10, 3, 12, False), "recover": (13, 3, 10, False),
    "cheer": (16, 4, 8, True), "anticipation": (20, 3, 10, False),
    "attackA": (23, 6, 12, False), "attackB": (29, 6, 12, False),
    "finisher": (35, 8, 12, False), "deathEntry": (43, 5, 10, False),
}


def source_piece(image: Image.Image, side: int, piece: int) -> Image.Image:
    width, height = image.size
    left = round(piece * width / 6)
    right = round((piece + 1) * width / 6)
    top = round(side * height / 2)
    bottom = round((side + 1) * height / 2)
    crop = image.crop((left, top, right, bottom))
    alpha = crop.getchannel("A")
    box = alpha.getbbox()
    if box is None:
        raise ValueError(f"empty source cell side={side} piece={piece}")
    return crop.crop(box)


def fitted(base: Image.Image) -> Image.Image:
    max_w, max_h = 104, 112
    scale = min(max_w / base.width, max_h / base.height, 1.0)
    size = (max(1, round(base.width * scale)), max(1, round(base.height * scale)))
    return base.resize(size, Image.Resampling.NEAREST)


def frame(base: Image.Image, index: int) -> Image.Image:
    # Procedural animation keeps every original character intact while giving
    # each state distinct motion without scattering the old 3-D fragments.
    if index < 4:
        phase = (index - 1.5) / 1.5
        angle, dx, dy, scale = phase * 1.3, 0, round(-phase * 2), 1 + abs(phase) * .012
    elif index < 10:
        phase = ((index - 4) % 2) * 2 - 1
        angle, dx, dy, scale = phase * 2.4, phase * 4, -2, 1.0
    elif index < 13:
        phase = index - 10
        angle, dx, dy, scale = -phase * 2, (phase - 1) * 3, -phase * 3, 1 + phase * .04
    elif index < 20:
        phase = index - 13
        angle, dx, dy, scale = phase * 1.5, 0, -round((6 - phase) * 1.5), 1.0
    elif index < 23:
        phase = index - 20
        angle, dx, dy, scale = phase * 3, -phase * 2, -phase * 2, 1 - phase * .02
    elif index < 29:
        phase = index - 23
        angle, dx, dy, scale = -12 + phase * 5, -8 + phase * 3, -phase * 3, 1 + phase * .05
    elif index < 35:
        phase = index - 29
        angle, dx, dy, scale = 18 - phase * 7, 8 - phase * 3, -phase * 5, 1.05 + phase * .06
    elif index < 43:
        phase = index - 35
        angle, dx, dy, scale = -18 + phase * 5, -6 + phase * 2, 4 - phase * 2, 1.12 - phase * .025
    else:
        phase = index - 43
        angle, dx, dy, scale = phase * 10, phase * 3, phase * 3, 1 - phase * .06

    w = max(1, round(base.width * scale))
    h = max(1, round(base.height * scale))
    pose = base.resize((w, h), Image.Resampling.NEAREST).rotate(
        angle, resample=Image.Resampling.NEAREST, expand=True
    )
    canvas = Image.new("RGBA", (CELL, CELL))
    x = round((CELL - pose.width) / 2 + dx)
    y = round(120 - pose.height + dy)
    canvas.alpha_composite(pose, (x, y))
    return canvas


def build() -> None:
    image = Image.open(SOURCE).convert("RGBA")
    for side, prefix in ((0, "b"), (1, "w")):
        for piece_index, piece in enumerate(PIECES):
            base = fitted(source_piece(image, side, piece_index))
            sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL))
            for index in range(48):
                sheet.alpha_composite(frame(base, index), ((index % COLS) * CELL, (index // COLS) * CELL))
            sheet.save(OUT / f"{prefix}{piece}-animated.png", optimize=True, compress_level=9)
    print("PACKED 12 character sheets, 48 frames each")


if __name__ == "__main__":
    build()
