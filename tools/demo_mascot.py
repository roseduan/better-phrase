#!/usr/bin/env python3
"""Mascot popup demo.

Shows a borderless, always-on-top window in the bottom-right corner of the
screen, displaying your PNG mascot. With 2+ images, frames cycle every 500ms.

Prefers Pillow (PIL) for proper PNG-with-alpha handling. Falls back to
tkinter's native PhotoImage if Pillow isn't installed (works but alpha may
render as black).

Usage:
    python3 demo_mascot.py path/to/idle.png
    python3 demo_mascot.py path/to/idle.png path/to/tip.png
    python3 demo_mascot.py path/to/idle.png --duration 5
"""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


MAX_DISPLAY_DIM = 280     # px; auto-downscale anything larger
SCREEN_PADDING = 60       # px from screen edge
FRAME_SWITCH_MS = 500     # ms between animation frames
FADE_TICK_MS = 50
FADE_STEP = 0.05

# Soft neutral background — chosen to look fine behind anime art and to NOT
# fight with macOS dark mode. Replace with "white" if your mascots are on a
# pure-white background already.
FALLBACK_BG = "#1e1e1e"


def _load_pil(path: str, max_dim: int) -> "Image.Image":
    img = Image.open(path).convert("RGBA")
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    return img


def _load_tk_native(path: str, root: tk.Tk, max_dim: int) -> tk.PhotoImage:
    photo = tk.PhotoImage(file=path, master=root)
    w, h = photo.width(), photo.height()
    factor = max(w // max_dim, h // max_dim, 1)
    if factor > 1:
        photo = photo.subsample(factor, factor)
    return photo


def _composite_on_bg(pil_img: "Image.Image", bg_color: str) -> "Image.Image":
    """Flatten an RGBA image onto a solid background so transparent pixels
    render as the chosen color instead of black."""
    from PIL import ImageColor

    bg = Image.new("RGB", pil_img.size, ImageColor.getrgb(bg_color))
    bg.paste(pil_img, mask=pil_img.split()[3])  # use alpha as mask
    return bg


def show(image_paths: list[str], duration_s: float = 3.0, bg_color: str = FALLBACK_BG) -> None:
    for p in image_paths:
        if not Path(p).is_file():
            raise SystemExit(f"Image not found: {p}")

    root = tk.Tk()
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.config(bg=bg_color)

    # Build the list of tk-displayable images.
    photos = []
    if HAS_PIL:
        for p in image_paths:
            pil = _load_pil(p, MAX_DISPLAY_DIM)
            # Composite onto solid bg so transparency doesn't render as black.
            flat = _composite_on_bg(pil, bg_color)
            photos.append(ImageTk.PhotoImage(flat, master=root))
    else:
        for p in image_paths:
            photos.append(_load_tk_native(p, root, MAX_DISPLAY_DIM))

    label = tk.Label(root, image=photos[0], bd=0, highlightthickness=0, bg=bg_color)
    label.pack()

    w, h = photos[0].width(), photos[0].height()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = sw - w - SCREEN_PADDING
    y = sh - h - SCREEN_PADDING * 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    # Frame cycling.
    if len(photos) > 1:
        cursor = {"i": 0}

        def cycle():
            cursor["i"] = (cursor["i"] + 1) % len(photos)
            label.config(image=photos[cursor["i"]])
            root.after(FRAME_SWITCH_MS, cycle)

        root.after(FRAME_SWITCH_MS, cycle)

    # Fade-out near the end. Use window-level alpha (works on macOS).
    fade_start_ms = int(duration_s * 1000 * 0.7)

    def fade(alpha: float = 1.0) -> None:
        if alpha <= 0:
            root.destroy()
            return
        try:
            root.wm_attributes("-alpha", alpha)
        except tk.TclError:
            pass
        root.after(FADE_TICK_MS, lambda: fade(alpha - FADE_STEP))

    root.after(fade_start_ms, fade)
    root.after(int(duration_s * 1000) + 1500, root.destroy)

    root.mainloop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="demo_mascot",
        description="Show a mascot popup as an always-on-top window.",
    )
    parser.add_argument("images", nargs="+", help="One or more PNG paths.")
    parser.add_argument(
        "--duration",
        type=float,
        default=3.0,
        help="Seconds to keep the popup visible (default: 3.0).",
    )
    parser.add_argument(
        "--bg",
        default=FALLBACK_BG,
        help=f"Background color hex / name (default: {FALLBACK_BG}). "
             "Try 'white' if your art is already on white.",
    )
    args = parser.parse_args(argv)

    if not HAS_PIL:
        print("⚠️  Pillow not installed — using tkinter native PNG loader.", file=sys.stderr)
        print("    Image may not render alpha correctly.", file=sys.stderr)
        print("    Fix:  python3 -m pip install pillow", file=sys.stderr)
        print(file=sys.stderr)

    show(args.images, args.duration, args.bg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
