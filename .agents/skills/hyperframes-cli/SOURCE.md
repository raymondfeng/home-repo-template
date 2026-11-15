# Where this skill comes from

The files in this folder, except this one, are copied byte for byte from
[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes): the folder `skills/hyperframes-cli/` and the file `LICENSE`,
at commit `9701f0639c3614f4fb33f2a83973adafd179ef08` (2026-11-15). The licence is Apache-2.0, copyright HeyGen; `LICENSE` here is
theirs and covers this folder only. Do not edit the copied files: an update replaces them.

One of four HyperFrames skills copied here: `hyperframes` (read it first), `hyperframes-cli`, `hyperframes-registry` and
`media-use`. They tell the agent how to make a video as HTML and render it with the `hyperframes` command, which
runs through `npx hyperframes` and needs Node, Chrome and `ffmpeg`. Use them through the `make-video` skill.

To update the copy, run `python3 -I scripts/update-skills.py`, read `git diff`, and commit this folder by its path.
`python3 -I scripts/update-skills.py --check` says whether the copy is behind upstream. This file is written by that
script.
