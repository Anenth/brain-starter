#!/usr/bin/env python3
"""Fixtures for `bin/brain top3`. Run: python3 tests/test_top3.py

Builds a throwaway library under a temp dir (BRAIN_ROOT). Three weekdays of
briefs: a Top 3 reviewed done/open, a Top 3 never reviewed, and one task that
sits three days undone and must be flagged stuck. The clock is pinned with
BRAIN_TODAY so the fixture days fall after the rule's start date.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BRAIN = REPO / "bin" / "brain"


TODAY = date(2026, 10, 9)  # a Friday after the rule started; the clock is pinned here


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1", BRAIN_TODAY=TODAY.isoformat())
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


def weekdays_back(n: int) -> list[date]:
    """The last n weekdays before today, oldest first. Never today."""
    out, d = [], TODAY - timedelta(days=1)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


class Top3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        (self.tmp / "memory" / "daily").mkdir(parents=True)
        shutil.copytree(REPO / "templates", self.tmp / "templates")
        self.days = weekdays_back(3)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, d: date, brief: str, log: str = "") -> None:
        (self.tmp / "memory" / "daily" / f"{d.isoformat()}.md").write_text(
            f"---\ntype: daily\ntitle: {d}\ndate: {d}\n---\n\n# {d}\n\n## Brief\n\n{brief}\n\n## Log\n\n{log}\n", encoding="utf-8")

    def test_week_is_counted_by_code(self):
        d1, d2, d3 = self.days
        top3 = ("### Top 3\n"
                "1. **Acme single QR.** Confirm tested. <!-- hespia:AAA -->\n"
                "2. **Globex fallback.** Name an owner. <!-- hespia:BBB -->\n"
                "3. **Initech legal.** Pick one. <!-- hespia:CCC -->\n\n### Needs you\n- **Other** thing. <!-- gmail:x -->")
        review = ("### Top 3 review\n"
                  "- done  Acme single QR. <!-- hespia:AAA -->\n"
                  "- open  Globex fallback, day 1. <!-- hespia:BBB -->\n"
                  "- open  Initech legal. <!-- hespia:CCC -->\n<!-- hespia-msg:M1 -->")
        self.write(d1, top3, review)
        top3_2 = top3.replace("**Acme single QR.** Confirm tested. <!-- hespia:AAA -->", "**Hooli.** Send it. <!-- hespia:DDD -->")
        self.write(d2, top3_2, "")  # never reviewed
        review_3 = ("### Top 3 review\n"
                    "- open  Hooli. <!-- hespia:DDD -->\n"
                    "- open  Globex fallback, day 3. <!-- hespia:BBB -->\n"
                    "- not found  Initech legal. <!-- hespia:CCC -->")
        self.write(d3, top3_2, review_3)

        r = run(self.tmp, "top3", "--days", "10")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("1 of 9 Top 3 slot(s) done", out)
        self.assertIn("4 task(s)", out)
        self.assertIn(f"{d2} {d2.strftime('%a')}: Top 3 never reviewed", out)
        self.assertIn("3 day(s)  still open         Globex fallback  hespia:BBB  stuck", out)
        self.assertIn("1 day(s)  done " + d1.isoformat(), out)
        self.assertIn("not found on their list Initech legal", out)
        self.assertIn("2 stuck 3+ days", out)

    def test_brief_without_top3_is_a_gap(self):
        d1 = self.days[-1]
        self.write(d1, "### Needs you\n- **Thing.** <!-- gmail:y -->")
        r = run(self.tmp, "top3", "--days", "10")
        self.assertIn("brief with no Top 3", r.stdout)
        self.assertIn("0 of 0 Top 3 slot(s) done", r.stdout)

    def test_four_picks_is_a_gap(self):
        d1 = self.days[-1]
        self.write(d1, "### Top 3\n" + "".join(f"{i}. **T{i}.** x <!-- hespia:T{i} -->\n" for i in range(1, 5)))
        r = run(self.tmp, "top3", "--days", "10")
        self.assertIn("4 in the Top 3, not 3", r.stdout)


if __name__ == "__main__":
    unittest.main()
