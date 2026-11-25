#!/usr/bin/env python3
"""Regenerate the two boot splash screens for the AI-translated fork.

SCELOGO.png    (416x51) keeps the original pumpkin and "25 YEARS" icons from the
               upstream image and replaces the text in between.
BEXIDELOGO.png (192x71) thanks the original translators and points players to the
               upstream project.

Usage (from the repo root):
    python scripts/ai/make_splash.py            # write textures/GUI/TITLE/*.png
    python scripts/ai/make_splash.py --preview out_dir   # also write 3x previews

Uses Arial Rounded MT Bold (closest installed match to the upstream font) and
Segoe UI Symbol for the heart. Colours are sampled from the upstream images.
"""
import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TITLE = ROOT / "textures" / "GUI" / "TITLE"
FONT = r"C:\Windows\Fonts\ARLRDBD.TTF"
SYMBOL = r"C:\Windows\Fonts\seguisym.ttf"

BLACK = (0, 0, 0, 255)
GREY = (198, 201, 197, 255)
DIM = (151, 151, 151, 255)
GREEN = (97, 139, 58, 255)
PINK = (232, 120, 150, 255)
HEART = "\u2665"


def upstream_image(name):
    """The upstream version of a texture (from git), so re-running is idempotent."""
    data = subprocess.run(
        ["git", "show", f"upstream/dev:textures/GUI/TITLE/{name}"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    from io import BytesIO
    return Image.open(BytesIO(data)).convert("RGBA")


def segments(text, colour):
    """Split a line into (text, colour, font-kind) runs so hearts use the symbol font."""
    out, buf = [], ""
    for ch in text:
        if ch == HEART:
            if buf:
                out.append((buf, colour, "text"))
                buf = ""
            out.append((ch, PINK, "symbol"))
        else:
            buf += ch
    if buf:
        out.append((buf, colour, "text"))
    return out


def line_width(draw, runs, fonts):
    return sum(draw.textlength(t, font=fonts[k]) for t, _, k in runs)


def draw_lines(img, box, lines, size, line_gap=0, gaps_after=()):
    """Draw centred lines inside box=(x0, y0, x1, y1); shrink the font until it fits."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    while size > 6:
        fonts = {"text": ImageFont.truetype(FONT, size), "symbol": ImageFont.truetype(SYMBOL, size)}
        asc, desc = fonts["text"].getmetrics()
        lh = asc + desc + line_gap
        extra = sum(lh // 2 for i in gaps_after)
        widths = [line_width(d, segments(t, c), fonts) for t, c in lines]
        total_h = lh * len(lines) - line_gap + extra
        if max(widths) <= (x1 - x0) and total_h <= (y1 - y0):
            break
        size -= 1
    y = y0 + ((y1 - y0) - total_h) // 2
    for i, ((text, colour), w) in enumerate(zip(lines, widths)):
        x = x0 + ((x1 - x0) - w) / 2
        for t, c, k in segments(text, colour):
            # Hearts use the symbol font at the same size and baseline
            dy = 0
            d.text((x, y + dy), t, font=fonts[k], fill=c)
            x += d.textlength(t, font=fonts[k])
        y += lh + (lh // 2 if i in gaps_after else 0)
    return size


def ramp(colour, steps):
    return [tuple(round(c * i / steps) for c in colour[:3]) for i in range(1, steps + 1)]


# Fixed 16-colour palette: black + grey/green/pink ramps, so small accents (the heart)
# survive quantization. The build's pngquant pass keeps an image that already has 16 colours.
PALETTE = [(0, 0, 0)] + ramp(GREY, 9) + ramp(GREEN, 3) + ramp(PINK, 3)


def to_texture(img):
    """Opaque, 16-colour paletted image like the upstream files."""
    flat = Image.new("RGBA", img.size, BLACK)
    flat.alpha_composite(img)
    pal = Image.new("P", (1, 1))
    pal.putpalette([v for c in PALETTE for v in c] + [0] * (768 - 3 * len(PALETTE)))
    return flat.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)


def make_scelogo():
    src = upstream_image("SCELOGO.png")
    img = Image.new("RGBA", src.size, BLACK)
    # Keep the pumpkin (x 0-55) and the "25 YEARS" badge (x 361-411) from upstream
    img.paste(src.crop((0, 0, 60, src.height)), (0, 0))
    img.paste(src.crop((357, 0, src.width, src.height)), (357, 0))
    size = draw_lines(img, (62, 1, 355, 50), [
        ("Unofficial AI-translated fork of the", GREY),
        ("fan translation by PumpkinhasaPatch " + HEART, GREY),
        ("Not endorsed by them, Sony or BeXide.", DIM),
    ], size=15)
    return img, size


def make_bexidelogo():
    img = Image.new("RGBA", (192, 71), BLACK)
    size = draw_lines(img, (2, 1, 190, 70), [
        ("Thank you, PumpkinhasaPatch " + HEART, GREY),
        ("Support the original at", GREY),
        ("github.com/pumpkinhasapatch/", GREEN),
        ("dokodemo-psp-english", GREEN),
        ("Don't share game data.", DIM),
    ], size=14, line_gap=-1, gaps_after=(3,))
    return img, size


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview", type=Path, help="also write 3x previews to this folder")
    args = p.parse_args()
    for name, maker in (("SCELOGO.png", make_scelogo), ("BEXIDELOGO.png", make_bexidelogo)):
        img, size = maker()
        tex = to_texture(img)
        tex.save(TITLE / name)
        print(f"{name}: {img.size[0]}x{img.size[1]}, font {size}px")
        if args.preview:
            args.preview.mkdir(parents=True, exist_ok=True)
            tex.convert("RGB").resize((img.width * 3, img.height * 3), Image.NEAREST).save(args.preview / name)


if __name__ == "__main__":
    main()
