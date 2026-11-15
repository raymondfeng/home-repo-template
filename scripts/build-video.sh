#!/usr/bin/env bash
# Check and render one video project, make a contact sheet, and (with --publish) put the file under docs/video/.
#
#   scripts/build-video.sh video/<name>             # check, render, verify the file, write a contact sheet
#   scripts/build-video.sh video/<name> --publish   # the same, then copy the render to docs/video/<name>.mp4
#
# A video is a HyperFrames project: index.html mounts one scene file for each scene from compositions/. The steps are
# the hyperframes command's own (through npx, at a pinned version), and every step is a gate. It needs Node, Chrome
# and ffmpeg. The --publish step is the owner's word: the cut is reviewed first (video/README.md, the gates).
set -euo pipefail
HF_VERSION="0.9.53"   # pin the version, and change the pin on purpose
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
V="${1:?give a video folder, e.g. video/example-video}"; V="${V%/}"
PUBLISH=0; [ "${2:-}" = "--publish" ] && PUBLISH=1
die() { echo "STOP: $*" >&2; exit 1; }
cd "$REPO/$V" 2>/dev/null || die "$V is not a folder"
[ -f index.html ] || die "$V has no index.html"
[ -f BRIEF.md ] || die "BRIEF: $V has no BRIEF.md. Write the brief, and name each real capture in it, before a scene is built."
[ -f STORYBOARD.md ] || die "STORYBOARD: $V has no STORYBOARD.md. Agree the scenes before they are built."
command -v ffmpeg > /dev/null || die "ffmpeg is not installed"
NAME=$(basename "$V"); HF=(npx --yes "hyperframes@$HF_VERSION"); export HYPERFRAMES_SKIP_SKILLS=1
mkdir -p renders reviews

# Each scene that index.html mounts must exist, carry the same id as its host, and register its timeline under that
# id. The HyperFrames check passes a scene that does not: it then renders as a still frame.
python3 -I -c 'import re,sys,pathlib
root=open("index.html",encoding="utf-8").read(); bad=[]; n=0
for tag in re.findall(r"<div\b[^>]*data-composition-src=[^>]*>", root, re.S):
    n+=1
    hid=re.search(r"data-composition-id=\"([^\"]+)\"", tag); src=re.search(r"data-composition-src=\"([^\"]+)\"", tag)
    f=pathlib.Path(src.group(1))
    if not f.is_file(): bad.append("%s is mounted and does not exist" % f); continue
    t=f.read_text(encoding="utf-8"); h=hid.group(1) if hid else "?"
    if "data-composition-id=\"%s\"" % h not in t: bad.append("%s: its root does not have the id of its host, %s" % (f,h))
    if not re.search(r"__timelines\[\s*[\"\x27]%s[\"\x27]\s*\]\s*=" % re.escape(h), t): bad.append("%s: it does not register window.__timelines[\"%s\"]" % (f,h))
if "__timelines[\"main\"]" not in root and "__timelines[\x27main\x27]" not in root: bad.append("index.html does not register window.__timelines[\"main\"]")
print("scenes: %d mounted" % n)
sys.exit("\n".join(bad) if bad else 0)' || die "SCENES: a scene is not wired to its host (see the lines above)"

"${HF[@]}" check --json > renders/check.json 2> renders/check.log || true
python3 -I -c 'import json,sys
t=open(sys.argv[1],encoding="utf-8").read(); i=t.find("{")
if i<0: sys.exit("the check printed no report (see renders/check.log)")
d=json.loads(t[i:]); cats=[k for k,v in d.items() if isinstance(v,dict) and "errorCount" in v]
errs=sum(d[k]["errorCount"] for k in cats); warns=sum(d[k]["warningCount"] for k in cats)
for k in cats:
    for f in d[k].get("findings") or []:
        if isinstance(f,dict) and f.get("severity") in ("error","warning"): print("  %s %s: %s" % (f["severity"],f.get("code"),str(f.get("message"))[:160]))
print("check: %d errors, %d warnings" % (errs,warns))
sys.exit(0 if d.get("ok") and errs==0 else 1)' renders/check.json || die "CHECK: the HyperFrames check found errors (report: $V/renders/check.json). Each finding has a Fix line."

OUT="renders/$NAME.mp4"
"${HF[@]}" render --output "$OUT" > renders/render.log 2>&1 || { tail -8 renders/render.log; die "RENDER failed (log: $V/renders/render.log)"; }
[ -s "$OUT" ] || die "no file at $V/$OUT"
want=$(python3 -I -c 'import re,sys
m=re.search(r"data-composition-id=\"main\"[^>]*data-duration=\"([0-9.]+)\"", open("index.html",encoding="utf-8").read(), re.S)
print(m.group(1) if m else "")')
got=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
[ -n "$want" ] || die "index.html has no root with data-composition-id=\"main\" and a data-duration"
python3 -I -c 'import sys; sys.exit(0 if abs(float(sys.argv[1])-float(sys.argv[2]))<=0.2 else 1)' "$want" "$got" || die "LENGTH: the render is $got s, and the root declares $want s"
size=$(wc -c < "$OUT" | tr -d ' ')
echo "rendered: $V/$OUT ($got s, $((size / 1024)) KB)"

# One frame for each second, as one image. Read it before the storyboard, then write REVIEW.md beside it.
SHEET="reviews/contact-sheet.jpg"
ffmpeg -v error -y -i "$OUT" -vf "fps=1,scale=480:-1,tile=4x$(python3 -I -c 'import math,sys; print(max(1, math.ceil(float(sys.argv[1]) / 4)))' "$got")" -frames:v 1 "$SHEET" || die "the contact sheet failed"
echo "contact sheet: $V/$SHEET"

if [ "$PUBLISH" = 1 ]; then
  [ "$size" -le $((25 * 1024 * 1024)) ] || die "OVERSIZE: the render is over 25 MiB, the site's limit for one file. Render at a lower bitrate."
  mkdir -p "$REPO/docs/video"
  cp "$OUT" "$REPO/docs/video/$NAME.mp4"
  echo "published: docs/video/$NAME.mp4. Commit it, then rebuild the hub."
fi
