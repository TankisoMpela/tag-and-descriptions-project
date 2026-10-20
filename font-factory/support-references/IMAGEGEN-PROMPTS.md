# One-pass image materials

Each asset below is generated once with the built-in OpenAI image-generation
tool, using its listed reference for visual direction or as an edit target.
These are clean materials for the Skia templates, not finished supporting images; lettering,
logos, captions, and product names are rebuilt separately in code.

| Material | Reference |
|---|---|
| `materials/T30332_01_stardust-photo.png` | `T30332_01.jpg` |
| `materials/T30332_02_cliff-sea-background.png` | `T30332_02.jpg` |
| `materials/T30332_06-clean-index-plate.png` | `T30332_06.jpg` |
| `materials/T30332_07-clean-sunset-background.png` | `T30332_07.jpg` |
| `materials/T30332_08-clean-phone-plate-no-lettering.png` | `T30332_08.jpg` |
| `materials/T24908_00_amber-dawn-photo.png` | `T24908_00.jpg` |
| `materials/T24908_01_skin-portrait-background.png` | `T24908_01.jpg` |
| `materials/T24908_02_clean-photo-background.png` | `T24908_02.jpg` |
| `materials/T24908_03_gelato-background.png` | `T24908_03.jpg` |
| `materials/T26289_01_orange-fashion-cutout.png` | `T26289_01.jpg` |
| `materials/T28576_03_editorial-face-cutout.png` | `T28576_03.jpg` |
| `materials/T28576_04_eye-illustration-clean.png` | `materials/T28576_04_eye-illustration.png` |
| `materials/T28576_06_soft-focus-portrait.png` | `T28576_06.jpg` |
| `materials/T28576_09_beach-fashion-cutout.png` | `T28576_09.jpg` |
| `materials/T19827_01_electromagnetic-texture.png` | `T19827_01.jpg` |
| `materials/T19827_06_demolition-texture.png` | `T19827_06.jpg` |
| `materials/T21458_04_distressed-red-paper.png` | `T21458_04.jpg` |
| `materials/T21458_11_stadium-red-print.png` | `T21458_11.jpg` |
| `materials/T28660_00_red-jacket-photo.png` | `T28660_00.jpg` |
| `materials/T26003_01_lemonade-line-art.png` | `T26003_01.jpg` |

## Prompts

### T30332_06 — clean index-board backing plate

Use case: precise-object-edit. Asset type: text-free backing plate used as a local bitmap material in a typography specimen. Edit the attached image as an exact cleanup. Remove only the dark navy list text/numbers from the large pastel gradient rectangle and the two dark labels inside the small stacked plates at bottom right. Fill those letters naturally using the surrounding gradient so no ghost letters remain. Preserve everything else pixel-faithfully: 1184x792 framing, white background, thin navy frame, all seven pink circular nodes, all three left folder tabs, exact size/position/edges and pastel appearance of the central gradient rectangle, exact shapes/colors/outlines of both lower-right plates. Do not add, redraw, move, recolor, or remove any other element. No text anywhere.

### T30332_07 — text-free sunset-promise background

Use case: precise-object-edit. Asset type: clean 3:2 backing plate for a reference-matched typography specimen. Edit the attached T30332_07 reference. Remove only the large white-filled, dark-outlined headline from the lavender area and remove the two source labels 'TAN TYPE CO.' and 'SADIE' from the white header. Seamlessly restore the exact surrounding lavender/pink textured field and white header where those letters were. Preserve the entire composition and all non-text artwork: page crop, original pixel-art sunset illustration at upper-left with its dark frame (do not redraw it), pale lavender floral background, all pink pixel sparkles/flower decorations, small outlined globe icon, top-right pixel marks, and both corner four-point stars. Do not add text or other design elements. Do not change colors, scale, crop, positions, or layout. Output the same 3:2 composition as a text-free material plate.

### T30332_08 — text-free three-phone plate

Use case: precise-object-edit. Asset type: text-free backing plate for a three-phone typography specimen. Edit the attached T30332_08 reference. Remove all words and lettering from all three phone screens, including every occurrence of 'CONVENT GARDEN' and the right-screen message 'Timeless Charm, Rooted in Grace.', plus the two vertical source labels between the phones ('TAN TYPE CO.' and 'SADIE'). Restore the original warm-cream screen areas cleanly where text was. Preserve the exact 3:2 page crop, bright yellow background, all three black outlined phone bodies and their size/position/rounded corners, cream screens, top speaker islands and menu/search icons, every flower illustration (including petals, leaves and centers), and every small star/sparkle. Do not redraw, move, recolor, enlarge, or remove any flower, phone, or decorative star. Add no text and no new elements. The output is a clean plate for separately typeset copy.

### T30332_01 — grayscale editorial portrait

