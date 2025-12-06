import unittest
import tempfile
import os
from pathlib import Path
import multiprocessing
from configparser import ConfigParser
from highlight_extractor import HighlightExtractor, writer_process, extract_words_for_color_html


class TestHighlightExtractor(unittest.TestCase):

    def setUp(self):
        if multiprocessing.get_start_method(allow_none=True) != "spawn":
            multiprocessing.set_start_method("spawn", force=True)
        # Create temporary config, input, and output paths
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_config.ini"
        self.input_path = Path(self.temp_dir.name) / "input.htm"
        self.output_path = Path(self.temp_dir.name) / "output.txt"

        # Write minimal config
        config = ConfigParser()
        config["paths"] = {
            "input_path": str(self.input_path),
            "output_path": str(self.output_path)
        }
        config["settings"] = {
            "default_colors": "highlight-yellow, highlight-blue",
            "encoding": "utf-8"
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            config.write(f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_loads_config_correctly(self):
        extractor = HighlightExtractor(self.config_path)
        self.assertEqual(extractor.input_path, self.input_path)
        self.assertEqual(extractor.output_path, self.output_path)
        self.assertEqual(set(extractor.default_colors), {"highlight-yellow", "highlight-blue"})
        self.assertEqual(extractor.encoding, "utf-8")

    def test_parse_html_raises_exit_on_missing_file(self):
        # Ensure input file does NOT exist
        if self.input_path.exists():
            os.remove(self.input_path)

        extractor = HighlightExtractor(self.config_path)
        with self.assertRaises(FileNotFoundError):
            extractor.parse_html()

    def test_parse_html_reads_file_successfully(self):
        sample_html = '<html><body><nrmark class="highlight-red">word</nrmark></body></html>'
        self.input_path.write_text(sample_html, encoding="utf-8")

        extractor = HighlightExtractor(self.config_path)
        tree = extractor.parse_html()
        self.assertIn("word", tree.text_content())

    def test_list_highlight_colors_detects_from_tree(self):
        html_str = '''
        <nrmark class="highlight-green">a</nrmark>
        <nrmark class="highlight-red">b</nrmark>
        <nrmark class="other highlight-blue">c</nrmark>
        '''
        tree = html.fromstring(html_str)

        extractor = HighlightExtractor(self.config_path)
        colors = extractor._list_highlight_colors(tree)
        # Should find all highlight-* classes, even among others
        self.assertEqual(set(colors), {"highlight-green", "highlight-red", "highlight-blue"})

    def test_list_highlight_colors_uses_defaults_if_none_found(self):
        html_str = '<div>no highlights</div>'
        tree = html.fromstring(html_str)

        extractor = HighlightExtractor(self.config_path)
        colors = extractor._list_highlight_colors(tree)
        self.assertEqual(set(colors), {"highlight-yellow", "highlight-blue"})

    def test_extract_words_for_color_html_function(self):
        q = multiprocessing.Queue()
        html = '''
        <nrmark class="highlight-red">apple</nrmark>
        <nrmark class="highlight-blue">banana</nrmark>
        <nrmark class="highlight-red"> cherry </nrmark>
        <nrmark class="highlight-red"></nrmark>  <!-- empty -->
        '''
        # Run function
        extract_words_for_color_html(q, html, "highlight-red")
        q.put(None)  # sentinel for reading

        results = []
        while True:
            item = q.get()
            if item is None:
                break
            results.append(item)

        self.assertEqual(set(results), {"apple", "cherry"})

    def test_writer_process_writes_to_file(self):
        test_words = ["hello", "world", "test"]
        q = multiprocessing.Queue()
        output_file = self.output_path

        # Put words + sentinel
        for word in test_words:
            q.put(word)
        q.put(None)

        writer_process(q, output_file, "utf-8")

        # Read back
        content = output_file.read_text(encoding="utf-8")
        lines = [line.strip() for line in content.splitlines()]
        self.assertEqual(set(lines), set(test_words))

    def test_full_integration_with_multiprocessing(self):
        html = '''
        <html>
        <body>
            <nrmark class="highlight-yellow">sun</nrmark>
            <nrmark class="highlight-blue">sky</nrmark>
            <nrmark class="highlight-yellow">light</nrmark>
        </body>
        </html>
        '''
        self.input_path.write_text(html, encoding="utf-8")

        extractor = HighlightExtractor(self.config_path)
        extractor.run()

        # Check output file
        self.assertTrue(self.output_path.exists())
        content = self.output_path.read_text(encoding="utf-8")
        words = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertEqual(set(words), {"sun", "sky", "light"})

    def test_empty_highlights_produces_empty_output(self):
        html = '<div>no marks</div>'
        self.input_path.write_text(html, encoding="utf-8")

        extractor = HighlightExtractor(self.config_path)
        extractor.run()

        content = self.output_path.read_text(encoding="utf-8")
        self.assertEqual(content.strip(), "")


# Needed for Windows multiprocessing compatibility in tests
if __name__ == "__main__":
    unittest.main()
