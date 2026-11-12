#!/usr/bin/env bash
# Check, finalize and export one deck project to .pptx, and (with --publish) put the file under docs/deck/.
#
#   scripts/build-deck.sh projects/<name>_ppt169_<date>             # check, split notes, finalize, export
#   scripts/build-deck.sh projects/<name>_ppt169_<date> --publish   # the same, then copy the export to docs/deck/<name>.pptx
#
# A deck is a folder of hand-edited slides: one SVG for each slide under svg_output/, and one notes file,
# notes/total.md, with a "# <slide file name>" heading for each slide. The steps are the ppt-master skill's own
# scripts (.agents/skills/ppt-master), run in its Quick Generate mode, which needs no design spec. Every step is a gate.
# The export needs python-pptx (pip install python-pptx).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
SK=.agents/skills/ppt-master/scripts
P="${1:?give a project folder, e.g. projects/example-deck_ppt169_20261112}"; P="${P%/}"
PUBLISH=0; [ "${2:-}" = "--publish" ] && PUBLISH=1
die() { echo "STOP: $*" >&2; exit 1; }
[ -d "$P/svg_output" ] || die "$P has no svg_output/ folder"
[ -f "$P/notes/total.md" ] || die "$P has no notes/total.md"
NAME=$(basename "$P"); NAME=${NAME%%_ppt*}

# The notes and the slides must name the same pages, one to one. A renamed slide otherwise loses its notes silently.
slides=$(cd "$P/svg_output" && ls *.svg | sed 's/\.svg$//' | sort)
notes=$(grep -E '^# ' "$P/notes/total.md" | sed 's/^# //' | sort)
[ "$slides" = "$notes" ] || die "ROSTER: the slide files and the '# ' headings in notes/total.md differ:
$(diff <(echo "$slides") <(echo "$notes") || true)"
# The footer of slide N of T reads "PNN / TT".
total=$(echo "$slides" | wc -l | tr -d ' '); n=0
for s in $slides; do
  n=$((n + 1)); want=$(printf 'P%02d / %02d' "$n" "$total")
  grep -qF "$want" "$P/svg_output/$s.svg" || die "FOOTER: $s.svg does not hold '$want'. After a slide is added, removed or moved, fix the file numbers, the footers, the kickers and the notes headings together."
done
echo "roster: $total slides, notes and footers agree"

python3 "$SK/attribution_guard.py" || die "the ppt-master copy failed its own integrity check. Restore it with python3 -I scripts/update-skills.py"
python3 "$SK/svg_quality_checker.py" "$P" --quick-generate --stage final --json > "$P/validation-check.log" 2>&1 \
  || { grep -E 'ERROR' "$P/validation-check.log" | head -20; die "CHECK: the quality checker found errors (full log: $P/validation-check.log)"; }
echo "check: 0 errors, $(grep -c 'WARN\]' "$P/validation-check.log" || true) warning lines (log: $P/validation-check.log)"
python3 "$SK/total_md_split.py" "$P" > /dev/null || die "the notes split failed"
python3 "$SK/finalize_svg.py" "$P" > /dev/null || die "finalize failed"
python3 "$SK/svg_to_pptx.py" "$P" --quick-generate --with-notes > "$P/validation-export.log" 2>&1 \
  || { tail -12 "$P/validation-export.log"; die "EXPORT failed (full log: $P/validation-export.log)"; }
OUT=$(ls -t "$P"/exports/*.pptx | head -1)
[ -s "$OUT" ] || die "no export under $P/exports/"
echo "exported: $OUT"

if [ "$PUBLISH" = 1 ]; then
  mkdir -p docs/deck/history
  DEST="docs/deck/$NAME.pptx"
  if [ -f "$DEST" ]; then cp "$DEST" "docs/deck/history/${NAME}_pre-$(date +%Y%m%d-%H%M%S).pptx"; fi
  cp "$OUT" "$DEST"
  echo "published: $DEST (the previous file, if any, is under docs/deck/history/). Commit it, then rebuild the hub."
fi
