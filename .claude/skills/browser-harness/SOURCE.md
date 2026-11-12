# Where this skill comes from

The files in this folder, except this one, are copied byte for byte from
[browser-use/browser-harness](https://github.com/browser-use/browser-harness): the folder `skills/browser-harness/` and the file `LICENSE`,
at commit `c2420943526d41b9af6182d5c5f11b9cad506ab9` (2026-11-11). The licence is MIT, copyright Browser Use; `LICENSE` here is
theirs and covers this folder only. Do not edit the copied files: an update replaces them.

The skill tells the agent how to use the `browser-harness` command. It does not install the command. Install it
once for your user, following `references/install.md` in this folder, and check with `command -v browser-harness`.

To update the copy, run `python3 -I scripts/update-skills.py`, read `git diff`, and commit this folder by its path.
`python3 -I scripts/update-skills.py --check` says whether the copy is behind upstream. This file is written by that
script.
