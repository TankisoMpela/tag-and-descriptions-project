# The skia pin renderer — verified capability reference

Ground truth for anyone generating Pinterest pin artwork with `skia-python`.
**Read this before inventing a call.** Every form here was executed against the
installed wheel and printed an `OK` line in one of `vendor/typography-labs/py/probe*.py`.
`vendor/` is gitignored, so this file — not the dump — is the durable artifact.

Wheel: `skia-python 144.0.post2`, CPU raster only, Linux x86-64.
Python: `bin/pin-studio/.venv/bin/python` (production, via `bin/render-pins`); the
probes themselves still ran under `vendor/typography-labs/py/.venv/bin/python`.

### The one rule that overrides the internet

skia's C++ docs and the upstream Skia pages describe **skia 149**; this wheel is
**144**, and the pybind layer renames and drops things arbitrarily. When web
documentation and this file disagree, **this file is right** — it was measured on
the machine that renders. Six symbols the web claims exist are absent here
(§12). Do not code against hope; run a two-line probe and see.

---

## 1. Boot and fonts

```python
import skia, uharfbuzz as hb
from fontTools.ttLib import TTFont

TF   = skia.Typeface.MakeFromFile("/path/Font.ttf", 0)   # NOT MakeFreeTypeFaceFromPath
FAM  = TF.getFamilyName()                                # e.g. 'Adwaita Sans'
UNI  = skia.Unicodes.ICU.Make()                          # see gotcha below
```

**`skia.Unicodes` is a `SimpleNamespace`, not a class.** `skia.Unicodes()` raises
`'types.SimpleNamespace' object is not callable`; the factory is
`skia.Unicodes.ICU.Make()`. Without ICU, `textlayout` loses word wrapping and
CJK line breaking — it silently degrades instead of failing. Same namespace
pattern applies to `skia.textlayout`, `skia.ImageFilters`, `skia.ColorFilters`,
`skia.cms`, `skia.PDF`.

Classes are reachable **both** as `skia.textlayout_ParagraphStyle` (flat, faster to
type) and `skia.textlayout.ParagraphStyle`. Enum members sometimes only resolve
through the dotted form: `skia.textlayout.TextAlign.kJustify`.

Point the layout engine at a directory of fonts (used to render the display face
by family name rather than by object):

```python
fc = skia.textlayout_FontCollection()
fc.setDefaultFontManager(skia.FontMgr.New_Custom_Directory("/dir/with/the/otf"))
```

`skia.Font` metrics that drive layout math:

```python
f = skia.Font(TF, 300)
m = f.getMetrics()      # fCapHeight, fXHeight, fAscent, fDescent, fLeading,
                        # fUnderlinePosition, fStrikeoutPosition, fXMin, fXMax
gl  = f.textToGlyphs("text")
adv = f.getWidths(gl)              # verified — the array a manual tracking pass needs
box = f.getBounds(gl)             # run bounds, for optical (not metric) centring
```

`Typeface.textToGlyphs` does **not** exist. `Font.textToGlyphs(text)` and
`Typeface.unicharsToGlyphs([ord(c)…])` both do and return the same ints.

---

## 2. Surfaces and reading pixels back

```python
s  = skia.Surface(1000, 1500)          # default
cv = s.getCanvas()
cv.clear(skia.Color(240, 238, 232))
img = s.makeImageSnapshot()
img.save("/path/pin.png")                             # PIL-ish convenience
img.save("/path/pin.jpg", skia.EncodedImageFormat.kJPEG, 90)
```

### The channel-order trap

`Surface(w, h)` defaults to **`kBGRA_8888`**, and `Image.toarray()` returns the raw
buffer — so `arr[y, x]` is **[B, G, R, A]**, not RGBA. Test colours that happen to be
symmetric (black, white, grey, pure red vs pure blue read as each other) will hide
this. It was found by drawing `Color(10, 200, 120)` and reading `[120, 200, 10]`.

If you are sampling pixels to measure contrast, ink coverage, or banding, build the
surface in the order you want:

```python
ii = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType,
                         skia.AlphaType.kPremul_AlphaType)
s  = skia.Surface(ii)                                 # arr[y,x] == [R,G,B,A]
```

Verified colour types that round-trip through `toarray()`: `kBGRA_8888`,
`kRGBA_8888`, `kN32`, `kRGBA_F16` (float16 — a real 16-bit linear working space,
useful when a gradient band must not posterise). `kRGB_565`, `kARGB_4444`,
`kAlpha_8`, `kGray_8` come back as packed scalars — not iterable rows.

**Alpha is not a coverage measure.** `cv.clear(anything opaque)` makes every pixel
alpha 255, so `count_nonzero(alpha)` reports the canvas size and tells you nothing.
Measure ink as "not equal to the ground colour":

```python
a = s.makeImageSnapshot().toarray()[..., :3].astype(int)
ink = int(np.count_nonzero((a != [240, 238, 232]).any(axis=-1)))
```

### Measuring the rendered pin (what the checks in §12 of the direction doc run on)

Re-opening a shipped file — `Image` has no `MakeFromFileName`/`MakeFromPath`, the route
is `Data` then `MakeFromEncoded`:

```python
img = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName("pin.png"))
a = img.toarray()[:, :, :3].astype(float) / 255.0        # PNG carries its own order
```

Contrast must be **WCAG 2.x relative luminance**, which linearises sRGB first. The
shortcut everyone writes (`luma = 0.2126R+0.7152G+0.0722B` on 0–255 values, then
`(hi+0.05)/(lo+0.05)`) is not WCAG and understates a light-ground/dark-ink pair by
**2.3×** — 5.39:1 measured against 12.23:1 on the identical pixels of the proof pin. A
generator using the naive form would reject good pins.

```python
def rel_lum(px):                       # px: (…, 3) float array in 0..1
    c = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]

ground = float(np.median(rel_lum(a[GROUND_BOX].reshape(-1, 3))))
ink    = float(np.percentile(rel_lum(a[INK_BOX].reshape(-1, 3)), 5))
ratio  = (max(ground, ink) + 0.05) / (min(ground, ink) + 0.05)   # want >= 4.5
```

