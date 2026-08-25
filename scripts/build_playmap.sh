#!/usr/bin/env bash
#
# build_playmap.sh -- stage 2 of the map pipeline.
#
# Stage 1 (scripts/build_reference.py) turns OSM data into a faint US-Letter
# PDF you print, put under paper, and ink by hand. This script takes a *photo*
# of that hand-inked tracing and turns it into a big play surface:
#
#   1. clean   -- kill the paper tone and the phone-camera lighting gradient,
#                 leaving black ink on white
#   2. enlarge -- vectorise the ink with potrace, so the map can be blown up to
#                 any size without going soft (a plain raster upscale turns
#                 pen lines into grey mush)
#   3. tile    -- slice the enlarged map into printer-sized sheets with butt-cut
#                 lines, registration marks and an assembly guide, ready to
#                 sleeve in plastic and lay out
#
# Run it inside:  nix develop .#map
#
set -euo pipefail

# ---------------------------------------------------------------- defaults --
IN=""
OUT="out/playmap"
TARGET_W="36in"     # finished width of the assembled map
PAPER="letter"
ORIENT="auto"       # auto | portrait | landscape
MARGIN="0.25in"     # unprintable/safety border, discarded when trimming
OVERLAP="0.5in"     # band shared with the neighbouring sheet
DPI=300             # rendering resolution of the printed sheets
BLUR=50             # flat-field radius, in px, for background removal
BLACK="auto"        # black point for the ink, in % (auto = derive from image)
WHITE=90            # white point for the paper, in %
THRESHOLD=0.70      # potrace black level; higher keeps fainter strokes
TURD=8              # potrace speckle suppression, in px
ROTATE=0
DESPECKLE=0

usage() {
  cat <<'USAGE'
Usage: build_playmap.sh [options] <traced-photo.jpg>

  --out STEM          output path stem            (default out/playmap)
  --width DIM         finished assembled width    (default 36in)
  --paper NAME        letter|a4|legal|tabloid     (default letter)
  --orient MODE       auto|portrait|landscape     (default auto)
  --margin DIM        unprintable border          (default 0.25in)
  --overlap DIM       shared band between sheets  (default 0.5in)
  --dpi N             sheet render resolution     (default 300)
  --rotate DEG        rotate the photo first      (default 0)
  --blur N            flat-field radius in px     (default 50)
  --black PCT|auto    ink black point             (default auto)
  --white PCT         paper white point           (default 90)
  --threshold F       potrace black level 0..1    (default 0.70)
  --turd N            drop speckles under N px    (default 8)
  --despeckle         extra speckle removal pass
  -h, --help          this message

DIM accepts 36in / 914mm / 91cm / 2592pt; a bare number means inches.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --out)       OUT="$2"; shift 2 ;;
    --width)     TARGET_W="$2"; shift 2 ;;
    --paper)     PAPER="$2"; shift 2 ;;
    --orient)    ORIENT="$2"; shift 2 ;;
    --margin)    MARGIN="$2"; shift 2 ;;
    --overlap)   OVERLAP="$2"; shift 2 ;;
    --dpi)       DPI="$2"; shift 2 ;;
    --rotate)    ROTATE="$2"; shift 2 ;;
    --blur)      BLUR="$2"; shift 2 ;;
    --black)     BLACK="$2"; shift 2 ;;
    --white)     WHITE="$2"; shift 2 ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    --turd)      TURD="$2"; shift 2 ;;
    --despeckle) DESPECKLE=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    -*)          echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)           IN="$1"; shift ;;
  esac
done

[ -n "$IN" ] || { echo "error: no input photo given" >&2; usage >&2; exit 2; }
[ -f "$IN" ] || { echo "error: no such file: $IN" >&2; exit 2; }

for tool in magick potrace gs; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "error: $tool not found -- run inside 'nix develop .#map'" >&2; exit 1; }
done

FONT="${PLAYMAP_FONT:-DejaVu-Sans}"

