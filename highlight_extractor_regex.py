# main.py or highlight_extractor.py
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os

from configparser import ConfigParser
from lxml import html
from mp_workers import extract_words_for_color_html
import re


@dataclass
class HighlightExtractor:
    """
    Extract highlighted words from HTML files using multiprocessing.
    Uses ultra-fast pure-regex workers via ProcessPoolExecutor.
    """

    config_path: str | Path = "config.ini"

    config: ConfigParser = field(init=False, repr=False)
    chapter_num: int = field(init=False)
    input_path: Path = field(init=False)
    output_path: Path = field(init=False)
    default_colors: List[str] = field(init=False)
    encoding: str = field(init=False)

    def __post_init__(self) -> None:
        self.config = ConfigParser()
        self.config.read(self.config_path, encoding="utf-8")

        self.chapter_num = self.config.getint("paths", "chapter_num")
        chapter_dir = Path(f"book_chapters/chapter{self.chapter_num}")

        self.input_path = chapter_dir / "input.htm"
        self.output_path = chapter_dir / "words.txt"

        self.default_colors = [
            c.strip() for c in self.config.get("settings", "default_colors", fallback="").split(",")
            if c.strip()
        ]
        self.encoding = self.config.get("settings", "encoding", fallback="utf-8")

    def _read_html_as_string(self) -> str:
        """Read and clean HTML once using lxml (safe + fast)"""
        with open(self.input_path, "r", encoding=self.encoding) as f:
            tree = html.parse(f).getroot()
            return html.tostring(tree, encoding="unicode", method="html")

    def _detect_colors(self, html_str: str) -> List[str]:
        """Quick regex scan to find which highlight-* classes actually exist"""
        colors = {
            cls for match in re.finditer(
                r'<nrmark[^>]+class=["\']([^"\']*)["\']', html_str, re.IGNORECASE
            )
            for cls in match.group(1).split()
            if cls.startswith("highlight-")
        }
        return sorted(colors) or self.default_colors.copy()

    def extract_highlights(self, html_str: str, colors: Optional[List[str]] = None) -> None:
        if colors is None:
            colors = self._detect_colors(html_str)

        max_workers = min(len(colors) or 1, os.cpu_count() or 4)

        with open(self.output_path, "w", encoding=self.encoding) as f:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(extract_words_for_color_html, None, html_str, color)
                    for color in colors
                ]

                for future in as_completed(futures):
                    for word in future.result():
                        f.write(word + "\n")

    def run(self) -> None:
        print(f"Processing chapter {self.chapter_num}...")
        html_str = self._read_html_as_string()

        colors = self._detect_colors(html_str)
        print(f"Detected colors: {colors or '(using defaults)'}")

        self.extract_highlights(html_str, colors)
        print(f"Done! → {self.output_path.resolve()}")


if __name__ == "__main__":
    extractor = HighlightExtractor("config.ini")
    extractor.run()