Sample a ground box that contains **no ink at all** and an ink box that is the focal
band, and take the *darkest 5%* of ink rather than the mean — a mean over a type band is
mostly background and reports a meaningless ratio. Feed one pixel and you get 1.0:1.

Thumbnail legibility is a downsample, not a resize library:

```python
small = skia.Surface(skia.ImageInfo.Make(200, 300, skia.ColorType.kRGBA_8888_ColorType,
                                         skia.AlphaType.kPremul_AlphaType))
small.getCanvas().drawImageRect(img, skia.Rect.MakeXYWH(0, 0, W, H),
                                skia.Rect.MakeXYWH(0, 0, 200, 300),
                                skia.SamplingOptions(skia.FilterMode.kLinear,
                                                     skia.MipmapMode.kNone))
```

`skia.FilterQuality` does not exist on this wheel; the 4th positional of
`drawImage`/`drawImageRect` is a `SamplingOptions`. Count "dark" pixels in the focal
band of the 200 px version and expect **15–60%** — under that the hook is too thin to
see in the grid, over that it is a black slab.

Other verified surface routes:

| Form | Note |
|---|---|
| `skia.Surface(numpy_array)` | draws straight into an `ndarray` `(h, w, 4)`; keep the array alive |
| `skia.Surface.MakeRasterDirect(info, ptr, rowBytes)` | zero-copy |
| `s.imageInfo().colorSpace()` | may be `None` on a plain surface — guard before calling methods |
| `skia.Surface(w, h, None, cs)` | **does not exist**; colour space goes through `ImageInfo` |

---

## 3. Colour

```python
C = skia.Color                                    # C(r, g, b, a=255) — a is an INT 0..255
C(255, 0, 0, 128)          -> 0x80ff0000          # half-alpha red. Correct.
C(255, 0, 0, 0.5)         -> TypeError           # float alpha is NOT accepted here
skia.Color4f(1.0, 0.0, 0.0, 0.5)                  # floats live here, and only here
```

Paint construction takes a small, fixed kwarg set:

```python
skia.Paint(Color=C(20, 20, 20), BlendMode=skia.BlendMode.kMultiply)
```

`Width=` and `Dither=` raise `KeyError`. The stroke kwarg is `StrokeWidth`; dither is
`pt.setDither(True)`. Full verified setter list on `Paint`:
`setARGB setAlpha setAlphaf setAntiAlias setBlendMode setColor setColor4f
setColorFilter setDither setImageFilter setMaskFilter setPathEffect setShader
setStrokeCap setStrokeJoin setStrokeMiter setStrokeWidth setStyle`.

**`Canvas` has no `setBlendMode`.** Blending is per-`Paint`, or per-filter via
`ImageFilters.Xfermode`. Verified multiply:

```python
cv.drawRect(rect_a, skia.Paint(Color=C(255, 60, 60)))
cv.drawRect(rect_b, skia.Paint(Color=C(60, 60, 255), BlendMode=skia.BlendMode.kMultiply))
# overlap reads [60, 15, 60]
```

### ColorFilters — exactly seven exist

`Blend, Compose, HSLAMatrix, Lerp, LinearToSRGBGamma, Matrix, SRGBToLinearGamma`.
That is the whole namespace; verified by dumping `skia.ColorFilters.__dict__`.
`LuminanceToAlpha`, `Saturate`, `Gain`, `Gamma` are upstream-Skia and **absent here**.

`ColorFilters.Matrix` takes **20 floats, 4 rows × 5 columns**, rows = output
R,G,B,A, columns = r,g,b,a,bias. Verified luma collapse of `Color(220, 60, 40)`:

```python
pt.setColorFilter(skia.ColorFilters.Matrix(
    [0.2126, 0.7152, 0.0722, 0, 0,
     0.2126, 0.7152, 0.0722, 0, 0,
     0.2126, 0.7152, 0.0722, 0, 0,
     0,      0,      0,      1, 0]))     # reads [93, 93, 93]
```

Put the weights in the **R,G,B rows**. Putting them in the last row makes alpha and
outputs black — that mistake cost a probe round.

`ColorFilters.HSLAMatrix` also takes 20 floats but is interpreted as **4 rows × 5 in
H,S,L,A space plus bias**; identity (`diag(1,1,1,1)`) is close to a passthrough on an
RGB gradient (midpoint read `[148, 40, 147]` against `[148, 40, 148]`), i.e. the round
trip is not bit-exact. Use it for hue/saturation moves, not for preserving values.

A custom grade belongs in a `ColorFilter` compiled from SkSL — verified:

```python
eff = skia.RuntimeEffect.MakeForColorFilter(
    "half4 main(half4 c){ return half4(vec3(dot(c.rgb, vec3(0.299,0.587,0.114))), c.a); }")
pt.setColorFilter(skia.RuntimeColorFilterBuilder(eff).makeColorFilter())
```

The signature is picky: `half4 main(half4 c)`. `MakeForColorFilter` with
`main half4 precision(...)` raises a compile error.

### Linear working space

```python
LIN = skia.ColorSpace.MakeSRGBLinear()
ii  = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType,
                          skia.AlphaType.kPremul_AlphaType, LIN)
s   = skia.Surface(ii)
s.imageInfo().colorSpace().gammaIsLinear()   # True
```

Rendering a red→blue linear gradient and sampling the midpoint: **sRGB surface reads
`[128, 0, 127]`, linear surface reads `[127, 0, 128]`** — the curves differ, and on a
large soft wash a linear ground keeps mid-tones from muddying. `gammaIsLinear()` and
`isSRGB()` are methods on `ColorSpace`, **not** on `Surface` (no `Surface.gammaIsLinear`).

`skia.cms` exposes `NamedGamut {kAdobeRGB, kDisplayP3, kRec2020, kSRGB, kXYZ}` and
`NamedTransferFn {k2Dot2, kHLG, kLinear, kPQ, kRec2020, kSRGB}`, each resolving to a
`cms.TransferFunction` / `cms.Matrix3x3`. Compose them:

```python
p3 = skia.ColorSpace.MakeRGB(skia.cms.NamedTransferFn.kSRGB,   # transferFn FIRST
                              skia.cms.NamedGamut.kDisplayP3)  # toXYZ SECOND
```