# ------------------------------------------------------------------ helpers --
# All internal geometry is in PostScript points (1/72 inch).
to_pt() {
  case "$1" in
    *in) awk -v n="${1%in}" 'BEGIN{printf "%.4f", n*72}' ;;
    *mm) awk -v n="${1%mm}" 'BEGIN{printf "%.4f", n*72/25.4}' ;;
    *cm) awk -v n="${1%cm}" 'BEGIN{printf "%.4f", n*72/2.54}' ;;
    *pt) awk -v n="${1%pt}" 'BEGIN{printf "%.4f", n}' ;;
    *)   awk -v n="$1"      'BEGIN{printf "%.4f", n*72}' ;;
  esac
}
f()  { awk "BEGIN{printf \"%.4f\", $1}"; }     # float
i()  { awk "BEGIN{printf \"%d\", int(($1)+0.5)}"; }  # rounded int
inch() { awk "BEGIN{printf \"%.2f\", ($1)/72}"; }

case "$PAPER" in
  letter)  PAPER_W=612;    PAPER_H=792 ;;
  legal)   PAPER_W=612;    PAPER_H=1008 ;;
  a4)      PAPER_W=595.28; PAPER_H=841.89 ;;
  tabloid) PAPER_W=792;    PAPER_H=1224 ;;
  *) echo "error: unknown paper '$PAPER'" >&2; exit 2 ;;
esac

TARGET_W_PT=$(to_pt "$TARGET_W")
MARGIN_PT=$(to_pt "$MARGIN")
OVERLAP_PT=$(to_pt "$OVERLAP")

OUTDIR=$(dirname "$OUT")
STEM=$(basename "$OUT")
SHEETDIR="$OUT.sheets"
mkdir -p "$OUTDIR" "$SHEETDIR"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "=== play-map pipeline ==============================================="
echo "input      : $IN"
echo "output stem: $OUT"

# -------------------------------------------------------------- 1. clean up --
# The photo is warm-toned paper lit unevenly by a phone. Dividing the image by
# a heavily blurred copy of itself flattens both at once: the blur approximates
# "what the paper looks like here", so image/blur is ~1 (white) everywhere the
# pen didn't go, whatever the local paper colour or brightness.
echo
echo "[1/4] cleaning up ..."
DIV="$TMP/divided.png"
magick "$IN" -auto-orient \
  $( [ "$ROTATE" != 0 ] && echo "-rotate $ROTATE" ) \
  -colorspace Gray \
  \( +clone -blur "0x$BLUR" \) -compose Divide_Src -composite \
  "$DIV"

if [ "$BLACK" = auto ]; then
  # Median-filter first so a single dust speck can't set the black point.
  RAW_MIN=$(magick "$DIV" -statistic Median 3x3 -format "%[fx:minima*100]" info:)
  BLACK=$(f "$RAW_MIN + 2")
  echo "      darkest ink ${RAW_MIN}%  ->  black point ${BLACK}%"
fi

CLEAN="$OUT.clean.png"
magick "$DIV" -level "${BLACK}%,${WHITE}%" \
  $( [ "$DESPECKLE" = 1 ] && echo "-despeckle" ) \
  -trim +repage \
  "$CLEAN"
read -r IMG_W IMG_H <<< "$(magick identify -format "%w %h" "$CLEAN")"
echo "      cleaned: ${IMG_W}x${IMG_H}px -> $CLEAN"

# -------------------------------------------------------------- 2. enlarge --
# potrace fits smooth Bezier outlines to the ink, so the map is resolution-free
# from here on: every later render is drawn at its final size, never upscaled.
echo
echo "[2/4] vectorising ..."
magick "$CLEAN" -compress none "$TMP/clean.pgm"
potrace "$TMP/clean.pgm" -k "$THRESHOLD" -t "$TURD" -b svg -o "$OUT.svg"
potrace "$TMP/clean.pgm" -k "$THRESHOLD" -t "$TURD" -b pdf \
        -W "${TARGET_W_PT}pt" -o "$OUT.full.pdf"

read -r MAP_W MAP_H <<< "$(magick identify -format "%w %h\\n" "$OUT.full.pdf" 2>/dev/null | head -1)"
echo "      full-size vector: $(inch "$MAP_W") x $(inch "$MAP_H") in -> $OUT.full.pdf"
echo "      scalable outline                        -> $OUT.svg"

# ----------------------------------------------------------- 3. sheet grid --
# Each sheet prints a LIVE = paper - 2*margin window of the map. Consecutive
# windows advance by STEP = LIVE - overlap, so neighbours share an overlap-wide
# band. Trimming that band off every sheet's left and top edge makes the sheets
# butt together exactly, with no double-printed strip.
echo
echo "[3/4] planning sheets ..."

