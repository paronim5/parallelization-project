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

def extract_words_for_color_html(q, html_text, color):
    """
    Parse HTML text and enqueue words for a specific highlight color.

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