The reverse order raises `TypeError`. `gamutTransformTo(dst, src_to_dst)` needs a
third argument (a `Matrix3x3`), so a two-arg transform does not work; for shipping
pins, author in sRGB and skip the conversion rather than guessing the matrix.
`ColorSpace.serialize()` returns `skia.Data` (use `.size()`, or `bytes(data)`;
`len()` raises) — `ColorSpace.Deserialize` wants a capsule + length and is not
practically reachable. Treat serialisation as unavailable.

---

## 4. Text: pick the right tier

Three tiers, in ascending power. The single biggest capability gain over the
older `pin_studio.py` is tier C.

### Tier A — one run, one baseline

```python
cv.drawString("WORD", x, baseline_y, skia.Font(TF, 300), paint)   # y is the BASELINE
blob = skia.TextBlob.MakeFromString("WORD", skia.Font(TF, 300))
cv.drawTextBlob(blob, x, baseline_y, paint)
blob.bounds()                                # Rect; NOT getSize(), which is absent
```

`Font.getMetrics()` gives you the baseline offsets you need for exact optical centring.

### Tier B — per-glyph transforms (kinetic, staggered, rotated type)

```python
f  = skia.Font(TF, 40)
gl = list(f.textToGlyphs("TYPEMOON"))
b  = skia.TextBlobBuilder()
b.allocRunRSXform(f, gl, [skia.RSXform.Make(scale, skew, tx, ty) for ...])
blob = b.make()                              # .make(), not .GetBlob()
```

| Builder call | Signature (verified) | Use |
|---|---|---|
| `allocRun` | `(text, font, x, y, bounds=None, encoding=…)` | note: **text first** |
| `allocRunPos` | `(font, glyphs, [skia.Point(x, y)…])` | per-glyph free placement |
| `allocRunPosH` | `(font, glyphs, [x…], y)` | shared baseline, custom tracking. The `x` list is **absolute pen positions**, not advances — accumulate `Font.getWidths` + tracking yourself or the word stacks into a smudge |
| `allocRunRSXform` | `(font, glyphs, [skia.RSXform…])` | rotate/scale each glyph |

`allocRunPos` **rejects numpy arrays and flat float lists** with a pybind cast error.
Pass a Python list of `skia.Point` objects. `RSXform.Make(sx, kx, tx, ty)` for an
affine, or `RSXform.MakeFromRadians(scale, radians, tx, ty, ax, ay)` when you want
rotation about an anchor — the ink-verified rotation test drew 4,361 px of type with
this form.

Cheaper when no per-glyph matrix is needed:
`skia.TextBlob.MakeFromRSXform(text, xforms, font)` — **str first**, then xforms, then font.
`MakeFromShapedText(text, font, leftToRight=True)` gets skia's own shaper (kerning)
without uharfbuzz; verified 99.8 units wide for "TYPE" at 40pt.

### Tier C — `textlayout` paragraphs (multi-line, align, leading, mixed runs)

This is a real layout engine: wrapping, justification, per-run size and paint,
underline styles, CJK breaking. All in pure CPU raster, no GPU.

```python
ps = skia.textlayout_ParagraphStyle()
ps.setTextAlign(skia.textlayout.TextAlign.kJustify)

ss = skia.textlayout_StrutStyle(); ss.setStrutEnabled(True); ss.setLeading(64.0)
ps.setStrutStyle(ss)                            # paragraph-wide line box

pb = skia.textlayout_ParagraphBuilder.make(ps, fc, UNI)   # UNI is required
ts = skia.textlayout_TextStyle()
ts.setFontSize(50); ts.setFontFamilies([skia.String(FAM)])
ts.setForegroundPaint(paint_with_shader)        # gradient inside one run
pb.pushStyle(ts); pb.addText("…"); pb.pop()

p = pb.Build()
p.layout(820)                                   # hard requirement before metrics/paint
p.paint(cv, x, y)                               # y is the paragraph TOP, not baseline
```

| Fact | Consequence |
|---|---|
| `ParagraphStyle` setters are **only** `setStrutStyle`, `setTextAlign`, `setTextStyle` | **no `maxLines`, no ellipsis, no height, no textAlign fallback tricks** — cap line count by choosing the copy width and measuring `Height` |
| `StrutStyle` has **only** `setStrutEnabled`, `setLeading` — and `setLeading` is broken (§4.1) | line rhythm is not a paragraph knob here; break lines yourself |
| `ParagraphBuilder` has `make, pushStyle, pop, addText, Build` | no per-position insertion, no `addPlaceholder` |
| Metrics are **properties**: `p.Height`, `p.LongestLine`, `p.Width`, `p.MinIntrinsicWidth`, `p.MaxIntrinsicWidth`, `p.AlphabeticBaseline`, `p.IdeographicBaseline`, `p.ExceedMaxLines` | writing `p.getHeight()` raises `TypeError: 'float' object is not callable` — this blocked a whole probe round |
| `TextAlign`: `kCenter kEnd kJustify kLeft kRight kStart` | `kJustify` verified: ink reaches the declared right edge |
| `TextDecorationStyle`: `kDashed kDotted kDouble kSolid kWavy` | a wavy rule under a phrase is free |
| `TextStyle` setters: `setColor setDecoration setDecorationColor setDecorationMode setDecorationStyle setDecorationThicknessMultiplier setFontFamilies setFontSize setFontStyle setForegroundColor setForegroundPaint setLetterSpacing setLocale setWordSpacing` | `setLetterSpacing` is in em fractions: 0.35 tracked "TRACKING" from 204.6 → 207.4 px |

**`setForegroundPaint` beats `setForegroundColor`** whenever the run should carry a
gradient, and it is the only way to get a gradient inside wrapped text. Verified: a
70 pt justified paragraph painted with a two-stop linear shader produced 204 distinct
colours in the inked region.

**Silent font fallback is real and detectable.** A bogus family still paints (2,884 px
of ink from the default face), it does not raise. Compare `LongestLine` against the
known family and against `MaxIntrinsicWidth`; if they differ the face was not used.
There is no exception to catch.

### 4.1 Line pitch, and why `StrutStyle.setLeading` is not a knob

Default line pitch is **1.2 × font size** and is consistent (measured: size 12 → 15,
24 → 29, 40 → 48, 48 → 58, 96 → 116). Multiplied by `Height / 1.2 / size` you get the
line count.

