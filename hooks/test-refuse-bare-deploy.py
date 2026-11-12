#!/usr/bin/env python3
"""Cases for refuse-bare-deploy.py: python3 -I hooks/test-refuse-bare-deploy.py (exit 1 on any wrong verdict).
The CLI name is built by concatenation so that the hook does not refuse the command that edits or runs this file."""
import json, pathlib, subprocess, sys
W, HOOK = "wran" + "gler", pathlib.Path(__file__).with_name("refuse-bare-deploy.py")
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
# The Worker commands: cf deploy, wrangler deploy and wrangler versions upload, with the same shell shapes.
BLOCK += ["cf deploy dist", "npx cf deploy dist", "npx --yes cf@1.0.0-beta.31 deploy dist --message x", "cd w && cf deploy",
          "CLOUDFLARE_ACCOUNT_ID=x npx cf deploy dist", "bash -c 'npx cf deploy dist'", "node_modules/.bin/cf deploy",
          "cf --profile work deploy dist", f"npx {W} deploy", f"{W} deploy --config x.jsonc", f"npx --yes {W}@4 deploy",
          f"{W} versions upload", f"npx {W} versions --x y upload", f"echo ok; {W} deploy"]
BLOCK += [f"{W} rollback", f"npx {W} rollback --message x", f"{W} versions deploy", f"npx {W} versions deploy --yes",
          "cf workers deployments create --worker x", "npx cf@1 workers deployments create", "cf workers versions create --worker x"]
ALLOW = ["cf deploy".join(["echo '", "'"]), "npx cf@1.0.0-beta.31 workers deployments list --worker x", "cf workers scripts search --name x",
         "cf zero-trust access applications create --body '{}'", "cf docs search deploy", f"npx {W} deployments list --json",
         f"{W} versions list", "git commit -m 'cf deploy notes'", "grep -n 'cf deploy' scripts/deploy.sh", "scf deploy", "cf deployments", "cf workers deployments get x", "cf workers versions list --worker x", f"{W} rollbacks", f"{W} versions view x",
         "bash scripts/deploy.sh --deploy", f'grep -n "{W} pages deploy" AGENTS.md',
         f"npx --yes {W} pages deployment list --project-name my-site", f"git log --grep {W}",
         f"echo 'see {W} pages deploy in AGENTS.md'",
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
# The input's shape: a list of arguments is joined and checked; anything that is not a command is let through.
SHAPES = [(2, {"tool_input": {"command": ["npx", W, "pages", "deploy", "d"]}}), (0, {"tool_input": {"command": ["ls", "-la"]}}),
          (0, {"tool_input": {"command": None}}), (0, {"tool_input": "x"}), (0, {})]
for want, payload in SHAPES:
    rc = subprocess.run([sys.executable, "-I", str(HOOK)], input=json.dumps(payload), text=True, capture_output=True).returncode
    if rc != want:
        bad += 1
        print(f"WRONG: exit {rc}, want {want}: {payload}")
print(f"{len(SHAPES)} input shapes checked")
print(f"{len(BLOCK)} refused, {len(ALLOW)} allowed, {bad} wrong")
sys.exit(1 if bad else 0)
