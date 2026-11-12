# Deploy rules

`scripts/deploy.sh` runs the chain and its gates. This file says why each gate exists. Each rule was earned by a real
deploy of the repo this template comes from. When a deploy of yours earns a rule, add the rule here and the incident
to `DEPLOY-LEDGER.md`.

## One-time setup (the owner does this)

1. **Create the Pages project:** `npx --yes wrangler pages project create <project> --production-branch main`. Put
   the name in `PROJECT` at the top of `scripts/deploy.sh`, and the site's address in `SITE_URL`.
2. **Protect it before it holds anything.** For a private site, create the Access application and its allow policy
   first, and only then add the custom domain and its DNS record.
3. **Close the per-deployment gap.** Every deployment also gets its own `<hash>.<project>.pages.dev` address. An
   Access application on the custom domain does not cover those addresses. Turn on the Access policy of the Pages
   project itself (the project's settings in the dashboard), so that they are covered too. Step 6 of the script
   checks this after every deploy.
4. **Keep the deploy credential out of the agent's environment.** The hook stops an accident. The credential is the
   boundary.
5. **For a public site,** set `PROTECTED=0`. The script then skips the 302 check. Every other gate still runs.

The Cloudflare dashboard changes over time. Check each step against Cloudflare's current documentation.

## Build rules

- **Never deploy the repo root.** It holds `node_modules`, `.claude/`, `.agents/`, scripts and drafts. The script builds a dist
  that holds only the hub pages, `md.html`, the files under `site/` and the `SHIP` folders. The `LEAK` gate checks
  the root of the dist against that list. At any depth it refuses `node_modules`, `.claude`, `.agents`, `.codex`, `.git`, a symlink, and
  an environment file (`.env`, `.env.*`) other than `.env.example`, `.env.sample` and `.env.template`.
- **The dist is pinned to HEAD** (`git archive`). Another session's uncommitted drafts never ship, and neither do
  yours. Commit first, then build.
- **The baseline is the last deploy by anyone.** Several sessions can deploy on one day. The ledger's top entry names
  the baseline, and before the upload the script checks that this entry is still the newest production deployment.
- **Name the delta file by file.** The file count is a tripwire: an added file that you cannot name is a leak or a
  regression until you prove otherwise.
- **Gate the deploy on content, not on git.** A commit can fall off the branch when another session commits on the
  older sha, and `git log -1` right after your commit does not show it. Pass a `--marker` for each change, and check
  `git merge-base --is-ancestor <sha> HEAD`.
- **Scan the delta for credentials,** not the whole dist. Older archives may hold known, ruled hits. A new hit is a
  stop.
- **Exclude by name.** A file that must stay in git but must not ship (a licence that forbids posting, a file over
  25 MiB, a capture that holds a token) goes in `EXCL`. The script checks that each one is in the stage and absent
  from the dist, so a moved file cannot ship silently. Only a file under `docs/assets/`, or one the hub does not list, can be
  excluded: the hub and its search index carry the title, the note and the whole text of every doc they list, so the
  script stops with `EXCLUDED_IN_HUB` for a listed doc.
- **Archived captures are served inert.** A raw capture under `docs/assets/` keeps the origin's scripts. `site/_headers`
  gives that folder a policy with no script and no network access. Access does not replace this: it identifies the
  viewer, and it does not stop a third-party script that runs in the viewer's signed-in session. Do not remove
  scripts from an archive to make it safe; keep each capture byte-identical. The policy does not stop a
  `<meta http-equiv="refresh">` in a capture. Adding `sandbox` to the policy would, but it may also stop the
  browser's PDF viewer; test both before you add it. `md.html` refuses any path under `docs/assets/`.
- **A `_headers` pattern takes one splat, at the end.** A pattern with two splats, or with a file extension after
  the splat, does not match. The zone's browser cache setting can also replace your `Cache-Control` for the file
  types Cloudflare caches by default (PDF, images, SVG). Measure a header in a browser before you rely on it.
- **A marker that is right inside the repo can be a defect on a public page.** `[FILL]` is the rule against invented
  numbers. A page that leaves the repo for an outside reader must resolve each one: drop the claim or get the real
  figure. Check a public build for what it must not contain as well as for what it must.
- **Build the hub after the commit, never before.** `build-hub.py` lists tracked files and takes dates from git. A doc
  that is untracked when the hub is built is missing from the committed pages, and the `--check` gate then stops the
  deploy.
- **Remove the work folder after the live probes,** not before. The log and the delta list in it are what the ledger
  entry needs.

## Verify live

- **Check the new deployment's own host first.** On a protected site, each kind of path must answer `302`. A `200`
  means the corpus is public: stop and tell the owner.
- **Judge a page by its body, never by its status.** A site with a fallback page answers `200` for a missing path.
  Look for the `<title>` or a marker string.
- **Probe in a signed-in browser, in a tab you opened.** Put the `location.origin` check in the same evaluate as the
  fetch, so that a sign-in page cannot pass as content. Close only your own tab.
- **Fetch with `cache: 'no-store'`,** and compare byte counts for a file that is not HTML.
- **One gate per line, each ending in `|| exit 1`.** A gate whose output is piped to `tail` passes on the exit code
  of `tail`, and a trailing `|| true` hides every gate before it.
