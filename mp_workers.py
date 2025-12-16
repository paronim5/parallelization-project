
from __future__ import annotations

from typing import List
from lxml import html
from bs4 import BeautifulSoup


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


def extract_words_for_color_bs4(_dummy_queue, html_text: str, color: str) -> List[str]:
    """
    Extract highlighted words using BeautifulSoup.
    Used with ProcessPoolExecutor — returns list instead of using queue.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    tags = soup.find_all("nrmark", class_=color)

    words = []
    for tag in tags:
        text = tag.text.strip()
        if text:
            words.append(text)

    return words

extract_words_for_color_html = extract_words_for_color_lxml


from bs4 import BeautifulSoup

"""
Multiprocessing worker functions used by HighlightExtractor.

These functions are defined at module scope so they can be pickled and
imported correctly on Windows when using the `spawn` start method.
"""

def writer_process(q, path, encoding):
    """
    Consume words from a queue and write them to a file.

    Params:
    - q: multiprocessing.Queue
      Queue supplying strings; terminates when receiving `None`.
    - path: str | Path
      Output file path to write one word per line.
    - encoding: str
      Text encoding to use when opening the file.

    Returns:
    - None
    """
    with open(path, "w", encoding=encoding) as f:
        while True:
            item = q.get()
            if item is None:
                break
            f.write(item + "\n")

def extract_words_for_color_html_queue(q, html_text, color):
    """
    Parse HTML text and enqueue words for a specific highlight color.
    Used with manual multiprocessing.Queue approach.

    Params:
    - q: multiprocessing.Queue
      Queue to receive extracted word strings.
    - html_text: str
      HTML document as a string to parse with BeautifulSoup.
    - color: str
      Highlight class name to match (e.g., 'highlight-yellow').

    Returns:
    - None
    """
    local_soup = BeautifulSoup(html_text, "html.parser")
    tags = local_soup.find_all("nrmark", class_=color)
    for t in tags:
        text = t.text.strip()
        if text:
            q.put(text)
