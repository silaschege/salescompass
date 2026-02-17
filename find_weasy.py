import os

print("Searching for 'weasyprint' in .py files...")
for root, dirs, files in os.walk('.'):
    if 'env' in root: continue # Skip env
    for file in files:
        if file.endswith('.py') or file.endswith('.txt'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'weasyprint' in content.lower():
                        print(f"Found in: {path}")
            except Exception as e:
                print(f"could not read {path}: {e}")
print("Search complete.")
