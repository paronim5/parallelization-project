
from __future__ import annotations

from typing import List
from lxml import html


def extract_words_for_color_lxml(_dummy_queue, html_text: str, color: str) -> List[str]:
    """
    Extract highlighted words using lxml + XPath.
    Used with ProcessPoolExecutor — returns list instead of using queue.
    
    Params:
        _dummy_queue: None (kept for compatibility, ignored)
        html_text: Full HTML document as string
        color: Highlight class like "highlight-yellow"
    
    Returns:
        List of extracted words (one per highlighted <nrmark>)
    """
    tree = html.fromstring(html_text)
    tags = tree.xpath(f"//nrmark[contains(concat(' ', @class, ' '), ' {color} ')]")
    
    words = []
    for tag in tags:
        text = tag.text_content().strip()
        if text:
            words.append(text)
    
    return words

import re

_RE_NR_MARK = re.compile(
    r'<nrmark\b[^>]*\bclass=["\']([^"\']*)["\'][^>]*>(.*?)</nrmark>',
    re.DOTALL | re.IGNORECASE
)
_RE_STRIP_TAGS = re.compile(r'<[^>]+>')


def extract_words_for_color_regex(_dummy_queue, html_text: str, color: str) -> List[str]:
    """
    Ultra-fast pure-regex version.
    Recommended for maximum speed on well-formed ebook HTML.
    """
    words = []
    pattern = rf'\b{re.escape(color)}\b'

    for class_attr, inner_html in _RE_NR_MARK.findall(html_text):
        if re.search(pattern, class_attr):
            clean_text = _RE_STRIP_TAGS.sub('', inner_html).strip()
            if clean_text:
                words.append(clean_text)

    return words

extract_words_for_color_html = extract_words_for_color_lxml
