# AGENTS.md

**The Rangers** — a post-apocalyptic, tower-defense-flavored TTRPG played on real
state park maps. This repo holds the design notes, the printable play materials
(LaTeX/TikZ), and a two-stage pipeline that turns a real park into a printable
wall map.

There is no application code, no test suite, and no linter. "Building" means
producing PDFs, and "testing" means opening the PDF and looking at it.

---

## Nix shells: pick the right one

Three separate devShells. They are deliberately disjoint — do not assume a tool
from one is present in another.

| Shell | Command | Contains | Used for |
|---|---|---|---|
| default | `nix develop` | TeX Live (lua/xe/pdflatex, latexmk), pandoc, ghostscript, imagemagick, **google-fonts** | `book/`, `printables/` |
| python | `nix develop .#python` | osmnx, networkx, geopandas, shapely, matplotlib, rtree | `scripts/build_reference.py` |
| map | `nix develop .#map` | imagemagick, ghostscript, potrace, dejavu | `scripts/build_playmap.sh` |

**The fonts only exist inside the default shell.** `flake.nix`'s `shellHook`
exports `OSFONTDIR` and writes a temporary `FONTCONFIG_FILE` pointing at the
`google-fonts` store path. Running `lualatex` on anything in `printables/` from
a bare shell will fail to find EB Garamond / Josefin Sans / Caveat. Always wrap:

```bash
nix develop <repo-root> --command lualatex ...
```

`.claude/hooks/session-start.sh` does this once per session, but only when
`CLAUDE_CODE_REMOTE=true` (Claude Code on the web). Locally you must wrap
commands yourself.

---

## Building the printables

`printables/*.tex` use `fontspec`, so **they require LuaLaTeX**. `pdflatex`
aborts with `Fatal Package fontspec Error: The fontspec package requires either
XeTeX or LuaTeX`. The stale `printables/build/*.log` files are the wreckage of
exactly that mistake — ignore them, they are not a build system.

Build from *inside* `printables/`, because the sheets `\input{sheet_preamble}`
and `\input{sheet_body}` by relative path:

```bash
cd printables
nix develop .. --command lualatex -interaction=nonstopmode -halt-on-error hunter_sheet.tex
```

The PDF lands next to the `.tex`. One pass is enough (no TOC, no refs).

- **PDFs are committed** alongside their source. If you change a `.tex`, rebuild
  and commit the `.pdf` in the same change — that is the pattern in every prior
  commit.
- Builds are byte-reproducible (nix pins `SOURCE_DATE_EPOCH`; PDF timestamps read
  1980). A no-op rebuild produces **no git diff**, so a clean `git status` after
  rebuilding means your edit genuinely changed nothing visual.
- `./clean.sh` only wipes aux files in the repo **root**, not in `printables/`.
  Delete `printables/*.aux` and `printables/*.log` by hand.
- `auto/` and `printables/auto/` are AUCTeX (Emacs) droppings. Untracked, ignore.

### `book/`

`book/Makefile` (`make pdf` / `epub` / `all` / `watch` / `clean`) drives
`rulebook.tex` with **pdflatex** — that file has no `fontspec`, so pdflatex is
correct there. Do not point this Makefile at the printables.

`book/rulebook.tex` is still untouched upstream boilerplate ("Your TTRPG
Rulebook", "Your Name", placeholder chapters). The real content currently lives
in `notes/` and `printables/`. Treat the book as not yet started.

---

## Character sheet architecture

Every sheet is one landscape US-Letter, two-page (front = play surface, back =
rules reference) TikZ drawing.

```
sheet_preamble.tex   geometry + colors + font families        (shared)
sheet_body.tex       the entire two-page layout               (shared)
<archetype>_sheet.tex   defines 2 macros, then \input{sheet_body}
```

An archetype sheet is *only* these two macro definitions:

- `\archetypeField` — what goes in the archetype banner (a name, or a ruled line
  on the blank `character_sheet.tex`)
- `\actionContent` — the three TikZ nodes filling the PREP / DEFENSE /
  DESPERATION triptych

Both are expanded from inside the `tikzpicture` in `sheet_body.tex`, so they may
use the layout's `\def`s (`\leftcolwidth`, `\colonestart`, `\colonemid`,
`\coltwomid`, `\colend`, `\colheaderbottom`, `\archetypetop`, `\pagewidth`,
`\pageheight`). Adding a new archetype = copy `hunter_sheet.tex`, rewrite the two
macros. Never fork `sheet_body.tex` (commit `73f17ea` deliberately collapsed six
divergent copies into it).

