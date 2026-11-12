#!/usr/bin/env bash
# Build, gate and (with --deploy) deploy this repo's site to one Cloudflare Worker with static assets, using the cf CLI.
#
#   scripts/deploy.sh                                  # dry run: stage, dist, every gate, and cf's own dry run
#   scripts/deploy.sh --marker docs/x.md:'a string'    # also fail unless that file in the dist holds that string
#   scripts/deploy.sh --deploy                         # the same, then upload and probe the site
#   scripts/deploy.sh --first                          # the first deploy: no baseline in DEPLOY-LEDGER.md yet
#   scripts/deploy.sh --baseline <sha>                 # override the baseline HEAD (default: the ledger's top entry)
#
# Every gate is a stop. The rule behind each gate is in .agents/skills/deploy-site/RULES.md. Everything temporary
# lives in one folder ($WORK, printed first), and nothing is written into the repo.
# --deploy is the owner's command. Never run it on your own initiative.
#
# The Worker has no public address except the site's own: its workers.dev address and its Version URLs are off. On a
# protected site the first deploy (--first) attaches no domain at all, so that the owner can put Cloudflare Access on
# the Worker before anything is reachable. Every later deploy attaches the domain.
set -euo pipefail

# ---- Configuration: edit these values. ----
WORKER="my-site"                      # the Worker's name
SITE_URL="https://docs.example.com"   # the address people open; its hostname becomes the Worker's custom domain
PROTECTED=1                           # 1: the site is behind Cloudflare Access, and every path must answer 302
ACCOUNT_ID=""                         # the Cloudflare account id; needed when your login has more than one account
SHIP=(docs reports)                   # the folders that ship, beside the hub pages and md.html
MAX_FILES=20000                       # Cloudflare's limit on files in one Worker version: 20,000 free, 100,000 paid
CF_VERSION="1.0.0-beta.31"            # the cf CLI is a beta: pin a version, and change the pin on purpose
COMPAT_DATE="2026-11-12"              # the Worker's compatibility date
# Name exclusions: files or folders that stay in git but out of the dist (a licence, the size, or a token that the
# scan flags). Paths are relative to the repo root. Each one must be in the stage and must be absent from the dist.
EXCL=()
# -------------------------------------------

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
PAGES=(index.html docs.html changelog.html 404.html search-index.json md.html hub.css hub.js)   # root files that ship as they are
STATIC=(_headers _redirects)   # copied from site/ to the root of the dist

# 1. Pre-flight. The dist is pinned to HEAD, so the generated hub pages must be committed and current.
for f in "${PAGES[@]}" "${STATIC[@]/#/site/}" site/manifest.json; do
  git diff --quiet HEAD -- "$f" || die "$f has uncommitted changes. Commit it, then rerun."
done
python3 -I scripts/build-hub.py --check || die "the hub pages are stale. Run python3 -I scripts/build-hub.py after the last content commit, commit the five files it writes, then rerun."
REV=$(git rev-parse HEAD)
EMPTY_TREE=$(git hash-object -t tree /dev/null)
BASE_DEPLOY=""
if [ "$FIRST" = 1 ]; then
  if grep -qE 'at deploy `[0-9a-f-]+`, HEAD `[0-9a-f]+`' DEPLOY-LEDGER.md; then die "--first, but DEPLOY-LEDGER.md already has a deploy entry"; fi
  BASE=$EMPTY_TREE
else
  LEDGER_TOP=$(grep -m1 -oE 'at deploy `[0-9a-f-]+`, HEAD `[0-9a-f]+`' DEPLOY-LEDGER.md) || die "no deploy entry in DEPLOY-LEDGER.md. For the first deploy, pass --first."
  BASE_DEPLOY=$(echo "$LEDGER_TOP" | sed -E 's/at deploy `([0-9a-f-]+)`.*/\1/')
  [ -n "$BASE" ] || BASE=$(echo "$LEDGER_TOP" | sed -E 's/.*HEAD `([0-9a-f]+)`/\1/')
  git merge-base --is-ancestor "$BASE" "$REV" || die "baseline $BASE is not an ancestor of HEAD $REV"
fi
WORK=$(mktemp -d "${TMPDIR:-/tmp}/deploy-site.XXXXXX")
STAGE=$WORK/stage; DIST=$WORK/dist; mkdir -p "$STAGE" "$DIST"
# A run that stops before the upload removes its own folder. After the upload the folder stays, even on a stop:
# its deploy.log and delta.txt are what the ledger entry needs.
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
leak=$(find "$DIST" \( -name node_modules -o -name .claude -o -name .agents -o -name .codex -o -name .git -o \( \( -name .env -o -name '.env.*' \) \
  ! -name .env.example ! -name .env.sample ! -name .env.template \) \) | head -3)
