#!/usr/bin/env python3
"""Generate the site's hub from git and the files themselves: index.html, docs.html, changelog.html, 404.html, search-index.json.

    python3 -I scripts/build-hub.py           # write the five files
    python3 -I scripts/build-hub.py --check   # exit 1 if any of them is not what this script would write

- index.html: counts by type, the "Start here" list, and what is new.
- docs.html: every tracked doc and report, with type and age filters, a sort, and search. `?type=read`, `?age=30`,
  `?sort=title` and `?q=words` work as URLs.
- changelog.html: one row per deploy: each commit whose subject is `Deploy <id>: <what shipped>`.
- 404.html: the page a missing path answers with. Its links start at the site root, because it is served at any path.
- search-index.json: the text of every doc, for full-text search. docs.html loads it on the first search.

The roster is `git ls-files`, so a deploy pinned to HEAD never links a file that is not in it. Dates come from git.
A doc's type comes from its folder (a folder that TYPES does not name gives the type "Doc"), its title from its first `# ` heading, and its note from site/manifest.json or
else from its first paragraph. So a doc with no manifest entry still appears. Nothing in the output depends on today's
date: the pages carry each date, and site/hub.js works out what is new. Run this after the commit that adds a doc,
then commit the five files. Never edit them by hand."""
import html, json, pathlib, re, subprocess, sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
TYPES = [("canon", "Claim"), ("landscape", "Read"), ("syncs", "Sync"), ("plans", "Plan"), ("design", "Design"),
         ("decisions", "Decision"), ("registers", "Register"), ("reports", "Report"), ("other", "Doc")]
LABEL = dict(TYPES)
SKIP = ("docs/README.md",)
E = html.escape


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotePath=false", *args], check=True, capture_output=True, text=True).stdout


def git_dates():
    """{path: (added, updated)} from one pass over the log, newest commit first."""
    out, date = {}, ""
    for ln in git("log", "--format=%x00%cs", "--name-only", "--", "docs", "reports").split("\n"):
        if ln.startswith("\x00"):
            date = ln[1:]
        elif ln:
            out[ln] = (date, out[ln][1] if ln in out else date)
    return out


class Title(HTMLParser):
    def __init__(self):
        super().__init__()
        self.on, self.done, self.text = False, False, ""

    def handle_starttag(self, tag, attrs):
        self.on = tag == "title" and not self.done  # the page's own title; an inline SVG has titles too

    def handle_endtag(self, tag):
        if self.on and tag == "title":
            self.done = True
        self.on = False

    def handle_data(self, data):
        if self.on:
            self.text += data


def plain(md):
    """Markdown to one line of plain text: enough for a note and for search, not a renderer."""
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"(?m)^\s*(#{1,6}|>|[-*+]|\d+\.)\s+", "", md)
    md = re.sub(r"(?m)^\s*\|?[\s:|-]+\|\s*$", " ", md)
    return re.sub(r"\s+", " ", re.sub(r"[*_`|]", "", md)).strip()


def read_doc(path):
    text = (ROOT / path).read_text(encoding="utf-8", errors="replace")
    if path.endswith(".html"):
        t = Title()
        t.feed(text)
        return t.text.strip() or pathlib.Path(path).stem, "", ""
    m = re.search(r"(?m)^#\s+(.+)$", text)
    title = plain(m.group(1)) if m else pathlib.Path(path).stem
    body = text[m.end():] if m else text
    first = next((p for p in re.split(r"\n\s*\n", body) if p.strip() and not re.match(r"\s*(#|\||```|---)", p)), "")
    note = plain(first)
    return title, (note[:217].rsplit(" ", 1)[0] + "…" if len(note) > 220 else note), plain(body)


def entries(manifest):
    dates, notes, out = git_dates(), manifest.get("notes", {}), []
    for f in git("ls-files", "docs/*.md", "docs/**/*.md", "reports/*.html").split("\n"):
        if not f or f in SKIP or f.startswith("docs/assets/"):
            continue
        kind = "reports" if f.startswith("reports/") else f.split("/")[1]
        if kind not in LABEL:  # a doc at the top of docs/ or in a folder that TYPES does not name still appears
            kind = "other"
        title, note, text = read_doc(f)
        added, updated = dates.get(f, ("", ""))
        out.append(dict(path=f, kind=kind, title=title, note=notes.get(f, note), text=text, added=added, updated=updated,
                        href=f if f.endswith(".html") else "md.html?f=" + f))
    return sorted(out, key=lambda e: (e["updated"], e["path"]), reverse=True)


def deploys():
    out = []
    # A deploy commit's subject is "Deploy <id>: <what shipped>", where the id is a version id or a hash. A subject
    # that only starts with the word "Deploy" is not a deploy.
    for ln in git("log", "--grep=^Deploy ", "--format=%cs%x09%h%x09%s").split("\n"):
        if ln:
            date, sha, subject = ln.split("\t", 2)
            m = re.match(r"Deploy ([0-9a-f][0-9a-f-]{6,}):\s*(.*)", subject)
            if m:
                out.append(dict(date=date, sha=sha, deploy=m.group(1), title=m.group(2)))
    return out


def page(site, name, active, body, root=""):
    """root is "" for a page at the site root, and "/" for the 404 page, which is served at any path."""
    current = ' aria-current="page"'
    nav = "".join(f'<a href="{root + h if h != "./" else (root or "./")}"{current if h == active else ""}>{t}</a>'
                  for h, t in (("./", "Home"), ("docs.html", "Library"), ("changelog.html", "Changelog")))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(name)} · {E(site)}</title>