plan() { # $1=sheet_w $2=sheet_h -> "cols rows"
  awk -v sw="$1" -v sh="$2" -v mw="$MAP_W" -v mh="$MAP_H" \
      -v m="$MARGIN_PT" -v ov="$OVERLAP_PT" 'BEGIN{
    lw = sw - 2*m; lh = sh - 2*m;
    stw = lw - ov; sth = lh - ov;
    if (stw <= 0 || sth <= 0) { print "0 0"; exit }
    cols = int((mw - ov)/stw); if (cols*stw + ov < mw - 0.001) cols++;
    rows = int((mh - ov)/sth); if (rows*sth + ov < mh - 0.001) rows++;
    if (cols < 1) cols = 1; if (rows < 1) rows = 1;
    print cols, rows;
  }'
}

read -r P_COLS P_ROWS <<< "$(plan "$PAPER_W" "$PAPER_H")"
read -r L_COLS L_ROWS <<< "$(plan "$PAPER_H" "$PAPER_W")"
[ "$P_COLS" != 0 ] || { echo "error: margin+overlap exceed the paper size" >&2; exit 1; }

case "$ORIENT" in
  portrait)  SHEET_W=$PAPER_W; SHEET_H=$PAPER_H; COLS=$P_COLS; ROWS=$P_ROWS ;;
  landscape) SHEET_W=$PAPER_H; SHEET_H=$PAPER_W; COLS=$L_COLS; ROWS=$L_ROWS ;;
  auto)
    if [ "$(( L_COLS * L_ROWS ))" -lt "$(( P_COLS * P_ROWS ))" ]; then
      SHEET_W=$PAPER_H; SHEET_H=$PAPER_W; COLS=$L_COLS; ROWS=$L_ROWS
    else
      SHEET_W=$PAPER_W; SHEET_H=$PAPER_H; COLS=$P_COLS; ROWS=$P_ROWS
    fi ;;
  *) echo "error: unknown orient '$ORIENT'" >&2; exit 2 ;;
esac

LIVE_W=$(f "$SHEET_W - 2*$MARGIN_PT")
LIVE_H=$(f "$SHEET_H - 2*$MARGIN_PT")
STEP_W=$(f "$LIVE_W - $OVERLAP_PT")
STEP_H=$(f "$LIVE_H - $OVERLAP_PT")
# Centre the map in the covered area so the slack lands as an even white border.
PAD_X=$(f "($COLS*$STEP_W + $OVERLAP_PT - $MAP_W)/2")
PAD_Y=$(f "($ROWS*$STEP_H + $OVERLAP_PT - $MAP_H)/2")
N_SHEETS=$(( COLS * ROWS ))

[ "$SHEET_W" = "$PAPER_W" ] && ORIENT_NAME=portrait || ORIENT_NAME=landscape
echo "      paper   : $PAPER $ORIENT_NAME ($(inch "$SHEET_W") x $(inch "$SHEET_H") in)"
echo "      live area per sheet: $(inch "$LIVE_W") x $(inch "$LIVE_H") in"
echo "      grid    : ${COLS} x ${ROWS} = ${N_SHEETS} sheets"
echo "      assembled after trimming: $(inch "$MAP_W") x $(inch "$MAP_H") in"

# --------------------------------------------------------------- 4. render --
echo
echo "[4/4] rendering sheets at ${DPI}dpi ..."
PX_W=$(i "$SHEET_W * $DPI / 72")
PX_H=$(i "$SHEET_H * $DPI / 72")
M_PX=$(i "$MARGIN_PT * $DPI / 72")
O_PX=$(i "$OVERLAP_PT * $DPI / 72")
TICK=$(i "0.15 * $DPI")          # crop-mark arm length (drawn outside the cut)
LABEL_PT=$(i "0.11 * $DPI")      # label text size
LAB_W=$(awk -v w="$PX_W" -v m="$M_PX" -v t="$TICK" -v d="$DPI" 'BEGIN{
  avail = w - 2*(m + t + 20); cap = 4.7*d; print int((avail<cap?avail:cap))}')
LAB_X1=$(i "($PX_W - $LAB_W)/2"); LAB_X2=$(i "($PX_W + $LAB_W)/2")

