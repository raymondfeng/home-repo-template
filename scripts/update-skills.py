#!/usr/bin/env python3
"""Refresh the skills that this repo copies from outside, each from its upstream repo at one commit.

    python3 -I scripts/update-skills.py            # fetch the newest upstream commit and rewrite each copy
    python3 -I scripts/update-skills.py --check    # exit 1 if a copy is behind upstream; change nothing
    python3 -I scripts/update-skills.py --ref SHA  # copy from this commit instead of the newest one

A copied skill is a set of instructions that the agent follows, so an update is a change to read, not to trust. This
script never commits. After it runs: read `git diff`, then commit the folder by its path. Each copy keeps the
upstream licence file beside it, and SOURCE.md records the commit it came from.

The script reads the upstream archive in memory and writes only regular files from the one folder it names. A
symlink in the archive is followed only when its target is inside the same archive. It needs Python 3 and network
access to github.com, and nothing else."""
import io, json, pathlib, posixpath, re, sys, tarfile, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
# name: the folder under .claude/skills/ · repo: owner/name on GitHub · path: the skill's folder in that repo ·
# licence: the licence file in that repo, copied beside the skill
VENDORED = [
    dict(name="browser-harness", repo="browser-use/browser-harness", path="skills/browser-harness", licence="LICENSE",
         holder="Browser Use", spdx="MIT",
         note="The skill tells the agent how to use the `browser-harness` command. It does not install the command. Install it\n"
              "once for your user, following `references/install.md` in this folder, and check with `command -v browser-harness`."),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "update-skills", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def commit(repo, ref):
    d = json.loads(get(f"https://api.github.com/repos/{repo}/commits/{ref}"))
    return d["sha"], d["commit"]["committer"]["date"][:10]


def archive(repo, sha):
    """{path inside the repo: member} and a reader that follows a symlink only inside the archive."""
    tar = tarfile.open(fileobj=io.BytesIO(get(f"https://codeload.github.com/{repo}/tar.gz/{sha}")), mode="r:gz")
    members = {}
    for m in tar.getmembers():
        parts = m.name.split("/", 1)
        if len(parts) == 2:
            members[parts[1]] = m

    def read(path, depth=0):
        m = members.get(path)
        if m is None or depth > 5:
            sys.exit(f"{repo}@{sha[:8]}: {path} is missing, or a link chain is too long")
        if m.issym():
            target = posixpath.normpath(posixpath.join(posixpath.dirname(path), m.linkname))
            if target.startswith("..") or posixpath.isabs(m.linkname):
                sys.exit(f"{repo}@{sha[:8]}: {path} links outside the archive ({m.linkname}); not copied")
            return read(target, depth + 1)
        if not m.isfile():
            sys.exit(f"{repo}@{sha[:8]}: {path} is not a regular file")
        return tar.extractfile(m).read()

    return members, read


def source_md(v, sha, date):
    return f"""# Where this skill comes from

The files in this folder, except this one, are copied byte for byte from
[{v["repo"]}](https://github.com/{v["repo"]}): the folder `{v["path"]}/` and the file `{v["licence"]}`,
at commit `{sha}` ({date}). The licence is {v["spdx"]}, copyright {v["holder"]}; `{v["licence"]}` here is
theirs and covers this folder only. Do not edit the copied files: an update replaces them.

{v["note"]}

To update the copy, run `python3 -I scripts/update-skills.py`, read `git diff`, and commit this folder by its path.
`python3 -I scripts/update-skills.py --check` says whether the copy is behind upstream. This file is written by that
script.
"""


def pinned(dest):
    f = dest / "SOURCE.md"
    m = re.search(r"at commit `([0-9a-f]{40})`", f.read_text(encoding="utf-8")) if f.exists() else None
    return m.group(1) if m else None


def main():
    args = sys.argv[1:]
    check = "--check" in args
    ref = args[args.index("--ref") + 1] if "--ref" in args else "HEAD"
    behind = 0
    for v in VENDORED:
        dest = ROOT / ".claude" / "skills" / v["name"]
        sha, date = commit(v["repo"], ref)
        have = pinned(dest)
        if check:
            state = "current" if have == sha else f"behind: pinned {have[:8] if have else 'nothing'}, upstream {sha[:8]} ({date})"
            behind += have != sha
            print(f"{v['name']}: {state}")
            continue
        members, read = archive(v["repo"], sha)
        prefix = v["path"].rstrip("/") + "/"
        want = {p[len(prefix):]: read(p) for p, m in members.items() if p.startswith(prefix) and (m.isfile() or m.issym())}
        if "SKILL.md" not in want:
            sys.exit(f"{v['repo']}@{sha[:8]}: no SKILL.md under {v['path']}/")
        want[v["licence"]] = read(v["licence"])
        want["SOURCE.md"] = source_md(v, sha, date).encode("utf-8")
        old = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()} if dest.exists() else set()
        changed = sorted(r for r, b in want.items() if not (dest / r).exists() or (dest / r).read_bytes() != b)
        for rel in sorted(old - set(want)):
            (dest / rel).unlink()
        for rel, data in want.items():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            (dest / rel).write_bytes(data)
        removed = sorted(old - set(want))
        print(f"{v['name']}: {v['repo']}@{sha[:8]} ({date}), {len(want)} files; "
              + (f"changed: {', '.join(changed)}" if changed else "nothing changed")
              + (f"; removed: {', '.join(removed)}" if removed else ""))
    if check:
        sys.exit(1 if behind else 0)
    print("Read `git diff` before you commit: a skill is instructions that the agent follows.")


if __name__ == "__main__":
    main()
