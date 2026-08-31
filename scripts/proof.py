"""Render specimen sheets, and compare fonts line-for-line.

Pass one font for a specimen, or several to stack them under each other so the
same line can be compared directly -- the usual reason being to see Hoysala
against the parent it was derived from.

Text is shaped with HarfBuzz, so conjuncts, matras and reordering are real
rather than a row of isolated glyphs.

Usage:
    python scripts/proof.py "fonts/Hoysala[wght].ttf" -o proof/specimen.png
    python scripts/proof.py "fonts/Hoysala[wght].ttf" NotoSerifKannada.ttf \
        --labels Hoysala "Noto Serif Kannada" -o proof/compare.png
"""

import argparse
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch

from outline import MplPen

LINES = [
    "ಕಖಗಘಙ ಚಛಜಝಞ ಟಠಡಢಣ",
    "ತಥದಧನ ಪಫಬಭಮ ಯರಲವಶಷಸಹ",
    "ಕನ್ನಡ ನುಡಿ ಸೊಬಗು",
    "ಬೆಣ್ಣೆ ಸಕ್ಕರೆ ಬೆಳಕು",
    "Hamburgefonstiv 123",
]

PX_PER_EM = 90
LINE_GAP = 1.35  # ems between the same line in successive fonts
GROUP_GAP = 0.75  # extra ems between one text line and the next


class Face:
    def __init__(self, path, wght, label):
        self.label = label
        self.tt = TTFont(path)
        self.order = self.tt.getGlyphOrder()
        variable = "fvar" in self.tt
        self.glyphset = self.tt.getGlyphSet(
            location={"wght": wght} if variable else None
        )
        blob = hb.Blob.from_file_path(str(path))
        hbface = hb.Face(blob)
        self.upem = hbface.upem
        self.hbfont = hb.Font(hbface)
        self.hbfont.scale = (self.upem, self.upem)
        if variable:
            self.hbfont.set_variations({"wght": wght})

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf)
        return list(zip(buf.glyph_infos, buf.glyph_positions))

    def draw(self, ax, text, baseline):
        """Draw one line, returning its advance width in font units."""
        run = self.shape(text)
        if all(info.codepoint == 0 for info, _ in run):
            return None  # nothing in this font supports the line
        x = 0
        for info, pos in run:
            pen = MplPen(
                self.glyphset,
                offset=(x + pos.x_offset, baseline + pos.y_offset),
            )
            self.glyphset[self.order[info.codepoint]].draw(pen)
            path = pen.path()
            if path is not None:
                ax.add_patch(PathPatch(path, fc="black", ec="none"))
            x += pos.x_advance
        return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="+")
    ap.add_argument("--labels", nargs="*", default=None)
    ap.add_argument("--wght", type=float, default=400)
    ap.add_argument("--text", nargs="*", default=LINES)
    ap.add_argument("-o", "--out", default="proof/specimen.png")
    args = ap.parse_args()

    labels = args.labels or [Path(f).stem for f in args.fonts]
    faces = [Face(f, args.wght, l) for f, l in zip(args.fonts, labels)]
    show_labels = len(faces) > 1
    em = faces[0].upem

    fig = Figure()
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    y = 0.0
    widest = 1.0
    for text in args.text:
        drawn = False
        for face in faces:
            width = face.draw(ax, text, y)
            if width is None:
                continue
            drawn = True
            widest = max(widest, width)
            if show_labels:
                ax.text(
                    -0.16 * em,
                    y + 0.15 * em,
                    face.label,
                    fontsize=13,
                    color="#3070c0",
                    ha="right",
                    va="baseline",
                )
            y -= LINE_GAP * em
        if not drawn:
            print("skipped (no glyphs in any font): %s" % text)
            continue
        y -= GROUP_GAP * em

    left = -2.2 * em if show_labels else -0.1 * em
    right = widest + 0.1 * em
    top = 1.0 * em
    bottom = y

    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.set_aspect("equal")
    fig.set_size_inches(
        (right - left) / em * PX_PER_EM / 100,
        (top - bottom) / em * PX_PER_EM / 100,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