rm -f "$SHEETDIR"/*.png
PAGES=()
BLANKS=()
n=0
for r in $(seq 0 $((ROWS-1))); do
  for c in $(seq 0 $((COLS-1))); do
    n=$((n+1))
    tag=$(printf "r%02dc%02d" $((r+1)) $((c+1)))
    tile="$SHEETDIR/$tag.png"

    # Map coordinate of this sheet's live-area lower-left corner. Rows are
    # numbered from the top, but PDF space counts y upwards from the bottom.
    X0=$(f "$c*$STEP_W - $PAD_X")
    Y0=$(f "($ROWS-1-$r)*$STEP_H - $PAD_Y")
    # Put that point at the live area's origin on the sheet.
    TX=$(f "$MARGIN_PT - $X0")
    TY=$(f "$MARGIN_PT - $Y0")

    # /Install runs in the device's default user space (+y up), unlike
    # /PageOffset, which gs applies in device space (+y *down* for raster
    # devices) and which therefore silently flips the row order.
    gs -q -dNOPAUSE -dBATCH -dSAFER \
       -sDEVICE=pnggray -r"$DPI" -g"${PX_W}x${PX_H}" -dFIXEDMEDIA \
       -sOutputFile="$tile" \
       -c "<</Install {$TX $TY translate}>> setpagedevice" \
       -f "$OUT.full.pdf"

    # Corner sheets of the grid often catch nothing but blank paper; flag them
    # so they can be skipped rather than printed and sleeved.
    INK=$(magick "$tile" -format "%[fx:1-mean]" info:)
    if [ "$(awk -v v="$INK" 'BEGIN{print (v < 0.00005) ? 1 : 0}')" = 1 ]; then
      BLANKS+=("$tag"); NOTE="   -- blank, skip"
    else
      NOTE=""
    fi

    # Cut lines: trim the shared band off the left and top of interior sheets,
    # and the plain margin off the outer edges. Every sheet then butt-joins.
    CL=$M_PX; CT=$M_PX
    [ "$c" -gt 0 ] && CL=$(( M_PX + O_PX ))
    [ "$r" -gt 0 ] && CT=$(( M_PX + O_PX ))
    CR=$(( PX_W - M_PX )); CB=$(( PX_H - M_PX ))

    magick "$tile" \
      -fill none -stroke '#c8c8c8' -strokewidth 1 \
      -draw "rectangle $CL,$CT $CR,$CB" \
      -stroke '#404040' -strokewidth 2 \
      -draw "line $((CL-TICK)),$CT $CL,$CT  line $CL,$((CT-TICK)) $CL,$CT" \
      -draw "line $CR,$CT $((CR+TICK)),$CT  line $CR,$((CT-TICK)) $CR,$CT" \
      -draw "line $((CL-TICK)),$CB $CL,$CB  line $CL,$CB $CL,$((CB+TICK))" \
      -draw "line $CR,$CB $((CR+TICK)),$CB  line $CR,$CB $CR,$((CB+TICK))" \
      -stroke none -fill white \
      -draw "rectangle $LAB_X1,$((CB+4)) $LAB_X2,$PX_H" \
      -fill '#707070' -font "$FONT" -pointsize "$LABEL_PT" \
      -gravity South -annotate "+0+$(i "$M_PX/4")" \
        "$STEM   row $((r+1)) / $ROWS   col $((c+1)) / $COLS   (sheet $n of $N_SHEETS)$NOTE" \
      "$tile"

    PAGES+=("$tile")
    printf "      %s  (%d/%d)\r" "$tag" "$n" "$N_SHEETS"
  done
done
echo "      $N_SHEETS sheets                        -> $SHEETDIR/"

# ------------------------------------------------------ assembly index page --
# A one-page picture of which sheet goes where, printed as page 1. Everything
# below is laid out in final-page pixels, so the grid can't drift away from the
# thumbnail it is drawn over.
GUIDE="$OUT.assembly.png"
GW=$(i "$SHEET_W * $DPI / 72"); GH=$(i "$SHEET_H * $DPI / 72")
TOP=$(i "$GH * 0.13"); BOT=$(i "$GH * 0.17"); SIDE=$(i "$GW * 0.06")
AVAIL_W=$(( GW - 2*SIDE )); AVAIL_H=$(( GH - TOP - BOT ))
TSCALE=$(awk -v aw="$AVAIL_W" -v ah="$AVAIL_H" -v mw="$MAP_W" -v mh="$MAP_H" \
  'BEGIN{a=aw/mw; b=ah/mh; printf "%.6f", (a<b)?a:b}')

gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pnggray \
   -r"$(f "$TSCALE * 72")" -sOutputFile="$TMP/thumb.png" "$OUT.full.pdf"
read -r TW TH <<< "$(magick identify -format "%w %h" "$TMP/thumb.png")"
OX=$(i "($GW - $TW)/2"); OY=$(i "$TOP + ($AVAIL_H - $TH)/2")

# Grid lines fall on the sheet steps, shifted by the same centring pad the
# sheets use; clip them to the thumbnail so stray lines don't run off the map.
LPT=$(i "$GW * 0.017")
draws=""
for c in $(seq 1 $((COLS-1))); do
  gx=$(i "$OX + ($c*$STEP_W - $PAD_X)*$TSCALE")
  [ "$gx" -gt "$OX" ] && [ "$gx" -lt "$((OX+TW))" ] &&
    draws="$draws -draw \"line $gx,$OY $gx,$((OY+TH))\""
done
for r in $(seq 1 $((ROWS-1))); do
  gy=$(i "$OY + ($r*$STEP_H - $PAD_Y)*$TSCALE")
  [ "$gy" -gt "$OY" ] && [ "$gy" -lt "$((OY+TH))" ] &&
    draws="$draws -draw \"line $OX,$gy $((OX+TW)),$gy\""
done
labels=""
for r in $(seq 0 $((ROWS-1))); do
  for c in $(seq 0 $((COLS-1))); do
    lx=$(i "$OX + (($c+0.5)*$STEP_W - $PAD_X)*$TSCALE - $LPT")
    ly=$(i "$OY + (($r+0.5)*$STEP_H - $PAD_Y)*$TSCALE")
    [ "$lx" -lt "$OX" ] && lx=$OX
    [ "$ly" -lt "$OY" ] && ly=$OY
    labels="$labels -draw \"text $lx,$ly '$(printf 'r%dc%d' $((r+1)) $((c+1)))'\""
  done
done

eval magick -size "${GW}x${GH}" xc:white -colorspace sRGB \
  "$TMP/thumb.png" -gravity NorthWest -geometry "+$OX+$OY" -composite \
  -fill none -stroke "'#d02020'" -strokewidth 2 $draws \
  -stroke none -fill "'#d02020'" -font "'$FONT'" -pointsize "$LPT" $labels \
  -fill "'#202020'" -gravity North \
  -pointsize "$(i "$GW*0.027")" -annotate "+0+$(i "$GH*0.025")" "'$STEM  --  assembly guide'" \
  -pointsize "$(i "$GW*0.0135")" -fill "'#404040'" \
  -annotate "+0+$(i "$GH*0.058")" \
    "'$COLS x $ROWS = $N_SHEETS sheets   |   assembled $(inch "$MAP_W") x $(inch "$MAP_H") in   |   $PAPER $ORIENT_NAME @ ${DPI}dpi'" \
  -gravity South -fill "'#303030'" \
  -annotate "+0+$(i "$GH*0.098")" "'Print at 100% / Actual Size -- do NOT use Fit to Page.'" \
  -annotate "+0+$(i "$GH*0.074")" "'Cut each sheet along the grey rectangle; the corner marks show where.'" \
  -annotate "+0+$(i "$GH*0.050")" "'That takes the shared band off the left and top edges, so trimmed'" \
  -annotate "+0+$(i "$GH*0.026")" "'sheets butt together edge to edge. Ink past the line is bleed.'" \
  -strip "$GUIDE"
echo "      assembly guide                     -> $GUIDE"

# ------------------------------------------------------- print-ready bundle --
magick -density "$DPI" -units PixelsPerInch \
  "$GUIDE" "${PAGES[@]}" -compress Zip "$OUT.sheets.pdf"

echo
echo "=== done ============================================================"
echo "print this : $OUT.sheets.pdf   ($((N_SHEETS+1)) pages, 100% scale)"
if [ ${#BLANKS[@]} -gt 0 ]; then
  echo "blank sheets: ${#BLANKS[@]} of $N_SHEETS carry no ink -- ${BLANKS[*]}"
  echo "              (they are labelled 'blank, skip'; leaving them out of the"
  echo "               print job saves paper without changing the layout)"
fi

echo "large-format: $OUT.full.pdf    (single $(inch "$MAP_W")in vector page)"
echo "editable    : $OUT.svg"