`setLeading` does **not** mean "v px extra per line". Measured on a single 40 pt line,
then across sizes:

| `setLeading` | Height, 1 line @40 pt | Height, same @12 / 24 / 48 / 96 pt |
|---:|---:|---|
| — | 48.0 | 15 / 29 / 58 / 116 |
| 10 | **158.0** | 158 / 158 / 158 / 167 |
| 20 | 298.0 | — |
| 40 | 578.0 | — |
| 100 | 1418.0 | — |

The value is amplified roughly `14·L − 30` px per line and the font size is ignored
altogether (leading 10 yields 158 px at every size). A quote block that "wanted" 46 px
of leading came out **1324 px tall** — it silently fills the pin.

**Do not use it.** Control rhythm explicitly instead, all verified:

* `\n` in the text — one paragraph, uniform 1.2× pitch;
* one single-line paragraph per line, each `paint`ed at a chosen y — full control,
  and it is how you get an irregular, hand-set rhythm;
* Tier B runs (`allocRunPos`) if each line wants its own baseline nudge.

In the end-to-end assembly (§13) removing the strut took the quote block from
Height 1986 → **179**, which is what the design needed.

---

## 5. Glyphs as artwork, not just text

```python
f   = skia.Font(TF, 340)
gid = list(f.textToGlyphs("R"))[0]
path = f.getPath(gid)          # returns a Path (not a tuple)
paths = f.getPaths(gids)       # list[Path]
```

Stroke it for a wireframe; overlay a dashed pass for a blueprint look — both verified
drawing real contour ink. Combine with the effects below and the glyph becomes a
pattern, a route, or a texture rather than a letter.

| Effect | Verified call | What it buys a pin |
|---|---|---|
| `Path1DPathEffect.Make(marker_path, advance, offset, style)` | style ∈ `kRotate kTranslate kMorph`; **marker can be a glyph outline** | type marching along a curve, letterforms as the repeated motif |
| `Path2DPathEffect.Make(matrix, tile_path)` | matrix built with `skia.Matrix()` then `.setScale(s, s)` (no `Matrix.MakeScale`) | halftone/trellis pattern fills inside a letter |
| `TrimPathEffect.Make(start, end)` | fraction of path length | partially drawn outlines, "unfinished" line work |
| `DiscretePathEffect.Make(segLength, dev, seedAssist:int)` | `seedAssist` **must be an int** | hand-cut, jittered rules |
| `DashPathEffect.Make([on, off, …], phase)` | | stitched colophon rules |
| `skia.Op(one, two, skia.PathOp.kDifference)` | free function; `Path.op` instance method **does not exist** | knock a bar out of a real glyph, stencil/inline letterforms |
| `skia.Simplify(path)` / `skia.AsWinding(path)` | | make overlapping contours boolean-safe before `kDifference` |
| `path.interpolate(ending, weight, out)` | instance method | morph between two letterforms |
| `skia.Path.Iter(path, forceClose)` / `path.Iter()` | | walk control points |
| `skia.PathBuilder` | `addArc, addOval, addPolygon, addRRect, arcTo, conicTo, offset, snapshot, detach, toggleInverseFillType` | build the geometric frame first |

`Path` has no `.copy()` — use `skia.Path(path)` or `.duplicate()`.
`PathMeasure(path, forceClosed, resScale)` → `getPosTan(d)` returns `(Point, Vector)`,
`getMatrix(d)` returns a `Matrix` (both take distance only; passing an out-param raises).
This is the plumbing for placing type on a curve word by word.

Text on a path in one call: `cv.drawTextOnPath(text, path, matrix, font, paint)` —
**third argument is a `Matrix`, not an hOffset integer.**

---

## 6. Meshes, stamps, and the paint trap

```python
vs = skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode,
                             [skia.Point…], None, [skia.Color…], None)
cv.drawVertices(vs, skia.Paint(Color=skia.Color(255, 255, 255)),
                skia.BlendMode.kModulate)
```

**The trap that produces black rectangles:** `drawVertices`/`drawPatch` default to
`mode=kModulate`, which multiplies the vertex colours by the **paint's colour**, and a
default `Paint` is black. `drawVertices(vs, skia.Paint())` therefore paints nothing but
black — verified, 2 unique colours. Three measured outcomes:

| mode | paint | result |
|---|---|---|
| `kModulate` | black (default) | dead: all black, 2 colours |
| `kModulate` | **white** | mesh gradient, 48,556 unique colours ✓ |
| `kSrcOver` | white | washed: the paint colour covers, 1 colour |

So: **`kModulate` + white `Paint`** is the correct mesh-gradient recipe, for both
`drawVertices` and `drawPatch`. `drawPatch` takes **exactly 12 cubic points** (4 edges ×
3, corners shared), 4 corner colours, 4 `texCoords`, mode, paint — a real Coons patch,
verified at 54,950 unique colours in the quad.

`cv.drawAtlas(atlas_image, xforms, tex, colors, mode, options=None, cull=None, paint=None)`
— per-instance rotation, scale and colour from one source raster: 200 rotated stamps,
147,212 px of ink, verified. This is the confetti / halftone / scattered-glyph move.
`kRotate kTranslate kMorph` on a PathEffect are the vector equivalents.

`cv.drawPatch`/`drawVertices`/`drawAtlas` are the only ways to get a per-pixel colour
ramp without a shader.

---

## 7. Shaders, filters, and what SkSL is worth

Gradients — `TileMode` **must** be an enum member; raw ints fail:

```python
skia.GradientShader.MakeLinear(points=[skia.Point(x0,y0), skia.Point(x1,y1)],
                               colors=[C(…), C(…)],
                               tileMode=skia.TileMode.kMirror,   # optional
                               pos=[0.0, 0.4, 1.0])              # optional stops
```
`MakeRadial`, `MakeSweep`, `MakeTwoPointConical` exist. Solid colour as a shader is
`skia.Shaders.Color(...)` — **`Shader.MakeColor` does not exist**; `skia.Shaders` is
`{Blend, Color, Empty, Lerp}` and `Shaders.Lerp(t, dst, src)` interpolates two shaders.

