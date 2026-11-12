#!/usr/bin/env python3
"""Verify every quotation in a doc as a fixed string against the sources it quotes. One normalizer for every read.

A quote must be a substring of ONE source file after both
sides go through `norm()`. When a new miss shape turns up, decide whether the doc is wrong or the source is; change
`norm()` only for an encoding difference that is not a misquote, and never loosen the match to pass one doc.

    python3 -I scripts/check-quotes.py --doc docs/landscape/x-read-2026-10-24.md --archive docs/assets/x-2026-10-24
    python3 -I scripts/check-quotes.py --doc D --archive A --source docs/design/y.md --svg projects/p/svg_output/02_x.svg \\
        --git ../other-repo@4611a8d95:src/x.ts --expect-files 26
    python3 -I scripts/check-quotes.py --all       # every read in scripts/quote-reads.json
    python3 -I scripts/check-quotes.py ... --plant # prove the check fails on a planted quote
    python3 -I scripts/check-quotes.py --selftest  # prove norm() still folds encodings and still catches misquotes
    python3 -I scripts/check-quotes.py --read check-example-quotes     # one read, by its name in scripts/quote-reads.json

Sources: every file under each --archive (recursive), minus self-authored files (SNAPSHOT.txt, CENSUS.txt, QUOTES*) and
binaries, plus each --source file, the text of each --svg slide, and each --git file at its pinned revision (a slide's text for *.svg).
Quotes (--style): italic `*"…"*` (default) · italic-strict, which skips bold `**"…"**` · angle `«…»` and `“…”` · q `<q>…</q>` · corner `「…」`
· straight `"…"` (for a slide given as --doc *.svg) · blockquote (each `>` block and each fenced code block).
A quote with an elision (`...` or `…`) matches when every part is in the same source file.
A `.vtt` source contributes its cue text only (for rolling auto-captions, the lines with inline timing tags); --times
prints the cue time where each spoken quote starts. --skip TEXT leaves out quotes that contain TEXT (our own lines).
--markdown strips link targets, `*` and backticks on both sides; --from/--to limit the check to one block of the doc.
Run from the repo root. Exits 1 on any miss, or when the doc holds no quote."""
import argparse, fnmatch, html, json, pathlib, re, shlex, subprocess, sys, unicodedata
import xml.etree.ElementTree as ET

SELF_AUTHORED = ("SNAPSHOT.txt", "CENSUS.txt", "QUOTES*")
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".pptx", ".mp4", ".mp3", ".wav", ".woff",
          ".woff2", ".ttf", ".otf"}
STYLES = {
    "italic": r'\*"(.+?)"\*',
    "italic-strict": r'(?<!\*)\*"(.+?)"\*(?!\*)',
    "angle": r"«(.+?)»|“(.+?)”",
    "q": r"<q>(.+?)</q>",
    "corner": r"「(.+?)」",
    "straight": r'"(.+?)"',
    "blockquote": None,  # blockquotes() splits the doc; no regex
}
ELISION = re.compile(r"\.\.\.|…")
PLANTED = "This sentence was planted by check-quotes.py and appears in no source."


def norm(s):
    """Fold the differences that are encoding, not wording."""
    s = unicodedata.normalize("NFKC", s)                         # fi/fl ligatures in PDF text layers
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')  # curly vs straight quotes
    s = s.replace("­", "").replace("\f", " ")               # soft hyphen and form feed in pdftotext output
    s = s.replace('\\"', '"').replace("\\n", " ")                # string-literal escapes in captured code
    s = re.sub(r"(?m)^\s*(>|//|/\*\*|\*(?!\*))\s?", " ", s)      # blockquote and code-comment markers at a line start
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("[ __ ] ", "").replace(" [ __ ]", "")      # the ASR censor token, after whitespace collapse


def demark(s):
    """--markdown: a link keeps its text, and emphasis and code marks go, on both sides."""
    return re.sub(r"[*`]", "", re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s))


