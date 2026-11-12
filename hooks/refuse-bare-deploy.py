#!/usr/bin/env python3
"""PreToolUse hook (Bash), for Claude Code and for Codex: refuse a bare deploy command in this repo.

The site deploys only through the script that runs its gates (scripts/deploy.sh, the deploy-site skill). A bare deploy
skips them: run from the repo root it would ship node_modules, .agents/ and every draft. The commands that change
what a site serves are refused, with or without npx: `cf deploy`, `cf workers deployments create`,
`cf workers versions create`, `wrangler deploy`, `wrangler rollback`, `wrangler versions upload`,
`wrangler versions deploy`, `wrangler pages deploy`, and wrangler's `publish`, `triggers deploy` and
`versions secret put`. A command that only reads, such as a deployments list, passes. The list is a set of known
commands, not every way to change a site: see the last paragraph. Exit 2
blocks the call and shows the reason to the agent. A script that calls cf inside it is not affected: the hook sees
only the command. This is the pattern for any outward-facing command: copy the file and change the regex.

It is a guard against an accident by a cooperative agent, not a security boundary: a regex over a shell command can be
bypassed (a here-string fed to a shell, an evaluator other than `-c`). The boundary is the credential. Keep the deploy
token out of the agent's environment, and let scripts/deploy.sh or CI obtain it."""
import json, re, sys

FLAGS = r"(?:\s+-{1,2}[\w-]+(?:[ =](?!pages\b|deploy\b|publish\b|versions\b|upload\b|rollback\b|triggers\b|secret\b|put\b|workers\b|deployments\b|create\b)[^\s;&|]+)?)*"
RUNNER = r"(?:(?:npx|bunx|(?:pnpm|yarn|npm)\s+(?:dlx|exec))" + FLAGS + r"\s+)?"
BARE = re.compile(r"(?:^|[;&|(`\n]|\$\(|(?:\s-[A-Za-z]*c|\beval)\s+[\"']|\bthen\b|\bdo\b|\belse\b|\bexec\b|\bsudo\b)\s*(?:\w+=\S*\s+)*"
                  + RUNNER + r"(?:(?:\S*/)?wrangler(?:@\S+)?" + FLAGS + r"\s+(?:pages" + FLAGS + r"\s+(?:deploy|publish)|deploy|publish|rollback|triggers" + FLAGS + r"\s+deploy|versions" + FLAGS + r"\s+(?:upload|deploy|secret" + FLAGS + r"\s+(?:put|bulk|delete)))"
                  r"|(?:\S*/)?cf(?:@\S+)?" + FLAGS + r"\s+(?:deploy|workers" + FLAGS + r"\s+(?:deployments|versions)" + FLAGS + r"\s+create))\b")


def literal_spans(cmd):
    """Spans of text the shell will not run: terminated single-quoted strings and terminated quoted-delimiter heredoc
    bodies. Code, not a span: a quoted string after `-c` (any flag cluster ending in c, as in `bash -lc`) or `eval`, and a
    heredoc fed to a shell (`bash <<'EOF'`). Anything unterminated adds no span, so a match in it is refused (fail
    closed). A `#` comment is skipped to the end of its line and adds no span."""
    spans, i, n, state = [], 0, len(cmd), None
    while i < n:
        c = cmd[i]
        if state == "d":
            if c == "\\":
                i += 2
                continue
            if c == '"':
                state = None
        elif c == "\\":
            i += 2
            continue
        elif c == "#" and (i == 0 or cmd[i - 1] in " \t\n;&|()<>"):
            nl = cmd.find("\n", i)
            i = n if nl < 0 else nl
            continue
        elif c == '"':
            state = "d"
        elif c == "'":
            ansi = i > 0 and cmd[i - 1] == "$"
            j = i + 1
            while j < n and cmd[j] != "'":
                j += 2 if ansi and cmd[j] == "\\" else 1
            if j >= n:
                return spans
            if not ansi and not re.search(r"(?:\s-[A-Za-z]*c|\beval)\s+$", cmd[:i]):
                spans.append((i, j + 1))
            i = j + 1
            continue
        elif cmd.startswith("<<", i) and not cmd.startswith("<<<", i):
            m = re.match(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*", cmd[i:])
            if m:
                body = i + m.end()
                term = re.compile(r"\n[ \t]*" + re.escape(m.group(2)) + r"[ \t]*(?=\n|$)").search(cmd, body)
                if not term:
                    return spans
                line = cmd[cmd.rfind("\n", 0, i) + 1:body]  # the whole marker line: `cat <<'EOF' | sh` feeds a shell too
                to_shell = re.search(r"(?:^|[;&|(]\s*|\s)(?:\S*/)?(?:ba|z|da|k)?sh\b|\beval\b|\bsource\b|\bxargs\b|>\(", line)
                if m.group(1) and not to_shell:
                    spans.append((body, term.end()))
                i = term.end()
                continue
        i += 1
    return spans


def refused(cmd):
    spans = literal_spans(cmd)
    return any(not any(a <= m.start() and m.end() <= b for a, b in spans) for m in BARE.finditer(cmd))


def main():
    try:
        cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return 0
    if isinstance(cmd, list):  # a harness may send the command as a list of arguments
        cmd = " ".join(str(c) for c in cmd)
    if not isinstance(cmd, str):
        return 0
    if refused(cmd):
        print("Refused: a bare deploy skips the deploy gates. Deploy with `bash scripts/deploy.sh --deploy` "
              "(the deploy-site skill). A deploy is the owner's command.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
