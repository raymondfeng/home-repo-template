# Review: example-video, first cut (2026-11-15)

Read from `contact-sheet.jpg`, one frame for each second, before the storyboard was reopened.

| # | Time | Defect | Evidence | Fix | Done |
|---|---|---|---|---|---|
| 1 | 4 to 9 s | The row text is too small for a player at half width | The row detail was 36 px on a 1920 canvas, which is 18 px at 960 | Labels to 56 px, detail to 44 px, rows 140 px apart | Yes |
| 2 | 0 to 4 s | The lower two thirds of the frame are empty | The title block ends at about a third of the height | Left as it is: the example shows the least that passes, and a real video puts its subject there | No |
| 3 | 0 s | The check warned that nothing moved for three seconds in scene 1 | `dead_stretch`, 0.5 to 3.6 s | A rule draws under the title from 0.8 s | Yes |

The contact sheet in this folder is from the cut after the fixes.
