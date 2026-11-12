# Deploy rules

`scripts/deploy.sh` runs the chain and its gates. This file says why each gate exists. The build rules were earned by
real deploys of the repo this template comes from. The Worker rules were measured on 2026-11-12 with two throwaway
Workers and cf `1.0.0-beta.31`. When a deploy of yours earns a rule, add the rule here and the incident to
`DEPLOY-LEDGER.md`.

The site is one Cloudflare Worker with static assets and no code, deployed with the `cf` CLI. The Worker has no
public address except the site's own: its `workers.dev` address and its Version URLs are off.

## One-time setup (the owner does this)

For a private site, the order matters: the Worker exists first, Access goes on it second, and the domain comes last.
Access takes about ten seconds to apply, so a domain that is attached first is public for that time.

1. **Set the values** at the top of `scripts/deploy.sh`: `WORKER`, `SITE_URL`, `PROTECTED`, and `ACCOUNT_ID` if your
   login has more than one account. The hostname of `SITE_URL` must be in a zone of that account. Sign in once with
   `npx cf@<CF_VERSION> auth login`. `cf` needs Node 22.23, 24.22 or 26.12, or later in each line.
2. **First deploy:** `bash scripts/deploy.sh --first`, then the same with `--deploy`. On a protected site this creates
   the Worker with no domain, so nothing is reachable yet.
3. **Put Access on the Worker.** One application of type `self_hosted` with one destination of type `worker` covers
   every address the Worker has or gets. Find the Worker's id, then create the application:

   ```bash
   npx cf@<CF_VERSION> workers scripts search --name <WORKER>      # the "id" field is the Worker's id
   npx cf@<CF_VERSION> zero-trust access applications create --body '{
     "type": "self_hosted",
     "name": "<a name for the site>",
     "destinations": [{ "type": "worker", "worker_id": "<the id>" }],
     "policies": [{ "name": "readers", "decision": "allow",
                    "include": [{ "email_domain": { "domain": "<your-company.com>" } }] }]
   }'
   ```

   The same can be done in the dashboard: the Worker's page, then **Access**. For a rule other than an email domain,
   use the dashboard or Cloudflare's Access documentation; only the email-domain form was run here.
4. **Record the first deploy** in `DEPLOY-LEDGER.md`, with the version id that the script printed, and commit it.
5. **Deploy again**, without `--first`. This attaches the domain, and the script then checks that every kind of path
   answers `302`. The DNS record and the certificate are created by the deploy.
6. **Keep the deploy credential out of the agent's environment.** The hook stops an accident. The credential is the
   boundary.
7. **For a public site,** set `PROTECTED=0`. The first deploy then attaches the domain at once, steps 3 and 5 are not
   needed, and the script skips the `302` check. Every other gate still runs.

**To take the site down:** delete the Access application
(`npx cf@<CF_VERSION> zero-trust access applications delete <app id> --force`), then the Worker
(`npx cf@<CF_VERSION> workers delete <WORKER>`), which also removes its domain. The first command was run in the
measurement. The second is from `cf`'s help and was not run. Both are the owner's commands.

`cf` is a beta, and Cloudflare's dashboard changes. Check each step against Cloudflare's current documentation, and
change `CF_VERSION` only on purpose: run the dry run after a change of version.

## Build rules

- **Never deploy the repo root.** It holds `node_modules`, `.claude/`, `.agents/`, scripts and drafts. The script
  builds a dist that holds only the hub pages, `md.html`, the files under `site/` and the `SHIP` folders. The `LEAK`
  gate checks the root of the dist against that list. At any depth it refuses `node_modules`, `.claude`, `.agents`,
  `.codex`, `.git`, a symlink, and an environment file (`.env`, `.env.*`) other than `.env.example`, `.env.sample` and
  `.env.template`.
- **The dist is pinned to HEAD** (`git archive`). Another session's uncommitted drafts never ship, and neither do
  yours. Commit first, then build.
- **The baseline is the last deploy by anyone.** Several sessions can deploy on one day. The ledger's top entry names
  the baseline, and before the upload the script checks that this entry's version is still the one serving.
- **Name the delta file by file.** The file count is a tripwire: an added file that you cannot name is a leak or a
  regression until you prove otherwise.
- **Gate the deploy on content, not on git.** A commit can fall off the branch when another session commits on the
  older sha, and `git log -1` right after your commit does not show it. Pass a `--marker` for each change, and check
  `git merge-base --is-ancestor <sha> HEAD`.
- **Scan the delta for credentials,** not the whole dist. Older archives may hold known, ruled hits. A new hit is a
  stop.
- **Exclude by name.** A file that must stay in git but must not ship (a licence that forbids posting, a file over
  25 MiB, a capture that holds a token) goes in `EXCL`. The script checks that each one is in the stage and absent
  from the dist, so a moved file cannot ship silently. Only a file under `docs/assets/`, or one the hub does not
  list, can be excluded: the hub and its search index carry the title, the note and the whole text of every doc they
  list, so the script stops with `EXCLUDED_IN_HUB` for a listed doc.
- **Two size limits.** One file may be at most 25 MiB. One Worker version may hold 20,000 files on the free plan and
  100,000 on a paid plan; set `MAX_FILES` to yours.
- **Archived captures are served inert.** A raw capture under `docs/assets/` keeps the origin's scripts. `site/_headers`
  gives that folder a policy with no script and no network access. Access does not replace this: it identifies the
  viewer, and it does not stop a third-party script that runs in the viewer's signed-in session. Do not remove
  scripts from an archive to make it safe; keep each capture byte-identical. The policy does not stop a
  `<meta http-equiv="refresh">` in a capture. Adding `sandbox` to the policy would, but it may also stop the
  browser's PDF viewer; test both before you add it. `md.html` refuses any path under `docs/assets/`.
- **A `_headers` pattern takes one splat, at the end,** and never a file extension after it. A path that ends in
  `.html` redirects (status 307) to the path without it, and a pattern that ends in `.html` puts its headers on that
  redirect. Name the path without the extension, as the `/md` rule does. In the measurement, PDF and SVG files kept
  the `Cache-Control` that `_headers` gave them. A zone's browser cache setting can still replace it: measure a header
  in a browser before you rely on it.
- **A marker that is right inside the repo can be a defect on a public page.** `[FILL]` is the rule against invented
  numbers. A page that leaves the repo for an outside reader must resolve each one: drop the claim or get the real
  figure. Check a public build for what it must not contain as well as for what it must.
- **Build the hub after the commit, never before.** `build-hub.py` lists tracked files and takes dates from git. A doc
  that is untracked when the hub is built is missing from the committed pages, and the `--check` gate then stops the
  deploy.
- **Remove the work folder after the live probes,** not before. The log and the delta list in it are what the ledger
  entry needs.

## Verify live

- **On a protected site, each kind of path must answer `302`** to a request that is not signed in: the home page, the
  viewer, a doc, another file, and a path that does not exist. A `200` means the corpus is public: stop and tell the
  owner. A new version that is deployed while Access is on is protected at once.
- **A missing path answers `404`** with the body of `404.html`, so a status code is a valid check for "is this page
  there". Through Access, a signed-out request gets `302` for every path, missing or not.
- **Probe in a signed-in browser, in a tab you opened.** Put the `location.origin` check in the same evaluate as the
  fetch, so that a sign-in page cannot pass as content. Close only your own tab.
- **Fetch with `cache: 'no-store'`,** and compare byte counts for a file that is not HTML.
- **One gate per line, each ending in `|| exit 1`.** A gate whose output is piped to `tail` passes on the exit code
  of `tail`, and a trailing `|| true` hides every gate before it.
