# Where this skill comes from

`SKILL.md` and `LICENSE` in this folder are copied, byte for byte, from
[browser-use/browser-harness](https://github.com/browser-use/browser-harness) at commit
`c2420943526d41b9af6182d5c5f11b9cad506ab9` (2026-11-12). The licence is MIT, copyright Browser Use; `LICENSE` here is theirs
and covers `SKILL.md` only. Do not edit `SKILL.md`: an update replaces it.

The skill tells the agent how to use the `browser-harness` command. It does not install the command. Install it
once for your user, following
[install.md](https://github.com/browser-use/browser-harness/blob/main/install.md), and check with
`command -v browser-harness`.

To update the copy:

```bash
SHA=$(gh api repos/browser-use/browser-harness/commits/main --jq .sha)
curl -sL -o .claude/skills/browser-harness/SKILL.md "https://raw.githubusercontent.com/browser-use/browser-harness/$SHA/SKILL.md"
curl -sL -o .claude/skills/browser-harness/LICENSE  "https://raw.githubusercontent.com/browser-use/browser-harness/$SHA/LICENSE"
```

Then read the diff, and write the new commit and date in this file.
