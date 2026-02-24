"""
One-time script to restructure sample directories into proper project format.
Each sample (book, invoice, letter, poster, report, ticket) gets:
  - project.json
  - templates/main.html
  - queries/main.sql  
  - assets/fonts/  (font files moved here)
  - assets/images/ (image files moved here)
  - assets/styles/ (CSS files moved here)
  - templates/components/
  - output/
"""
import os
import json
import shutil
from datetime import datetime

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), 'samples')

# File extension categories
FONT_EXTENSIONS = {'.ttf', '.otf', '.woff', '.woff2'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
CSS_EXTENSIONS = {'.css'}
HTML_EXTENSIONS = {'.html'}
SKIP_EXTENSIONS = {'.pdf'}  # Don't include PDFs in project

PROJECT_DIRS = [
    'queries',
    'templates',
    'templates/components',
    'assets/fonts',
    'assets/images',
    'assets/styles',
    'output'
]

# Sample descriptions
DESCRIPTIONS = {
    'book': 'Book layout with chapters, fonts and images',
    'invoice': 'Professional invoice template',
    'letter': 'Formal letter template with letterhead',
    'poster': 'Poster/flyer design template',
    'report': 'Multi-section report with typography features',
    'ticket': 'Event ticket with barcode support',
}


def restructure_sample(sample_name: str):
    """Restructure a single sample directory into project format."""
    sample_path = os.path.join(SAMPLES_DIR, sample_name)
    if not os.path.isdir(sample_path):
        print(f"  Skipping {sample_name}: not a directory")
        return

    print(f"\n=== Restructuring '{sample_name}' ===")

    # Collect all files (including from subdirectories)
    all_files = []
    for root, dirs, files in os.walk(sample_path):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, sample_path)
            all_files.append((full_path, rel_path, f))

    # Categorize files
    html_files = []
    css_files = []
    font_files = []
    image_files = []
    other_files = []

    for full_path, rel_path, filename in all_files:
        ext = os.path.splitext(filename)[1].lower()
        if ext in HTML_EXTENSIONS:
            html_files.append((full_path, rel_path, filename))
        elif ext in CSS_EXTENSIONS:
            css_files.append((full_path, rel_path, filename))
        elif ext in FONT_EXTENSIONS:
            font_files.append((full_path, rel_path, filename))
        elif ext in IMAGE_EXTENSIONS:
            image_files.append((full_path, rel_path, filename))
        elif ext in SKIP_EXTENSIONS:
            print(f"  Skipping PDF: {rel_path}")
        else:
            other_files.append((full_path, rel_path, filename))

    print(f"  Found: {len(html_files)} HTML, {len(css_files)} CSS, "
          f"{len(font_files)} fonts, {len(image_files)} images, {len(other_files)} other")

    # Create a temp directory for the restructured project
    temp_path = sample_path + '_restructured'
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)

    # Create project directory structure
    for subdir in PROJECT_DIRS:
        os.makedirs(os.path.join(temp_path, subdir), exist_ok=True)

    # Move HTML -> templates/main.html (use the primary one)
    # Find the primary HTML file (matches sample name or is the only one)
    primary_html = None
    for full_path, rel_path, filename in html_files:
        base = os.path.splitext(filename)[0].lower()
        if base == sample_name:
            primary_html = (full_path, rel_path, filename)
            break
    if not primary_html and html_files:
        primary_html = html_files[0]

    if primary_html:
        src = primary_html[0]
        dst = os.path.join(temp_path, 'templates', 'main.html')
        shutil.copy2(src, dst)
        print(f"  Template: {primary_html[1]} -> templates/main.html")

    # Move CSS -> assets/styles/
    asset_styles = []
    for full_path, rel_path, filename in css_files:
        dst = os.path.join(temp_path, 'assets', 'styles', filename)
        shutil.copy2(full_path, dst)
        asset_styles.append(f"assets/styles/{filename}")
        print(f"  Style: {rel_path} -> assets/styles/{filename}")

    # Move fonts -> assets/fonts/
    asset_fonts = []
    for full_path, rel_path, filename in font_files:
        dst = os.path.join(temp_path, 'assets', 'fonts', filename)
        shutil.copy2(full_path, dst)
        asset_fonts.append(f"assets/fonts/{filename}")
        print(f"  Font: {rel_path} -> assets/fonts/{filename}")

    # Move images -> assets/images/
    asset_images = []
    for full_path, rel_path, filename in image_files:
        dst = os.path.join(temp_path, 'assets', 'images', filename)
        shutil.copy2(full_path, dst)
        asset_images.append(f"assets/images/{filename}")
        print(f"  Image: {rel_path} -> assets/images/{filename}")

    # Create default main.sql query
    query_content = """-- Main report query
-- Replace this with your actual SQL query
-- Use :param_name syntax for parameters

SELECT * FROM CLIENT_AS_SAS_130_25.TLR_MODEL
"""
    query_path = os.path.join(temp_path, 'queries', 'main.sql')
    with open(query_path, 'w', encoding='utf-8') as f:
        f.write(query_content)
    print(f"  Query: queries/main.sql (TLR_MODEL default)")

    # Create project.json
    now = datetime.now().isoformat()
    display_name = sample_name.replace('_', ' ').title()
    project_config = {
        "name": display_name,
        "version": "1.0.0",
        "description": DESCRIPTIONS.get(sample_name, f"{display_name} template"),
        "author": "WeasyPrint Samples",
        "created": now,
        "updated": now,
        "settings": {
            "pageSize": "A4",
            "orientation": "portrait",
            "margins": {
                "top": "2cm",
                "right": "1.5cm",
                "bottom": "2cm",
                "left": "1.5cm"
            },
            "defaultFont": None
        },
        "mainTemplate": "templates/main.html",
        "mainQuery": "queries/main.sql",
        "subReports": [],
        "assets": {
            "fonts": asset_fonts,
            "images": asset_images,
            "styles": asset_styles
        },
        "parameters": []
    }

    config_path = os.path.join(temp_path, 'project.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(project_config, f, ensure_ascii=False, indent=2)
    print(f"  Config: project.json created")

    # Replace original with restructured
    shutil.rmtree(sample_path)
    shutil.move(temp_path, sample_path)
    print(f"  ✓ '{sample_name}' restructured successfully!")


def main():
    print("Restructuring samples into project format...")
    print(f"Samples directory: {SAMPLES_DIR}")

    for item in sorted(os.listdir(SAMPLES_DIR)):
        item_path = os.path.join(SAMPLES_DIR, item)
        if os.path.isdir(item_path):
            restructure_sample(item)

    print("\n\n=== All samples restructured! ===")


if __name__ == '__main__':
    main()
