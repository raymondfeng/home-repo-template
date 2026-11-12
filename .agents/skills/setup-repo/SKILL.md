---
name: setup-repo
description: Use when this repo is a fresh copy of the template and must be made the owner's own, or when the owner asks to set up, configure or customize the Home Repo, add or remove a repo pointer, change the site's title, or prepare the first deploy.
---

# Set up this Home Repo

A fresh copy of the template holds placeholders, a made-up example and a deploy script that names no real project.
This skill replaces each of them with the owner's facts. Look up every fact that you can find yourself, and ask the
owner only for decisions. Change nothing outside this repo.

## How to work

- Find facts with the filesystem, `git` and `gh`. Do not read `.env` files or other secret files.
- Ask in rounds. Number each question, give your recommended answer, and word the question so that "yes" accepts it.
- A step that the owner does not want is skipped, and you say so in the final report. Nothing here is required
  except steps 1 and 2.
- Commit after each step, by explicit paths, with a message that says what the step set.

## The steps

1. **What the repo is.** Ask for one paragraph: the project, and that this repo is its record and not its code. Write
   it into `AGENTS.md` → "What this repo is". Rename the heading of `README.md` and its first paragraph to match, and
   remove the README sections that describe the template itself.
2. **The other repos.** List the git repos beside this one (`ls ..`, then `git -C <path> remote get-url origin` and
   `git -C <path> log -1 --format=%cs`). Show the list with a recommendation for each: point at the ones with recent
   commits. For each repo the owner accepts, write one line under `AGENTS.md` → "Other Repos": its name, what it is,
   its local path, its remote, and a hint if it needs one. Remove the two placeholder lines. Past about 20 repos,
   group the lines into one file per area under `repos/` and list the areas instead.
3. **The glossary.** Ask for the three to ten terms that the project has fixed, and for each the words to avoid. Write
   them into `CONTEXT.md`. If the owner has none yet, leave the stub.
4. **The fixed vocabulary and the rules.** Read `AGENTS.md` → "Guardrails" with the owner. Fill the last placeholder
   line or delete it. Ask whether any stop rule in "When to keep going and when to stop" should be stricter or looser
   for this project, and record the answer with the owner's name and the date.
5. **The docs folders.** Show the table in `AGENTS.md` → "Where a doc goes". A folder the project will not use may
   go: delete its row and its folder. For a new folder, add a row, the folder, and an entry in `TYPES` in
   `scripts/build-hub.py`; a folder with no entry there still appears on the hub, with the type "Doc".
6. **The worked example.** Ask whether to keep it for now. To remove it: delete
   `docs/landscape/example-source-read-2026-01-01.md` and `docs/assets/example-source-2026-01-01/`, empty the list
   in `scripts/quote-reads.json` to `[]`, and remove its path from `startHere` and `notes` in `site/manifest.json`.
7. **The site.** Set `title` and `intro` in `site/manifest.json`. Then run `python3 -I scripts/build-hub.py` and
   commit the five files it writes. If the owner does not want a site, stop here for the site: skip step 8, and say
   in `AGENTS.md` → "Deployment and protection" that the site is not deployed.
8. **The deploy.** Ask four things: the Worker's name, the address people will open (its hostname must be in a zone
   of the owner's Cloudflare account), whether the site is private, and the account id if the login has more than one
   account. Set `WORKER`, `SITE_URL`, `PROTECTED` and `ACCOUNT_ID` at the top of `scripts/deploy.sh`. Then give the owner the
   one-time setup in `.agents/skills/deploy-site/RULES.md`: those steps are the owner's to do, in the Cloudflare
   dashboard and with a Cloudflare login. Run `bash scripts/deploy.sh --first` as a dry run and report its last line.
   Do not run `--deploy`: the first upload is the owner's command, through the `deploy-site` skill.
9. **The browser.** Run `command -v browser-harness`. If it prints nothing, tell the owner that `check-out` cannot read
   a client-rendered source and `share-report` cannot do its visual check until the command is installed, and point
   to `.agents/skills/browser-harness/references/install.md`. Do not install it yourself. Then run
   `python3 -I scripts/update-skills.py --check` and report whether the copied skill is behind upstream. Do not update
   it without the owner's word.
10. **The hook.** If the owner does not deploy with `cf`, ask whether to remove the hook from
   `.claude/settings.json` and `.codex/hooks.json`, or to change its pattern to the owner's deploy command. Run the hook's test after a change.
11. **The licence.** The template's `LICENSE` names the template's author. Leave the `LICENSE` under
    `.agents/skills/browser-harness/` as it is: it belongs to that skill. Ask what the owner wants for this repo:
    their own notice, or no licence file in a private repo. Replace or remove the file.
12. **Check.** Run each line and report the result:

    ```bash
    python3 -I scripts/check-quotes.py --selftest
    python3 -I scripts/check-quotes.py --all     # skip if quote-reads.json is empty
    python3 -I scripts/credscan.py --controls
    python3 -I hooks/test-refuse-bare-deploy.py
    python3 -I scripts/build-hub.py --check
    ```

    Then search for placeholders that are left, and list each one:

    ```bash
    grep -n '`<[A-Za-z]' AGENTS.md CONTEXT.md
    ```
13. **Point back.** For each repo in step 2, propose one line for its own `AGENTS.md` that names this repo as the home
    of designs and decisions. Show the lines. Do not edit those repos: the owner adds each line, or tells you to.

## The final report

Give three lists: what each step set, what was skipped and why, and what is left for the owner (the Cloudflare setup,
the first deploy, the lines for the other repos).

## Later changes

The same steps work one at a time. To add a repo, do step 2 for that repo. To rename the site, do step 7. To move to
another Worker, do step 8 and then the one-time setup in `RULES.md` again. The first deploy to the new Worker runs with
`--first --baseline <sha>`, where the sha is the HEAD of the ledger's top entry, and the change is noted in the
ledger's next entry.
