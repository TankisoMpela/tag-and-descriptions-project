import os

agent_file = "agents/agent-13-font-prep-specialist.md"
with open(agent_file, "r") as f:
    content = f.read()

old_block1 = """Use the simple black-and-white treatment: no background images,
callouts, transitions, or style switching. First render the main MP4 at"""

new_block1 = """Extract a highly contrasting color pair (dark background, clear light lettering)
based on the font's aesthetic (from `visual-direction/theme.txt` if available)
and pass it via `backgroundColor` and `textColor` in the config JSON. Do not
use background images, callouts, transitions, or style switching. First render the main MP4 at"""

if old_block1 in content:
    content = content.replace(old_block1, new_block1)
else:
    print("Block 1 not found")

old_block2 = """Create `$OUTPUT/video/showcase.config.json` before running the helper. It is the
text handoff between font preparation and video generation and must contain a
non-empty `segments` array. Use exactly five scenes, each `7` seconds, for a
35-second video. Keep every scene at four words or fewer and deliberately vary
the copy length between one and four words where it suits the font; do not
force a fixed word-count order or distribution. Preserve the original
character-by-character typing effect:
descriptive scenes use `charactersPerSecond: 10`, and the final font-name scene
uses `charactersPerSecond: 8`. Do not use word-by-word animation or sliding
reveals."""

new_block2 = """Create `$OUTPUT/video/showcase.config.json` before running the helper. It is the
text handoff between font preparation and video generation. It must contain a
non-empty `segments` array, as well as `backgroundColor` and `textColor` string
properties containing hex codes. Choose highly contrasting colors (e.g. a dark
background with clear light lettering) that suit the font's aesthetic, derived
from `visual-direction/theme.txt` if available. Use exactly five scenes, each
`7` seconds, for a 35-second video. Keep every scene at four words or fewer and
deliberately vary the copy length between one and four words where it suits the
font. Preserve the original character-by-character typing effect: descriptive
scenes use `charactersPerSecond: 10`, and the final font-name scene uses
`charactersPerSecond: 8`. Do not use word-by-word animation or sliding reveals."""

if old_block2 in content:
    content = content.replace(old_block2, new_block2)
else:
    print("Block 2 not found")

with open(agent_file, "w") as f:
    f.write(content)

# Also update .codex/agents/font-preparer.toml
toml_file = ".codex/agents/font-preparer.toml"
if os.path.exists(toml_file):
    with open(toml_file, "r") as f:
        toml_content = f.read()
    
    old_toml = "Use the simple black-and-white treatment: no background images"
    new_toml = "Extract contrasting hex colors (dark background, light text) from theme.txt for the config. No background images"
    toml_content = toml_content.replace(old_toml, new_toml)
    
    with open(toml_file, "w") as f:
        f.write(toml_content)
        
print("Updated agent-13 successfully")
