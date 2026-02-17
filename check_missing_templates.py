import os

def check_templates():
    with open('unique_templates.txt', 'r') as f:
        templates = [line.strip() for line in f if line.strip()]

    # Templates that look like they have extra bits from grep
    # e.g. tenants/archive_confirm.html', {'tenant
    clean_templates = []
    for t in templates:
        if "'," in t:
            t = t.split("',")[0]
        if '"' in t:
            t = t.split('"')[0]
        if "'" in t:
            t = t.split("'")[0]
        clean_templates.append(t)
    
    clean_templates = sorted(list(set(clean_templates)))

    # Find all template directories
    base_dir = '/home/silaskimani/Documents/replit/git/salescompass/core'
    template_dirs = []
    for root, dirs, files in os.walk(base_dir):
        if 'templates' in dirs:
            template_dirs.append(os.path.join(root, 'templates'))

    missing = []
    for t in clean_templates:
        found = False
        for td in template_dirs:
            # Django looks for templates relative to the 'templates' directory
            # but usually it's app_name/template_name.html
            full_path = os.path.join(td, t)
            if os.path.exists(full_path):
                found = True
                break
        if not found:
            missing.append(t)
    
    print(f"Total templates checked: {len(clean_templates)}")
    print(f"Total missing templates: {len(missing)}")
    for m in missing:
        print(m)

if __name__ == "__main__":
    check_templates()