### TikZ conventions

- `[x=1in, y=-1in]` — **coordinates are inches and y grows downward.** Origin is
  the top-left of the page. `\archetypetop+0.28` is *below* `\archetypetop`.
- Layout constants are `\def`s declared near where they are used, then referenced
  arithmetically (`\def\rolltop{\turntop + 1.9}`). Adjusting a section means
  changing one `\def`, not the nodes below it.
- Text blocks are `\node[anchor=north west, text width=...]` with explicit
  `\fontsize{}{}\selectfont`. Sizes are hand-tuned per column; 9/11 is the body
  default, 7-8pt for parentheticals.

### The one real gotcha

**TikZ node overflow is silent.** Text longer than its `text width` just runs off
the column divider or off the page — no warning, no error, exit code 0. After
any text edit you must open the PDF and look. Commit `0a05773` ("Fix character
prompts overflow") exists solely to repair overflow that compiled cleanly.

### Colors

`parkbrown`, `parkgreen`, `mutedtext` are all defined as **pure black**
(`RGB 0,0,0`) on purpose: the sheets are designed for B&W home printers at
maximum contrast. Only `rulelight` (grey 100) differs. Do not "fix" the names to
match the values, and do not introduce real color without a reason.

### `locations.tex`

Different structure: 3.5"×5" cards tiled 2×2 per page with crop marks, built
from a single `\locationcard{x}{y}{name}{def-name}{def-desc}{rec-name}{rec-desc}{prompt}`
macro. Add locations by calling the macro, not by drawing.

---

## Typography

Set in `sheet_preamble.tex`, rationale in `notes/art_style_and_typography.md`.
Three registers, do not mix them up:

| Family | Font | Role |
|---|---|---|
| `\headerfont` | Josefin Sans Bold, letterspaced 5 | WPA-poster register: big titles, banners |
| `\sectionfont` | Josefin Sans Bold | Section labels, ability names |
| main / `\setmainfont` | EB Garamond | Field-guide register: all rules prose |
| `\promptfont` | Caveat | Handwritten register: character prompts only |

These are Google *variable* fonts; weight comes from a `wght` axis instance,
not from a separate bold file. Caveat needs `Renderer=HarfBuzz` (hence
LuaHBTeX).

**`RawFeature={wght=700}` is a silent no-op.** luaotfload only honours axis
values written as `RawFeature={axis={wght=700}}` (fontspec's `Weight=700` also
works). Written the first way it compiles cleanly, produces no warning, and
renders byte-identical ink to no feature at all, so the font stays at its
*default* instance. That matters because the defaults are the thin ends of the
axes:

| Font | `wght` range | default |
|---|---|---|
| EB Garamond | 400–800 | **400** |
| Caveat | 400–700 | **400** |
| Josefin Sans | 100–700 | **100** (Thin) |

So a file using the broken syntax renders all Garamond prose at 400 and every
`\bfseries` identically to regular, which prints washed-out gray. Both
`locations.tex` and `sheet_preamble.tex` now use `axis={...}` (Garamond 600
body / 800 bold, Josefin 700, Caveat 700). `FakeBold` was dropped from the
Josefin families once real weight worked; it existed only to compensate for
the ignored axis.

Raising a weight **re-wraps every `text width` node**, and the sheets hard-code
section offsets (`\def\rolltop{\turntop + 1.9}`), so added lines collide
silently. After any weight change, check the gap between the last inked row of
a block and the rule below it. The tightest spot is the ACTIONS triptych on
sheet page 1, which bottoms out at a rule at tikz y=3.85: `navigator_sheet`
gained two lines there and now clears it by 0.25in.

To check a weight change actually landed, rasterise and compare ink coverage
rather than trusting the log:

```bash
nix develop .. --command gs -q -dNOPAUSE -dBATCH -sDEVICE=pgmraw -r300 \
  -sOutputFile=/tmp/p-%d.pgm locations.pdf
```

Ghostscript renders these bilevel, so the fraction of pixels below 128 is a
direct toner-coverage proxy. Equal ink before and after means the feature was
ignored.

---

## Map pipeline

Two stages, each with its own shell, joined by a sheet of paper.

**Stage 1 — `scripts/build_reference.py`** (`nix develop .#python`): geocodes a
park via OpenStreetMap, pulls the trail/road graph, consolidates junctions,
finds chokepoints and entrances, and renders a *faint* US-Letter PDF meant to be
printed, placed under paper, and hand-inked. It is a tracing guide, not art.

```bash
python scripts/build_reference.py --out out/hard_labor_creek
```

- Needs network access (Overpass API). `cache/` holds osmnx's HTTP cache, so
  re-runs are offline and fast — do not delete it casually.
- It prints the resolved boundary name and area and **aborts if the polygon looks
  wrong** (the classic failure is geocoding the reservoir instead of the
  ~5,800-acre state park). Pass `--osmid R17230165` for reliability; `--allow-any`
  disables the guard.
- Writes `STEM.graphml` / `STEM.gpkg` so later stages reuse the graph, plus
  `STEM.report.{json,txt}` with topology/coverage counts.
- Deliberately no grid and no distance ticks — the game's units are junctions and
  POIs, not distance. Don't "helpfully" add a scale bar.

**Stage 2 — `scripts/build_playmap.sh`** (`nix develop .#map`): takes a photo of
the finished hand-inked tracing and produces printable tiles.

```bash
./scripts/build_playmap.sh --out out/hard_labor_play map-images/hard-labor-sketch.jpg
```

Three internal steps, worth knowing before tuning flags: **clean** (divide the
photo by a blurred copy of itself to flat-field uneven lighting, then level to
black), **enlarge** (potrace to vector, so wall-size output stays crisp — never
raster-upscale), **tile** (Ghostscript renders each sheet directly from the
vector PDF). Geometry is computed in PostScript points throughout.

Tuning: faint strokes dropping out → raise `--threshold` toward 0.8; paper
speckle → raise `--turd`; blotchy background → raise `--blur` (but keep it well
above the widest pen stroke or it eats thick lines).

Full flag tables and assembly instructions are in `README.md` — that file is the
authoritative user-facing doc for both scripts and is kept current.

---

## Design notes (`notes/`)

Prose design docs, ~1,900 lines. These are the source of truth for rules, but
**they are not uniformly current**:

- `overview.md` still describes a 4-level injury track with generic disadvantage.
  The shipped sheets implement 3 harm + 3 exhaustion, where harm restricts
  *movement* (no bushwhack → roads only → immobile) and exhaustion shrinks the
  dice pool (3d6 → min 1d6), and taking harm is a player *choice* between the
  two tracks.
- `essential_rules_for_character_sheet.md` is the reconciliation pass and matches
  what is on the sheets. `ranger_turns.md`, `prep_phase.md`, `assault_phase.md`,
  `desperation_phase.md`, `wave_turn.md` are the detailed current rules.
- `ranger_archetypes.md` is the shorthand list of all six archetypes; the sheets
  are the polished wording. Where they differ, the sheet won (see commit
  `eeac187`).

If a rules change touches play, it usually needs to land in three places: the
relevant `notes/*.md`, every affected `printables/*_sheet.tex`, and the shared
rules reference on page 2 of `sheet_body.tex`.

### Terminology

Current vocabulary, standardized in commit `0e22baf` — do not regress to the old
words:

- **assault** (not "attack") — a ranger damaging the wave, or a wave token
  hitting a position
- **defense** (not "breach") — the roll when a wave assaults your position
- **harm** — the damage event; the player then marks **injury** or **exhaustion**
- **momentum** — the wave's hit-point pool (10/15/25/40/65 across waves)
- **tokens** — the narrative↔mechanical currency, earned for story contributions
  and spent on prep defenses or Act 3 desperation moves

The three acts are **Prep**, **Crisis/Assault**, **Desperation**. Archetype
abilities are grouped as prep / safe / costly / desperation.

---

## Repo state and hygiene

- `scripts/`, `out/`, `cache/`, `map-images/`, `sketches/`, `setup.sh` are
  **untracked and not gitignored** — the map pipeline is in flight. Check
  `git status` before assuming a file is committed.
- `.gitignore` covers LaTeX aux files only.
- `setup.sh` bootstraps Nix on a bare Debian/Ubuntu container (used for remote
  sessions); it is not needed locally.
- Generated artifacts that *are* tracked: every `printables/*.pdf`. Everything in
  `out/` is disposable.
