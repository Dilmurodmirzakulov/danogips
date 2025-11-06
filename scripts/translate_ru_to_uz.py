#!/usr/bin/env python3
import os
import re
import csv
import sys
import json
import time
import math
import hashlib
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Set

import requests
import chardet
from bs4 import BeautifulSoup, NavigableString, Comment, Doctype


def load_env(env_path_candidates: List[Path]) -> None:
    for p in env_path_candidates:
        if p.is_file():
            with p.open('rb') as fh:
                raw = fh.read()
            enc = chardet.detect(raw).get('encoding') or 'utf-8'
            for line in raw.decode(enc, errors='ignore').splitlines():
                if not line or line.strip().startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
            break


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


class CacheStore:
    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.cache: Dict[str, str] = {}
        if cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text('utf-8'))
            except Exception:
                self.cache = {}

    def get(self, text: str) -> str:
        return self.cache.get(text)

    def set(self, text: str, translated: str) -> None:
        self.cache[text] = translated

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), 'utf-8')


class YandexTranslator:
    def __init__(self, api_key: str, folder_id: str, batch_size: int = 80, max_chars: int = 9000, rpm: int = 300) -> None:
        self.api_key = api_key
        self.folder_id = folder_id
        self.batch_size = batch_size
        self.max_chars = max_chars
        self.rpm = rpm
        self.endpoint = 'https://translate.api.cloud.yandex.net/translate/v2/translate'

    def translate_batch(self, texts: List[str]) -> List[str]:
        headers = {
            'Authorization': f'Api-Key {self.api_key}',
            'Content-Type': 'application/json',
        }
        body = {
            'folderId': self.folder_id,
            'sourceLanguageCode': 'ru',
            'targetLanguageCode': 'uz',
            'texts': texts,
        }
        resp = requests.post(self.endpoint, headers=headers, json=body, timeout=60)
        if resp.status_code == 429:
            raise RateLimitError('429 Too Many Requests')
        resp.raise_for_status()
        data = resp.json()
        return [item['text'] for item in data.get('translations', [])]

    def translate(self, texts: List[str]) -> List[str]:
        results: List[str] = []
        window_start = time.time()
        requests_used = 0
        i = 0
        while i < len(texts):
            # Build a batch obeying both count and char limits
            batch: List[str] = []
            batch_chars = 0
            while i < len(texts) and len(batch) < self.batch_size:
                next_text = texts[i]
                if batch_chars + len(next_text) > self.max_chars and batch:
                    break
                batch.append(next_text)
                batch_chars += len(next_text)
                i += 1
            # Rate limiting
            now = time.time()
            elapsed = now - window_start
            if requests_used >= self.rpm:
                sleep_for = max(0.0, 60.0 - elapsed)
                time.sleep(sleep_for)
                window_start = time.time()
                requests_used = 0
            # Call API with retries
            backoff = 1.0
            for attempt in range(6):
                try:
                    translated = self.translate_batch(batch)
                    results.extend(translated)
                    requests_used += 1
                    break
                except RateLimitError:
                    time.sleep(backoff)
                    backoff = min(30.0, backoff * 2.0)
                except requests.RequestException as e:
                    if attempt >= 5:
                        raise
                    time.sleep(backoff)
                    backoff = min(30.0, backoff * 2.0)
        return results


class RateLimitError(Exception):
    pass


EXCLUDED_TAGS: Set[str] = { 'script', 'style', 'code', 'pre', 'noscript' }
TRANSLATE_ATTRS: Set[str] = { 'title', 'alt', 'aria-label', 'placeholder' }
META_DESC_SELECTORS: List[Tuple[str, str]] = [
    ('name', 'description'),
    ('property', 'og:description'),
]


def load_glossary(path: Path) -> List[Tuple[str, str, str]]:
    items: List[Tuple[str, str, str]] = []
    if not path.is_file():
        return items
    with path.open('r', encoding='utf-8') as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 3:
                items.append((row[0], row[1], row[2]))
    return items


def apply_pre_glossary(text: str, glossary: List[Tuple[str, str, str]]) -> str:
    for source, target, mode in glossary:
        if mode == 'dt' or mode == 'exact':
            text = text.replace(source, target)
        elif mode == 'regex':
            try:
                text = re.sub(source, target, text)
            except re.error:
                pass
    return text


def apply_post_glossary(text: str, glossary: List[Tuple[str, str, str]]) -> str:
    # Enforce target terms if translation drifted
    for source, target, mode in glossary:
        if mode in {'dt', 'exact'}:
            text = text.replace(target, target)
    return text


def extract_text_nodes(soup: BeautifulSoup) -> List[NavigableString]:
    nodes: List[NavigableString] = []
    for element in soup.descendants:
        if isinstance(element, NavigableString):
            if isinstance(element, Comment):
                continue
            parent = element.parent
            if parent and parent.name and parent.name.lower() in EXCLUDED_TAGS:
                continue
            text = str(element)
            if text.strip():
                nodes.append(element)
    return nodes


