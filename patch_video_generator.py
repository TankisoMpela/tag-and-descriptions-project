import os

showcase_file = "font-video-generator/src/showcase.ts"
with open(showcase_file, "r") as f:
    content = f.read()

old_props = """export type ShowcaseProps = {
  fontName: string;
  segments: ShowcaseSegment[];
  width?: number;
  height?: number;
};"""

new_props = """export type ShowcaseProps = {
  fontName: string;
  segments: ShowcaseSegment[];
  width?: number;
  height?: number;
  backgroundColor?: string;
  textColor?: string;
};"""

if old_props in content:
    content = content.replace(old_props, new_props)
    with open(showcase_file, "w") as f:
        f.write(content)
    print("Patched showcase.ts")
else:
    print("Could not find ShowcaseProps in showcase.ts")

comp_file = "font-video-generator/src/Composition.tsx"
with open(comp_file, "r") as f:
    comp_content = f.read()

old_bg = 'backgroundColor: "#111111",'
new_bg = 'backgroundColor: props.backgroundColor || "#111111",'
old_text = 'color: "#f4f0e8",'
new_text = 'color: props.textColor || "#f4f0e8",'

if old_bg in comp_content and old_text in comp_content:
    comp_content = comp_content.replace(old_bg, new_bg)
    comp_content = comp_content.replace(old_text, new_text)
    with open(comp_file, "w") as f:
        f.write(comp_content)
    print("Patched Composition.tsx")
else:
    print("Could not find color styles in Composition.tsx")

