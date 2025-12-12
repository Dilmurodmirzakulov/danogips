#!/usr/bin/env python3
"""
Script to update contact information across all HTML files.
Updates address, phone numbers, email, and social media links to Uzbek company data.
"""

import os
import re
from pathlib import Path

# Root directory of the website
ROOT_DIR = Path(__file__).parent.parent / "www.danogips.ru"

# Contact information replacements
REPLACEMENTS = [
    # Address replacements
    (r'192102,\s*Россия,\s*г\.\s*Санкт-Петербург,\s*<br/>\s*ул\.\s*Салова\s*д\.\s*45,\s*лит\.\s*Ж,\s*ПОМ/КОМ,\s*1-Н/17',
     'ТАШКЕНТСКАЯ ОБЛАСТЬ, КИБРАЙСКИЙ РАЙОН, <br/>\n                            улица Карамурт, дом 2А'),
    (r'192102,\s*Rossiya,\s*Sankt-Peterburg\s*shahri,\s*<br/>\s*salov\s*ko\'chasi,\s*45-uy,\s*lit\.\s*F,\s*POM/COM,\s*1-N\s*/\s*17',
     'ТАШКЕНТСКАЯ ОБЛАСТЬ, КИБРАЙСКИЙ РАЙОН, <br/>\n                            улица Карамурт, дом 2А'),
    # Old format address
    (r'192102, Россия, г\. Санкт Петербург, ул\. Салова д\. 45, лит\. Ж ПОМ/КОМ, 1-Н/17',
     'ТАШКЕНТСКАЯ ОБЛАСТЬ, КИБРАЙСКИЙ РАЙОН, улица Карамурт, дом 2А'),
    
    # Phone number replacements
    (r'<a href="tel:88002507926">8 \(800\) 250-79-26</a>',
     '<a href="tel:+998712310909">+998 71 231 09 09</a><br/><a href="tel:+998971575859">+998 97 157 58 59</a>'),
    (r'<a href="tel: 8 800 250 79 26">8 800 250 79 26</a>',
     '<a href="tel:+998712310909">+998 71 231 09 09</a>'),
    (r'<a class="trial-phone" href="tel: 8 800 250 79 26">8 800 250 79 26</a>',
     '<a class="trial-phone" href="tel:+998712310909">+998 71 231 09 09</a>'),
    (r'8 \(800\) 250-79-26', '+998 71 231 09 09'),
    (r'8 800 250 79 26', '+998 71 231 09 09'),
    (r'\+7 \(812\) 347-79-26, доб\. 46103', '+998 71 231 09 09'),
    (r'\+7 \(812\) 347-79-26', '+998 71 231 09 09'),
    
    # Email replacements
    (r'cs@danogips\.ru', 'info.uzchem@gmail.com'),
    
    # Telegram replacements
    (r'https://t\.me/danogips_russia', 'https://t.me/uzchem_official'),
    
    # Instagram replacements
    (r'https://www\.instagram\.com/danogips_russia/?', 'https://www.instagram.com/uzchem?igsh=Yjc5dXF2emhpZm51'),
    
    # Facebook replacements
    (r'https://www\.facebook\.com/danogips(?!\.)(?!/)', 'https://www.facebook.com/uzchem.uz?locale=ru_RU'),
    
    # VK removal - replace with nothing or keep only the closing tag
    # We'll handle social media section separately
    
    # JSON-LD structured data
    (r'"postalCode":\s*"192102"', '"postalCode": ""'),
    (r'"streetAddress":\s*"ул\. Салова д\. 45, лит\. Ж, ПОМ/КОМ, 1-Н/17"',
     '"streetAddress": "ТАШКЕНТСКАЯ ОБЛАСТЬ, КИБРАЙСКИЙ РАЙОН, улица Карамурт, дом 2А"'),
    (r'"telephone":\s*"8 \(800\) 250-79-26"', '"telephone": "+998 71 231 09 09"'),
    (r'"email":\s*"cs@danogips\.ru"', '"email": "info.uzchem@gmail.com"'),
]

def update_file(file_path: Path) -> bool:
    """Update contact information in a single HTML file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)
        
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


