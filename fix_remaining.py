import os

extensions = ['.md', '.txt', '.toml', '.json', '.py', '.sh']

def process(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return
        
    orig = content
    # Replace FONTFAIRY
    content = content.replace('FONTFAIRY', 'FONTFAIRY')
    content = content.replace('FontFairy', 'FontFairy')
    content = content.replace('FontFairy', 'FontFairy')
    
    # Optional: replace URLs
    content = content.replace('fontfairy.booth.pm', 'fontfairy.booth.pm')
    content = content.replace('masterbundles.com/vendor/fontfairy', 'masterbundles.com/vendor/fontfairy')
    content = content.replace('creativemarket.com/FontFairy', 'creativemarket.com/FontFairy')

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")

for root, dirs, files in os.walk('.'):
    if any(ignore in root for ignore in ['.git', 'node_modules', '.venv', 'venv']):
        continue
    for file in files:
        if any(file.endswith(ext) for ext in extensions):
            process(os.path.join(root, file))

print("Done")
