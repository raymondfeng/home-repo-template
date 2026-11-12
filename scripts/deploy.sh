#!/usr/bin/env bash
# Build, gate and (with --deploy) deploy this repo's site to one Cloudflare Pages project.
#
#   scripts/deploy.sh                                  # dry run: stage, dist, every gate; stops before wrangler
#   scripts/deploy.sh --marker docs/x.md:'a string'    # also fail unless that file in the dist holds that string
#   scripts/deploy.sh --deploy                         # the same, then upload and probe the new deployment
#   scripts/deploy.sh --first                          # the first deploy: no baseline in DEPLOY-LEDGER.md yet
#   scripts/deploy.sh --baseline <sha>                 # override the baseline HEAD (default: the ledger's top entry)
#
# Every gate is a stop. The rule behind each gate is in .claude/skills/deploy-site/RULES.md. Everything temporary
# lives in one folder ($WORK, printed first), and nothing is written into the repo.
# --deploy is the owner's command. Never run it on your own initiative.
set -euo pipefail

# ---- Configuration: edit these four values. ----
PROJECT="my-site"                     # the Pages project name
SITE_URL="https://docs.example.com"   # the address people open
PROTECTED=1                           # 1: the site is behind Cloudflare Access, and every path must answer 302
SHIP=(docs reports)                   # the folders that ship, beside the hub pages and md.html
# Name exclusions: files or folders that stay in git but out of the dist (a licence, the size, or a token that the
# scan flags). Paths are relative to the repo root. Each one must be in the stage and must be absent from the dist.
EXCL=()
# ------------------------------------------------

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
DEPLOY=0; FIRST=0; BASE=""; MARKERS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --deploy) DEPLOY=1 ;;
    --first) FIRST=1 ;;
    --baseline) BASE="$2"; shift ;;
    --marker) MARKERS+=("$2"); shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done
die() { echo "STOP: $*" >&2; exit 1; }
PAGES=(index.html docs.html changelog.html search-index.json md.html hub.css hub.js)   # root files that ship as they are
STATIC=(_headers _redirects)   # copied from site/ to the root of the dist

# 1. Pre-flight. The dist is pinned to HEAD, so the generated hub pages must be committed and current.
for f in "${PAGES[@]}" "${STATIC[@]/#/site/}" site/manifest.json; do
  git diff --quiet HEAD -- "$f" || die "$f has uncommitted changes. Commit it, then rerun."
done
python3 -I scripts/build-hub.py --check || die "the hub pages are stale. Run python3 -I scripts/build-hub.py after the last content commit, commit the four files it writes, then rerun."
REV=$(git rev-parse HEAD)
EMPTY_TREE=$(git hash-object -t tree /dev/null)
BASE_DEPLOY=""
if [ "$FIRST" = 1 ]; then
  if grep -qE 'at deploy `[0-9a-f]+`, HEAD `[0-9a-f]+`' DEPLOY-LEDGER.md; then die "--first, but DEPLOY-LEDGER.md already has a deploy entry"; fi
  BASE=$EMPTY_TREE
else
  LEDGER_TOP=$(grep -m1 -oE 'at deploy `[0-9a-f]+`, HEAD `[0-9a-f]+`' DEPLOY-LEDGER.md) || die "no deploy entry in DEPLOY-LEDGER.md. For the first deploy, pass --first."
  BASE_DEPLOY=$(echo "$LEDGER_TOP" | sed -E 's/at deploy `([0-9a-f]+)`.*/\1/')
  [ -n "$BASE" ] || BASE=$(echo "$LEDGER_TOP" | sed -E 's/.*HEAD `([0-9a-f]+)`/\1/')
  git merge-base --is-ancestor "$BASE" "$REV" || die "baseline $BASE is not an ancestor of HEAD $REV"
