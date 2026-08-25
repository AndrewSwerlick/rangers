# TTRPG Rulebook Project

A professional book publishing setup using LaTeX and Pandoc for creating both print (PDF) and digital (ePub) versions of your TTRPG rulebook.

## Quick Start

### Enter the Development Environment

```bash
nix develop
```

This will load all necessary tools including LaTeX, Pandoc, and build utilities.

### Build Your Book

```bash
cd book

# Build PDF for print
make pdf

# Build ePub for eReaders
make epub

# Build both formats
make all

# Auto-rebuild PDF on changes
make watch
```

## Project Structure

```
.
├── flake.nix          # Nix development environment
├── book/              # Your book source files
│   ├── rulebook.tex   # Main LaTeX document
│   ├── Makefile       # Build automation
│   └── cover.jpg      # Cover image for ePub (add your own)
└── README.md          # This file
```

## Workflow

Based on the workflow described in [this blog post](http://theroadchoseme.com/how-i-self-published-a-professional-paperback-and-ebook-using-latex-and-pandoc):

1. **Write** your content in LaTeX (`book/rulebook.tex`)
2. **Build PDF** for print version with `make pdf`
3. **Build ePub** for digital version with `make epub`
4. **Publish** to Amazon KDP, Apple Books, or other platforms

### PDF (Print Version)

The PDF is generated using LaTeX with precise control over typography, layout, and print specifications. Perfect for:
- Amazon Kindle Direct Publishing (KDP) paperback
- Professional print-on-demand services
- High-quality PDF downloads

### ePub (Digital Version)

The ePub is generated using Pandoc from your LaTeX source. Compatible with:
- Amazon Kindle (upload .epub directly, or convert to .mobi)
- Apple Books
- Kobo
- Any standard eReader

## Customization

### Page Size and Margins

Edit the `\geometry` settings in `book/rulebook.tex`:

```latex
\geometry{
  paperwidth=6in,      % Customize for your trim size
  paperheight=9in,
  margin=0.75in,
  top=1in,
  bottom=1in
}
```

Common print sizes:
- 6" × 9" (standard trade paperback)
- 5.5" × 8.5" (digest size)
- 8.5" × 11" (US Letter)

### Cover Image

Add a `book/cover.jpg` file for your ePub cover image.

## Tools Included

- **LaTeX** - Professional typesetting system
- **Pandoc** - Universal document converter
- **latexmk** - Automated LaTeX building
- **ImageMagick** - Image processing
- **Ghostscript** - PDF utilities

## Tips

- Use `make watch` during writing for live PDF preview
- Run LaTeX twice to ensure table of contents and references update
- Keep images in a subdirectory (e.g., `book/images/`)
- Test your ePub on multiple devices before publishing

## Park-Map Tracing Reference (OSM → traceable PDF)

`scripts/build_reference.py` turns a real park into a **faint, US-Letter,
print-and-trace PDF** — stage 1 of the map pipeline. The PDF is a *tracing
guide* (it goes under paper, gets hand-inked, then discarded), so it is
deliberately plain: its only jobs are to be **correct** (right topology) and
**followable** (clear enough to trace by hand). No aesthetic processing, no
grid, no distance ticks — the meaningful units are junctions and POIs, not
distance.

### Setup

The pipeline has its own Python devShell (kept separate from the LaTeX one):

```bash
nix develop .#python
```

This provides `osmnx`, `networkx`, `geopandas`, `matplotlib`, `shapely`.
It hits the OpenStreetMap Overpass API, so you need internet access.

### Run

```bash
python scripts/build_reference.py --out out/hard_labor_creek
```

Options:

| flag | default | meaning |
|------|---------|---------|
| `--park` | `Hard Labor Creek State Park, Georgia, USA` | place name to geocode |
| `--osmid` | — | OSM id (e.g. `R17230165`) — more reliable than the name |
| `--out` | `out/hard_labor_creek` | output path **stem** (siblings written next to it) |
| `--orientation` | `auto` | `auto` / `portrait` / `landscape` (auto picks whichever wastes less US-Letter paper) |
| `--consolidate-tolerance` | `12` | metres for junction consolidation (`0` disables) |
| `--min-poi-sep-in` | `0.16` | min POI spacing on paper (a game-token-width "don't overlap" check) |
| `--drop-cart-paths` | off | remove edges flagged as golf cart paths |
| `--allow-any` | off | skip the "is this really the park?" guard |

### Outputs

Given `--out DIR/STEM`, it writes:

- `STEM.pdf` — the traceable reference. Roads = solid medium grey, trails =
  dashed lighter grey, unclassified = dotted tan, POIs = labelled dots,
  entrances = teal triangles, the strongest funnel/chokepoints = faint red.
- `STEM.graphml` and `STEM.gpkg` — the intermediate graph, so later pipeline
  stages reuse it instead of re-hitting OSM.
- `STEM.report.json` / `STEM.report.txt` — node/edge counts, road:trail ratio,
  golf-cart-path count, bridges, chokepoints, entrances, longest road span, and
  any unclassified `highway=` values for you to decide on. Use these counts to
  judge whether OSM's coverage of the park is complete enough.

The script prints the resolved boundary **name and area** first so you can
confirm it fetched the ~5,800-acre *state park* and not the similarly named
*reservoir* in Walton County; it aborts with a hint if the polygon looks wrong.

## Play-Map Post-Processing (traced sketch → wall map)

`scripts/build_playmap.sh` is **stage 2**. Stage 1 gives you a faint reference
PDF to ink by hand; stage 2 takes a *photo* of that finished hand-inked tracing
and turns it into a play surface big enough to plan on — cleaned, enlarged, and
sliced across printer-sized sheets you can sleeve in plastic and assemble.

### Setup

```bash
nix develop .#map
```

An image-only shell (ImageMagick, Ghostscript, potrace). It skips the LaTeX
toolchain, so it loads fast when you are just iterating on a map.

### Run

```bash
./scripts/build_playmap.sh --out out/hard_labor_play map-images/hard-labor-sketch.jpg
```

Options:

| flag | default | meaning |
|------|---------|---------|
| `--out` | `out/playmap` | output path **stem** (siblings written next to it) |
| `--width` | `36in` | finished width of the *assembled* map |
| `--paper` | `letter` | `letter` / `a4` / `legal` / `tabloid` |
| `--orient` | `auto` | `auto` / `portrait` / `landscape` (auto minimises sheet count) |
| `--margin` | `0.25in` | unprintable border, trimmed off during assembly |
| `--overlap` | `0.5in` | band shared with the neighbouring sheet |
| `--dpi` | `300` | resolution the sheets are rendered at |
| `--rotate` | `0` | straighten a crooked photo before anything else |
| `--blur` | `50` | flat-field radius, in px (see below) |
| `--black` / `--white` | `auto` / `90` | ink and paper points, in % |
| `--threshold` | `0.70` | potrace black level; **raise it to keep fainter strokes** |
| `--turd` | `8` | discard speckles smaller than this, in px |
| `--despeckle` | off | extra speckle-removal pass |

Dimensions accept `36in` / `914mm` / `91cm` / `2592pt`; a bare number is inches.

### How the three stages work

**1. Clean.** A phone photo of paper is warm-toned and lit unevenly, so no
single threshold separates ink from paper across the whole sheet. The script
divides the image by a heavily blurred copy of itself: the blur approximates
"what the paper looks like *here*", so `image / blur` is ≈1 (white) everywhere
the pen didn't go, whatever the local paper colour or brightness. A level pass
then pulls the ink to black. The black point is measured from the image
(median-filtered first, so one dust speck can't set it) rather than hard-coded,
so the same numbers work on the next sketch.

**2. Enlarge.** The ink is vectorised with potrace. This is the step that
matters: a plain raster upscale to wall size turns crisp pen lines into grey
mush, whereas fitted Bézier outlines stay sharp at any size. Everything after
this point is *drawn* at its final size, never upscaled.

**3. Tile.** Each sheet prints a `LIVE = paper − 2×margin` window of the map,
and consecutive windows advance by `STEP = LIVE − overlap`, so neighbours share
an overlap-wide band. Sheets are rendered straight from the vector PDF one at a
time (no giant intermediate bitmap) by Ghostscript.

### Outputs

Given `--out DIR/STEM`:

- `STEM.sheets.pdf` — **the thing you print.** Page 1 is the assembly guide;
  the rest are the sheets in reading order, each exactly one sheet of paper.
- `STEM.sheets/rNNcMM.png` — the same sheets individually, if you want to
  reprint just one.
- `STEM.assembly.png` — the guide on its own: a thumbnail of the whole map with
  the sheet grid and `rNcM` labels drawn over it.
- `STEM.full.pdf` — the whole map as a **single vector page** at full size.
  Hand this to a print shop if you would rather have one large-format print.
- `STEM.svg` — the same outlines, for editing in Inkscape.
- `STEM.clean.png` — the cleaned-up flat scan, before vectorising.

The run also reports which sheets carry no ink (`blank sheets: …`); those are
labelled *"blank, skip"* on the sheet itself, and leaving them out of the print
job saves paper without changing the layout.

### Assembling

1. Print `STEM.sheets.pdf` at **100% / Actual Size**. Do *not* use "Fit to
   Page" — that silently rescales, and the sheets will no longer line up.
2. Cut each sheet along the light grey rectangle; the darker corner marks sit
   just *outside* it and show where the line runs. Ink past the line is bleed,
   so a slightly wandering cut still leaves no white sliver.
3. Butt the trimmed sheets edge to edge in the `rNcM` order from the guide.
   Cutting removes the shared band from every sheet's left and top edge, so the
   joins land exactly with no doubled strip and nothing to overlap.

### Tuning

- **Faint strokes dropping out** (pencil under-drawing, light dashed trails):
  raise `--threshold` toward `0.8`. Lower it toward `0.5` to shed noise.
- **Paper texture showing up as speckle**: raise `--turd`, or add
  `--despeckle`.
- **Blotchy background**, or shading that survives: raise `--blur`. The radius
  must stay comfortably larger than the widest pen stroke — too small and the
  blur starts tracking the ink itself, which eats the middle of thick lines.
- **Too many sheets**: shrink `--width`, or move to `--paper tabloid`.

## Publishing Platforms

- **Amazon KDP**: https://kdp.amazon.com
- **Apple Books**: https://books.apple.com/us/author
- **Draft2Digital**: https://draft2digital.com
- **IngramSpark**: https://www.ingramspark.com

## Resources

- [Original blog post](http://theroadchoseme.com/how-i-self-published-a-professional-paperback-and-ebook-using-latex-and-pandoc)
- [LaTeX Documentation](https://www.latex-project.org/)
- [Pandoc Manual](https://pandoc.org/MANUAL.html)
