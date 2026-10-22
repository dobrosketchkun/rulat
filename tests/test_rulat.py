"""Transliteration cases from tests/cases.json, shared with test_userscript.js.

python -m unittest discover tests
"""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rulat import transliterate, transliterate_parts

with open(os.path.join(ROOT, 'tests', 'cases.json'), encoding='utf-8') as f:
    CASES = json.load(f)


def run(source):
    # A list is the text of one paragraph split by tags
    if isinstance(source, list):
        return transliterate_parts(source)
    return transliterate(source)


class TestCases(unittest.TestCase):
    def check_category(self, category):
        for source, expected in CASES[category]:
            with self.subTest(source=source):
                self.assertEqual(run(source), expected)

    def test_idempotent(self):
        # Romanized text has no Russian letters left, so it must not change again
        for category, cases in CASES.items():
            for _, expected in cases:
                with self.subTest(category=category, text=expected):
                    self.assertEqual(run(expected), expected)

    def test_split_by_whitespace(self):
        # Splitting a paragraph between words must not change the result
        for category, cases in CASES.items():
            for source, expected in cases:
                if isinstance(source, list):
                    continue
                parts = re.split(r'(\s+)', source)
                with self.subTest(category=category, source=source):
                    self.assertEqual(''.join(transliterate_parts(parts)), expected)


for _category in CASES:
    setattr(TestCases, 'test_' + _category,
            lambda self, category=_category: self.check_category(category))


if __name__ == '__main__':
    unittest.main()
