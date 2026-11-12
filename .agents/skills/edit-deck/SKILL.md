---
name: edit-deck
description: 'Use when the owner asks to change, add, remove or reorder a slide in a deck of this repo, to export or publish a deck to .pptx, or to start a small new deck by hand — "update slide 3", "add a slide about X", "re-export the deck", "publish the deck".'
---

# Edit a deck

A deck here is a folder of hand-edited slides under `projects/<name>_ppt169_<date>/`: one SVG file for each slide in
`svg_output/`, and one notes file, `notes/total.md`. You edit a slide and export again. You never edit the `.pptx`,
and you never regenerate a deck that exists: the next export would erase both. `scripts/build-deck.sh` runs the whole
chain, and every step in it is a gate.

The scripts come from the `ppt-master` skill, of which this repo holds a trimmed copy
(`.agents/skills/ppt-master/SOURCE.md` says what it leaves out). Do not follow that skill's own workflow for an
existing deck: it generates a deck from a document, and it needs files the trimmed copy does not have.

## The chain

1. **Read the deck first.** Open the slides on both sides of the one you change, and take the colours, the fonts, the
   sizes and the positions from them. A deck has one visual system: a new value is a defect unless the owner asked
   for it. Use `<text>` with `<tspan>` for a line break. No `<style>`, no `class`, no `<foreignObject>`.
2. **Where a change goes is a decision.** If the request names a fact and a slide but not the place on it, show two
   placements and ask. For a deck that the owner has signed off, keep the old slide beside the new one (copy it to
   `projects/<deck>/candidates/`) until the owner accepts the change.
3. **Edit the SVG** in `svg_output/`, and the matching section of `notes/total.md`.
4. **If a slide is added, removed or moved, five things change together:**
   - the number in each file name (`NN_name.svg`), which sets the order;
   - the footer in each slide (`PNN / TT`), where the total changes on every slide;
   - the kicker in each slide (`NN · TITLE`), which is a separate string from the footer;
   - the headings in `notes/total.md` (`# NN_name`), which must match the file names one to one;
   - any slide that refers to another by number ("see slide 4"): search `svg_output/` for `slide [0-9]`.

   Add a new slide at the end unless the owner gives its place: nothing else then renumbers.
5. **Build:** `bash scripts/build-deck.sh projects/<deck>`. It stops on a notes heading or a footer that does not
   match, on an error from the quality checker, and on a failed export. Read a `STOP:` line and fix the slide; never
   change the script to pass. Warnings about ungrouped elements and page roles are expected for hand-edited slides.
6. **Look at every slide you changed.** A text change is a change of geometry. Open `svg_final/NN_name.svg` with the
   `browser-harness` skill and take a screenshot. Then measure with `getBBox()`: each text against the box it sits in,
   on both edges; text against text; and each text against the canvas (1280 by 720). Fix every overlap and build again.
7. **Publish when the owner says so:** `bash scripts/build-deck.sh projects/<deck> --publish`. It copies the export to
   `docs/deck/<name>.pptx` and keeps the previous file under `docs/deck/history/`. Commit the slide files, the notes
   and the `.pptx` by explicit paths, then rebuild the hub (`python3 -I scripts/build-hub.py`) and commit its files.
8. **Reply** with the slides that changed, what the checker and the visual check found, and the path of the file.

## A new deck by hand

`python3 .agents/skills/ppt-master/scripts/project_manager.py init <name> --format ppt169` makes the project folder.
Copy the slides of `projects/example-deck_ppt169_20261112/` as a start, and keep `lang="en"` (or your language) on the
root of the first slide. For a deck generated from a document, or one that uses icons, the owner installs the full
`ppt-master` skill for their user; bring the finished project into `projects/` and edit it here.

## What is in git

`svg_output/`, `notes/total.md` and the project's `README.md`. Everything else in a project is derived and is ignored:
`svg_final/`, `exports/`, `backup/`, `validation/`, the per-slide notes and the logs. So only the checkout that ran a
build has the export; the published copy under `docs/deck/` is the one that is shared.
