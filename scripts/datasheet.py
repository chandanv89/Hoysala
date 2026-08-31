"""Render the specimen and comparison sheet.

Every number on the sheet is measured from the two binaries at render time
rather than written in by hand, so it cannot drift away from what the fonts
actually do.

Usage:
    python scripts/datasheet.py "fonts/Hoysala[wght].ttf" NotoSerifKannada.ttf \
        -o documentation/specimen.png
"""

import argparse
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.transforms import Affine2D

from contrast import EM_HI, EM_LO, SAMPLE, rasterise, thicknesses
from outline import MplPen
from proof import Face

W, H = 1750, 3860

PAPER = "#F7F4EF"
INK = "#17130F"
ACCENT = "#A6462F"
MUTED = "#8C8279"
RULE = "#D9D2C8"

MARGIN = 110

WORDMARK = "ಹೊಯ್ಸಳ"
HERO = "ಕನ್ನಡ ನುಡಿ"
COMPARE = "ಸೊಬಗು ಬೆಳಕು"
CHARSET = ["ಕ ಖ ಗ ಘ ಙ ಚ ಛ ಜ ಝ ಞ", "ಟ ಠ ಡ ಢ ಣ ತ ಥ ದ ಧ ನ", "ಪ ಫ ಬ ಭ ಮ ಯ ರ ಲ ವ ಶ ಷ ಸ ಹ"]
WEIGHTS = [("Regular", 400), ("Medium", 500), ("SemiBold", 600),
           ("Bold", 700), ("ExtraBold", 800), ("Black", 900)]


def place(ax, face, text, x, y, size, colour=INK):
    """Draw shaped text with its em set to `size` canvas units. Returns width."""
    scale = size / face.upem
    transform = Affine2D().scale(scale).translate(x, y) + ax.transData
    cursor = 0
    for info, pos in face.shape(text):
        pen = MplPen(face.glyphset, offset=(cursor + pos.x_offset, pos.y_offset))
        face.glyphset[face.order[info.codepoint]].draw(pen)
        path = pen.path()
        if path is not None:
            ax.add_patch(PathPatch(path, fc=colour, ec="none", transform=transform))
        cursor += pos.x_advance
    return cursor * scale


def label(ax, text, x, y, size=15, colour=MUTED, weight="normal", ha="left"):
    ax.text(x, y, text, fontsize=size, color=colour, ha=ha, va="baseline",
            fontweight=weight, family="serif")


def rule(ax, y, x0=MARGIN, x1=W - MARGIN, colour=RULE, lw=1.0):
    ax.plot([x0, x1], [y, y], color=colour, lw=lw, solid_capstyle="butt")


def section(ax, title, y):
    label(ax, title.upper(), MARGIN, y, size=13, colour=ACCENT, weight="bold")
    rule(ax, y - 18)