<link rel="stylesheet" href="{root}hub.css">
</head>
<body>
<header><a class="site" href="{root or "./"}">{E(site)}</a><nav>{nav}</nav></header>
<main>
{body}
</main>
<script src="{root}hub.js" defer></script>
</body>
</html>
"""


def row(e):
    note = f'<p class="note">{E(e["note"])}</p>' if e["note"] else ""
    return (f'<li data-type="{e["kind"]}" data-added="{e["added"]}" data-updated="{e["updated"]}" data-path="{E(e["path"])}">'
            f'<a class="title" href="{E(e["href"])}">{E(e["title"])}</a> <span class="badge b-{e["kind"]}">{LABEL[e["kind"]]}</span>'
            f'{note}<p class="meta"><code>{E(e["path"])}</code> · updated {e["updated"] or "—"}</p><p class="hit" hidden></p></li>')


def home(site, manifest, es, ds):
    count = {k: sum(e["kind"] == k for e in es) for k, _ in TYPES}
    tiles = "".join(f'<a class="tile" href="docs.html?type={k}"><b>{count[k]}</b><span>{label}{"" if count[k] == 1 else "s"}</span></a>'
                    for k, label in TYPES if count[k])
    by_path = {e["path"]: e for e in es}
    start = "".join(row(by_path[p]) for p in manifest.get("startHere", []))
    start = f'<section><h2>Start here</h2><ul class="list">{start}</ul></section>' if start else ""
    last = (f'<p class="lede">Last deploy: <a href="changelog.html"><code>{E(ds[0]["deploy"])}</code></a> on {ds[0]["date"]}: '
            f'{E(ds[0]["title"])}</p>') if ds else ""
    intro = f'<p class="lede">{E(manifest["intro"])}</p>' if manifest.get("intro") else ""
    return page(site, "Home", "./", f"""<h1>{E(site)}</h1>
{intro}{last}
<section><h2>Browse</h2><div class="tiles">{tiles}</div></section>
{start}
<section id="whatsnew"><h2>What's new</h2>
<p class="controls" hidden><button data-days="7">7 days</button><button data-days="30">30 days</button><button data-days="0">Latest</button></p>
<ul class="list">{"".join(row(e) for e in es[:40])}</ul>
<p class="empty" hidden>Nothing changed in this window.</p>
</section>""")


def library(site, es):
    chips = '<button data-type="" aria-pressed="true">All</button>' + "".join(
        f'<button data-type="{k}" aria-pressed="false">{label}</button>' for k, label in TYPES if any(e["kind"] == k for e in es))
    return page(site, "Library", "docs.html", f"""<h1>Library</h1>
<form id="filters" class="filters" onsubmit="return false">
<input id="q" type="search" placeholder="Search titles, paths and full text" autocomplete="off" aria-label="Search">
<p class="chips" id="types">{chips}</p>
<label>Changed <select id="age"><option value="">any time</option><option value="7">last 7 days</option><option value="30">last 30 days</option><option value="90">last 90 days</option></select></label>
<label>Sort <select id="sort"><option value="updated">last changed</option><option value="added">first added</option><option value="title">title</option></select></label>
<span id="count" class="count">{len(es)} of {len(es)}</span>
</form>
<ul class="list" id="library">{"".join(row(e) for e in es)}</ul>
<p class="empty" hidden>No doc matches.</p>""")


def changelog(site, ds):
    rows = "".join(f'<tr><td>{d["date"]}</td><td><code>{E(d["deploy"])}</code></td><td>{E(d["title"])}</td><td><code>{d["sha"]}</code></td></tr>'
                   for d in ds)
    body = (f'<table class="log"><thead><tr><th>Date</th><th>Deploy</th><th>What shipped</th><th>Commit</th></tr></thead><tbody>{rows}</tbody></table>'
            if ds else '<p class="lede">No deploy yet. A row appears here for each commit whose message starts with <code>Deploy &lt;hash&gt;:</code>.</p>')
    return page(site, "Changelog", "changelog.html", f"<h1>Changelog</h1>\n{body}")


def not_found(site):
    return page(site, "Not found", "", """<h1>Not found</h1>
<p class="lede">There is no page at this address. It may have moved, or the link may be wrong.</p>
<p><a href="/docs.html">Search the library</a> · <a href="/">Go to the home page</a></p>""", root="/")


def build():
    mpath = ROOT / "site" / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    site = manifest.get("title", "Home Repo")
    es, ds = entries(manifest), deploys()
    known = {e["path"] for e in es}
    missing = [p for p in list(manifest.get("startHere", [])) + list(manifest.get("notes", {})) if p not in known]
    if missing:
        sys.exit("site/manifest.json names a path that is not a tracked doc or report: " + ", ".join(missing))
    index = [dict(p=e["path"], t=e["text"].lower()) for e in es if e["text"]]
    return {"index.html": home(site, manifest, es, ds), "docs.html": library(site, es), "changelog.html": changelog(site, ds), "404.html": not_found(site),
            "search-index.json": json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n"}, len(es), len(ds)


def main():
    files, n, d = build()
    if sys.argv[1:] == ["--check"]:
        stale = [f for f, want in files.items() if not (ROOT / f).exists() or (ROOT / f).read_text(encoding="utf-8") != want]
        if stale:
            print("stale: " + ", ".join(stale))
        sys.exit(1 if stale else 0)
    for f, want in files.items():
        (ROOT / f).write_text(want, encoding="utf-8")
    print(f"built {len(files)} files: {n} entries, {d} deploys")


if __name__ == "__main__":
    main()
