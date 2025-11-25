# Parallel Highlight Words Extractor From book

A Python tool that extracts highlighted words from HTML files using multiprocessing for better performance.

## What It Does

- Scans an HTML file for `<nrmark class="highlight-*">...</nrmark>` tags  
- Extracts the text inside each highlighted span  
- Groups words by highlight color (e.g., `highlight-yellow`, `highlight-red`)  
- Writes all extracted words to a text file (one word per line)  
- Uses **parallel processing** — one worker per color — for faster extraction

## Requirements

- Python 3.7+
- Packages: `beautifulsoup4`

Install dependencies:
```bash
pip install beautifulsoup4
```

## Configuration

Edit `config.ini` to set:

```ini
[paths]
input_path = input.htm      # Your HTML file
output_path = words.txt     # Output word list

[settings]
default_colors = highlight-yellow,highlight-red,highlight-green,highlight-blue,highlight-purple
encoding = utf-8
```

If no highlight classes are found in the HTML, the tool falls back to the `default_colors`.

## How to Run

```bash
python highlight_extractor.py
```

The script reads `config.ini` by default and outputs results to the file specified in `output_path`.

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