def measure(path, weights):
    """Contrast of a font at each weight, measured not asserted."""
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    cmap = font.getBestCmap()
    units_per_px = (EM_HI - EM_LO) / 512
    out = {}
    for wght in weights:
        glyphset = font.getGlyphSet(location={"wght": wght} if "fvar" in font else None)
        gathered = []
        for char in SAMPLE:
            name = cmap.get(ord(char))
            if not name:
                continue
            mask = rasterise(glyphset, name)
            if mask is None or not mask.any():
                continue
            th = thicknesses(mask, units_per_px)
            if len(th) >= 10:
                gathered.append(th)
        allth = np.concatenate(gathered)
        thin, thick = np.percentile(allth, 10), np.percentile(allth, 90)
        out[wght] = (thin, thick, thick / thin)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hoysala")
    ap.add_argument("parent")
    ap.add_argument("-o", "--out", default="documentation/specimen.png")
    args = ap.parse_args()

    shown = [400, 700, 900]
    print("measuring...")
    mine = measure(args.hoysala, shown)
    theirs = measure(args.parent, shown)

    fig = Figure(figsize=(W / 100, H / 100), dpi=100)
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), W, H, fc=PAPER, ec="none"))

    y = H - 130

    # ---- masthead -------------------------------------------------------
    label(ax, "SPECIMEN & COMPARISON", MARGIN, y, size=13, colour=ACCENT, weight="bold")
    label(ax, "SIL OPEN FONT LICENSE 1.1", W - MARGIN, y, size=13, colour=MUTED, ha="right")
    y -= 26
    rule(ax, y, lw=2.2, colour=INK)

    y -= 300
    hero = Face(args.hoysala, 900, "")
    place(ax, hero, WORDMARK, MARGIN, y, 250)

    y -= 190  # Kannada descends deep; the wordmark carries a subjoined ya
    label(ax, "Hoysala", MARGIN, y, size=40, colour=INK)
    y -= 46
    label(ax, "A high-contrast display serif for Kannada.", MARGIN, y, size=22, colour=MUTED)
    y -= 34
    label(ax, "Derived from Noto Serif Kannada under the OFL. Six weights, 400–900,"
              " variable.", MARGIN, y, size=17, colour=MUTED)

    # ---- the difference -------------------------------------------------
    y -= 130
    section(ax, "What changed", y)
    y -= 130

    mine400 = Face(args.hoysala, 400, "")
    theirs400 = Face(args.parent, 400, "")

    for face, name in ((mine400, "Hoysala"), (theirs400, "Noto Serif Kannada")):
        place(ax, face, COMPARE, MARGIN, y, 150)
        label(ax, name, W - MARGIN, y + 26, size=17,
              colour=ACCENT if name == "Hoysala" else MUTED, ha="right")
        y -= 190

    y += 40
    label(ax, "Same skeleton, same weight, same proportions. The vertical strokes are"
              " thinner; the horizontals are not.", MARGIN, y, size=17, colour=MUTED)

    # ---- contrast -------------------------------------------------------
    y -= 92
    section(ax, "Stroke contrast", y)
    y -= 60

    label(ax, "Kannada is stressed the opposite way to Latin: its horizontals are the"
              " thick strokes. Contrast comes from thinning the verticals.",
          MARGIN, y, size=17, colour=MUTED)
    y -= 60

    bar_x = MARGIN
    bar_w = (W - 2 * MARGIN) / 3 - 60
    top = 210
    worst = max(v[2] for v in list(mine.values()) + list(theirs.values()))

    for i, wght in enumerate(shown):
        x0 = bar_x + i * (bar_w + 90)
        for j, (data, colour, who) in enumerate(
            ((theirs, "#CFC7BB", "Noto"), (mine, ACCENT, "Hoysala"))
        ):
            value = data[wght][2]
            height = top * value / worst
            bx = x0 + j * (bar_w / 2 + 8)
            ax.add_patch(Rectangle((bx, y - top), bar_w / 2, height, fc=colour, ec="none"))
            label(ax, "%.2f" % value, bx + bar_w / 4, y - top + height + 14,
                  size=17, colour=INK if j else MUTED, ha="center", weight="bold")
            label(ax, who, bx + bar_w / 4, y - top - 26, size=13, colour=MUTED, ha="center")
        label(ax, "wght %d" % wght, x0 + bar_w / 2 + 4, y - top - 54,
              size=15, colour=INK, ha="center")

    y -= top + 96

    hairlines = "   ".join(
        "%d: hairline %.0f→%.0f units" % (w, theirs[w][0], mine[w][0]) for w in shown
    )
    label(ax, hairlines, MARGIN, y, size=16, colour=MUTED)

    # ---- weights --------------------------------------------------------
    y -= 92
    section(ax, "Weights", y)
    y -= 108

    for name, wght in WEIGHTS:
        face = Face(args.hoysala, wght, "")
        place(ax, face, HERO, MARGIN, y, 118)
        label(ax, "%s %d" % (name, wght), W - MARGIN, y + 18, size=16,
              colour=MUTED, ha="right")
        y -= 150

    # ---- character set --------------------------------------------------
    y -= 6
    section(ax, "Character set", y)
    y -= 96

    charset = Face(args.hoysala, 400, "")
    for line in CHARSET:
        place(ax, charset, line, MARGIN, y, 96)
        y -= 130

    # ---- footer ---------------------------------------------------------
    y -= 20
    rule(ax, y, lw=2.2, colour=INK)
    y -= 34
    label(ax, "419 glyphs · Kannada · variable wght 400–900 · contrast measured over"
              " 15 consonants at render time", MARGIN, y, size=15, colour=MUTED)
    y -= 28
    label(ax, "Early release. Serifs and terminals are not yet drawn for display;"
              " 15 glyphs await hand correction.", MARGIN, y, size=15, colour=MUTED)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor=PAPER)
    print("wrote", out)


if __name__ == "__main__":
    main()
