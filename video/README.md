# video/

One folder for each video. A video is an HTML project that the `hyperframes` command renders to a file: `index.html`
mounts one scene file for each scene from `compositions/`. Use the `make-video` skill for any change.

## What git tracks

Git tracks the files that hold a video's decisions, and ignores what a build can make again.

| Tracked | Holds |
|---|---|
| `BRIEF.md` | The message, the audience, the length, the look, and each real asset with the scene that uses it |
| `STORYBOARD.md` | The scenes in order: time, what is on screen, the motion, and why the scene exists |
| `index.html`, `compositions/` | The video itself |
| `assets/` | The real captures, images, fonts and sound the video uses |
| `reviews/` | One folder for each reviewed cut: the contact sheet and `REVIEW.md` |
| `hyperframes.json`, `meta.json`, `package.json`, `AGENTS.md`, `CLAUDE.md` | What `hyperframes init` wrote |

Ignored: `renders/`, `.hyperframes/` and `node_modules/`. The published file lives where it is served, under
`docs/video/`.

## The gates

A video passes these in order. Each gate leaves a file, so a later session can see which gate a video reached.

1. **Brief and assets.** `BRIEF.md` names every real capture. A missing capture stops the work: nobody draws a
   replacement for a real screen.
2. **Storyboard.** `STORYBOARD.md` is agreed before any scene is built.
3. **Build and check.** `bash scripts/build-video.sh video/<name>`: the HyperFrames check with no errors, the render,
   a check of the file's length, and a contact sheet.
4. **Review the rendered cut.** Read the contact sheet without the storyboard open. Write `REVIEW.md` beside it: the
   three largest defects, each with a time, the evidence and a fix. Fix them and build again.
5. **Publish.** `--publish` copies the render to `docs/video/`. The owner approves the cut before this step.
