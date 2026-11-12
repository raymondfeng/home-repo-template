---
name: check-out
description: Use when the owner asks to read an outside source in this repo — "check out <url>", "read <url>", "evaluate <url|file>", "what can we borrow from X" — a repo, a docs site, a paper, a post, a talk, or a vendor page, to be captured as a read doc with an archive and borrows.
---

# Check out a source

A read here is evidence: other docs cite it. So the archive comes first, every quote is checked against it, and a
claim that something is absent is the claim most likely to be wrong. The rules are in `AGENTS.md` → Capture
discipline. This skill puts them in order.

## The chain

0. **Look for an earlier read** of the same source: `grep -ril <name> docs/landscape docs/assets/*/SNAPSHOT.txt`. If
   one exists, read it and its pinned sha or date, and write a read of what changed since then.
1. **Fetch the primary source, by host.**
   - A docs site or a blog: try `/llms.txt`, a `.md` view, or `Accept: text/markdown` first. Judge the response by its
     body, never by its status code.
   - A GitHub repo: clone it shallow into a scratch folder and pin the sha. Archive what you quote: the README,
     `docs/`, the source files you cite, `git log --oneline -50`, and the repo metadata.
   - A client-rendered site: a browser and `innerText`, with the `browser-harness` skill. Open
     your own tab and close only that tab. Copy the DOM into a page global before you slice it, because the page
     changes between calls. If the page shows the reader's account, capture it in a context with no cookies.
     Use the browser only when a plain fetch returns a shell page.
   - A PDF: download it and read it with page ranges. Never cite a number from a summarizing fetch.
2. **Archive the full raw body** under `docs/assets/<topic>-<date>/`: the raw HTML or PDF, a text extraction made with
   a parser, and a `SNAPSHOT.txt` with the URLs, the date, the method and the sha256 of each file. Keep each capture
   byte-identical. Note any licence that forbids posting the capture.
3. **Write the read** in `docs/landscape/<topic>-read-<date>.md`. Lead with the answer. The provenance line names what
   you read. Quote as `*"…"*`. Tag every absence claim and every number DO-NOT-CITE until you have checked it in the
   archive. A spoken number stays DO-NOT-CITE. A vendor's figure is "X says".
4. **Check every quote:**
   `python3 -I scripts/check-quotes.py --doc <read> --archive docs/assets/<topic>-<date> [--source …] [--git …]`.
   On a miss, fix the doc, never the check. Run it once more with `--plant`: it must fail. Then add the read's
   arguments to `scripts/quote-reads.json`, so that `--all` covers it.
5. **Borrows.** Write a table with IDs (two letters from the source plus a number): what the source does, what we
   would take, where it goes, and the cost. Take ideas only: never code or a runtime dependency.
6. **Offer, then stop.** Give lettered options with a recommendation: which borrows to file as issues and in which
   repo (`AGENTS.md` → Other Repos), and which go to a design.
7. **Scan the archive** before you commit it: write its file list to a scratch file and run
   `python3 -I scripts/credscan.py . <list>`. A hit is a stop: name it and propose excluding the file.
8. **Commit** the archive and the read by explicit paths.

## Common mistakes

| Mistake | Instead |
|---|---|
| Quoting from a summarizer's output | Quote from the archive; the summarizer drops and invents sentences |
| "X has no Y" from a docs index | Read the page and the repo; say which one in the provenance line |
| A regex over HTML, `.pptx` or JSON | A parser, proved on a string you know is present |
| A new quote script for each read | `check-quotes.py` plus one `quote-reads.json` entry |
