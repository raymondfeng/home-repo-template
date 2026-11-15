---
name: make-video
description: 'Use when the owner asks for a video in this repo, or to change, render or publish one — "make a short video about X", "a demo video", "an explainer", "re-render the video", "publish the video" — and for any edit inside a folder under video/.'
---

# Make a video

A video here is a folder under `video/`: an HTML project that the `hyperframes` command renders to a file.
`scripts/build-video.sh` runs the check, the render, a check of the file and a contact sheet, and every step in it
is a gate. `video/README.md` says what git tracks.

How to write the HTML is in the `hyperframes` skill, which this repo holds as a copy with three more
(`hyperframes-cli`, `hyperframes-registry`, `media-use`). Read `hyperframes` before you write a scene: its contract
decides whether a scene renders at all. This skill is the order of work around it.

## The gates

1. **Brief.** Write `video/<name>/BRIEF.md` with the owner: the message in one sentence, the audience, the length, the
   canvas, whether it has sound, the look, and each real asset with the scene that uses it. Take the look from the
   deck or the site if one exists, so that the project has one visual system.
   - A video that shows a real screen uses a real capture, taken with the `browser-harness` skill and saved under
     `assets/`. If a capture is missing, stop. Never draw a replacement for a real screen.
   - Never invent a number, a quote or a customer name for a frame. Write `[FILL]` in the brief and ask.
2. **Storyboard.** Write `STORYBOARD.md`: one row for each scene, with its file, its time, what is on screen, the
   motion, and why the scene exists. Show it to the owner and wait for agreement before you build a scene. A scene
   with no reason is cut here, where a cut is cheap.
3. **Build.** `npx hyperframes init video/<name> --non-interactive --skip-skills --example blank` for a new project.
   Then one scene file for each storyboard row under `compositions/`, mounted from `index.html`. Keep the first frame
   non-empty: it is the thumbnail.
4. **Check and render:** `bash scripts/build-video.sh video/<name>`. It stops if the brief or the storyboard is
   missing, on any error from the HyperFrames check, on a failed render, and if the file's length is not the length
   the root declares. It also stops if a mounted scene is missing, has another id than its host, or
   does not register its timeline: the tool's own check lets that through, and the scene then renders as a still.
   Read a `STOP:` line and fix the scene; never change the script to pass. Weigh each warning: fix it or say why it
   stands. The check does not judge whether text fits or reads well. In a test, a line far too long for the frame
   passed with one warning. The review in the next step is what finds that.
5. **Review the rendered cut.** Open `reviews/contact-sheet.jpg`, which has one frame for each second, and read it
   before you reopen the storyboard. Then write `reviews/REVIEW.md`: the three largest defects, each with its time,
   the evidence and a fix. Check at least these: text readable at the width the video will be played at; the subject
   is the largest thing in the frame; no element crosses the text it sits beside; no part of the frame is empty for
   no reason; a changed screen holds long enough to read. Fix the three and build again. Stop when a review finds
   nothing larger than a matter of taste.
6. **Publish when the owner says so:** `bash scripts/build-video.sh video/<name> --publish`. It copies the render to
   `docs/video/<name>.mp4`. Commit the project's tracked files and the published file by explicit paths, then rebuild
   the hub (`python3 -I scripts/build-hub.py`) and commit its files.
7. **Reply** with what the check and the review found, what you fixed, and the path of the file.

## Sound

A video under about 15 seconds needs no sound. A longer one that tells something usually has a voice or music. Both
go through the `media-use` skill. A voice needs a provider and a key that the owner supplies: ask, and do not read a
key from a file. Keep the narration text in the project, so that the voice can be made again.

## What to know about the tool

- The command runs as `npx hyperframes`. It needs Node, Chrome and `ffmpeg`. The build script pins a version.
- The command may say that its skills are out of date and name `npx hyperframes skills update`. That updates skills
  in the owner's user folder, not the copies here. Update the copies with
  `python3 -I scripts/update-skills.py hyperframes hyperframes-cli hyperframes-registry media-use`, and read the diff.
- `AGENTS.md` and `CLAUDE.md` inside a video folder are written by `hyperframes init`. Leave them.
