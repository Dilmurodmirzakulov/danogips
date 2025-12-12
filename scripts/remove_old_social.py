#!/usr/bin/env python3
"""
Script to remove VK, YouTube, and Rutube social links from all HTML files.
Keeps only Telegram, Facebook, and Instagram.
"""

import os
import re
from pathlib import Path

# Root directory of the website
ROOT_DIR = Path(__file__).parent.parent / "www.danogips.ru"

# Patterns to remove (entire link elements)
# VK link pattern
VK_LINK_PATTERN = re.compile(
    r'<a[^>]*href="https://vk\.com/[^"]*"[^>]*>.*?</a>\s*',
    re.DOTALL | re.IGNORECASE
)

# YouTube link pattern  
YOUTUBE_LINK_PATTERN = re.compile(
    r'<a[^>]*href="https://www\.youtube\.com/[^"]*"[^>]*>.*?</a>\s*',
    re.DOTALL | re.IGNORECASE
)

# Rutube link pattern
RUTUBE_LINK_PATTERN = re.compile(
    r'<a[^>]*href="https://rutube\.ru/[^"]*"[^>]*>.*?</a>\s*',
    re.DOTALL | re.IGNORECASE
)

def update_file(file_path: Path) -> bool:
    """Remove VK, YouTube, Rutube links from a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Remove VK links
        content = VK_LINK_PATTERN.sub('', content)
        
        # Remove YouTube links
        content = YOUTUBE_LINK_PATTERN.sub('', content)
        
        # Remove Rutube links
        content = RUTUBE_LINK_PATTERN.sub('', content)
        
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

