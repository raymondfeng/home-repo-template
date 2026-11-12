---
name: deploy-site
description: Use when the owner asks to deploy or publish this repo's site — "deploy", "push and deploy", "publish the site", "share it now" — or to set up the Cloudflare Pages project and its Access protection for the first time.
---

# Deploy the site

The deploy is the owner's command. When the owner gives it, run the whole chain without stopping between steps. A
failed gate is a stop: report its `STOP:` line and never loosen the gate. The steps are in `scripts/deploy.sh`, and
every gate in it exits. The rule behind each gate is in `RULES.md` beside this file. The record of every deploy is
`DEPLOY-LEDGER.md`.

A `PreToolUse` hook (`hooks/refuse-bare-wrangler.py`) refuses a bare `wrangler pages deploy`. Do not work
around it. In Codex the hook runs only after the owner has trusted it, so follow this chain there even when nothing
stops you.

For the first deploy, do the one-time setup in `RULES.md` first, then pass `--first` in steps 4 and 5. The `302` check
runs only after the upload. So on a private site, confirm with the owner that setup step 3 is done before you run
`--first --deploy`.

## The chain

1. **Read the state.** Run `git log --oneline -5` and read the top entry of `DEPLOY-LEDGER.md`. The baseline is the
   last deploy by anyone.
2. **Commit your content by explicit paths,** after `git add` of every new file. Then run
   `git merge-base --is-ancestor <your sha> HEAD`: another session can orphan a commit.
3. **Rebuild the hub:** `python3 -I scripts/build-hub.py`, after the commit that adds a doc and never before: the hub
   takes its roster and its dates from git. Then commit the four files it writes (`index.html`, `docs.html`,
   `changelog.html`, `search-index.json`).
4. **Dry run:** `bash scripts/deploy.sh --marker <path>:<string>`, with one `--marker` for each change you ship. Take
   each string from the file itself, not from memory. Read the printed delta and name every added file.
5. **Deploy:** remove the dry run's folder (the `WORK=` path it printed), then run the same command with `--deploy`.
   It uploads, waits 12 seconds, and on a protected site checks that each kind of path on the new deployment's own
   host answers `302`.
6. **Probe the live content** on the site's address, signed in. For each change, fetch the page with
   `cache: 'no-store'` and find its marker string. Check the page's `<title>` or body, never the status code.
7. **Record the deploy.** Prepend an entry to `DEPLOY-LEDGER.md` in the format at its top, and commit it with a
   message that starts `Deploy <hash>:` and then says what shipped. The changelog page is built from these messages.
   So rebuild the hub once more after this commit (`python3 -I scripts/build-hub.py`) and commit its files; the
   deploy then appears on the changelog at the next deploy, and the next dry run does not stop on a stale hub.
8. **Clean up:** `rm -rf` the `WORK=` folder. A run that stopped before the upload removed its own.
9. **Reply** with the deploy hash, the HEAD sha, the file count, the probe results, and the address of each changed
   page. A doc's address is `<site>/md.html?f=docs/<path>.md`.

## When a gate stops

| `STOP:` line | Meaning | Do |
|---|---|---|
| `… has uncommitted changes`, `the hub pages are stale` | A hub page or a file under `site/` is not committed or not current | Step 3, then rerun |
| `no deploy entry in DEPLOY-LEDGER.md` | There is no baseline | Pass `--first` if this is the first deploy; otherwise restore the ledger |
| `baseline … is not an ancestor` | HEAD moved, or the ledger names another branch | Read the ledger entry and `git log` |
| `CREDENTIAL HIT` | The scan matched a file in the delta | Show the masked hit to the owner. An allowance is the owner's ruling: one exact string in `ALLOW_EXACT` in `scripts/credscan.py`, or a name exclusion |
| `name exclusion not in the stage` | An excluded file moved | Fix the `EXCL` list in the script |
| `OVERSIZE` | A file is over 25 MiB | Add it to `EXCL` by name; never re-encode it |
| `EXCLUDED_IN_HUB` | A file in `EXCL` is a doc that the hub lists | Move it under `docs/assets/`, or remove it from git. Do not exclude a listed doc |
| `LEAK`, `SYMLINK`, `EXCLUDED_PRESENT`, `… differs from <rev>` | The dist is wrong | Read the message. Never edit a gate to pass |
| `MARKER_MISSING` | A change you meant to ship is not in the dist | Check `git merge-base --is-ancestor`; the commit may be orphaned |
| `the newest Production deployment is …` | Someone deployed after the ledger's top entry | Reconcile the ledger first |
| `ACCESS` | A path answered something other than 302 | Stop everything and tell the owner: the corpus may be public |