def svg_text(path, xml=None):
    """A slide's <text>, from a file, or from its XML when a --git *.svg gives it at a pinned revision."""
    root = ET.fromstring(xml) if xml is not None else ET.parse(path).getroot()
    return " ".join("".join(el.itertext()) for el in root.iter() if el.tag.endswith("text"))


def vtt_text(path):
    """Cue text of a WebVTT file and the start time of each cue's text, as (text, [(offset, "HH:MM:SS")]). Rolling
    auto-captions repeat each line; only the lines with inline timing tags hold a cue's new words."""
    cues = []
    for cue in re.split(r"\n\n+", path.read_text(encoding="utf-8")):
        m = re.search(r"(\d\d:\d\d:\d\d)\.\d+ -->", cue)
        if m:
            cues.append((m.group(1), [l for l in cue.split("\n") if "-->" not in l]))
    rolling = any(re.search(r"<\d\d:\d\d:\d\d\.\d+>|<c>", l) for _, ls in cues for l in ls)
    text, starts = "", []
    for ts, lines in cues:
        for line in lines:
            if rolling and not re.search(r"<\d\d:\d\d:\d\d\.\d+>|<c>", line):
                continue
            t = html.unescape(re.sub(r"<[^>]+>", "", line)).replace(">>", " ").strip()
            if t:
                starts.append((len(text), ts))
                text += t + " "
    return text, starts


def blockquotes(doc):
    """Each `>` block and each fenced code block of a Markdown doc, as one quote."""
    out, buf, fence, infence = [], [], [], False
    for ln in doc.split("\n"):
        if ln.startswith("```"):
            if infence:
                out.append("\n".join(fence))
                fence = []
            infence = not infence
        elif infence:
            fence.append(ln)
        elif ln.startswith(">"):
            buf.append(re.sub(r"^>\s?", "", ln))
        elif buf:
            out.append("\n".join(buf))
            buf = []
    return out + (["\n".join(buf)] if buf else [])


def found(q, bodies, clean):
    """The body index where every elided part of q occurs, or None."""
    parts = [x.strip() for x in ELISION.split(clean(q)) if x.strip()]
    return next((i for i, b in enumerate(bodies) if parts and all(x in b for x in parts)), None)


def git_show(spec):
    repo, rest = spec.split("@", 1)
    rev, path = rest.split(":", 1)
    return subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], check=True, capture_output=True,
                          text=True).stdout


def archive_files(root, globs, excludes):
    for p in sorted(pathlib.Path(root).rglob("*")):
        if not p.is_file() or p.suffix.lower() in BINARY or p.name == ".DS_Store":
            continue
        if any(fnmatch.fnmatch(p.name, x) for x in SELF_AUTHORED + tuple(excludes)):
            continue
        if globs and not any(fnmatch.fnmatch(p.name, g) for g in globs):
            continue
        yield p


