"""Measure stroke contrast, so raising it can be tracked as a number.

Hoysala's whole reason to exist is higher contrast than its parent. "Looks
sharper" is not reviewable, so this reports the actual thick/thin ratio.

Method: rasterise each sample glyph on a fixed grid, take the Euclidean
distance transform of the ink, and keep its ridge (the local maxima, which
approximate the stroke skeleton). Twice the distance at a ridge point is the
local stroke thickness. Contrast is then a high percentile of that thickness
distribution over a low one -- direction-agnostic, so it works on Kannada
curves as well as Latin stems.

Usage:
    python scripts/contrast.py fonts/Hoysala[wght].ttf --wght 400
"""

import argparse

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.ndimage import distance_transform_edt, maximum_filter

# A spread of Kannada consonants: straight stems, bowls, loops and the
# head-stroke, so the sample is not biased toward one construction.
SAMPLE = "ಕಖಗಚಟತನಪಮಯರಲವಸಹ"

GRID = 512  # raster size in pixels for the em box below
EM_LO, EM_HI = -250, 1050  # font units covered by the raster, fixed across glyphs


class MplPen(BasePen):
    """Collect an outline as a matplotlib Path. BasePen turns quadratics into
    cubics for us, so only the cubic case needs handling."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.verts = []
        self.codes = []

    def _moveTo(self, pt):
        self.verts.append(pt)
        self.codes.append(Path.MOVETO)

    def _lineTo(self, pt):
        self.verts.append(pt)
        self.codes.append(Path.LINETO)

    def _curveToOne(self, a, b, c):
        self.verts.extend([a, b, c])
        self.codes.extend([Path.CURVE4] * 3)

    def _closePath(self):
        self.verts.append((0, 0))
        self.codes.append(Path.CLOSEPOLY)


def rasterise(glyphset, name):
    pen = MplPen(glyphset)
    glyphset[name].draw(pen)
    if not pen.verts:
        return None

    fig = Figure(figsize=(GRID / 100, GRID / 100), dpi=100)
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(EM_LO, EM_HI)
    ax.set_ylim(EM_LO, EM_HI)
    ax.add_patch(PathPatch(Path(pen.verts, pen.codes), fc="black", ec="none"))
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[..., 0] < 128


def thicknesses(mask, units_per_px):
    """Local stroke thickness in font units, sampled along the stroke skeleton."""
    dt = distance_transform_edt(mask)
    ridge = (dt >= maximum_filter(dt, size=3)) & (dt > 1.5)
    return 2.0 * dt[ridge] * units_per_px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("--wght", type=float, default=400)
    ap.add_argument("--text", default=SAMPLE)
    args = ap.parse_args()

    font = TTFont(args.font)
    location = {"wght": args.wght} if "fvar" in font else None
    glyphset = font.getGlyphSet(location=location)
    cmap = font.getBestCmap()
    units_per_px = (EM_HI - EM_LO) / GRID

    print("%s  wght=%g" % (args.font, args.wght))
    print("%-8s %8s %8s %8s" % ("glyph", "thin", "thick", "contrast"))

    everything = []
    for char in args.text:
        name = cmap.get(ord(char))
        if name is None:
            continue
        mask = rasterise(glyphset, name)
        if mask is None or not mask.any():
            continue
        th = thicknesses(mask, units_per_px)
        if len(th) < 10:
            continue
        everything.append(th)
        thin, thick = np.percentile(th, 10), np.percentile(th, 90)
        print("%-8s %8.0f %8.0f %8.2f" % (char, thin, thick, thick / thin))

    if not everything:
        raise SystemExit("no measurable glyphs")

    allth = np.concatenate(everything)
    thin, thick = np.percentile(allth, 10), np.percentile(allth, 90)
    print("-" * 36)
    print("%-8s %8.0f %8.0f %8.2f" % ("OVERALL", thin, thick, thick / thin))


if __name__ == "__main__":
    main()
