"""Say which glyphs to thin first, and how far each still is from target.

Two things make the drawing tractable. Most glyphs are composites, so they
inherit their parts' correction for free and should not be drawn at all; and
among the rest, the ones other glyphs are built from pay back many times over.
So the list is ordered by how many glyphs depend on each one, then by how much
hairline is left to remove.

Re-run it as drawing progresses: "remove" falling to zero is the finish line.

Read the contrast column before trusting a row. A glyph already near 1.0 is a
uniform mark rather than a modulated letter, and taking it down to the letter
hairline is a judgement call, not an obvious win -- small marks disappear.
The ordering also optimises effort, not design sequence: the style itself gets
settled on a handful of consonants first, whatever their reuse count.

Usage:
    python scripts/worklist.py "fonts/Hoysala[wght].ttf"
    python scripts/worklist.py "fonts/Hoysala[wght].ttf" --wght 900 --target 28
"""

import argparse
from collections import Counter

import numpy as np
from fontTools.ttLib import TTFont

from contrast import EM_HI, EM_LO, rasterise, thicknesses

GRID = 256  # coarser than contrast.py: this runs over the whole font
SKIP = {".notdef", "space", "NULL", "CR"}


def dependents(font):
    """How many glyphs use each glyph as a component."""
    glyf = font["glyf"]
    counts = Counter()
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph.isComposite():
            for component in glyph.components:
                counts[component.glyphName] += 1
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("--wght", type=float, default=400)
    ap.add_argument("--target", type=float, default=23, help="hairline in units")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    font = TTFont(args.font)
    glyf = font["glyf"]
    location = {"wght": args.wght} if "fvar" in font else None
    glyphset = font.getGlyphSet(location=location)
    units_per_px = (EM_HI - EM_LO) / GRID
    used_by = dependents(font)

    reverse_cmap = {v: k for k, v in font.getBestCmap().items()}

    rows = []
    composites = 0
    for name in font.getGlyphOrder():
        if name in SKIP:
            continue
        glyph = glyf[name]
        if glyph.isComposite():
            composites += 1
            continue
        if glyph.numberOfContours <= 0:
            continue
        mask = rasterise(glyphset, name, grid=GRID)
        if mask is None or not mask.any():
            continue
        th = thicknesses(mask, units_per_px)
        if len(th) < 10:
            continue
        hairline = float(np.percentile(th, 10))
        thick = float(np.percentile(th, 90))
        rows.append(
            (used_by.get(name, 0), hairline - args.target, name, hairline, thick / hairline)
        )

    rows.sort(key=lambda r: (-r[0], -r[1]))

    print(
        "%s  wght=%g  target hairline %g units"
        % (args.font, args.wght, args.target)
    )
    print(
        "\n%d glyphs to draw, %d composites inherit the fix for free\n"
        % (len(rows), composites)
    )
    print(
        "%-26s %6s %8s %9s %7s %9s"
        % ("glyph", "char", "used by", "hairline", "remove", "contrast")
    )
    for used, excess, name, hairline, ratio in rows[: args.top]:
        codepoint = reverse_cmap.get(name)
        char = chr(codepoint) if codepoint else ""
        print(
            "%-26s %6s %8d %9.0f %7.0f %9.2f"
            % (name, char, used, hairline, max(0.0, excess), ratio)
        )

    if len(rows) > args.top:
        print("... and %d more" % (len(rows) - args.top))

    done = sum(1 for r in rows if r[1] <= 0)
    print(
        "\n%d of %d already at or under target (%.0f%%)"
        % (done, len(rows), 100.0 * done / len(rows))
    )


if __name__ == "__main__":
    main()
