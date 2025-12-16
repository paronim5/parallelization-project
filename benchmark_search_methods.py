#!/usr/bin/env python3
"""
Benchmark tests to compare search method performance for highlight extraction.

This script benchmarks two different approaches for extracting highlighted words:
1. lxml-based XPath search (extract_words_for_color_lxml)
2. Pure regex-based search (extract_words_for_color_regex)

Usage: python benchmark_search_methods.py
"""

import time
import statistics
from typing import List, Callable
from mp_workers import extract_words_for_color_lxml, extract_words_for_color_regex, extract_words_for_color_bs4


def generate_test_html(num_highlights: int = 1000, num_colors: int = 5) -> str:
    """Generate test HTML with various highlighted words."""
    colors = ['highlight-yellow', 'highlight-red', 'highlight-green',
              'highlight-blue', 'highlight-purple'][:num_colors]

    html_parts = ['<html><body>']

    for i in range(num_highlights):
        color = colors[i % len(colors)]
        word = f"word{i}"
        html_parts.append(f'<nrmark class="{color}">{word}</nrmark>')

        # Add some regular text between highlights
        if i % 10 == 0:
            html_parts.append(f'<p>This is some regular text paragraph {i//10}.</p>')

    html_parts.append('</body></html>')
    return ''.join(html_parts)


def benchmark_search_method(
    method: Callable[[None, str, str], List[str]],
    html: str,
    color: str,
    iterations: int = 10
) -> dict:
    """Benchmark a single search method."""
    times = []

    for _ in range(iterations):
        start_time = time.perf_counter()
        result = method(None, html, color)
        end_time = time.perf_counter()

        times.append(end_time - start_time)

        # Verify results are consistent
        if _ == 0:
            first_result = result
        else:
            assert len(result) == len(first_result), "Inconsistent results between runs"

    return {
        'method_name': method.__name__,
        'avg_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'iterations': iterations,
        'result_count': len(first_result)
    }


def run_benchmarks():
    """Run comprehensive benchmarks comparing both search methods."""
    print("Benchmark Results")
    print()

    # Test configurations
    test_configs = [
        {'highlights': 100, 'colors': 2},
        {'highlights': 500, 'colors': 3},
        {'highlights': 1000, 'colors': 5},
        {'highlights': 2000, 'colors': 5},
    ]

    methods = [
        ('lxml_xpath', extract_words_for_color_lxml),
        ('regex', extract_words_for_color_regex),
        ('bs4', extract_words_for_color_bs4),
    ]

    for config in test_configs:
        highlights = config['highlights']
        colors = config['colors']

        html = generate_test_html(highlights, colors)

        # Collect all times for averaging
        lxml_times = []
        regex_times = []
        bs4_times = []

        for color_idx in range(colors):
            color = f'highlight-{["yellow", "red", "green", "blue", "purple"][color_idx]}'

            for method_name, method in methods:
                result = benchmark_search_method(method, html, color, iterations=5)

                if 'lxml' in result['method_name']:
                    lxml_times.append(result['avg_time'])
                elif 'regex' in result['method_name']:
                    regex_times.append(result['avg_time'])
                else:  # bs4
                    bs4_times.append(result['avg_time'])

        # Calculate averages
        avg_lxml = statistics.mean(lxml_times)
        avg_regex = statistics.mean(regex_times)
        avg_bs4 = statistics.mean(bs4_times)

        print(f"**{highlights} highlights, {colors} colors:**")
        print(f"lxml: {avg_lxml:.4f}s, regex: {avg_regex:.4f}s, bs4: {avg_bs4:.4f}s")

        # Find fastest method
        times = [('lxml', avg_lxml), ('regex', avg_regex), ('bs4', avg_bs4)]
        fastest = min(times, key=lambda x: x[1])
        slowest = max(times, key=lambda x: x[1])

        print(f"{fastest[0]} is fastest ({fastest[0]}: {fastest[1]:.4f}s, {slowest[0]}: {slowest[1]:.4f}s)")
        print()


def benchmark_edge_cases():
    """Benchmark edge cases and special scenarios."""
    print("\n" + "=" * 60)
    print("Benchmarking Edge Cases")
    print("=" * 60)

    edge_cases = [
        ("Empty HTML", '<html><body></body></html>', 'highlight-yellow'),
        ("No highlights", '<html><body><p>Just regular text</p></body></html>', 'highlight-yellow'),
        ("Single highlight", '<html><body><nrmark class="highlight-yellow">word</nrmark></body></html>', 'highlight-yellow'),
        ("Multiple classes", '<html><body><nrmark class="highlight-yellow other-class">word</nrmark></body></html>', 'highlight-yellow'),
        ("Nested tags", '<html><body><nrmark class="highlight-yellow"><em>word</em></nrmark></body></html>', 'highlight-yellow'),
    ]

    methods = [
        ('lxml_xpath', extract_words_for_color_lxml),
        ('regex', extract_words_for_color_regex),
    ]

    for case_name, html, color in edge_cases:
        print(f"\n{case_name}:")
        print("-" * 30)

        for method_name, method in methods:
            result = benchmark_search_method(method, html, color, iterations=3)
            print(f"    {method_name}: {result['avg_time']:.6f}s "
                  f"(found {result['result_count']} words)")


if __name__ == "__main__":
    run_benchmarks()
