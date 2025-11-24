import multiprocessing as mp
from pathlib import Path
from bs4 import BeautifulSoup
from configparser import ConfigParser
from mp_workers import writer_process, extract_words_for_color_html


class HighlightExtractor:
    """
    Extract highlighted words from HTML files using multiprocessing.

    This class reads configuration from an INI file, parses the input HTML,
    discovers highlight color classes, and spawns worker processes to extract
    words for each color. A dedicated writer process collects the words from
    a queue and writes them to the configured output file.
    """
    
    def __init__(self, config_path="config.ini"):
        """
        Initialize the extractor with configuration values from an INI file.

        ## Params:
         - config_path: str | Path
          Path to the INI configuration file containing `paths` and `settings`.

        ## Returns:
         - None
        """
        self.config = ConfigParser()
        self.config.read(config_path, encoding='utf-8')

        self.input_path = Path(self.config.get('paths', 'input_path'))
        self.output_path = Path(self.config.get('paths', 'output_path'))
        default_colors_str = self.config.get('settings', 'default_colors')
        self.default_colors = [color.strip() for color in default_colors_str.split(',')]
        self.encoding = self.config.get('settings', 'encoding')

    def parse_html(self):
        """
        Parse the input HTML file into a BeautifulSoup object.

        If the configured input file is not found, a small sample HTML
        document is used as a fallback.

        ## Params:
         - None

        ## Returns:
         - BeautifulSoup: Parsed HTML document.
        """
        try:
            with open(self.input_path, "r", encoding=self.encoding) as file:
                soup = BeautifulSoup(file, "html.parser")
                return soup
        except FileNotFoundError:
            print(f"Input file {self.input_path} not found.")
            exit(1)

    def _list_highlight_colors(self, soup):
        """
        Detect all highlight color classes present in the document.

        If no highlight classes are detected, the default colors from
        configuration are used instead.

        ## Params:
         - soup: BeautifulSoup
          Parsed HTML document to scan for `nrmark` tags and their classes.

        ## Returns:
         - list[str]: Sorted list of highlight class names (e.g., 'highlight-red').
        """
        colors = set()
        for tag in soup.find_all("nrmark"):
            classes = tag.get("class") or []
            for c in classes:
                if c.startswith("highlight-"):
                    colors.add(c)
        if not colors:
            colors = set(self.default_colors)
        return sorted(colors)

    def _extract_with_processes(self, soup, colors):
        """
        Extract highlighted words using separate processes per color.

        Spawns a writer process to persist words to the configured output file,
        and multiple worker processes that parse the HTML and push words to a
        shared queue.

        ## Params:
         - soup: BeautifulSoup
          Parsed HTML document.
         - colors: list[str]
          Highlight class names to process (e.g., 'highlight-yellow').

        ## Returns:
         - None
        """
        html = str(soup)

        q = mp.Queue()

        writer = mp.Process(target=writer_process, args=(q, self.output_path, self.encoding))
        writer.start()

        workers = []
        for color in colors:
            p = mp.Process(target=extract_words_for_color_html, args=(q, html, color))
            p.start()
            workers.append(p)

        # Wait for all workers to finish
        for p in workers:
            p.join()

        # Signal writer to stop
        q.put(None)
        writer.join()
        
    def extract_highlights(self, soup, colors=None):
        """
        Extract highlighted words from the given HTML document.

        If no `colors` are provided, they are detected from the document or
        fall back to defaults from configuration.

        Params:
         - soup: BeautifulSoup
          Parsed HTML document.
        ## Params:
         - colors: list[str] | None
          Optional list of highlight classes to process.

        ## Returns:
         - None
        """
        if colors is None:
            colors = self._list_highlight_colors(soup)

        self._extract_with_processes(soup, colors)

    def run(self):
        """
        Run the full extraction pipeline: parse HTML, detect colors, and
        extract highlighted words via multiprocessing.

        ## Params:
         - None

        ## Returns:
         - None
        """
        soup = self.parse_html()
        self.extract_highlights(soup)
        

if __name__ == "__main__":
    extractor = HighlightExtractor("config.ini")
    words = extractor.run()
    print("Extraction completed. Check the output file.")