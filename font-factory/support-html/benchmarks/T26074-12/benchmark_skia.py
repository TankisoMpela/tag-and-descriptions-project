#!/usr/bin/env python3
"""Render the same 3:2 road-runner benchmark through the current Skia path."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STUDIO = ROOT / "bin" / "pin-studio"
sys.path.insert(0, str(STUDIO))
import pin_studio as ps  # noqa: E402

font = HERE / "assets" / "LilitaOne-Regular.ttf"
label = HERE / "assets" / "NotoSans-CondensedExtraBold.ttf"
out = HERE / "output" / "skia"
out.mkdir(parents=True, exist_ok=True)

start = time.perf_counter()
ctx = ps.build_ctx(font, "Nektar", dict.fromkeys(("line", "sub", "over", "word"), ""), cls="sports")
ctx["label"] = ps.Type(label)
context_ms = (time.perf_counter() - start) * 1000
runs = []
for index in range(3):
    started = time.perf_counter()
    surf, sh = ps.render("roadrunner32", ctx)
    render_ms = (time.perf_counter() - started) * 1000
    image = surf.makeImageSnapshot()
    save_started = time.perf_counter()
    ship, size = ps.save_specimen(image, out, "3x2", "70_roadrunner32", prefix="support")
    encode_ms = (time.perf_counter() - save_started) * 1000
    runs.append({
        "run": index + 1,
        "layoutAndDrawMs": round(render_ms, 2),
        "pngOptimizeAndWriteMs": round(encode_ms, 2),
        "outputBytes": size,
        "verificationMessages": sh.verify(),
        "textSlots": [
            {"name": slot.name, "fontSize": round(slot.size, 2), "lines": slot.lines}
            for slot in sh.slots if slot.size > 0
        ],
    })
report = {
    "frame": {"width": 2400, "height": 1600},
    "font": font.name,
    "labelFont": label.name,
    "contextBuildMs": round(context_ms, 2),
    "runs": runs,
}
(HERE / "output" / "skia-benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
