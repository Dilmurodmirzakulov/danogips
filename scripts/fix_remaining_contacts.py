#!/usr/bin/env python3
"""
Script to fix remaining contact information patterns.
"""

import os
import re
from pathlib import Path

# Root directory of the website
ROOT_DIR = Path(__file__).parent.parent / "www.danogips.ru"

# Patterns to fix
REPLACEMENTS = [
    # Fix tel href that wasn't caught
    (r'href="tel:88002507926"', 'href="tel:+998712310909"'),
    (r'href="tel: 88002507926"', 'href="tel:+998712310909"'),
    
    # Any remaining old phone display format
    (r'>8 \(800\) 250-79-26<', '>+998 71 231 09 09<'),
    (r'>8 800 250 79 26<', '>+998 71 231 09 09<'),
    
    # Any remaining old email
    (r'>cs@danogips\.ru<', '>info.uzchem@gmail.com<'),
    (r'mailto:cs@danogips\.ru', 'mailto:info.uzchem@gmail.com'),
    
    # Any remaining Telegram
    (r'href="https://t\.me/danogips_russia"', 'href="https://t.me/uzchem_official"'),
    
    # Any remaining Instagram  
    (r'href="https://www\.instagram\.com/danogips_russia/"', 'href="https://www.instagram.com/uzchem?igsh=Yjc5dXF2emhpZm51"'),
    (r'href="https://www\.instagram\.com/danogips_russia"', 'href="https://www.instagram.com/uzchem?igsh=Yjc5dXF2emhpZm51"'),
    
    # Any remaining Facebook
    (r'href="https://www\.facebook\.com/danogips"', 'href="https://www.facebook.com/uzchem.uz?locale=ru_RU"'),
]

def update_file(file_path: Path) -> bool:
    """Fix remaining contact patterns in a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to update all HTML files."""
    html_files = list(ROOT_DIR.rglob("*.html"))
    updated_count = 0
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    for file_path in html_files:
        if update_file(file_path):
            updated_count += 1
            print(f"Updated: {file_path.relative_to(ROOT_DIR)}")
    
    print(f"\nDone! Updated {updated_count} files out of {len(html_files)} total.")

if __name__ == "__main__":
    main()

