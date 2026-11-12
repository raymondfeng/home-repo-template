# CLAUDE.md

Start every session in this repo. It is the Home Repo: it holds the shared skills, the rules, the document corpus and
the pointers to the other repos. The `setup-repo` skill replaces each `<placeholder>` with you; until it has run, treat
a placeholder as a fact you do not have.

## What this repo is

`<One paragraph: what the company or project is, and that this repo is its record, not its product code.>`

There is no test suite. The checks are the scripts under `scripts/` and the hook under `.claude/hooks/`. Six
files are generated: `index.html`, `docs.html`, `changelog.html` and `search-index.json` by `build-hub.py`, and the
two files under `docs/diagrams/` by `build-readme-diagram.py`. Never edit them by hand.
To change what the hub says about a doc, edit the doc or `site/manifest.json`, then run `python3 -I scripts/build-hub.py`.

## Other Repos

One line per repo: its name, what it is, its local path, its remote, and a hint if it needs one.

- `<product>` (`<what it is>`): `../<product>`. Clone from `<git remote>` if missing. Read its `CLAUDE.md` before
  changing it. Work there in a worktree, one per feature: `git -C ../<product> worktree add .worktrees/<name> -b <branch> origin/main`.
- `<library>` (`<what it is>`): `../<library>`. Run `git fetch` first; the checkout is often behind.

Rules for work that crosses repos:

- Cite code in another repo at a pinned revision (`<repo>@<sha>:<path>`), read from `origin/main`. The checkout may be
  on a feature branch.
- A design, plan or decision about another repo's code is written here, under `docs/`. The other repo's `CLAUDE.md`
  points back at it. File each issue in the repo whose code it changes.
- Past about 20 repos, move the pointers to one file per area (`repos/<area>.md`) and list the areas here.

## Where a doc goes

Nothing sits at the top of `docs/`. A doc goes in the folder that answers its question. A filename ends with its type
word and its date: `<topic>-read-2026-01-31.md`.

| Folder | The question it answers |
|---|---|
| `canon/` | What do we claim? |
| `landscape/` | What did we read about others? |
| `syncs/` | What was said in a meeting or a review? |
| `plans/` | What do we build, and in what order? |
| `design/` | How does a piece of the product work? |
| `decisions/` | What did we decide, and why? |
| `registers/` | Append-only shared lists |
| `assets/<topic>-<date>/` | The raw capture behind a read |
| `diagrams/` | Static SVG figures that a doc or the README embeds: no script, no web font |

## Capture discipline

- **Chat is not canon.** A table, a frame or a one-line statement from a session exists only when it is in a `docs/`
  file, word for word. Before a capture task ends, list every such output of the session and find each one in a doc.
- **Read the primary source.** Raw Markdown, the repo, the PDF, or the rendered page. Never quote, count or cite a
  number from a summarizing fetch: a summarizer drops sentences and invents rows.
- **An absence claim is the claim most likely to be wrong.** Before you write "X has no Y", read the source itself,
  and name what you read in the doc's provenance line.
- **Parse a structured format with a parser,** not a regex. Before you trust a zero, prove that the check finds a
  string you know is present.
- **Archive the full raw body** of each source under `docs/assets/<topic>-<date>/`, with a `SNAPSHOT.txt` (URL, date,
  method, sha256).
- **Check every quote** as a fixed string against the archive: `python3 -I scripts/check-quotes.py`. On a miss, fix the
  doc. Never loosen the check.
- **A spoken number is not citable.** A vendor's figure is "X says".
- **Tag first.** Mark an unverified number or absence claim DO-NOT-CITE when you write it, and remove the tag only
  after the check.

## Concurrent sessions

Several sessions can work in this repo at once.

- For doc work, stay on `main` and commit small and often. Use a worktree only for work that writes shared build
  output or binds a fixed port.
- Before you edit a shared append list (`scripts/quote-reads.json`, a register), run `git log --oneline -5`.
- Stage explicit paths. Never `git add -A`: it cannot tell your work from another session's.
- Never stop a process by pattern. Start a server on a free port, keep its PID, and stop that PID.

## When to keep going and when to stop

If a step does not need the owner's input, take it, and put the status note in the same message. Stop and ask before:

- a deploy, a `git push`, or any history rewrite;
- deleting or overwriting a file you did not create in this session;
- anything outside this repository: another repo's branch, an issue, a PR, an email.

A failed check is a stop. Report it with its output. End a long run with three headings: **Blocked on me**,
**Changed**, **Found**.

## Guardrails

- Never invent a number. Leave a `**[FILL]**` marker.
- A fact about a person comes from a source you can name.
- Write plain prose: short sentences, one term for one thing, the active voice, one claim per sentence, the condition
  before the instruction.
- `<Add the vocabulary your project has fixed, and the words to avoid. Keep the full glossary in CONTEXT.md.>`

## Deployment and protection

The site is one Cloudflare Pages project: the generated hub (a home page, a library with filters and search, and a
changelog), `md.html`, `docs/` and `reports/`. A doc's type badge on the hub comes from its folder, so a doc in the
wrong folder shows the wrong badge. Deploy only through the
`deploy-site` skill (`bash scripts/deploy.sh`: a dry run unless given `--deploy`, which is the owner's command). A
hook refuses a bare `wrangler pages deploy`. The rules are in `.claude/skills/deploy-site/RULES.md`, and the record
of every deploy is `DEPLOY-LEDGER.md`. Add a new deploy rule there, not here.

Two facts matter outside a deploy too:

- If the corpus is private, everything Cloudflare serves it from must sit behind Access: the custom domain and every
  `<hash>.<project>.pages.dev` address. After each deploy the new address must answer `302`, never `200`.
- A site with a fallback page answers `200` for a missing path. Check a page's `<title>`, never its status code.

**Current deploy:** `<none yet. After each deploy, replace this line with the hash, the HEAD sha and the file count.>`

## Skills

In this repo (`.claude/skills/`): `setup-repo` (make a fresh copy of the template the owner's own, and change its
settings later), `check-out` (read an outside source into an archive, a read doc and a table of
borrows), `capture-sync` (turn a meeting or a chat into a record), `share-report` (build a page for a reader), `deploy-site`
(publish the site through its gates).
One skill is a copy from outside and is not edited here: `browser-harness` (how to control a real browser; the command
is installed for the user, see `SOURCE.md` beside it). Update it only with `python3 -I scripts/update-skills.py`, and
read the diff before you commit it. `README.md` lists the installed skills that the others call.
