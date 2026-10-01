"""Render the browser logos in tools/logos/ to coloured braille and write src/logos.js.

Each logo is an SVG rasterised with rsvg-convert, dithered to braille dots on luminance,
then coloured per cell from the pixels under it, quantised to a few colours per logo.
A .braille.txt beside an SVG supplies hand-drawn dots and the SVG is used only for colour.

    python3 tools/logos/logos.py
"""
import subprocess
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "src" / "logos.js"
COLS, ROWS, GAMMA, COLORS = 25, 13, 0.6, 10
DOTS = [(0, 0, 0x01), (1, 0, 0x02), (2, 0, 0x04), (3, 0, 0x40), (0, 1, 0x08), (1, 1, 0x10), (2, 1, 0x20), (3, 1, 0x80)]
BLANK = "⠀"


def raster(svg, cols, rows):
    png = subprocess.run(["rsvg-convert", "-w", "400", "-h", "400", "-b", "none", str(svg)], capture_output=True, check=True).stdout
    im = Image.open(BytesIO(png)).convert("RGBA").resize((cols * 2, rows * 4), Image.Resampling.LANCZOS)
    a = np.asarray(im).astype(float) / 255
    return a[..., :3], a[..., 3]


def dither(rgb, alpha):
    lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) ** GAMMA * alpha
    h, w = lum.shape
    rows_n, cols_n = h // 4, w // 2
    v = lum.copy()
    on = np.zeros_like(v, dtype=bool)
    for y in range(h):
        for x in range(w):
            old = v[y, x]
            new = old >= 0.5
            on[y, x] = new
            e = old - new
            if x + 1 < w:
                v[y, x + 1] += e * 7 / 16
            if y + 1 < h:
                if x:
                    v[y + 1, x - 1] += e * 3 / 16
                v[y + 1, x] += e * 5 / 16
                if x + 1 < w:
                    v[y + 1, x + 1] += e * 1 / 16
    rows = []
    for r in range(rows_n):
        line = ""
        for c in range(cols_n):
            code = 0
            for dy, dx, bit in DOTS:
                if on[r * 4 + dy, c * 2 + dx]:
                    code |= bit
            line += chr(0x2800 + code)
        rows.append(line)
    return rows


def colour(rows, rgb, alpha):
    rows_n, cols_n = len(rows), len(rows[0])
    cells = np.zeros((rows_n, cols_n, 3))
    mask = np.zeros((rows_n, cols_n), dtype=bool)
    for r in range(rows_n):
        for c in range(cols_n):
            ca = alpha[r * 4:r * 4 + 4, c * 2:c * 2 + 2].reshape(-1)
            if (ca > 0.5).any() and rows[r][c] != BLANK:
                cells[r, c] = rgb[r * 4:r * 4 + 4, c * 2:c * 2 + 2].reshape(-1, 3)[ca > 0.5].mean(0)
                mask[r, c] = True
    q = np.asarray(Image.fromarray((cells * 255).astype(np.uint8)).quantize(COLORS, method=Image.Quantize.MEDIANCUT).convert("RGB"))
    out = []
    for r, line in enumerate(rows):
        h, cur = "", None
        for c, ch in enumerate(line):
            col = "#%02x%02x%02x" % tuple(q[r, c]) if mask[r, c] else None
            if col != cur:
                if cur:
                    h += "</span>"
                if col:
                    h += f'<span style="color:{col}">'
                cur = col
            h += ch
        if cur:
            h += "</span>"
        out.append(h)
    return "\n".join(out)


def main():
    logos = {}
    for svg in sorted(HERE.glob("*.svg")):
        dots = svg.with_suffix(".braille.txt")
        rows = dots.read_text().strip("\n").split("\n") if dots.exists() else None
        rgb, alpha = raster(svg, len(rows[0]), len(rows)) if rows else raster(svg, COLS, ROWS)
        rows = rows or dither(rgb, alpha)
        logos[svg.stem.capitalize()] = colour(rows, rgb, alpha)
    OUT.write_text("var logos = {\n" + "".join(f"  {k}: `{v}`,\n" for k, v in logos.items()) + "};\n")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(logos)} logos)")


if __name__ == "__main__":
    main()
