---
name: share-report
description: Use when the owner asks for a page to show or share in this repo — "generate an html report to share with <name>", "build an html page to visualize X", "make a diagram of Y", "an html version of this doc" — or when a doc is still hard to read as text.
---

# Share a report

A shared page is how a reader who does not open the repo reads the work. The page must say the same thing as the doc
it explains.

## The chain

1. **Look for an existing page first** under `reports/` and in `site/manifest.json`. If one exists, update it, and update its Markdown doc too, so
   that the two still agree.
2. **Build it as `reports/<topic>.html`**, one self-contained file. Use an installed diagram skill
   (`README.md` lists them). Write plain prose. Link every cited source. Never invent a number.
3. **Look at it.** Render the page in a browser (`browser-harness` if it is installed) and take a screenshot at
   1440×900. Check each SVG for overlap: text
   against boxes on both edges, text against text, and the ends of arrows. Fix every overlap before you go on.
4. **Commit** the page by its explicit path. The diagram skills leave `*.visual-check.*` files beside a page, and a
   glob would take them in.
5. **Put it on the hub.** The hub lists every tracked page under `reports/` with the page's `<title>`, so give the
   page a title that says what it answers. For a one-line note under the title, add the page's path to `notes` in
   `site/manifest.json`; add it to `startHere` only if a new reader should open it first. Then run
   `python3 -I scripts/build-hub.py` and commit the manifest and the four files the script writes, each by name.
6. **Publish only when the message says so** ("and deploy", "share it now"), and then with the `deploy-site` skill.
7. **End the reply** with the local path of the page, its address on the site (`<site>/reports/<topic>`) marked "live" or "after the next
   deploy", and one sentence that says what question the page answers.
