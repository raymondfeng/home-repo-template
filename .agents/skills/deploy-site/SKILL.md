---
name: deploy-site
description: Use when the owner asks to deploy or publish this repo's site — "deploy", "push and deploy", "publish the site", "share it now" — or to set up the Cloudflare Worker and its Access protection for the first time.
---

# Deploy the site

The deploy is the owner's command. When the owner gives it, run the whole chain without stopping between steps. A
failed gate is a stop: report its `STOP:` line and never loosen the gate. The steps are in `scripts/deploy.sh`, and
every gate in it exits. The rule behind each gate is in `RULES.md` beside this file. The record of every deploy is
`DEPLOY-LEDGER.md`.

A `PreToolUse` hook (`hooks/refuse-bare-deploy.py`) refuses a bare `cf deploy` or `wrangler deploy`. Do not work
around it. In Codex the hook runs only after the owner has trusted it, so follow this chain there even when nothing
stops you.

The first deploy is part of the one-time setup in `RULES.md`, which is the owner's. On a private site it has two
deploys: `--first` creates the Worker with no domain, the owner then puts Access on the Worker, and the next deploy
attaches the domain. Do not run that second deploy until the owner confirms that the Access application exists.

## The chain

1. **Read the state.** Run `git log --oneline -5` and read the top entry of `DEPLOY-LEDGER.md`. The baseline is the
   last deploy by anyone.
2. **Commit your content by explicit paths,** after `git add` of every new file. Then run
   `git merge-base --is-ancestor <your sha> HEAD`: another session can orphan a commit.
3. **Rebuild the hub:** `python3 -I scripts/build-hub.py`, after the commit that adds a doc and never before: the hub
   takes its roster and its dates from git. Then commit the five files it writes (`index.html`, `docs.html`,
   `changelog.html`, `404.html`, `search-index.json`).
4. **Dry run:** `bash scripts/deploy.sh --marker <path>:<string>`, with one `--marker` for each change you ship. Take
   each string from the file itself, not from memory. Read the printed delta and name every added file.
5. **Deploy:** remove the dry run's folder (the `WORK=` path it printed), then run the same command with `--deploy`.
   It uploads, and on a protected site it checks that each kind of path on the site's address answers `302`.
6. **Probe the live content** on the site's address, signed in. For each change, fetch the page with
   `cache: 'no-store'` and find its marker string. Check the marker in the body: through Access, a sign-in page answers too.
7. **Record the deploy.** Prepend an entry to `DEPLOY-LEDGER.md` in the format at its top, and commit it with a
   message that starts `Deploy <version id>:` and then says what shipped. The changelog page is built from these messages.
   So rebuild the hub once more after this commit (`python3 -I scripts/build-hub.py`) and commit its files; the
   deploy then appears on the changelog at the next deploy, and the next dry run does not stop on a stale hub.
8. **Clean up:** `rm -rf` the `WORK=` folder. A run that stopped before the upload removed its own.
9. **Reply** with the version id, the HEAD sha, the file count, the probe results, and the address of each changed
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
| `TOO_MANY_FILES` | The dist holds more files than `MAX_FILES` | Exclude an archive by name, or raise `MAX_FILES` if the plan allows it |
| `cf deploy --dry-run failed` | cf rejected the config or could not run | Read the log it names. A new `CF_VERSION` may have changed a config key |
| `EXCLUDED_IN_HUB` | A file in `EXCL` is a doc that the hub lists | Move it under `docs/assets/`, or remove it from git. Do not exclude a listed doc |
| `LEAK`, `SYMLINK`, `EXCLUDED_PRESENT`, `… differs from <rev>` | The dist is wrong | Read the message. Never edit a gate to pass |
| `MARKER_MISSING` | A change you meant to ship is not in the dist | Check `git merge-base --is-ancestor`; the commit may be orphaned |
| `CONFIG` | cf's dry run built a Worker config with `workers.dev` or Version URLs on, or with the wrong domain | Stop. Do not upload. A new `CF_VERSION` may have renamed a key: read `cloudflare.config.ts` in the work folder against Cloudflare's reference |
| `NO_ANSWER` | The upload is done, but the site's address gave no answer in five minutes | Check the address from another network. If it answers `302` there, record the deploy. If it answers `200`, treat it as `ACCESS` |
| `the version now serving is …` | Someone deployed after the ledger's top entry | Reconcile the ledger first |
| `ACCESS` | A path answered something other than 302 | Stop everything and tell the owner: the corpus may be public |