Use case: photorealistic-natural. Asset type: text-free 3:2 background plate for a type specimen. Input image: `T30332_01.jpg`, reference for monochrome mood and portrait placement only. Create a polished black-and-white fashion-editorial head-and-shoulders photograph of an adult woman wearing a simple high-neck dark top, with dark windswept hair, soft atmospheric light, and subtle film grain. Keep the fully clothed subject toward the left half and reserve calm dark negative space on the right for separately typeset copy. Non-suggestive portrait. No lettering, logos, watermark, frame, or graphic overlays.

### T30332_02 — quiet sea and lone figure

Use case: photorealistic-natural. Asset type: text-free 3:2 landscape background. Input image: `T30332_02.jpg`, reference for the solitary figure and coastal mood only. Create a serene pale turquoise sea beneath a wide soft sky, with a small back-facing person standing on a rocky ledge near the horizon. Keep the palette misty blue, warm sand, and cream; preserve generous uncluttered sky for later typography. No lettering, logos, watermark, or frame.

### T24908_00 — warm fashion-photo backdrop

Use case: photorealistic-natural. Asset type: text-free 3:2 fashion-editorial background. Input image: `T24908_00.jpg`, reference for warm light, glass-block setting, and portrait scale only. Create an editorial fashion photograph of a fully clothed adult woman with long dark hair in a simple black outfit, standing by a softly lit aqua glass-block wall. Use amber sunlight and gentle film grain; leave a clean open area across the left side for separately drawn display lettering. No lettering, logos, watermark, or graphic overlays.

### T24908_01 — beauty portrait backdrop

Use case: photorealistic-natural. Asset type: text-free 3:2 beauty-editorial background. Input image: `T24908_01.jpg`, reference for close portrait scale and soft lilac/rose atmosphere only. Create a close head-and-shoulders portrait of a fully clothed adult with real skin texture and dark hair, lit softly in muted lilac, rose, and warm cream. Keep the face toward one side and leave the opposite side visually quiet for circular type labels. No lettering, logos, watermark, circles, or graphic overlays.

### T24908_02 — clean red-blazer lookbook photo

Use case: precise-object-edit. Asset type: clean full-bleed editorial fashion photograph plate for a typography specimen. Input image: the attached T24908_02 reference is the edit target. Remove all overprinted white lettering and the small footer labels, then naturally reconstruct only the photo areas hidden by the text. Preserve the original photograph as closely as possible: same adult model, cropped pose, red ribbed blazer, black top, necklaces, left-of-center placement, concrete-and-glass architecture, lighting, colors, camera angle, framing, and photographic grain. Change only the overprinted typography and labels. The clean result must contain no text, logos, graphic shapes, added objects, or watermark.

### T24908_03 — gelato-shop photo backdrop

Use case: photorealistic-natural. Asset type: text-free 3:2 dessert-editorial background. Input image: `T24908_03.jpg`, reference for a gelato cone and pastel shop mood only. Create a close editorial photograph of a hand holding a colorful gelato cone in a bright, softly focused pastel-pink dessert shop. Keep the cone in the upper-right area, with calm pale counter space across the lower half for separately drawn product cards. No lettering, logos, watermark, or graphic overlays.

### T26289_01 — orange-fashion portrait cutout

Use case: illustration-story. Asset type: transparent-background 4:5 editorial photo cutout. Input image: `T26289_01.jpg`, reference for the playful pose, hair buns, and orange slices over the eyes only. Create a joyful, fully clothed adult woman from the waist up, wearing a colorful top, with dark hair in two buns and one orange slice held over each eye. Natural hands, believable anatomy, playful fashion-magazine photography, crisp subject edges. Isolated on genuine transparency; no background, text, logos, watermark, border, or extra props.

### T28576_03 — ink-fashion face cutout

Use case: illustration-story. Asset type: transparent-background editorial illustration cutout. Input image: `T28576_03.jpg`, reference for the tightly cropped face, short dark hair, and fashion-magazine line-work only. Create a refined black-and-white ink illustration of a fully clothed adult woman's head and shoulders, short sculpted dark hair, direct gaze, fine hatch shading, and a small restrained red accent on the lips. Keep the face complete and centered with clean edges. Isolated on genuine transparency; no background, text, logos, watermark, or frame.

### T28576_04 — clean lettering from the eye illustration

Use case: precise-object-edit. Asset type: transparent illustration crop used as a supporting-image material in a typography layout. Edit the input crop. Change only the tiny light-colored source-font lettering printed across the larger eye's iris: remove those letters and reconstruct the iris/pupil and eyelash linework underneath so it reads as a clean eye. Preserve the existing eye shapes, gaze, brows, nose, hair strands, monochrome etched ink style, crop, scale, and every other detail. Keep the transparent background and original aspect ratio. Add no text, logos, marks, props, or new features. This was one built-in image-generation pass; the 2170x725 output was then trimmed 12px at the top and 14px at the bottom to discard edge artifacts.

