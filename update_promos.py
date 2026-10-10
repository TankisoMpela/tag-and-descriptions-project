import os

def update_file(path, old, new):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    with open(path, 'r') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(path, 'w') as f:
            f.write(content)
        print(f"Updated {path}")
    else:
        print(f"Text not found in {path}")

agent_27 = "agents/agent-27-font-image-generator.md"
old_27 = """  two materially new visual decisions. Across the eight promos, use at least
  six distinct visual strategies (for example:"""
new_27 = """  two materially new visual decisions. Crucially, every promo image must use a distinctly
  different color palette (e.g., entirely different dominant hue families) and a completely
  unique conceptual hook or visual metaphor. Do not reuse a dominant color scheme.
  Across the eight promos, use at least six distinct visual strategies (for example:"""
update_file(agent_27, old_27, new_27)

agent_toml = ".codex/agents/font-image-generator.toml"
old_toml = """new visual decisions, and no motif, layout language, or near-identical prompt
may be reused. Across the eight promos, use at least six distinct visual strategies"""
new_toml = """new visual decisions, and no motif, layout language, or near-identical prompt
may be reused. Crucially, every promo image must feature a distinctly different
color palette (e.g., completely different dominant hue families) and a unique
conceptual hook. Do not reuse a dominant color scheme across the promos.
Across the eight promos, use at least six distinct visual strategies"""
update_file(agent_toml, old_toml, new_toml)

director = "custom-gpt/font-image-director-instructions.txt"
old_director = """Do not repeat the same context across the set merely to make it feel consistent; keep only the family constants that the font genuinely supports."""
new_director = """Do not repeat the same context across the set merely to make it feel consistent; keep only the family constants that the font genuinely supports. Ensure each image uses a distinctly different color palette and a completely unique concept."""
update_file(director, old_director, new_director)

renamer = "custom-gpt/Font Renamer.txt"
old_renamer = """metaphor, and composition. Do not reuse one context across the thumbnail and all promos. Family
resemblance comes from letterform fidelity, quality, and selected visual constants—not from
repeating the same setting, object, palette treatment, or layout."""
new_renamer = """metaphor, and composition. Do not reuse one context across the thumbnail and all promos.
Every promo must also use a distinctly different color palette and a unique conceptual hook.
Family resemblance comes from letterform fidelity, quality, and selected visual constants—not from
repeating the same setting, object, palette treatment, or layout."""
update_file(renamer, old_renamer, new_renamer)

reimag = "custom-gpt/supporting-image-reimagination-prompt.txt"
old_reimag = """creative direction, not as permission to invent a product claim. Do not reuse
one context across every promo. Family resemblance comes from the font
letterforms, quality, and selected visual constants—not from repeating the same
setting, object, palette treatment, or layout."""
new_reimag = """creative direction, not as permission to invent a product claim. Do not reuse
one context across every promo. Every image must use a distinctly different
color palette and a unique conceptual hook. Family resemblance comes from the font
letterforms, quality, and selected visual constants—not from repeating the same
setting, object, palette treatment, or layout."""
update_file(reimag, old_reimag, new_reimag)

