#!/usr/bin/env python3
"""Write the README's diagram as two SVG files, one for a light page and one for a dark page.

    python3 -I scripts/build-readme-diagram.py           # write docs/diagrams/home-repo-{light,dark}.svg
    python3 -I scripts/build-readme-diagram.py --check   # exit 1 if either file is not what this script would write

GitHub shows an SVG in a README as an image: no script runs, and no web font or other outside file loads. So each file
is self-contained and uses system fonts. Edit the text or the layout here, never in the two files. A change to a
string is a change to the geometry: open both files in a browser and look before you commit."""
import html, pathlib, sys

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrams"
THEMES = {
    "light": dict(text="#1f2328", muted="#59636e", line="#59636e", group="#f6f8fa", box="#ffffff", edge="#d1d9e0", accent="#0969da"),
    "dark": dict(text="#f0f6fc", muted="#9198a1", line="#9198a1", group="#151b23", box="#0d1117", edge="#3d444d", accent="#4493f8"),
}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def box(x, y, w, h, title, lines, c, mono=False):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{c["box"]}" stroke="{c["edge"]}"/>']
    cx, n = x + w / 2, len(lines)
    ty = y + h / 2 - 9 * n + 5
    fam = ' font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"' if mono else ""
    out.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="14" font-weight="600" fill="{c["text"]}"{fam}>{html.escape(title)}</text>')
    for i, ln in enumerate(lines):
        out.append(f'<text x="{cx}" y="{ty + 18 * (i + 1)}" text-anchor="middle" font-size="12" fill="{c["muted"]}">{html.escape(ln)}</text>')
    return out


def arrow(x, y1, y2, c, dashed=False):
    """A vertical arrow from y1 to y2, with its head at y2."""
    d = 1 if y2 > y1 else -1
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    return [f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 7 * d}" stroke="{c["line"]}" stroke-width="1.5"{dash}/>',
            f'<path d="M{x - 5} {y2 - 9 * d} L{x + 5} {y2 - 9 * d} L{x} {y2} Z" fill="{c["line"]}"/>']


def label(x, y, lines, c):
    return [f'<text x="{x}" y="{y + 17 * i}" font-size="12.5" fill="{c["text"]}">{html.escape(ln)}</text>' for i, ln in enumerate(lines)]


def svg(c):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560" width="960" height="560" font-family="{FONT}" role="img" '
         f'aria-labelledby="t d">',
         '<title id="t">How a Home Repo works</title>',
         '<desc id="d">Every session starts in the Home Repo, which holds the rules, the shared skills, the record and the checks. '
         'The agent follows a pointer to another repo, writes designs and decisions back, and can publish the record as a site.</desc>']
    # Top row
    p.append(f'<rect x="150" y="20" width="220" height="50" rx="25" fill="{c["box"]}" stroke="{c["accent"]}" stroke-width="1.5"/>')
    p.append(f'<text x="260" y="50" text-anchor="middle" font-size="14" font-weight="600" fill="{c["text"]}">You and your agent</text>')
    p += box(520, 20, 240, 50, "Outside sources and meetings", [], c)
    p += arrow(260, 70, 130, c) + label(272, 98, ["1. Every session", "starts here"], c)
    p += arrow(640, 70, 130, c) + label(652, 98, ["check-out,", "capture-sync"], c)
    # The Home Repo
    p.append(f'<rect x="60" y="130" width="840" height="160" rx="8" fill="{c["group"]}" stroke="{c["accent"]}" stroke-width="1.5"/>')
    p.append(f'<text x="80" y="155" font-size="14" font-weight="700" fill="{c["accent"]}">Home Repo</text>')
    for x, title, lines in ((80, "AGENTS.md", ["rules and", "Other Repos pointers"]), (285, ".agents/skills", ["the shared", "method"]),
                            (490, "docs/", ["decisions, designs,", "reads, syncs"]), (695, "scripts/ and hooks", ["quote check,", "credential scan"])):
        p += box(x, 170, 185, 100, title, lines, c, mono=True)
    # Between the groups
    p += arrow(200, 290, 390, c) + label(212, 335, ["2. Follow a pointer:", "path, remote, hint"], c)
    p += arrow(540, 390, 290, c, dashed=True) + label(552, 335, ["3. Designs and decisions", "are written back"], c)
    p += arrow(800, 290, 410, c) + label(812, 335, ["4. deploy.sh,", "through its gates"], c)
    # The other repos, and the site
    p.append(f'<rect x="60" y="390" width="560" height="150" rx="8" fill="{c["group"]}" stroke="{c["edge"]}" stroke-width="1.5"/>')
    p.append(f'<text x="80" y="415" font-size="14" font-weight="700" fill="{c["text"]}">Your other repos</text>')
    p += box(80, 430, 160, 90, "Product repo", ["code, tests,", "its own AGENTS.md"], c)
    p += box(260, 430, 160, 90, "Library repo", ["its own rules", "and history"], c)
    p += box(440, 430, 160, 90, "More repos", ["one pointer", "for each"], c)
    p += box(700, 410, 200, 110, "Site", ["a Cloudflare Worker,", "optional"], c)
    return "\n".join(p + ["</svg>"]) + "\n"


def main():
    files = {OUT / f"home-repo-{name}.svg": svg(c) for name, c in THEMES.items()}
    if sys.argv[1:] == ["--check"]:
        sys.exit(0 if all(f.exists() and f.read_text(encoding="utf-8") == want for f, want in files.items()) else 1)
    for f, want in files.items():
        f.write_text(want, encoding="utf-8")
        print(f"built {f.relative_to(OUT.parent.parent)}")


if __name__ == "__main__":
    main()
