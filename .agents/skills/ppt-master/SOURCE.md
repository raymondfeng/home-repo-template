# Where this skill comes from

The files in this folder, except this one, are copied byte for byte from
[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master): part of the folder `skills/ppt-master/`,
at commit `01fe549371b98f44be22cd337bbc911013452f09` (2026-11-12). The licence is MIT, copyright Hugo He; `LICENSE` here is
theirs and covers this folder only. Do not edit the copied files: an update replaces them.

This is a trimmed copy: `SKILL.md`, `scripts/`, `workflows/`, `requirements.txt`, and the licence and sponsor files,
which the skill's own integrity check requires and which must stay. It covers editing the slides
of an existing deck project and exporting it to `.pptx`. It leaves out upstream's `templates/` and `references/`
(about 100 MB of layouts, icons and style guides), which are needed to generate a new deck from a document and
for any slide that uses an icon. For those, install the full skill for your user (`npx skills add hugohe3/ppt-master`).
The export needs `pip install python-pptx`.

To update the copy, run `python3 -I scripts/update-skills.py`, read `git diff`, and commit this folder by its path.
`python3 -I scripts/update-skills.py --check` says whether the copy is behind upstream. This file is written by that
script.