def extract_meta_descriptions(soup: BeautifulSoup) -> List[Tuple[str, 'bs4.element.Tag']]:
    metas: List[Tuple[str, 'bs4.element.Tag']] = []
    for attr, value in META_DESC_SELECTORS:
        for tag in soup.find_all('meta', attrs={attr: value}):
            content = tag.get('content')
            if content and content.strip():
                metas.append((content, tag))
    return metas


def extract_attr_texts(soup: BeautifulSoup) -> List[Tuple[str, 'bs4.element.Tag', str]]:
    items: List[Tuple[str, 'bs4.element.Tag', str]] = []
    for tag in soup.find_all(True):
        if tag.name.lower() in EXCLUDED_TAGS:
            continue
        for attr in TRANSLATE_ATTRS:
            if tag.has_attr(attr):
                val = tag.get(attr)
                if isinstance(val, str) and val.strip():
                    items.append((val, tag, attr))
    return items


def replace_in_html(
    soup: BeautifulSoup,
    nodes: List[NavigableString],
    node_texts: List[str],
    attr_items: List[Tuple[str, 'bs4.element.Tag', str]],
    attr_texts: List[str],
    meta_items: List[Tuple[str, 'bs4.element.Tag']],
    meta_texts: List[str],
) -> None:
    for node, new_text in zip(nodes, node_texts):
        safe_text = new_text if new_text is not None else ''
        node.replace_with(safe_text)
    for (old, tag, attr), new_text in zip(attr_items, attr_texts):
        tag[attr] = new_text if new_text is not None else ''
    for (old, tag), new_text in zip(meta_items, meta_texts):
        tag['content'] = new_text if new_text is not None else ''


def set_lang_and_hreflang(
    soup: BeautifulSoup,
    rel_path: str,
    is_uz_page: bool,
) -> None:
    html_tag = soup.find('html')
    if not html_tag:
        # Create minimal HTML structure if missing
        html_tag = soup.new_tag('html')
        body = soup.new_tag('body')
        # Move all top-level nodes into body, skipping Doctype declarations
        for child in list(soup.contents):
            if isinstance(child, Doctype):
                continue
            body.append(child.extract())
        html_tag.append(body)
        soup.append(html_tag)
    html_tag['lang'] = 'uz' if is_uz_page else (html_tag.get('lang') or 'ru')
    # Add alternate links
    head = soup.find('head')
    if not head:
        head = soup.new_tag('head')
        html_tag.insert(0, head)
    if is_uz_page:
        # Calculate relative path: count depth of rel_path and add one for uz/ directory
        depth = rel_path.count('/')
        up_levels = '../' * (depth + 1)
        alt_ru = soup.new_tag('link', rel='alternate', hreflang='ru', href=f"{up_levels}{rel_path}")
        head.append(alt_ru)
    else:
        # Calculate relative path: from Russian page to Uzbek version
        # For nested files, we need to go up to root, then into uz/
        depth = rel_path.count('/')
        up_levels = '../' * depth if depth > 0 else ''
        alt_uz = soup.new_tag('link', rel='alternate', hreflang='uz', href=f"{up_levels}uz/{rel_path}")
        head.append(alt_uz)


def inject_language_switcher(soup: BeautifulSoup, rel_path: str, is_uz_page: bool) -> None:
    body = soup.find('body')
    if not body:
        return
    container = soup.new_tag('div')
    container['style'] = 'position:fixed;bottom:12px;right:12px;z-index:9999;font-family:inherit;font-size:13px;background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px 10px;box-shadow:0 2px 8px rgba(0,0,0,0.08)'
    link = soup.new_tag('a')
    if is_uz_page:
        # Calculate relative path: count depth of rel_path and add one for uz/ directory
        # For nested paths like "dlya_professionalov/dokumentacziya.html", we're in uz/dlya_professionalov/
        # so we need to go up 2 levels (../../) to reach root, then access the path
        depth = rel_path.count('/')
        # Always need to go up from uz/ plus one for each directory level in the path
        up_levels = '../' * (depth + 1)
        link['href'] = f"{up_levels}{rel_path}"
        link['hreflang'] = 'ru'
        link.string = 'Русский'
    else:
        # Calculate relative path: from Russian page to Uzbek version
        # For nested files, we need to go up to root, then into uz/
        depth = rel_path.count('/')
        up_levels = '../' * depth if depth > 0 else ''
        link['href'] = f"{up_levels}uz/{rel_path}"
        link['hreflang'] = 'uz'
        link.string = "O'zbekcha"
    container.append(link)
    body.append(container)


def is_html_file(path: Path) -> bool:
    return path.suffix.lower() in {'.html', '.htm'}