### T28576_06 — soft-focus portrait background

Use case: photorealistic-natural. Asset type: text-free 3:2 fashion-editorial background for a large-type poster. Create a tasteful, non-identifiable, heavily defocused monochrome beauty portrait: only an adult model's vague face and dark hair are suggested, the face sits slightly right of center, dark hair blends into the upper edge, and the rest fades into pale gray-white. Soft analog-photo blur, low contrast, high-key, uncluttered, suitable beneath separate red typography and a small eye-detail insert. No sharp facial detail, no inset image, no text, logos, watermark, border, or graphic overlays.

### T28576_09 — vintage beach-fashion cutout

Use case: illustration-story. Asset type: transparent-background full-body fashion illustration. Input image: `T28576_09.jpg`, reference for the full-body pose, broad sunhat, sunglasses, and red polka-dot one-piece only. Create a poised adult woman in a modest, full-coverage vintage red polka-dot one-piece swimsuit, broad-brim sunhat, and dark sunglasses. Neutral standing pose, non-suggestive fashion-catalog illustration, elegant black ink contours with light grayscale shading and restrained red accents; show the entire figure and keep the silhouette clean. Isolated on genuine transparency; no beach scene, text, logos, watermark, or frame.

### T19827_01 — clean electromagnetic-poster texture

Use case: precise-object-edit. Asset type: clean reusable background plate for a typography poster. Input image: the provided reference poster, used as the edit target. Remove all typography, logos, tiny symbols, rules, and text from the image. Reconstruct only the underlying background where those elements were: dark rough charcoal concrete with subtle mottled grain, a soft violet glow left-of-center and a restrained acid-green glow right-of-center, fading into a nearly black vignette at the edges. Preserve the source image's color placement, lighting, grain character, and wide 3:2 composition as closely as possible. Constraints: background only; no text, letters, logos, symbols, lines, borders, objects, gradients with hard edges, or watermark. Keep the texture natural and understated.

### T19827_06 — clean demolition-poster texture

Use case: precise-object-edit. Asset type: reusable text-free background plate for a typography poster. Input image: the provided poster reference, used as the edit target. Remove all lettering, logos, tiny symbols, labels, and the globe illustration. Reconstruct only the underlying luminous abstract ground: softly mottled charcoal-black paper with broad warm amber and rust-colored haze around the left and upper portions, a restrained violet glow near the upper middle, and a bright lime-green center fading into violet near the lower edge. Preserve the source's soft atmospheric light placement, gentle analog grain, dark corners, and wide 3:2 crop as closely as possible. No text, letters, logos, symbols, globe, lines, borders, objects, hard-edged gradients, or watermark.

### T21458_04 — clean distressed-red paper

Use case: precise-object-edit. Asset type: reusable text-free background plate for a monumental date poster. Input image: the provided reference, used as the edit target. Remove every letter, number, logo, footer label, and licensing text. Rebuild the background as a full-bleed deep vermilion/crimson sheet with the same distressed printed-paper surface: subtle fibers, scuffs, cloudy ink variation, and darker worn edges. Preserve the source's exact 3:2 composition and red hue family. Do not leave pale ghosting from the large numerals; fill those areas with matching red paper texture. Background only: no text, digits, logos, objects, lines, symbols, border, or watermark.

### T21458_11 — clean stadium-red print plate

Use case: precise-object-edit. Asset type: reusable clean background plate for a sports typography poster. Input image: the provided football poster reference, used as the edit target. Remove all words, letters, logos, and small labels, including the huge white lettering. Reconstruct the source's full-bleed football-stadium crowd and players as a subtle photographic layer under a deep red distressed print treatment. Preserve the source's red monochrome tint, rough ink/grain texture, smoky shadows, player/crowd forms visible mostly through the right and lower areas, and wide 3:2 crop as closely as possible. No text, letters, logos, numbers, symbols, lines, or watermark.

### T28660_00 — red-jacket fashion photo

Use case: photorealistic-natural. Asset type: text-free 3:2 fashion-editorial background. Input image: `T28660_00.jpg`, reference for the red leather jacket, close crop, and weathered urban texture only. Create a candid editorial photograph of a fully clothed adult, cropped from shoulders to hips, featuring a vivid red tailored leather jacket over a dark top against a softly blurred gray city wall. Use natural overcast light and subtle analog grain; leave enough calm texture for large type. No lettering, logos, watermark, or graphic overlays.

### T26003_01 — engraved lemonade cutout

Use case: illustration-story. Asset type: transparent-background line-art illustration. Input image: `T26003_01.jpg`, reference for a single glass with citrus and straw only. Create a clean vintage engraved drawing of a tall glass of lemonade with ice, a curved straw, and two lemon slices, in confident dark ink with sparse etched shading. Center the full glass and fruit with crisp edges. Isolated on genuine transparency; no background, lettering, logos, watermark, or frame.
