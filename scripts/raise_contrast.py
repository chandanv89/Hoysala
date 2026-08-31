"""Raise stroke contrast by thinning verticals, leaving horizontal strokes alone.

Kannada is stressed the opposite way to Latin. Measured on the parent, its
vertical strokes run 53-66 units and its horizontals 86-91: the horizontals are
the thick strokes, as the broad-nib origin shared with Devanagari's headline
would suggest. So contrast here comes from thinning the verticals. Doing the
Latin thing and thinning horizontals lowers contrast instead -- measurably, from
2.04 to 1.70.

Each outline point is moved horizontally by an amount proportional to the
horizontal component of its outward normal. Where a stroke runs vertically the
normal points left or right, so the edge moves inward and the stroke thins;
where it runs horizontally the term goes to zero and nothing moves. This is the
same operation as the Offset Curve filter in Glyphs, and the standard way to
add contrast to an existing skeleton.

It is a starting point, not a finished face. Inward offsets can self-intersect
at tight junctions, serifs and terminals do not sharpen by themselves, and the
subjoined consonants over-thin because they are already at about 60% scale.
Every glyph still wants a hand pass afterwards.

Composites are skipped: they inherit the correction from their parts.

The amounts hold the hairline roughly constant while the thick strokes keep
their weight, which is what produces contrast. Re-running double-applies, so
restore the source first:

    git checkout sources/Hoysala.glyphs
    python scripts/raise_contrast.py
"""

import argparse
from math import hypot
from pathlib import Path

import glyphsLib
from glyphsLib.types import Point

SOURCE = Path(__file__).resolve().parent.parent / "sources" / "Hoysala.glyphs"

# Half the material to remove from each master, in units: the hairline loses
# twice this. Measured hairlines are 46, 61 and 66; targets are 23, 26 and 28.
AMOUNTS = {"Regular": 11.5, "Bold": 17.5, "Black": 19.0}

# Glyphs the offset breaks: it opens corners in some masters and not others,
# which changes their point counts and makes them uninterpolatable. Left alone
# so the family builds; they are the hand-work list, and they are mostly
# subjoined forms, which over-thin because they already sit at about 60% scale.
HAND_FIX = [
    "bha_kannada.below",
    "cha_kannada.below",
    "ddha_kannada.below",
    "dha_kannada.below",
    "gha_kannada.below",
    "j_nya_kannada.below",
    "ja_kannada.below",
    "ja_nukta_kannada.below",
    "jha_kannada.below",
    "nya_kannada.base",
    "nyaa_kannada",
    "nye_kannada",
    "pha_kannada.below",
    "pha_nukta_kannada.below",
    "tha_kannada.below",
]


def thin_path(path, amount):
    points = [(n.position.x, n.position.y) for n in path.nodes]
    count = len(points)
    if count < 3:
        return

    moved = []
    for i, (x, y) in enumerate(points):
        prev_x, prev_y = points[(i - 1) % count]
        next_x, next_y = points[(i + 1) % count]
        tangent_x, tangent_y = next_x - prev_x, next_y - prev_y
        length = hypot(tangent_x, tangent_y)
        if length == 0:
            moved.append((x, y))
            continue
        # Outward normal of the tangent. With PostScript winding this points
        # away from the ink for outer contours and holes alike.
        normal_x = tangent_y / length
        moved.append((x - amount * normal_x, y))

    for node, (x, y) in zip(path.nodes, moved):
        node.position = Point(round(x), round(y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="multiply all amounts, for dialling the effect in",
    )
    ap.add_argument(
        "--skip",
        default=",".join(HAND_FIX),
        help="comma-separated glyphs to leave alone, for ones the offset breaks",
    )
    args = ap.parse_args()
    skip = {name for name in args.skip.split(",") if name}

    font = glyphsLib.load(open(SOURCE, encoding="utf-8"))

    for master in font.masters:
        if master.name not in AMOUNTS:
            raise SystemExit("no amount defined for master %r" % master.name)

    touched = skipped = 0
    for glyph in font.glyphs:
        if glyph.name in skip:
            continue
        for layer in glyph.layers:
            master = font.masters[layer.layerId]
            amount = AMOUNTS.get(master.name)
            if amount is None or not layer.paths:
                skipped += 1
                continue
            for path in layer.paths:
                thin_path(path, amount * args.scale)
            touched += 1

    with open(SOURCE, "w", encoding="utf-8", newline="\n") as fp:
        glyphsLib.dump(font, fp)

    print("thinned %d layers, skipped %d without outlines" % (touched, skipped))
    for name, amount in AMOUNTS.items():
        print("  %-8s hairline -%.0f units" % (name, 2 * amount * args.scale))


if __name__ == "__main__":
    main()
