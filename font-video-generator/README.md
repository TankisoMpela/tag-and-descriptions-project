# Font Showcase Video Generator

Reusable Remotion generator for simple, text-only font showcase videos.

## Output

- YouTube landscape: 1920x1080
- Etsy landscape: 1920x960 (2:1), using the same text-only renderer
- 30 FPS
- Default duration: 35 seconds (five 7-second scenes)
- No images, transitions, callouts, or style switching
- Character-by-character typing reveals

## Render a font

From this directory:

```bash
node scripts/render-showcase.mjs \
  --font /absolute/path/to/Font-Regular.woff2 \
  --name "Font Name" \
  --slug font-name \
   --config showcase.config.json \
   --output out/font-name-font-showcase.mp4
```

For Etsy's dedicated 2:1 video, pass the dimensions explicitly. The config and
rendered composition remain otherwise identical:

```bash
node scripts/render-showcase.mjs \
  --font /absolute/path/to/Font-Regular.woff2 \
  --name "Font Name" \
  --slug font-name-etsy \
  --width 1920 \
  --height 960 \
  --config etsy-showcase.config.json \
  --output out/font-name-etsy-video.mp4
```

The font is copied to `public/fonts/ShowcaseFont.woff2` for a render-safe local
font load. The source font is not modified.

## Text configuration

The `--config` JSON file is the handoff between the font-prep agent and the video
renderer. It can contain any number of text segments:

```json
{
  "segments": [
    {"text": "Built for speed.", "seconds": 7, "fontSize": 300, "charactersPerSecond": 10},
    {"text": "Strong type.", "seconds": 7, "fontSize": 294, "charactersPerSecond": 10}
  ]
}
```

Each segment remains text-only. `fontSize` is measured in pixels at 1920x1080
and is **required** for every segment. The renderer fails closed unless each
scene defines an integer `fontSize` between 200 and 600 pixels; a missing or
tiny font size silently produced browser-default ~16px lettering in earlier
runs, so the validator now rejects it. Prefer 260-380px for dominant
single-line scenes and 240-300px for two-line scenes.
The integrated font-prep workflow requires exactly five segments totaling 35
seconds. Every scene may contain no more than four words. The first four should
be short factual phrases suited to the font with naturally varied lengths
between one and four words; there is no fixed word-count sequence. The fifth
scene is the exact final font name.

Font-prep integration writes the final MP4, `video-title.txt`, and
`video-description.txt` together inside the product's `video/` output folder.
The title and description are authored by the font-prep agent from the supplied
product facts; the renderer does not invent marketing copy.

## Development

```bash
npm run dev
npm run lint
```
