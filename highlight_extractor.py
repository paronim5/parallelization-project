from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from lxml import html
from configparser import ConfigParser
from mp_workers import extract_words_for_color_html


@dataclass
class HighlightExtractor:
    """
    Extract highlighted words from HTML files using multiprocessing.

    This class reads configuration from an INI file, parses the input HTML,
    discovers highlight color classes, and spawns worker processes to extract
    words for each color. Results are collected and written to file in the
    main process using the modern concurrent.futures API.
    """

    config_path: str | Path = "config.ini"
    """Path to the INI configuration file containing `paths` and `settings`."""
    config: ConfigParser = field(init=False, repr=False)
    chapter_num: int = field(init=False)
    input_path: Path = field(init=False)
    output_path: Path = field(init=False)
    default_colors: List[str] = field(init=False)
    encoding: str = field(init=False)

    def __post_init__(self) -> None:
        """
        Initialize the extractor with configuration values from an INI file.

        ## Params:
            - config_path: str | Path
                Path to the INI configuration file (passed to the dataclass).

        ## Returns:
            - None
        """
        self.config = ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")

        self.chapter_num = self.config.getint("paths", "chapter_num")

        chapter_dir = Path(f"book_chapters/chapter{self.chapter_num}")
        self.input_path = chapter_dir / "input.htm"
        self.output_path = chapter_dir / "words.txt"

        default_colors_str = self.config.get("settings", "default_colors")
        self.default_colors = [
            color.strip() for color in default_colors_str.split(",") if color.strip()
        ]

        self.encoding = self.config.get("settings", "encoding")

    def parse_html(self) -> html.HtmlElement:
        """
        Parse the input HTML file into an lxml HTML element tree.
        If the configured input file is not found, raises FileNotFoundError.

        ## Params:
            - None

        ## Returns:
            - lxml.html.HtmlElement: Parsed HTML document root.
        """
        try:
            with open(self.input_path, "r", encoding=self.encoding) as file:
                tree = html.parse(file).getroot()
                return tree
        except FileNotFoundError:
            print(f"Input file {self.input_path} not found.")
            raise

    def _list_highlight_colors(self, tree: html.HtmlElement) -> List[str]:
        """
        Detect all highlight color classes present in the document.
        If no highlight classes are detected, the default colors from
        configuration are used instead.

        ## Params:
            - tree: lxml.html.HtmlElement
                Parsed HTML document root to scan for `nrmark` tags and their classes.

        ## Returns:
            - list[str]: Sorted list of highlight class names (e.g., 'highlight-red').
        """
        colors = set()
        for tag in tree.xpath("//nrmark[@class]"):
            class_attr = tag.get("class")
            if class_attr:
                for c in class_attr.split():
                    if c.startswith("highlight-"):
                        colors.add(c)

        if not colors:
            colors = set(self.default_colors)

        return sorted(colors)

    def extract_highlights(self, tree: html.HtmlElement, colors: Optional[List[str]] = None) -> None:
        """
        Extract highlighted words from the given HTML document using ProcessPoolExecutor.
        If no `colors` are provided, they are detected from the document or
        fall back to defaults from configuration.

        ## Params:
            - tree: lxml.html.HtmlElement
                Parsed HTML document root.
            - colors: list[str] | None
                Optional list of highlight classes to process.

        ## Returns:
            - None
        """
        if colors is None:
            colors = self._list_highlight_colors(tree)

        html_str = html.tostring(tree, encoding="unicode")

        max_workers = min(len(colors), (cpu_count := __import__("os").cpu_count()) or 4)

        with open(self.output_path, "w", encoding=self.encoding) as outfile:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_color = {
                    executor.submit(extract_words_for_color_html, None, html_str, color): color
                    for color in colors
                }

                for future in as_completed(future_to_color):
                    words = future.result()
                    for word in words:
                        outfile.write(word + "\n")

    def run(self) -> None:
        """
        Run the full extraction pipeline: parse HTML, detect colors, and
        extract highlighted words via multiprocessing.

        ## Params:
            - None

        ## Returns:
            - None
        """
        tree = self.parse_html()
        self.extract_highlights(tree)
        print(f"Extraction completed → {self.output_path}")


if __name__ == "__main__":
    extractor = HighlightExtractor("config.ini")
    extractor.run()