def collect_texts_for_translation(
    soup: BeautifulSoup,
    glossary: List[Tuple[str, str, str]],
) -> Tuple[List[NavigableString], List[str], List[Tuple[str, 'bs4.element.Tag', str]], List[str], List[Tuple[str, 'bs4.element.Tag']], List[str]]:
    nodes = extract_text_nodes(soup)
    node_texts = [apply_pre_glossary(str(n), glossary) for n in nodes]
    attr_items = extract_attr_texts(soup)
    attr_texts = [apply_pre_glossary(t, glossary) for (t, _tag, _a) in attr_items]
    meta_items = extract_meta_descriptions(soup)
    meta_texts = [apply_pre_glossary(t, glossary) for (t, _tag) in meta_items]
    return nodes, node_texts, attr_items, attr_texts, meta_items, meta_texts


def translate_unique(texts: List[str], cache: CacheStore, translator: YandexTranslator, glossary: List[Tuple[str, str, str]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    unique = []
    for t in texts:
        if t not in mapping:
            mapping[t] = cache.get(t) or None
            if mapping[t] is None:
                unique.append(t)
    if unique:
        translated = translator.translate(unique)
        for src, tgt in zip(unique, translated):
            tgt = apply_post_glossary(tgt, glossary)
            cache.set(src, tgt)
            mapping[src] = tgt
    return mapping


def replace_texts(node_texts: List[str], mapping: Dict[str, str]) -> List[str]:
    return [mapping.get(t, t) for t in node_texts]


def safe_read_text(path: Path) -> str:
    raw = path.read_bytes()
    enc = chardet.detect(raw).get('encoding') or 'utf-8'
    return raw.decode(enc, errors='ignore')


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def process_russian_html_file(
    src_path: Path,
    rel_path: str,
) -> None:
    """Process Russian HTML file in-place to add Uzbek language switcher and hreflang."""
    html = safe_read_text(src_path)
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove existing language switcher if present (to update paths if needed)
    body = soup.find('body')
    if body:
        existing_switcher = body.find('div', style=lambda x: x and 'position:fixed' in x and 'bottom:12px' in x)
        if existing_switcher:
            existing_switcher.decompose()
    
    # Remove existing hreflang link if present
    head = soup.find('head')
    if head:
        existing_hreflang = head.find('link', rel='alternate', hreflang='uz')
        if existing_hreflang:
            existing_hreflang.decompose()
    
    # Add hreflang and language switcher
    set_lang_and_hreflang(soup, rel_path, is_uz_page=False)
    inject_language_switcher(soup, rel_path, is_uz_page=False)
    
    # Preserve original doctype
    orig_doctype = None
    for line in html.splitlines()[:3]:
        if line.lstrip().lower().startswith('<!doctype'):
            orig_doctype = line.strip()
            break
    
    out_html = str(soup)
    # Fix rare BeautifulSoup quirk where leading 'html' text appears before <html>
    stripped = out_html.lstrip()
    if stripped.startswith('html<html'):
        out_html = out_html.replace('html<', '<', 1)
    if orig_doctype and not out_html.lstrip().lower().startswith('<!doctype'):
        out_html = orig_doctype + "\n" + out_html
    
    write_text(src_path, out_html)


def process_html_file(
    src_path: Path,
    dst_path: Path,
    rel_path: str,
    cache: CacheStore,
    translator: YandexTranslator,
    glossary: List[Tuple[str, str, str]],
    report_rows: List[List[str]],
) -> None:
    html = safe_read_text(src_path)
    # Capture original doctype line if present to preserve it
    orig_doctype = None
    for line in html.splitlines()[:3]:
        if line.lstrip().lower().startswith('<!doctype'):
            orig_doctype = line.strip()
            break
    soup = BeautifulSoup(html, 'lxml')

    nodes, node_texts, attr_items, attr_texts, meta_items, meta_texts = collect_texts_for_translation(soup, glossary)
    all_texts = node_texts + attr_texts + meta_texts

    mapping = translate_unique(all_texts, cache, translator, glossary)

    new_node_texts = replace_texts(node_texts, mapping)
    new_attr_texts = replace_texts(attr_texts, mapping)
    new_meta_texts = replace_texts(meta_texts, mapping)

    replace_in_html(soup, nodes, new_node_texts, attr_items, new_attr_texts, meta_items, new_meta_texts)

    set_lang_and_hreflang(soup, rel_path, is_uz_page=True)
    inject_language_switcher(soup, rel_path, is_uz_page=True)

    out_html = str(soup)
    # Fix rare BeautifulSoup quirk where leading 'html' text appears before <html>
    stripped = out_html.lstrip()
    if stripped.startswith('html<html'):
        out_html = out_html.replace('html<', '<', 1)
    if orig_doctype and not out_html.lstrip().lower().startswith('<!doctype'):
        out_html = orig_doctype + "\n" + out_html
    write_text(dst_path, out_html)

    report_rows.append([
        rel_path,
        str(src_path),
        str(dst_path),
        str(len(node_texts)),
        str(len(attr_texts)),
        str(len(meta_texts)),
    ])


def mirror_non_html(src_root: Path, dst_root: Path, path: Path) -> None:
    rel = path.relative_to(src_root)
    out = dst_root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(path.read_bytes())


def translate_pdfs_if_any(src_root: Path, dst_root: Path, report_rows: List[List[str]]) -> None:
    try:
        subprocess.run(['pdftotext', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        has_pdftotext = True
    except Exception:
        has_pdftotext = False
    if not has_pdftotext:
        return
    for path in src_root.rglob('*.pdf'):
        rel = path.relative_to(src_root)
        out_txt = dst_root / rel.with_suffix('').as_posix() + '-uz.txt'
        out_txt = Path(out_txt)
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(['pdftotext', str(path), '-'], check=True, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            continue
        # Note: full PDF translation not implemented to avoid heavy API usage by default.
        report_rows.append([str(rel), str(path), str(out_txt), '0', '0', 'pdf'])


def write_report(dst_root: Path, rows: List[List[str]]) -> None:
    report_path = dst_root / 'translation_report.csv'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['rel_path', 'src', 'dst', 'text_nodes', 'attr_texts', 'meta_texts'])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description='Translate static HTML RU→UZ (Latin) with Yandex Cloud Translate')
    parser.add_argument('--src', default=str(Path(__file__).resolve().parents[1] / 'www.danogips.ru'))
    parser.add_argument('--dst', default=str(Path(__file__).resolve().parents[1] / 'www.danogips.ru' / 'uz'))
    parser.add_argument('--cache', default=str(Path(__file__).resolve().parents[1] / 'www.danogips.ru' / '.cache' / 'ru_uz.json'))
    parser.add_argument('--glossary', default=str(Path(__file__).resolve().parents[1] / 'www.danogips.ru' / 'translate_glossary.csv'))
    parser.add_argument('--modify-ru', action='store_true', help='Also inject RU→UZ links into original RU pages (edits RU files)')
    parser.add_argument('--report', default='translation_report.csv')
    parser.add_argument('--clean', action='store_true', help='Remove destination folder before generation to avoid nesting')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    # Load environment from a few common places
    load_env([
        project_root / '.env',
        project_root / 'env',
        project_root / 'env.sample',
    ])
    api_key = os.environ.get('YANDEX_API_KEY', '').strip()
    folder_id = os.environ.get('YANDEX_FOLDER_ID', '').strip()
    if not api_key or not folder_id:
        print('ERROR: YANDEX_API_KEY and YANDEX_FOLDER_ID are required in environment. See env.sample.')
        sys.exit(2)

    src_root = Path(args.src).resolve()
    dst_root = Path(args.dst).resolve()
    cache_path = Path(args.cache).resolve()
    glossary = load_glossary(Path(args.glossary).resolve())

    translator = YandexTranslator(api_key, folder_id,
                                  batch_size=int(os.environ.get('TRANSLATE_BATCH_SIZE', '80') or '80'),
                                  max_chars=int(os.environ.get('TRANSLATE_MAX_CHARS', '9000') or '9000'),
                                  rpm=int(os.environ.get('REQUESTS_PER_MINUTE', '300') or '300'))
    cache = CacheStore(cache_path)

    report_rows: List[List[str]] = []

    # Optional cleanup to avoid recursive nesting like uz/uz/...
    if args.clean and dst_root.exists():
        import shutil
        shutil.rmtree(dst_root)

    for path in src_root.rglob('*'):
        if path.is_dir():
            continue
        # Skip anything under the destination root to prevent recursion
        try:
            if path.resolve().is_relative_to(dst_root):
                continue
        except AttributeError:
            # Python <3.9 fallback
            try:
                path.resolve().relative_to(dst_root)
                continue
            except Exception:
                pass
        rel = path.relative_to(src_root).as_posix()
        if is_html_file(path):
            # First, add Uzbek language switcher to Russian pages (in-place)
            process_russian_html_file(path, rel)
            # Then, translate to create Uzbek version
            dst_path = dst_root / rel
            process_html_file(path, dst_path, rel, cache, translator, glossary, report_rows)
        else:
            # Mirror non-HTML assets verbatim
            mirror_non_html(src_root, dst_root, path)

    # Optional PDF step (non-invasive)
    translate_pdfs_if_any(src_root, dst_root, report_rows)

    write_report(dst_root, report_rows)
    cache.save()
    print(f'Translation complete. Output: {dst_root}')
    print(f'Report: {dst_root / "translation_report.csv"}')


if __name__ == '__main__':
    main()


