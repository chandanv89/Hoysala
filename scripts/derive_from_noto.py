"""Derive sources/Hoysala.glyphs from an unmodified NotoSerifKannada.glyphs.

Hoysala starts as an OFL derivative of Noto Serif Kannada. This script performs
the one-time rebranding so the provenance is documented and reproducible: it
copies the parent verbatim and rewrites only the metadata that must not carry
over (family name, designer/manufacturer credits, version, vendor ID and the
Noto trademark). Outlines, kerning, features and masters are untouched.

Usage:
    python scripts/derive_from_noto.py <path-to-NotoSerifKannada.glyphs>
"""

import io
import sys
from pathlib import Path

REPO = "https://github.com/chandanv89/Hoysala"

# (old, new) -- new == None means delete the block. Each must match exactly once.
REPLACEMENTS = [
    (
        'copyright = "Copyright 2022 The Noto Project Authors '
        '(https://github.com/notofonts/kannada)";',
        'copyright = "Copyright 2026 The Hoysala Project Authors (%s), '
        "based on Noto Serif Kannada, Copyright 2022 The Noto Project Authors "
        '(https://github.com/notofonts/kannada)";' % REPO,
    ),
    (
        'value = "Designed by Monotype design team.";',
        'value = "A high-contrast display serif for Kannada and Latin.";',
    ),
    ("value = GOOG;", "value = HYSL;"),
    # The Noto trademark belongs to Google and cannot be inherited.
    ("{\nname = trademark;\nvalue = \"Noto is a trademark of Google Inc.\";\n},\n", ""),
    ('value = "Version 2.005";', 'value = "Version 1.000";'),
    (
        'designer = "Universal Thirst, Indian Type Foundry and the Monotype Design Team";',
        'designer = "Chandan Veerabhadrappa";',
    ),
    ('designerURL = "http://www.monotype.com/studio";', 'designerURL = "%s";' % REPO),
    ('familyName = "Noto Serif Kannada";', "familyName = Hoysala;"),
    ('manufacturer = "Monotype Imaging Inc.";', 'manufacturer = "Chandan Veerabhadrappa";'),
    ('manufacturerURL = "http://www.google.com/get/noto/";', 'manufacturerURL = "%s";' % REPO),
    ("versionMajor = 2;", "versionMajor = 1;"),
    ("versionMinor = 5;", "versionMinor = 0;"),
]


def main(src):
    text = io.open(src, encoding="utf-8").read()
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            raise SystemExit("expected 1 occurrence, found %d: %r" % (count, old[:60]))
        text = text.replace(old, new)

    for token in ("Monotype", "GOOG", "trademark", "google.com"):
        assert token not in text, "parent branding survived: %s" % token
    # "Noto" may only remain as the OFL-required attribution in the copyright.
    assert text.count("Noto") == 2, "unexpected Noto references: %d" % text.count("Noto")

    out = Path(__file__).resolve().parent.parent / "sources" / "Hoysala.glyphs"
    io.open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
