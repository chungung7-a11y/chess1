#!/usr/bin/env python3
"""Turn the six coherent character cells into lightweight animated sheets."""

import math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# Use the original high-resolution sheet for the animated pieces. The web
# sheet is intentionally smaller and is only kept for the legacy CSS layer.
SOURCE = ROOT / "sprites.png"
OUT = ROOT / "assets/pieces"
CELL = 256
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
    max_w, max_h = 208, 224
    scale = min(max_w / base.width, max_h / base.height, 1.0)
    size = (max(1, round(base.width * scale)), max(1, round(base.height * scale)))
    return base.resize(size, Image.Resampling.LANCZOS)


def state_at(index: int) -> tuple[str, int, int]:
    for name, (start, count, _fps, _loop) in STATES.items():
        if start <= index < start + count:
            return name, index - start, count
    raise ValueError(f"frame outside state ranges: {index}")


def motion(piece: str, state: str, local: int, count: int) -> tuple[float, float, float, float]:
    t = local / max(count - 1, 1)
    wave = math.sin(t * math.pi * 2)
    arc = math.sin(t * math.pi)
    signed = t * 2 - 1

    # Each piece has its own silhouette rhythm, then its attack state adds the
    # recognizable action for that unit instead of reusing one generic wobble.
    if piece == "K":
        if state in {"attackA", "attackB", "finisher"}:
            return (-28 + 58 * t, -9 + 18 * t, -12 * arc, 1 + .08 * arc)
        return (2.5 * wave, 2 * wave, -3 * arc, 1 + .018 * arc)
    if piece == "Q":
        if state in {"attackA", "attackB"}:
            return (18 * wave, 9 * wave, -14 * arc, 1 + .08 * arc)
        if state == "finisher":
            return (-24 + 48 * t, 10 * wave, -16 * arc, 1 + .1 * arc)
        return (4 * wave, 3 * wave, -5 * arc, 1 + .025 * arc)
    if piece == "R":
        if state in {"attackA", "attackB"}:
            recoil = math.sin(t * math.pi)
            return (-3 * signed, -18 * recoil, -4 * recoil, 1 + .13 * recoil)
        return (1.5 * wave, 1.5 * wave, -2 * arc, 1 + .012 * arc)
    if piece == "B":
        if state in {"attackA", "attackB", "finisher"}:
            return (-16 + 32 * t, -10 + 20 * t, -10 * arc, 1 + .05 * arc)
        return (5 * wave, -2 * wave, -6 * arc, 1 + .022 * arc)
    if piece == "N":
        if state in {"anticipation", "attackA", "attackB", "finisher"}:
            jump = -28 * arc if state != "finisher" else -12 * arc
            return (-14 + 28 * t, 12 * signed, jump, 1 + .1 * arc)
        return (3 * wave, 3 * wave, -5 * arc, 1 + .03 * arc)
    # Pawn: short, quick forward thrust and a small recovery bounce.
    if state in {"attackA", "attackB", "finisher"}:
        return (12 * wave, -12 + 24 * t, -12 * arc, 1 + .06 * arc)
    return (3 * wave, 2 * wave, -7 * arc, 1 + .02 * arc)


def frame(base: Image.Image, piece: str, index: int) -> Image.Image:
    state, local, count = state_at(index)
    angle, dx, dy, scale = motion(piece, state, local, count)

    w = max(1, round(base.width * scale))
    h = max(1, round(base.height * scale))
    pose = base.resize((w, h), Image.Resampling.LANCZOS).rotate(
        angle, resample=Image.Resampling.BICUBIC, expand=True
    )
    canvas = Image.new("RGBA", (CELL, CELL))
    x = round((CELL - pose.width) / 2 + dx)
    y = round(240 - pose.height + dy * 2)
    canvas.alpha_composite(pose, (x, y))
    return canvas


def build() -> None:
    image = Image.open(SOURCE).convert("RGBA")
    for side, prefix in ((0, "b"), (1, "w")):
        for piece_index, piece in enumerate(PIECES):
            base = fitted(source_piece(image, side, piece_index))
            sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL))
            for index in range(48):
                sheet.alpha_composite(frame(base, piece, index), ((index % COLS) * CELL, (index // COLS) * CELL))
            sheet.save(OUT / f"{prefix}{piece}-animated.webp", format="WEBP", quality=92, method=6)
    print("PACKED 12 character sheets, 48 frames each")


if __name__ == "__main__":
    build()