fi
WORK=$(mktemp -d "${TMPDIR:-/tmp}/deploy-site.XXXXXX")
STAGE=$WORK/stage; DIST=$WORK/dist; mkdir -p "$STAGE" "$DIST"
# A run that stops before the upload removes its own folder. After the upload the folder stays, even on a stop:
# its wrangler.log and delta.txt are what the ledger entry needs.
UPLOADED=0
trap 'st=$?; if [ $st -ne 0 ] && [ "$UPLOADED" = 0 ]; then rm -rf "$WORK"; echo "(removed $WORK)" >&2; fi' EXIT
echo "WORK=$WORK"
echo "REV=$REV  BASE=$BASE${BASE_DEPLOY:+ (ledger deploy $BASE_DEPLOY)}"
untracked=$(git ls-files --others --exclude-standard "${SHIP[@]}" | wc -l | tr -d ' ')
echo "untracked under ${SHIP[*]}: $untracked (not shipped: the dist is pinned to HEAD)"

# 2. Stage and dist. Never deploy the repo root: build a dist that holds only what ships.
git archive "$REV" | tar -x -C "$STAGE"
for f in "${PAGES[@]}"; do cp "$STAGE/$f" "$DIST/"; done
for f in "${STATIC[@]}"; do cp "$STAGE/site/$f" "$DIST/$f"; done
for d in "${SHIP[@]}"; do
  [ -d "$STAGE/$d" ] || die "SHIP folder not in HEAD: $d"
  rsync -a --exclude .DS_Store --exclude .gitkeep "$STAGE/$d" "$DIST/"
done
for x in ${EXCL[@]+"${EXCL[@]}"}; do
  [ -e "$DIST/$x" ] || die "name exclusion not in the stage: $x (moved or renamed? fix the list)"
  rm -rf "${DIST:?}/$x"
done

# 3. Gates.
# The hub pages and the search index are built from every tracked doc. A doc that is excluded from the dist would
# still ship its title, its note and its whole text through them. Captures under docs/assets/ are not in the hub.
for x in ${EXCL[@]+"${EXCL[@]}"}; do
  if grep -qF -e "data-path=\"$x\"" -e "data-path=\"${x%/}/" "$DIST/docs.html"; then
    die "EXCLUDED_IN_HUB $x: the hub lists it, so its text would ship in search-index.json. Move it under docs/assets/, or take it out of git."
  fi