[ -z "$leak" ] || die "LEAK: $leak"
# A symlink would ship a file that the delta and the scan never read.
links=$(find "$DIST" -type l | head -3)
[ -z "$links" ] || die "SYMLINK in the dist (commit the file itself, or exclude the link by name): $links"
over=$(find "$DIST" -type f -size +25M)
[ -z "$over" ] || die "OVERSIZE (the limit is 25 MiB a file; exclude it by name, never re-encode it): $over"
count=$(find "$DIST" -type f | wc -l | tr -d ' ')
[ "$count" -le "$MAX_FILES" ] || die "TOO_MANY_FILES: $count files, and MAX_FILES is $MAX_FILES"
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
echo "files: $count"

# 5. The Worker's config, written into the work folder from the values at the top of this script. cf reads
#    cloudflare.config.ts and not a Wrangler config. This one is a plain object with no import, so cf needs no install.
HOST=${SITE_URL#*://}; HOST=${HOST%%/*}
DOMAINS=""
if [ "$PROTECTED" = 0 ] || [ "$FIRST" = 0 ]; then DOMAINS="domains: [\"$HOST\"],"; fi
cat > "$WORK/cloudflare.config.ts" <<CONFIG
export default {
	worker: {
		name: "$WORKER",
		compatibilityDate: "$COMPAT_DATE",
		workersDev: false,
		previewUrls: false,
		$DOMAINS
		assets: { notFoundHandling: "404-page" },
	},
};
CONFIG
if [ -n "$ACCOUNT_ID" ]; then export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"; fi
CF=(npx --yes "cf@$CF_VERSION")
(cd "$WORK" && "${CF[@]}" deploy dist --dry-run) > "$WORK/cf-dry-run.log" 2>&1 || { tail -8 "$WORK/cf-dry-run.log"; die "cf deploy --dry-run failed (see $WORK/cf-dry-run.log)"; }
echo "cf dry run: ok (${DOMAINS:-no domain on this deploy})"

if [ "$DEPLOY" = 0 ]; then
  echo "DRY_RUN_OK: every gate passed; stopped before the upload. Remove the work folder when done: rm -rf $WORK"
  exit 0
fi

# 6. Deploy. The ledger's version must still be the one serving: another session may have deployed since.
if [ "$FIRST" = 0 ]; then
  (cd "$WORK" && "${CF[@]}" workers deployments list --worker "$WORKER") > "$WORK/deployments.txt" 2>&1 \
    || die "could not list deployments (see $WORK/deployments.txt)"
  newest=$(python3 -I -c 'import json,sys
t=open(sys.argv[1],encoding="utf-8").read(); d=json.loads(t[t.index("{"):])
print(d["deployments"][0]["versions"][0]["version_id"])' "$WORK/deployments.txt" 2>/dev/null) || newest=""
  [ "$newest" = "$BASE_DEPLOY" ] || die "the version now serving is ${newest:-unknown}, not the ledger's $BASE_DEPLOY. Someone deployed without a ledger entry, or the ledger is behind: reconcile first."
fi
UPLOADED=1
(cd "$WORK" && "${CF[@]}" deploy dist --message "$REV") 2>&1 | tee "$WORK/deploy.log"
VERSION=$(grep -oE 'Current Version ID: [0-9a-f-]+' "$WORK/deploy.log" | tail -1 | awk '{print $4}') || true
[ -n "$VERSION" ] || die "no version id in $WORK/deploy.log"
echo "DEPLOYED version $VERSION  (REV $REV)"

# 7. Protection. With Access on the Worker, every kind of path answers 302 to a request that is not signed in. A 200
#    means the corpus is public.
if [ "$PROTECTED" = 1 ] && [ "$FIRST" = 1 ]; then
  echo "FIRST_DEPLOY: no domain is attached and the Worker has no public address. Now put Access on the Worker"
  echo "(.agents/skills/deploy-site/RULES.md, one-time setup, step 3), record this deploy in DEPLOY-LEDGER.md, and deploy again."
elif [ "$PROTECTED" = 1 ]; then
  probe() { (cd "$DIST" && find "$@" -type f | sort | head -1); }
  PATHS=("" "md.html" "$(probe "${SHIP[0]}" -name '*.md')" "$(probe "${SHIP[@]}" -not -name '*.md')" "no-such-page")
  status() { curl -sI --max-time 15 "$SITE_URL/$1" | head -1 | awk '{print $2}'; }
  # A new domain needs its DNS record and certificate first: wait for any answer, up to five minutes.
  for _ in $(seq 1 30); do [ -n "$(status "")" ] && break; sleep 10; done
  fail=0
  for p in "${PATHS[@]}"; do
    code=$(status "$p")
    echo "  access ${code:-none} /$p"
    [ "$code" = 302 ] || fail=1
  done
  [ "$fail" = 0 ] || die "ACCESS: a path did not answer 302 on $SITE_URL. The corpus may be public: check the Access application on the Worker now."
  echo "ACCESS_OK ${#PATHS[@]}/${#PATHS[@]} 302"
fi
[ "$PROTECTED" = 1 ] || echo "PROTECTED=0: the 302 check was skipped. This site is public."
echo "Next: probe the changed content on $SITE_URL, prepend the DEPLOY-LEDGER.md entry, commit it with a message"
echo "that starts 'Deploy <version id>:', then: rm -rf $WORK"
