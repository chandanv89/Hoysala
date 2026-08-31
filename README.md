# Hoysala

Hoysala is a high-contrast display serif for Kannada and Latin.

It is named after the Hoysala dynasty, whose temples at Belur and Halebidu are
known for intricate, deeply undercut soapstone relief — a fitting reference for
a face built on sharp modulation and strong light-and-shadow.

## Status

Early. The sources are currently an unmodified rebrand of the parent design; the
contrast work has not started. Do not treat builds from this repository as a
finished typeface.

## Provenance

Hoysala is derived from [Noto Serif Kannada](https://github.com/notofonts/kannada),
copyright 2022 The Noto Project Authors, used under the SIL Open Font License 1.1.
The parent is released without a Reserved Font Name, so this derivative is free
to carry its own name.

`scripts/derive_from_noto.py` reproduces the initial rebrand from an unmodified
copy of `NotoSerifKannada.glyphs`. It rewrites only metadata — family name,
credits, version and vendor ID — and drops the Noto trademark string. Outlines,
kerning, features and masters are inherited untouched.

## Design direction

The parent is a low-contrast text serif. Hoysala keeps its skeleton and
proportions and changes the modulation:

- raise stroke contrast, thinning horizontals against retained vertical weight
- sharpen terminals and serifs
- tighten spacing for display sizes
- narrow the shipped weight range to what a display face needs

`scripts/contrast.py` measures the thick/thin ratio so this is trackable rather
than a matter of opinion. The inherited baseline, over a sample of fifteen
Kannada consonants:

| wght | thin | thick | contrast |
| ---- | ---- | ----- | -------- |
| 100  | 22   | 25    | 1.18     |
| 400  | 46   | 93    | 2.04     |
| 700  | 61   | 138   | 2.27     |
| 900  | 66   | 162   | 2.46     |

The light end is effectively monolinear, so it needs the most work. A display
serif of this kind wants something closer to 4 at Regular, reached mainly by
thinning the thins rather than fattening the thicks.

## Sources

Four drawn masters on a single `wght` axis — Light, Regular, SemiBold and Bold —
inherited from the parent. The nine named weights are interpolated instances.

## Building

The full pipeline — Latin subset merge, Google Fonts fixes, STAT table, static
instances — runs on Linux:

```
pip install -r requirements.txt
gftools builder sources/config.yaml
```

It does not run on Windows: gftools emits build rules that shell out to `mv` and
`cp`, and drives them with a `ninja` binary. Use CI or WSL there. For quick
design iteration a plain variable build is enough and is pure Python, so it
works anywhere:

```
fontmake -o variable -g sources/Hoysala.glyphs --output-path "fonts/Hoysala[wght].ttf"
```

That skips the Latin merge and the Google Fonts fixes, so it is for looking at
shapes, not for release. Output lands in `fonts/`, which is not committed.

## Proofing

`scripts/proof.py` shapes text with HarfBuzz — so conjuncts, matras and
reordering are real — and renders it. Pass one font for a specimen, or several
to stack them line-for-line:

```
python scripts/proof.py "fonts/Hoysala[wght].ttf" -o proof/specimen.png
python scripts/proof.py "fonts/Hoysala[wght].ttf" NotoSerifKannada.ttf \
    --labels Hoysala "Noto Serif Kannada" -o proof/compare.png
```

Against the parent, the Kannada is currently identical and both measure 2.04
contrast, which is the intended starting state: the rebrand changed no outlines.
That comparison is the "before" to judge the contrast work against.

Output goes to `proof/`, which is not committed.

## Open items

- Vendor ID is a placeholder (`HYSL`) and needs registering with Microsoft.
- Latin is merged at build time from Noto Serif as a placeholder. It is
  low-contrast and must be redrawn to match the Kannada, then baked into the
  source.
- Author email and project URL in the font metadata need confirming.

## License

SIL Open Font License 1.1. See [OFL.txt](OFL.txt).
