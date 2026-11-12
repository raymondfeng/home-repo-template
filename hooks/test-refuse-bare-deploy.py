#!/usr/bin/env python3
"""Cases for refuse-bare-deploy.py: python3 -I hooks/test-refuse-bare-deploy.py (exit 1 on any wrong verdict).
The CLI name is built by concatenation so that the hook does not refuse the command that edits or runs this file."""
import json, pathlib, subprocess, sys
C, HOOK = "c" + "f", pathlib.Path(__file__).with_name("refuse-bare-deploy.py")
D = f"{C} deploy"
BLOCK = [f"{D} dist", f"npx {D} dist", f"npx --yes {C}@1.0.0-beta.31 deploy dist --message x", f"cd w && {D}",
         f"CLOUDFLARE_ACCOUNT_ID=x npx {D} dist", f"FOO=1 npx -y {C}@1 deploy d", f"node_modules/.bin/{D}",
         f"pnpm dlx {D} d", f"npm exec {D} d", f"npx -p {C}@1 {D} d", f"{C} --profile work deploy dist",
         f'bash -c "npx {D} d"', f"bash -c 'npx {D} d'", f"bash -lc 'npx {D} d'", f"eval 'npx {D} d'",
         f"cat > d.md <<'EOF'\ntext\nEOF\nnpx {D} d", f"cat <<<x\nnpx {D} d\nx", f"echo `npx {D} d`",
         f"echo \"x\" | npx {D} d", f"echo \"it's\"; npx {D} d; echo \"'\"", f"cat <<EOF\n$(npx {D} d)\nEOF",
         f"echo a #'\nnpx {D} d\necho '", f"echo 'unterminated\nnpx {D} d", f"bash <<'EOF'\nnpx {D} d\nEOF",
         f"cat <<'EOF'\nnpx {D} d", f"echo $'it\\'s'; npx {D} d", f"cat <<'EOF' | sh\nnpx {D} d\nEOF",
         f"echo x)#'\nnpx {D} d\n'", f"echo ok; {D}",
         f"{C} workers deployments create --worker x", f"npx {C}@1 workers deployments create",
         f"{C} workers versions create --worker x", f"{C} workers --profile p versions create"]
ALLOW = ["bash scripts/deploy.sh --deploy", f"grep -n '{D}' scripts/deploy.sh", f"echo 'see {D} in AGENTS.md'",
         f"cat > d.md <<'EOF'\n| Hook | any `{D}` |\n{D} x\nEOF\nwc -l d.md", f"echo '| `{D}` |'",
         f"git commit -m '{D} notes'", f"git log --grep {C}", f"npx {C}@1.0.0-beta.31 workers deployments list --worker x",
         f"{C} workers scripts search --name x", f"{C} zero-trust access applications create --body '{{}}'",
         f"{C} docs search deploy", f"{C} workers deployments get x", f"{C} workers versions list --worker x",
         f"{C} auth login", f"s{D}", f"{C} deployments", f"{C} workers delete x", f"{C} deploy-notes.md"]
bad = 0
for want, cmds in ((2, BLOCK), (0, ALLOW)):
    for cmd in cmds:
        rc = subprocess.run([sys.executable, "-I", str(HOOK)], input=json.dumps({"tool_input": {"command": cmd}}),
                            text=True, capture_output=True).returncode
        if rc != want:
            bad += 1
            print(f"WRONG: exit {rc}, want {want}: {cmd}")
# The input's shape: a list of arguments is joined and checked; anything that is not a command is let through.
SHAPES = [(2, {"tool_input": {"command": ["npx", C, "deploy", "d"]}}), (0, {"tool_input": {"command": ["ls", "-la"]}}),
          (0, {"tool_input": {"command": None}}), (0, {"tool_input": "x"}), (0, {})]
for want, payload in SHAPES:
    rc = subprocess.run([sys.executable, "-I", str(HOOK)], input=json.dumps(payload), text=True, capture_output=True).returncode
    if rc != want:
        bad += 1
        print(f"WRONG: exit {rc}, want {want}: {payload}")
print(f"{len(SHAPES)} input shapes checked")
print(f"{len(BLOCK)} refused, {len(ALLOW)} allowed, {bad} wrong")
sys.exit(1 if bad else 0)