Noise: `skia.PerlinNoiseShader.MakeFractalNoise(freqX, freqY, seed, tile)` and
`.MakeTurbulence(...)` work as static factories (the constructor does not).

### `ImageFilters` — the complete, verified namespace

`Arithmetic Blur ColorFilter Compose Dilate DisplacementMap DistantLitDiffuse
DistantLitSpecular DropShadow DropShadowOnly Erode Image Magnifier MatrixConvolution
MatrixTransform Merge Offset Picture PointLitDiffuse PointLitSpecular SpotLitDiffuse
SpotLitSpecular Tile Xfermode`

**There is no `ImageFilters.Color` and no `ImageFilters.RuntimeShader`** on this wheel.
Pass a filter-able solid via `ImageFilters.Image(...)` from a one-pixel surface, or do
the colour work in a `ColorFilter`.

Call forms that were fought over and are now settled:

| Form | Note |
|---|---|
| `ImageFilters.DropShadow(dx, dy, sigmaX, sigmaY, color)` | verified under a card |
| `ImageFilters.Merge([f1, f2], cropRect=None)` | first arg is a **list** |
| `ImageFilters.MatrixTransform(matrix, sampling, input)` | |
| `ImageFilters.Tile(src=Rect, dst=Rect, input)` | |
| `ImageFilters.Arithmetic(k1,k2,k3,k4, enforcePMColor, bg_filter, fg_filter=None, crop=None)` | verified: 0.5/0.5/0/0 over red + cyan reads `[128,128,0]` — a genuine overprint/riso mixer |
| `ImageFilters.Xfermode(mode, bg_filter, fg_filter)` | args are **ImageFilters**, not Paints; use `ImageFilters.Image(img)` for inputs |
| `ImageFilters.Image(img, sampling, crop=None, xy=…)` | raster feeding a filter |
| `ImageFilters.Picture(pic, targetRect=None)` | a `SkPicture` feeding a filter |
| `ImageFilters.MatrixConvolution(...)` | custom kernel → emboss/sharpen |
| `ImageFilters.Magnifier(...)` | lens/inset |
| `PointLitDiffuse` / `SpotLitSpecular` / `DistantLitDiffuse` | light direction is a **`skia.Point3`** — `skia.Point` is 2D and fails |
| `ImageFilters.DisplacementMap(skia.ColorChannel.kR, skia.ColorChannel.kG, scale, disp_filter, color_filter)` | |

Mask filters: `ShaderMaskFilter.Make(shader)`, `TableMaskFilter.Create/CreateClip/CreateGamma`,
`BlurMaskFilter.Make`, `ComposeMaskFilter`. `MakeFrom` does not exist on `ShaderMaskFilter`.

### SkSL runtime effects

**Declaration order is enforced.** `uniform` lines must come *before* any helper
function, or the compile raises `error: 1: expected expression, but found 'uniform'`.
Putting `uniform float u_s;` inside/after a helper block is the most common way to
lose an hour.

```python
eff = skia.RuntimeEffect.MakeForShader(
    "uniform float u_scale;"                       # declarations first
    "float h(vec2 p){return fract(sin(dot(p, vec2(41.3,289.7)))*19347.3);}"
    "float vn(vec2 p){"                            # bilinear value noise
    "  vec2 i = floor(p), f = fract(p);"
    "  vec2 u = f * f * (3.0 - 2.0 * f);"
    "  return mix(mix(h(i), h(i + vec2(1, 0)), u.x),"
    "             mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), u.x), u.y); }"
    "half4 main(float2 c){"
    "float n = floor(vn(c / u_scale + vec2(7.3, 2.1)) * 5.0) / 5.0;"
    "return half4(vec3(1.0 - n * 0.09), 1.0); }")  # near-white: multiply-friendly
b = skia.RuntimeShaderBuilder(eff)
b.setUniform("u_scale", 260.0)                     # scalars, or lists for float2/3/4
pt = skia.Paint(BlendMode=skia.BlendMode.kMultiply)
pt.setShader(b.makeShader())                       # optional localMatrix argument
cv.drawRect(full, pt)
```

That last block **is the shipped paper-tooth recipe** — one interpolated octave,
quantised to 5 levels, blended `kMultiply` against a near-white return. §10 has the
byte measurements that forced each of those three choices.

Verified outcomes, all on the CPU raster backend:
* per-pixel hash grain → 256 unique steps (full-range film noise);
* blocky value noise at `u_scale=90` → 21 steps (a risograph ground, *not* paper —
  hard square cells read as a quilt at pin size);
* `setChild("u_src", someShader)` then `u_src.eval(float2(200.0, 200.0))` → 21 steps of a
  re-mapped gradient. **`eval` must be called with an explicit `float2(...)`** — the bare
  `eval(c)` form fails to compile in this binding, so sample children with literal or
  computed float2 coordinates.
* `MakeForColorFilter("half4 main(half4 c){…}")` → a working custom grade (§3).

**A shader return replaces the ground, it does not texture it.** Returning
`half4(vec3(0.5), 1.0)` at full alpha over a whole canvas is an opaque grey rect:
measured ground luminance 0.90 → 0.506 and contrast down to 3.33:1. Either return
near-white and blend `kMultiply`, or return near-black and blend `kScreen`, or give
the return a real alpha and composite inside a `saveLayer`. Never assume a shader
layer is "just" a texture.

`MakeForShader`/`MakeForColorFilter` return the effect alone (not an `(effect, error)`
tuple) and **raise** on a compile failure — wrap in `try` and fall back to a plain
gradient rather than losing the pin.

**`MakeForBlender` is a dead end here.** It compiles when `main` returns `half4`, but
`RuntimeBlendBuilder.makeBlender()` then raises
`Unable to convert function return value to a Python type` and there is no `skia.Blender`
class and no `Paint.setBlender` to attach one to. Blend with `Paint(BlendMode=…)` or
`ImageFilters.Xfermode`/`Arithmetic` instead. Do not budget time on custom blend modes.

---

## 8. Canvas operations worth using in a pin

