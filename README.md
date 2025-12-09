# Parallel Highlight Words Extractor from Books

A Python tool that extracts highlighted words from HTML book chapters using multiprocessing and regex for ultra-fast performance.

## What It Does

- Processes HTML files from `book_chapters/chapter{N}/input.htm`
- Scans for `<nrmark class="highlight-*">...</nrmark>` tags using regex
- Extracts the text inside each highlighted span
- Groups words by highlight color (e.g., `highlight-yellow`, `highlight-red`)
- Writes all extracted words to `book_chapters/chapter{N}/words.txt` (one word per line)
- Uses **parallel processing** — one worker per color — for faster extraction
- Supports multiple extraction methods: lxml XPath or pure regex

## Requirements

- Python 3.7+
- Packages: `lxml`

Install dependencies:
```bash
pip install lxml
```

## Configuration

Edit `config.ini` to set:

```ini
[paths]
chapter_num = 16            # Chapter number to process

[settings]
default_colors = highlight-yellow,highlight-red,highlight-green,highlight-blue,highlight-purple
encoding = utf-8
```

The tool automatically uses:
- Input: `book_chapters/chapter{chapter_num}/input.htm`
- Output: `book_chapters/chapter{chapter_num}/words.txt`

If no highlight classes are found in the HTML, the tool falls back to the `default_colors`.

## How to Run

```bash
python highlight_extractor_regex.py
```

The script reads `config.ini` by default and processes the specified chapter.

## Example Input

```html
<nrmark class="highlight-yellow">parallel</nrmark>
<nrmark class="highlight-red">processing</nrmark>
<nrmark class="highlight-yellow">multiprocessing</nrmark>
```

**Output (`words.txt`):**
```
parallel
processing
multiprocessing
```

## License

This project is licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.

---
