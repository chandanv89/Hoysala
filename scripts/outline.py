"""Shared glyph-outline plumbing for the proofing and measurement scripts."""

from fontTools.pens.basePen import BasePen
from matplotlib.path import Path


class MplPen(BasePen):
    """Collect an outline as a matplotlib Path. BasePen turns quadratics into
    cubics for us, so only the cubic case needs handling."""

    def __init__(self, glyphset, offset=(0, 0)):
        super().__init__(glyphset)
        self.dx, self.dy = offset
        self.verts = []
        self.codes = []

    def _shift(self, pt):
        return (pt[0] + self.dx, pt[1] + self.dy)

    def _moveTo(self, pt):
        self.verts.append(self._shift(pt))
        self.codes.append(Path.MOVETO)

    def _lineTo(self, pt):
        self.verts.append(self._shift(pt))
        self.codes.append(Path.LINETO)

    def _curveToOne(self, a, b, c):
        self.verts.extend([self._shift(a), self._shift(b), self._shift(c)])
        self.codes.extend([Path.CURVE4] * 3)

    def _closePath(self):
        self.verts.append((0, 0))
        self.codes.append(Path.CLOSEPOLY)

    def path(self):
        return Path(self.verts, self.codes) if self.verts else None