| Call | Verified use |
|---|---|
| `cv.save()` / `cv.restore()` / `cv.saveLayer()` | compositing a tint layer |
| `cv.clipPath(path)` / `clipRRect` / `clipRect` | type inside a letter's counter |
| `cv.concat(matrix)` / `setMatrix` / `rotate` / `scale` / `translate` | rotated compositions without re-laying-out |
| `cv.Lattice(xCount, yCount, bounds, positions, colors, mode, paint)` | 9-s patch stretch of a texture ground |
| `cv.drawRRect`, `drawOval`, `drawArc`, `drawLine`, `drawPoints`, `drawDRRect` | rules, plates, double-line frames |
| `skia.RSXform.Make/MakeFromRadians` | stamp placement |
| `cv.drawPicture(pic)` | compose once, stamp many |

No `drawShadow` and no `skia.ShadowOptions` on this wheel (§12). Soft depth comes from
`ImageFilters.DropShadow` / `DropShadowOnly`, or from a blurred `saveLayer`.

---

## 9. Vector export and round-tripping

```python
st  = skia.DynamicMemoryWStream()
doc = skia.PDF.MakeDocument(st, skia.PDF.Metadata())     # stream FIRST
cv  = doc.beginPage(1000.0, 1500.0)                      # returns a Canvas
…; doc.endPage(); doc.close()
pdf_bytes = bytes(st.detachAsData())                      # .size() for length
```

Two-page verified at 15,299 bytes; a 1000×1500 single page at ~6 KB. Pages are in
**points** (1 pt = 1/72 in). `doc.page(w, h)` is also usable as a context manager that
calls `endPage` for you (verified). `PDF.Metadata` fields:
`fAuthor fCreator fEncodingQuality fKeywords fPDFA fProducer fRasterDPI fSubject fTitle`
(+ `fStructureElementTreeRoot`). Assign them directly — verified. A vector PDF of a pin
is a genuinely different artifact from the raster: the type stays live and the file
stays tiny.

SVG both ways:

```python
data = skia.Data.MakeWithCopy(svg_text.encode())
dom  = skia.SVGDOM.MakeFromStream(skia.MemoryStream(data))
dom.render(canvas)                                      # in: SVG as artwork

st = skia.DynamicMemoryWStream()
cvs = skia.SVGCanvas.Make(skia.Rect.MakeLTRB(0, 0, W, H), st,
                          skia.SVGCanvas.kConvertTextToPaths_Flag)
cvs.drawString(…)           # Make() returns a Canvas directly — there is no .getCanvas()
del cvs                   # closing the canvas flushes the stream
svg_bytes = bytes(st.detachAsData())        # a 1-word pin measured 4 KB
```

Verified parsing of `<pattern>`, `<linearGradient>`, `feGaussianBlur` and `<text>`
(400×98.24 bbox). `kConvertTextToPaths_Flag` on export makes the SVG font-independent;
without it the `<text>` element survives. There is no `SVGDOM.FromString`, no
`SVGCanvas.Create`.
`WStream` has `bytesWritten` and `detachAsData` — **no `size()`**.

Drawing a finished raster into a smaller frame:
`cv.drawImageRect(image, src_rect, dst_rect)` — the **fourth positional argument is
`SamplingOptions`, not a `BlendMode`** (passing one raises `TypeError`).

---

## 10. Shipping constraints this repo actually enforces

* Canvas 1000×1500 (2:3). Read at 150–200 px in the grid, so the focal phrase must
  survive that size — check by downsampling, not by squinting.
* The repo caps images at **200 KB**. What actually costs bytes is **continuous tone**,
  not visual loudness — a ground that looks bolder can be cheaper, and a ground that
  looks subtle can blow the budget. Measured at 1000×1500 on the same ground, one
  treatment at a time (`vendor/typography-labs/py/probe12.py`):

  | Ground treatment (no type on it) | PNG | JPEG q90 |
  |---|---:|---:|
  | flat clear | 9.0 | 9.0 |
  | mesh `drawPatch` wash composited @ 45% | 18.8 | 10.5 |
  | blocky hash `u_scale=60` | 21.8 | 25.2 |
  | blocky hash `u_scale=28` | 28.9 | 42.9 |
  | blocky hash `u_scale=8` | 90.7 | 28.3 |
  | blocky hash `u_scale=4` | **220.3 breach** | 197.0 |
  | smooth value noise, 1 octave, `s=110`, continuous | **257.2 breach** | 36.2 |
  | smooth value noise, 2 octaves, `s=110`, continuous | **491.4 breach** | 46.4 |
  | smooth value noise, 2 octaves, `s=30`, continuous | **977.5** | 103.2 |
  | same, quantised to 8 levels | 117.1 | 77.4 |
  | same, quantised to 5 levels | 84.4 | 73.6 |
  | same, quantised to 3 levels | 59.7 | 65.2 |
  | **shipped:** 1 octave `s=260`, 5 levels, α .09 | 32.3 | 19.4 |
  | shipped recipe at 3 levels | 26.5 | 17.5 |
  | shipped recipe at 2 levels | 22.2 | 15.6 |

  **Read the rule off that table:**
  1. Interpolated (smooth) noise at full precision is the worst thing you can do to a
     PNG — 257–978 KB for a ground that *looks* quieter than a 29 KB blocky one, because
     every pixel differs from its neighbour by ±1 and the row filter has nothing to work
     with. `floor(n * k) / k` with k = 3…5 buys the organic look back for ~13 KB over flat.
  2. Grain *frequency* is everything, amplitude almost nothing: at `s=260` the same
     ground costs 29.2 / 29.2 / 29.3 KB PNG at α .05 / .075 / .15. Push amplitude for
     look, never for size. (JPEG *does* grow with amplitude — 16 → 24 KB — so PNG stays
     the ship format.)
  3. JPEG is sometimes bigger than PNG and sometimes half of it (blocky `s=28`:
     28.9 PNG vs 42.9 JPEG). Decide from `path.stat().st_size`, never from the design's
     appearance and never from a rule of thumb about formats.
* A **full designed pin** — mesh wash + 5-level tooth + 240 pt hook with rolled tracking
  + 3-line body with a gradient attribution run + ghost word + overprint rule + ornament
  glyph + rail — encodes at **153.1 KB PNG / 93.9 KB JPEG q90** (§13). The same pin with
  a continuous-tone tooth encoded at **594.6 KB**: the ground alone sank it. Budget
  ≈50 KB of headroom, and the first thing to cut is the tooth's level count (5 → 3),
  then the ghost word, before you touch the type.