done
# The dist is built from an allow-list, so the root may hold only the pages, the files from site/ and the SHIP folders.
# Deeper down, an archived capture may hold a folder named scripts/ or a file named .env.example; those are content.
for e in "$DIST"/* "$DIST"/.[!.]*; do
  [ -e "$e" ] || continue
  n=$(basename "$e"); ok=0
  for a in "${PAGES[@]}" "${STATIC[@]}" "${SHIP[@]}"; do if [ "$n" = "$a" ]; then ok=1; fi; done
  [ "$ok" = 1 ] || die "LEAK: $n is at the root of the dist and is not on the allow-list"
done
# An environment file is refused at any depth, except the three names that are templates by convention. To ship
# another one, the owner adds it to this list; to hold one back, put it in EXCL.
leak=$(find "$DIST" \( -name node_modules -o -name .claude -o -name .git -o \( \( -name .env -o -name '.env.*' \) \
  ! -name .env.example ! -name .env.sample ! -name .env.template \) \) | head -3)
[ -z "$leak" ] || die "LEAK: $leak"
# A symlink would ship a file that the delta and the scan never read.
links=$(find "$DIST" -type l | head -3)
[ -z "$links" ] || die "SYMLINK in the dist (commit the file itself, or exclude the link by name): $links"
over=$(find "$DIST" -type f -size +25M)
[ -z "$over" ] || die "OVERSIZE (the Pages limit is 25 MiB a file; exclude it by name, never re-encode it): $over"
for x in ${EXCL[@]+"${EXCL[@]}"}; do
  if [ -e "$DIST/$x" ]; then die "EXCLUDED_PRESENT $x"; fi
done
echo "name exclusions: ${#EXCL[@]} present in the stage, absent from the dist"
for f in "${PAGES[@]}"; do
  cmp -s "$DIST/$f" <(git show "$REV:$f") || die "$f in the dist differs from $REV"
done
for m in ${MARKERS[@]+"${MARKERS[@]}"}; do
  path=${m%%:*}; str=${m#*:}
  grep -qF -- "$str" "$DIST/$path" 2>/dev/null || die "MARKER_MISSING $path: $str"
done
echo "markers: ${#MARKERS[@]} found"

# 4. The delta against the baseline, and the credential scan over it.
shipped() { while read -r f; do if [ -f "$DIST/$f" ]; then echo "$f"; fi; done; }
git diff --no-renames --name-only --diff-filter=AMT "$BASE" "$REV" | shipped > "$WORK/delta.txt"
added=$(git diff --no-renames --name-only --diff-filter=A "$BASE" "$REV" | shipped | wc -l | tr -d ' ')
removed=$(git diff --no-renames --name-only --diff-filter=D "$BASE" "$REV" | wc -l | tr -d ' ')
echo "delta vs $BASE: $(wc -l < "$WORK/delta.txt" | tr -d ' ') shipped files added or modified ($added added), $removed removed from git"
echo "  list: $WORK/delta.txt. Name every added file before you deploy."
python3 -I scripts/credscan.py --controls || die "credential scan controls failed"
python3 -I scripts/credscan.py "$DIST" "$WORK/delta.txt" || die "CREDENTIAL HIT in the delta. A hit is a stop; an allowance is the owner's ruling."
echo "files: $(find "$DIST" -type f | wc -l | tr -d ' ')"

if [ "$DEPLOY" = 0 ]; then
  echo "DRY_RUN_OK: every gate passed; stopped before wrangler. Remove the work folder when done: rm -rf $WORK"
  exit 0
fi

# 5. Deploy. The baseline must still be the newest Production deployment: another session may have deployed since.
# The deployment's host is <hash>.<subdomain>.pages.dev. The subdomain is usually the project name, but the pattern
# does not assume it.
HOST_RE='https://[0-9a-f]+\.[a-z0-9-]+\.pages\.dev'
if [ "$FIRST" = 0 ]; then
  npx --yes wrangler pages deployment list --project-name "$PROJECT" --environment production > "$WORK/deployments.txt" 2>&1 \
    || die "could not list deployments (see $WORK/deployments.txt)"
  newest=$(grep -m1 -oE "$HOST_RE" "$WORK/deployments.txt" | sed -E 's#https://([0-9a-f]+)\..*#\1#') || true
  [ "$newest" = "$BASE_DEPLOY" ] || die "the newest Production deployment is ${newest:-unknown}, not the ledger's $BASE_DEPLOY. Someone deployed without a ledger entry, or the ledger is behind: reconcile first."
fi
UPLOADED=1
npx --yes wrangler pages deploy "$DIST" --project-name "$PROJECT" --branch main --commit-dirty=true 2>&1 | tee "$WORK/wrangler.log"
URL=$(grep -oE "$HOST_RE" "$WORK/wrangler.log" | tail -1) || true
[ -n "$URL" ] || die "no deployment URL in $WORK/wrangler.log"
echo "DEPLOYED $URL  (REV $REV)"

# 6. The new deployment's own host. Each deployment gets a <hash>.<project>.pages.dev address, which an Access
#    application on the custom domain does not cover. On a protected site every kind of path must redirect to
#    sign-in (302) and never serve (200).
if [ "$PROTECTED" = 1 ]; then
  sleep 12
  probe() { (cd "$DIST" && find "$@" -type f | sort | head -1); }
  PATHS=("" "md.html" "$(probe "${SHIP[0]}" -name '*.md')" "$(probe "${SHIP[@]}" -not -name '*.md')")
  fail=0
  for p in "${PATHS[@]}"; do
    code=$(curl -sI "$URL/$p" | head -1 | awk '{print $2}')
    echo "  access $code /$p"
    [ "$code" = 302 ] || fail=1
  done
  [ "$fail" = 0 ] || die "ACCESS: a path did not answer 302 on $URL. The corpus may be public: check the Pages project's Access policy now."
  echo "ACCESS_OK ${#PATHS[@]}/${#PATHS[@]} 302"
fi
[ "$PROTECTED" = 1 ] || echo "PROTECTED=0: the 302 check was skipped. This site is public."
echo "Next: probe the changed content on $SITE_URL, prepend the DEPLOY-LEDGER.md entry, commit it with a message"
echo "that starts 'Deploy <hash>:', then: rm -rf $WORK"