def check(a):
    files = [p for root in a.archive for p in archive_files(root, a.glob, a.exclude)]
    if not a.archive and not (a.source or a.svg or a.git):
        sys.exit("no sources: give --archive, --source, --svg or --git")
    if a.archive and not files:
        sys.exit(f"no archive files under {a.archive}")
    if a.expect_files is not None and len(files) != a.expect_files:
        sys.exit(f"expected {a.expect_files} archive files, found {len(files)}")
    clean = (lambda s: norm(demark(s))) if a.markdown else norm
    bodies, times = [], {}
    for p in files + [pathlib.Path(s) for s in a.source]:
        if p.suffix.lower() == ".vtt":
            t, starts = vtt_text(p)
            times[len(bodies)] = (t, starts)
            bodies.append(clean(t))
        else:
            bodies.append(clean(p.read_text(encoding="utf-8", errors="replace")))
    bodies += [clean(svg_text(p)) for p in a.svg] + [clean(svg_text(None, git_show(g)) if g.endswith(".svg") else git_show(g)) for g in a.git]
    doc = pathlib.Path(a.doc)
    text = svg_text(doc) if doc.suffix == ".svg" else doc.read_text(encoding="utf-8")
    for anchor in filter(None, (a.start, a.end)):
        if text.count(anchor) != 1:
            sys.exit(f"anchor occurs {text.count(anchor)} times in {a.doc}, not once: {anchor}")
    if a.start:
        text = text[text.index(a.start):]
    if a.end:
        text = text[:text.index(a.end) + len(a.end)]
    if a.plant:
        text += {"italic": f'\n*"{PLANTED}"*\n', "italic-strict": f'\n*"{PLANTED}"*\n', "angle": f"\n«{PLANTED}»\n", "q": f"\n<q>{PLANTED}</q>\n",
                 "corner": f"\n「{PLANTED}」\n", "straight": f' "{PLANTED}" ', "blockquote": f"\n\n> {PLANTED}\n\n"}[a.style]
    if a.style == "blockquote":
        quotes = blockquotes(text)
    else:
        quotes = ["".join(m) if isinstance(m, tuple) else m for m in re.findall(STYLES[a.style], text, flags=re.S)]
        if a.style == "q":  # a <q> on a page may hold markup and entities
            quotes = [html.unescape(re.sub(r"<[^>]+>", "", q)) for q in quotes]
    skipped = [q for q in quotes if any(k in q for k in a.skip)]
    quotes = [q for q in quotes if q not in skipped and clean(q)]
    misses = []
    for q in quotes:
        i = found(q, bodies, clean)
        if i is None:
            misses.append(q)
            print("MISS:", " ".join(q.split())[:160])
        elif a.times and i in times:
            raw, starts = times[i]
            first = ELISION.split(" ".join(q.split()))[0].strip()
            at = re.sub(r"\s+", " ", raw).find(first)
            print("spoken", next((t for o, t in reversed(starts) if o <= at), "?") if at >= 0 else "?", "|", first[:80])
    print(f"{a.doc}: {len(quotes) - len(misses)} verified, {len(misses)} missed, {len(quotes)} total, "
          f"{len(bodies)} sources" + (f", {len(skipped)} skipped" if skipped else ""))
    return bool(quotes) and not misses


# --selftest: --plant proves the check runs, but a planted sentence fails under any normalizer, so it cannot catch a
# norm() loosened until misquotes pass. Each pair goes through the same norm() and found() the real check uses.
# MUST_PASS: one pair per encoding fold in norm() and demark(). MUST_CATCH: common misquote shapes, which the doc must
# fix, never the check. Each entry: (quote, [source bodies], markdown?).
MUST_PASS = [
    ("the Workflow tab", ["the Workﬂow tab"], False),                       # NFKC: fl ligature
    ("the customer's record", ["the customer’s record"], False),           # curly vs straight
    ("the interface", ["the inter­face"], False),                          # soft hyphen
    ("end of page next", ["end of page\fnext"], False),                         # form feed
    ('say "hi" now', ['say \\"hi\\" now'], False),                              # string-literal escapes
    ("first line second line", ["first line\n> second line"], False),           # blockquote marker
    ("first line second line", ["first line\n * second line"], False),          # code-comment marker
    ("two lines", ["two\n   lines"], False),                                     # whitespace
    ("this is great", ["this is [ __ ] great"], False),                         # ASR censor token
    ("alpha ... gamma", ["alpha beta gamma"], False),                            # elision, one source
    ("returns `STALE_REF` here", ["returns STALE_REF here"], True),             # --markdown code marks
    ("see the docs", ["see [the docs](https://x.example/d)"], True),            # --markdown link text
]
MUST_CATCH = [
    ("the vendor owns the record", ["the customer owns the record"], False),    # a changed word
    ("it does ship a server", ["it does not ship a server"], False),            # a dropped negation
    ("the record.", ["the record, which it keeps"], False),                     # punctuation typed inside the quote
    ("The loop stays", ["and the loop stays in your agent"], False),            # sentence-initial capital
    ("Gemini 3.5", ["Gemini-\n3.5"], False),                                     # line-break hyphen
    ("alpha ... omega", ["alpha beta", "omega"], False),                         # elided parts in two sources
    ("the customer owns it", ["the *customer* owns it"], False),                # emphasis without --markdown
]


