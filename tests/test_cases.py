#!/usr/bin/env python3
"""Offline checks for tests/cases/. Run: python3 tests/test_cases.py

No model calls. Every case parses, its rule anchor is still in the repo, its
regexes compile, and the code checks fail the real bad output quoted in the
case's Fail example. A rule that moves breaks here first, not in a paid run.
"""

import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_cases  # noqa: E402


def fail_example(case: dict) -> str:
    """The quoted output under 'Example, FAIL' in the judge section."""
    m = re.search(r'Example, FAIL[^\n]*\n"(.+?)"', case["judge"], re.S)
    return m.group(1).replace("\n", " ") if m else ""


class CaseFiles(unittest.TestCase):
    def cases(self):
        files = sorted(p for p in run_cases.CASES.glob("*.md") if p.name != "README.md")
        self.assertTrue(files, "no cases")
        return [run_cases.parse_case(p) for p in files]

    def test_every_case_is_whole(self):
        for c in self.cases():
            with self.subTest(c["name"]):
                self.assertTrue(c["task"] and c["input"] and c["judge"])
                self.assertTrue(c["must"] or c["must_not"], "needs at least one code check")
                self.assertTrue(run_cases.rule_text(c["meta"]))
                for rx in c["must"] + c["must_not"]:
                    re.compile(rx)

    def test_code_checks_catch_the_real_mistake(self):
        for c in self.cases():
            with self.subTest(c["name"]):
                bad = fail_example(c)
                self.assertTrue(bad, "the judge section needs an 'Example, FAIL' with the real output")
                self.assertTrue(run_cases.check(c, bad), "code checks pass the output that was wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
