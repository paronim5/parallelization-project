from __future__ import annotations

import multiprocessing as mp
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from lxml import html
from configparser import ConfigParser
from mp_workers import writer_process, extract_words_for_color_html


@dataclass
class HighlightExtractor:
    """
    Extract highlighted words from HTML files using multiprocessing.

    This class reads configuration from an INI file, parses the input HTML,
    discovers highlight color classes, and spawns worker processes to extract
    words for each color. A dedicated writer process collects the words from
    a queue and writes them to the configured output file.
    """

    config_path: str | Path = "config.ini"
    """Path to the INI configuration file containing `paths` and `settings`."""

    # These will be filled in __post_init__
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

    def _extract_with_processes(self, tree: html.HtmlElement, colors: List[str]) -> None:
        """
        Extract highlighted words using separate processes per color.
        Spawns a writer process to persist words to the configured output file,
        and multiple worker processes that parse the HTML and push words to a
        shared queue.

        ## Params:
            - tree: lxml.html.HtmlElement
                Parsed HTML document root.
            - colors: list[str]
                Highlight class names to process (e.g., 'highlight-yellow').

        ## Returns:
            - None
        """
        html_str = html.tostring(tree, encoding="unicode")
        q: mp.Queue = mp.Queue(maxsize=1000)

        writer = mp.Process(
            target=writer_process,
            args=(q, self.output_path, self.encoding),
            daemon=True,
        )
        writer.start()

        workers = []
        for color in colors:
            p = mp.Process(
                target=extract_words_for_color_html,
                args=(q, html_str, color),
                daemon=True,
            )
            p.start()
            workers.append(p)

        for p in workers:
            p.join()

        q.put(None)        # Signal end of data
        writer.join()

    def extract_highlights(self, tree: html.HtmlElement, colors: Optional[List[str]] = None) -> None:
        """
        Extract highlighted words from the given HTML document.
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
        self._extract_with_processes(tree, colors)

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


if __name__ == "__main__":
    extractor = HighlightExtractor("config.ini")
    extractor.run()
    print("Extraction completed. Check the output file.")