def selftest():
    bad = []
    for want, cases in ((True, MUST_PASS), (False, MUST_CATCH)):
        for q, sources, md in cases:
            clean = (lambda s: norm(demark(s))) if md else norm
            if (found(q, [clean(s) for s in sources], clean) is not None) != want:
                bad.append(q)
                print(("MUST-PASS failed: " if want else "MUST-CATCH passed: ") + q)
    print(f"selftest: {len(MUST_PASS)} must-pass, {len(MUST_CATCH)} must-catch, {len(bad)} wrong")
    return not bad


def parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--doc")
    p.add_argument("--archive", action="append", default=[], help="folder of captured sources (recursive)")
    p.add_argument("--glob", action="append", default=[], help="only archive files whose name matches, e.g. '*.txt'")
    p.add_argument("--exclude", action="append", default=[], help="skip archive files whose name matches")
    p.add_argument("--source", action="append", default=[], help="one more source file, e.g. a doc of ours")
    p.add_argument("--svg", action="append", default=[], help="a slide whose <text> is a source")
    p.add_argument("--git", action="append", default=[], help="REPO@REV:PATH, a file at a pinned revision (a *.svg gives its slide text)")
    p.add_argument("--style", choices=sorted(STYLES), default="italic")
    p.add_argument("--skip", action="append", default=[], help="leave out quotes that contain this text (our own lines)")
    p.add_argument("--times", action="store_true", help="print the cue time where each quote found in a .vtt starts")
    p.add_argument("--markdown", action="store_true", help="strip Markdown links, emphasis and code marks on both sides")
    p.add_argument("--from", dest="start", help="check the doc only from this text, which must occur once")
    p.add_argument("--to", dest="end", help="check the doc only up to the end of this text, which must occur once")
    p.add_argument("--expect-files", type=int, help="fail unless the archives hold exactly N files")
    p.add_argument("--plant", action="store_true", help="add a planted quote; the run must then fail")
    p.add_argument("--all", action="store_true", help="check every read listed in scripts/quote-reads.json (after --selftest)")
    p.add_argument("--selftest", action="store_true", help="run the normalizer's must-pass and must-catch pairs")
    p.add_argument("--read", help="check the reads registered under this name, e.g. check-example-quotes (with --doc: "
                                  "the same sources against another doc)")
    return p


def main():
    a = parser().parse_args()
    if a.read:
        reads = [r for r in json.loads(pathlib.Path(__file__).with_name("quote-reads.json").read_text())
                 if r["name"] == a.read or r["name"].startswith(a.read + ":")]
        if not reads:
            sys.exit(f"no read named {a.read} in scripts/quote-reads.json")
        extra = (["--doc", a.doc] if a.doc else []) + (["--plant"] if a.plant else []) + (["--times"] if a.times else [])
        sys.exit(0 if all([check(parser().parse_args(shlex.split(r["args"]) + extra)) for r in reads]) else 1)
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.all:
        if not selftest():
            sys.exit(1)
        reads = json.loads(pathlib.Path(__file__).with_name("quote-reads.json").read_text())
        bad = [r["name"] for r in reads if not check(parser().parse_args(shlex.split(r["args"]) +
                                                                         (["--plant"] if a.plant else [])))]
        print(f"{len(reads) - len(bad)} of {len(reads)} reads pass" + (f"; failing: {', '.join(bad)}" if bad else ""))
        sys.exit(1 if bad else 0)
    if not a.doc:
        sys.exit("--doc is required (or --all)")
    sys.exit(0 if check(a) else 1)


if __name__ == "__main__":
    main()
