"""Cut the shipped weight range down to 400-900 for display use.

High-contrast serifs work by holding the hairline roughly constant while the
thick stroke grows with weight. At wght 100 the parent's thick stroke is only
25 units, so there is no material to remove and no contrast to be had; keeping
it would ship a family whose extremes read as different typefaces. Dropping it
costs nothing, because masters already exist at 400, 700 and 900.

The inherited master names are also off by a step -- the master called
"SemiBold" actually sits at wght 700 -- which invites drawing the wrong weight,
so they are renamed to match the instances they define.

This is a one-time structural change; the result is committed. It is kept for
the record because a glyphsLib round-trip rewrites the whole file, so the
commit diff on its own is not reviewable.

Usage:
    python scripts/trim_weight_range.py
"""

from pathlib import Path

import glyphsLib

SOURCE = Path(__file__).resolve().parent.parent / "sources" / "Hoysala.glyphs"

MIN_WEIGHT = 94  # internal value of the Regular master, i.e. wght 400
MASTER_NAMES = {94: "Regular", 152: "Bold", 194: "Black"}


def main():
    font = glyphsLib.load(open(SOURCE, encoding="utf-8"))

    doomed = [m for m in font.masters if m.axes[0] < MIN_WEIGHT]
    if not doomed:
        raise SystemExit("nothing to trim; already done?")

    for master in doomed:
        print("dropping master %s (weight %s)" % (master.name, master.axes[0]))
        for glyph in font.glyphs:
            if master.id in [layer.layerId for layer in glyph.layers]:
                del glyph.layers[master.id]
        font.kerning.pop(master.id, None)
        font.masters.remove(master)

    for master in font.masters:
        new = MASTER_NAMES[master.axes[0]]
        if new != master.name:
            print("renaming master %s -> %s (weight %s)" % (master.name, new, master.axes[0]))
            master.name = new

    kept = [i for i in font.instances if i.axes[0] >= MIN_WEIGHT]
    for instance in font.instances:
        if instance not in kept:
            print("dropping instance %s (weight %s)" % (instance.name, instance.axes[0]))
    font.instances = kept

    with open(SOURCE, "w", encoding="utf-8", newline="\n") as fp:
        glyphsLib.dump(font, fp)

    print(
        "\nmasters   : %s" % [(m.name, m.axes[0]) for m in font.masters]
    )
    print("instances : %s" % [i.name for i in font.instances])
    print("glyphs    : %d" % len(font.glyphs))


if __name__ == "__main__":
    main()
