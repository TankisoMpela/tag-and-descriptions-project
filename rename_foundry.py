import os
import re

directories_to_check = ['.', 'agents', 'custom-gpt', 'templates', '.claude', '.codex', '.kilo', 'font-factory', 'brush-factory']
extensions_to_check = ['.md', '.txt', '.toml', '.py']

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return

    original_content = content

    # Replace "FontFairy" with "FontFairy" just in case they added it already
    content = content.replace("FontFairy", "FontFairy")
    content = content.replace("FontFairy", "FontFairy")

    # Replace FontFairy
    content = content.replace("FontFairy", "FontFairy")
    content = content.replace("FontFairy", "FontFairy")
    
    # Replace FontFairy (if any left)
    content = content.replace("FontFairy", "FontFairy")
    content = content.replace("FontFairy", "FontFairy")

    # Replace FontFairy
    content = content.replace("FontFairy", "FontFairy")
    content = content.replace("FontFairy", "FontFairy")

    # Replace paper moon / pixel brush lowercase maybe?
    # content = content.replace("fontfairy.booth.pm", "fontfairy.booth.pm") # Maybe don't touch URLs unless requested? 
    # The user says "the foundry name, now the thumbnail should say FontFairy instead of FontFairy"
    # To be safe with URLs, let's leave them if they are in lowercase? Wait, if they are fontfairy.booth.pm, it's safer to keep the URL, or rename it.
    
    # "b'FAIR'" is the vendor code in Agent 13.
    content = content.replace("b'FAIR'", "b'FAIR'")
    content = content.replace("fontfairy", "fontfairy")

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

for root, dirs, files in os.walk('.'):
    if any(ignore in root for ignore in ['.git', 'node_modules', '.venv', 'venv']):
        continue
    for file in files:
        if any(file.endswith(ext) for ext in extensions_to_check):
            filepath = os.path.join(root, file)
            process_file(filepath)

print("Done")
