#!/usr/bin/env python3
"""Cases for refuse-bare-wrangler.py: python3 -I .claude/hooks/test-refuse-bare-wrangler.py (exit 1 on any wrong verdict).
The CLI name is built by concatenation so that the hook does not refuse the command that edits or runs this file."""
import json, pathlib, subprocess, sys
W, HOOK = "wran" + "gler", pathlib.Path(__file__).with_name("refuse-bare-wrangler.py")
BLOCK = [f"npx --yes {W} pages deploy $DIST --project-name my-site", f"cd x && npx {W} pages deploy d",
         f"{W} pages deploy dist", f"FOO=1 npx -y {W}@4.1 pages deploy d", f"node_modules/.bin/{W} pages deploy d",
         f"pnpm dlx {W} pages deploy d", f"npx {W} --cwd /tmp/d pages deploy .", f"npx {W} pages --config x deploy d",
         f'bash -c "npx {W} pages deploy d"', f"npx -p {W}@4 {W} pages deploy d", f"npm exec {W} pages deploy d",
         f"cat > d.md <<'EOF'\ntext\nEOF\nnpx {W} pages deploy d",
         f"cat <<<x\nnpx {W} pages deploy d\nx", f"echo `npx {W} pages deploy d`",
         f"bash -c 'npx {W} pages deploy d'", f"echo \"x\" | npx {W} pages deploy d",
         f"echo \"it's\"; npx {W} pages deploy d; echo \"'\"", f"bash -lc 'npx {W} pages deploy d'",
         f"eval 'npx {W} pages deploy d'", f"cat <<EOF\n$(npx {W} pages deploy d)\nEOF",
         f"echo a #'\nnpx {W} pages deploy d\necho '", f"echo 'unterminated\nnpx {W} pages deploy d",
         f"bash <<'EOF'\nnpx {W} pages deploy d\nEOF", f"cat <<'EOF'\nnpx {W} pages deploy d",
         f"echo $'it\\'s'; npx {W} pages deploy d",
         f"cat <<'EOF' | sh\nnpx {W} pages deploy d\nEOF", f"echo x)#'\nnpx {W} pages deploy d\n'"]
ALLOW = ["bash scripts/deploy.sh --deploy", f'grep -n "{W} pages deploy" CLAUDE.md',
         f"npx --yes {W} pages deployment list --project-name my-site", f"git log --grep {W}",
         f"echo 'see {W} pages deploy in CLAUDE.md'",
         f"cat > d.md <<'EOF'\n| Hook | any `{W} pages deploy` |\n{W} pages deploy x\nEOF\nwc -l d.md",
         f"echo '| `{W} pages deploy` |'"]
bad = 0
for want, cmds in ((2, BLOCK), (0, ALLOW)):
    for cmd in cmds:
        rc = subprocess.run([sys.executable, "-I", str(HOOK)], input=json.dumps({"tool_input": {"command": cmd}}),
                            text=True, capture_output=True).returncode
        if rc != want:
            bad += 1
            print(f"WRONG: exit {rc}, want {want}: {cmd}")
print(f"{len(BLOCK)} refused, {len(ALLOW)} allowed, {bad} wrong")
sys.exit(1 if bad else 0)
