# Showcase video generation — ARCHIVED 2026-09-21

Archived because the workflow does not use the showcase videos right now.
Nothing is deleted; the steps below restore the capability exactly.

## What is here

| File | Was at | Role |
|---|---|---|
| `render_font_showcase.py` | `bin/` | Renders the 35-second 5-scene typewriter showcase. Streams raw frames straight into ffmpeg over stdin (no intermediate frame files). Works for both canvases: 1920x1080 (16:9 main) and 1920x960 (2:1 Etsy). Optional `--audio` muxes a music bed. |
| `write_etsy_video_script.py` | `bin/` | Writes the human-readable Etsy scene script text next to the videos. Does not render. |

## Contract the renderer enforced

- exactly **5 scenes**, each exactly **7 seconds** — 35 s total, 30 fps;
- scene 5 contains exactly the font name and nothing else;
- scene copy keeps to at most four words per line;
- `charactersPerSecond` drives the typewriter reveal, house range 8–10;
- canvas `#111111` background, `#F4EEE7` ink;
- it validates the config and refuses a malformed one, so render **before**
  writing a completion summary.

## How to reinstate

1. **Restore the scripts.**

   ```bash
   git mv archive/video/render_font_showcase.py bin/render_font_showcase.py
   git mv archive/video/write_etsy_video_script.py bin/write_etsy_video_script.py
   ```

2. **Re-add the video step to Agent 13.** It was `## 🎬 STEP 2: SHOWCASE VIDEOS
   (MAIN 16:9 + ETSY 2:1)` in `agents/agent-13-font-prep-specialist.md`, and it
   is recoverable in full with:

   ```bash
   git show <commit-before-2026-09-21>:agents/agent-13-font-prep-specialist.md
   ```

3. **Re-add video rendering to the packager.** `bin/prepare_font_package.py` had
   a `render_videos()` function and a `--skip-videos` flag; it rendered when
   `video/showcase.config.json` and `video/etsy-showcase.config.json` already
   existed, and skipped with a clear message when they did not. Restore it from
   git history alongside the spec step.

4. **Update the orchestrator and docs** that named the videos: the
   `font-prep-specialist` wrapper, `agents/agent-28-full-workflow.md`,
   `.opencode/skills/full-workflow/SKILL.md`, and `bin/README.md`.

5. **Check the external dependency**: `ffmpeg` on PATH (the renderer exits with
   `error: ffmpeg not found on PATH` if absent). `ffprobe` is useful for
   verifying the output but is not required to render.

## Verified behaviour at the time of archiving

- 16:9 main: 1050 frames, 35.000 s, 1920x1080, 30 fps.
- 2:1 Etsy: 1050 frames, 35.000 s, 1920x960, 30 fps.
- Rendering both took about 29 s; the renderer was never the workflow
  bottleneck.