* `img.save(path, skia.EncodedImageFormat.kJPEG, 90)` is the one-call route;
  `kPNG kWEBP kBMP kGIF kICO kHEIF kJPEG` are all available formats.
* WCAG contrast between ink and ground is computed from the *rendered* pixels — see §2
  for the channel order you must use when sampling.
* Pinterest dedupes near-identical pins. Five pins per font that differ only in palette
  will be collapsed; §2 of `docs/PIN-ART-DIRECTION.md` is the structural answer.

---

## 11. Recipes proven end-to-end

| Goal | Recipe (every step verified above) |
|---|---|
| Body copy, wrapped, mixed runs | Tier C + `TextAlign.kLeft`; break lines with `\n` or one paragraph per line — **never** `StrutStyle.setLeading` (§4.1). `kJustify` stretches spaces into rivers on a display face (§13) |
| Gradient inside wrapped text | `setForegroundPaint(Paint with GradientShader.MakeLinear)`, vertical points `[0,-size]→[0,0]` |
| Hook at a size that fits, without shrinking | fixed rung list `[340, 288, 240, 196, 156, 124]`, take the first whose natural advance + tracking clears the margins (§13 step 3) |
| Mesh-gradient ground, no banding | `drawPatch` 12 cubics + 4 colours, `kModulate` + white paint **into its own surface**, then `cv.drawImage(snap, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.45))` — full strength kills contrast (§12) |
| Paper tooth that survives the 200 KB cap | SkSL interpolated value noise, **one octave, `u_scale ≥ 200`, quantised to 3–5 levels, near-white return, `kMultiply`** (§10) |
| Type marching along a curve | glyph outline → `Path1DPathEffect(marker, advance, 0, kRotate)` on a stroked `Path` |
| Scattered stamp field | `drawAtlas(image, RSXform.MakeFromRadians(…), tex, colors, kSrcOver)` |
| Hand-cut rules | `DiscretePathEffect.Make(9.0, 6.0, 3)` on a stroke paint |
| Stencil / inline letterform | `Font.getPath` → `skia.Op(a, b, kDifference)` after `AsWinding` |
| Wavy underline accent | `setDecoration(kUnderline)` + `setDecorationStyle(kWavy)` |
| Duotone grade of a rendered layer | `ColorFilters.Matrix` luma rows then bias columns (§3) |
| Ghost word (a second voice in the dead band) | Tier B `allocRunPosH` at a mid rung, paint one step off the ground, `kMultiply`, inside `cv.clipRect(band)` |
| Third ink from two plates | two `drawRect`s, the second `Paint(BlendMode=kMultiply)` — overlap reads as a new colour, measured `[40, 27, 23]` |
| Vector take of the same design | `PDF.MakeDocument` / `SVGCanvas.Make` (§9) |

---

## 12. NOT AVAILABLE on skia-python 144.0.post2

Do not search for these; they were looked for and are absent. Each entry is a measured
`AttributeError`, not a guess.

`skia.Blender` · `Paint.setBlender` · `Canvas.setBlendMode` · `Canvas.drawShadow` ·
`Canvas.drawShadowablePath` · `skia.ShadowOptions` · `ImageFilters.Color` ·
`ImageFilters.RuntimeShader` · `ColorFilters.LuminanceToAlpha` · `ColorFilters.Saturate` ·
`ColorFilters.Gain` · `ColorFilters.Gamma` · `ParagraphStyle.setMaxLines` ·
`ParagraphStyle.setEllipsis` · `ParagraphStyle.setHeight` · `Paragraph.getHeight/getLongestLine` (properties:
`Height`, `LongestLine`) · `TextBlob.getSize` (use `bounds()`) · `Path.op` (use `skia.Op`) ·
`Path.copy` · `Matrix.MakeScale` · `Shader.MakeColor` (use `skia.Shaders.Color`) ·
`Shaders.MakeColor` · `skia.Unicodes()` (namespace: `.ICU.Make()`) ·
`Typeface.MakeFreeTypeFaceFromPath` · `Typeface.textToGlyphs` · `Typeface.copy` ·
`TextBlobBuilder.GetBlob` (use `.make()`) · `TextBlob.MakeFromShapedText(glyphs,…)`
(text, font, ltr only) · `Surface.gammaIsLinear` (on `ColorSpace`) ·
`ColorSpace.getName` · `WStream.size` · `DynamicMemoryWStream` → `bytes(st)` (use
`detachAsData()`) · `skia.PDF.Document` (type is `skia.Document`) ·
`Document.makePage` (use `beginPage`/`page`) · `skia.textlayout_TextShaper` ·
`skia.TextShaper` · `RuntimeEffect.MakeForBlender` usable end-to-end · `len(skia.Data)` ·
`Image.encode_to_bytes` / `encode_to_png` (use `encodeToData` / `save`) ·
`SVGDOM.FromString` (use `MakeFromStream`) · `SVGCanvas.Create` (use `Make`) ·
`SVGCanvas` → `.getCanvas()` (`Make` already returns a `Canvas`) ·
`ColorSpace.Deserialize(bytes_or_Data)` (wants a capsule + length; treat as unavailable) ·
`Canvas.drawImageRect(image, src, dst, BlendMode)` (4th arg is `SamplingOptions`) ·
`skia.FilterQuality` (the enum is `skia.FilterMode`; `drawImage`'s 4th arg is
`SamplingOptions`, not a filter quality) · `Paragraph.getLineMetrics` /
`getLineNumber` / any line-count accessor (read rhythm off `Height / (1.2 × size)`) ·
`TextBlob.getBounds` (use `bounds()`).

If a design idea needs one of these, restructure the idea or add a probe — do not
write the call and hope.

### Works, but lies

These calls execute cleanly and produce something other than what the name promises.
They are more dangerous than the absent list, because nothing raises.

| Call | What it actually does | Evidence |
|---|---|---|
| `StrutStyle.setLeading(v)` | line box ≈ `14·v − 30` px, independent of font size | §4.1 table |
| bogus `setFontFamilies([…])` | silently falls back to another face and still paints | 2,884 px of ink, no error |
| `Typeface.MakeFromFile(bad_path)` | returns `None` — but `Font(None, size)` then renders a **default** face | a "serif" pin that was Adwaita Sans all along |
| `drawVertices` / `drawPatch` with a default `Paint` | multiplies your vertex colours by black → a solid black shape | 2 unique colours vs 48,556 |
| `drawPatch(…, kModulate)` + `Paint(Alphaf=…)` | the vertex colours are opaque, so Paint alpha is ignored — you cannot soften a mesh that way | wash stayed at full strength; composite the snapshot instead |
| a full-strength mesh under type | ground luminance drops enough to break the 4.5:1 rule | 6.28:1 → **3.33:1** at 100%; 12.5:1 at 45% |
| an SkSL return at alpha 1.0 | replaces the ground rather than texturing it | ground L 0.90 → 0.506 |
| `h(floor(c / u_scale))` as "paper grain" | hard square cells — reads as a quilt at 1000 px, and costs bytes proportional to cell count | §10 blocky rows |
| continuous-tone value noise | looks subtle, is catastrophic for PNG | 257–978 KB for a ground (§10) |
| `TextAlign.kJustify` on a display face | stretches word spaces into visible rivers | first proof render, body copy |
| `ColorFilters.HSLAMatrix(identity)` | not bit-exact on RGB→HSL→RGB | `[148,40,147]` vs `[148,40,148]` |
| `count_nonzero(alpha)` as an ink measure | every pixel is opaque after `clear()`, so it returns the canvas area | 160,000 of 160,000 |
| naive `(max+0.05)/(min+0.05)` on 8-bit luma | not WCAG — understates a light-ground/dark-ink pair by ~2.3×, so it fails pins that are fine | 5.39:1 naive vs **12.23:1** WCAG on the same pixels |

---

## 13. End-to-end proof: the recipes assemble into a pin

This file is not a wish list. `vendor/typography-labs/py/verify_doc_recipes.py` builds
one complete 1000×1500 pin using **only** the forms documented above — a mesh wash
composited at partial alpha, a 5-level SkSL paper tooth, a hook word placed with
`allocRunPos` under a per-glyph tracking roll, a three-line body paragraph whose second
run carries a gradient `setForegroundPaint`, a ghost word in a clipped band, a
`kMultiply` overprint rule, an ornament glyph drawn fill + dashed stroke, and a tracked
colophon rail — then runs the checks `docs/PIN-ART-DIRECTION.md` §12 names. Run it
against any face: `python verify_doc_recipes.py /path/to/Font.otf`. Last measured run,
all green, against `font-factory/fonts/13-andallan/…/Andallan.otf`:

```
0 glyph coverage of the face under test        loaded 'Andallan'; Harbour 7/7, body 112/112, 日本語 0/3
1 mesh ground (drawPatch kModulate + white)    66 unique colours, ground L~0.902
2 SkSL paper tooth, kMultiply                  4 levels in ground, range [0.84, 0.89]
3 hook word, allocRunPos stagger + roll        'Harbour' at rung 240, 7 glyphs, ink to x=814
4 body paragraph, mixed runs + gradient run    Height=131.0 LongestLine=799.4 ~3 lines, unowned=0
5 ghost word (kMultiply tint, clipped band)    'everybody' 150pt, 700px, bleeds x=420
6 overprint rule (Paint kMultiply)             overlap reads [40, 27, 23]
7 ornament glyph: fill + dashed outline        '&' gid 9, 156.4x213.2 at x=778
8 colophon rail (name as subtext)              rail width=181px, baseline=1332
CHECK contrast (WCAG, rendered pixels)         ground L=0.735 ink L=0.013 ratio=12.48:1 (floor 4.5)
CHECK thumbnail legibility (200px wide)        hook band 1531/9000 dark px = 17% (want 15-60%)
CHECK size cap, PNG vs JPEG                    PNG 153.1 KB / JPEG90 93.9 KB (cap 200)
SVG export keeps the design vector             9 KB, text-as-paths=True
```

Six corrections came out of *assembling* this, none out of reading the API:

1. The first render had the **font name as the hero** and the phrase small — the exact
   inversion §5 of the direction doc warns about. Swapping them (hook = a word from the
   copy, name = the rail) is what made it read as a design rather than a product tile.
2. A full-strength mesh under type measured **3.33:1**; the same wash composited at
   `Alphaf=0.45` measures 12.48:1. Paint alpha cannot soften a `kModulate` patch — it has
   to be composited from its own snapshot.
3. Continuous-tone tooth put the PNG at **594.6 KB**; quantising to 5 levels brought the
   whole pin back to 153 KB (§10).
4. `TextAlign.kJustify` on a script face opened rivers in the body copy → `kLeft`.
5. A dead middle band is a composition bug, not a spacing preference — the ghost word
   exists because the first proof had ~250 px of nothing in it.
6. `allocRunPosH` takes **absolute x per glyph**; passing `M + i*6` as "tracking" stacked
   the word into a 255 px smudge. Accumulate `advance + tracking` yourself.

Re-run it after any renderer-doc edit that touches a recipe, and paste the new numbers
here. If a number regresses (contrast under 4.5, PNG over 200 KB, thumbnail outside
15–60%), the doc is wrong or the pin is wrong — find out which before shipping.

Three of those numbers came from **fixing this document, not the code**: the quote block
was 1986 px tall until §4.1 killed the leading knob, the pin was 282 KB until §10 moved
the grain to `u_scale=28`, and the contrast check read 1.0:1 until it sampled the
darkest 5th percentile of the ink region instead of its top-left pixel. When a check
passes trivially, suspect the check.

Re-run it after any renderer-doc edit that touches a recipe, and paste the new numbers
here.

---

## 14. How to extend this file

Run a probe in `vendor/typography-labs/py/probeN.py` using the plain-function
`ask(label, fn)` harness (`probe4.py` onward). Nested-lambda one-liners produced five
`SyntaxError` rounds and were abandoned; write plain functions. Verify with **ink or
sampled pixels**, never with "it returned without raising" — `drawVertices` with the
default paint "worked" and drew black.

Add the `OK` line's exact call form here, keep the measured number with it, and add any
silent-failure discovery to §12 or the trap table. The next agent renders from this
document without re-deriving it.
