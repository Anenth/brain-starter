#!/usr/bin/env python3
"""Fixtures for `bin/brain sample`. Run: python3 tests/test_sample.py

A throwaway library with briefs, log blocks, a meeting and a decision. Checks that
every kind gets a turn, the same month gives the same picks, the sheet is never
overwritten, and the owner's notes come back out tied to their sample.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BRAIN = REPO / "bin" / "brain"
TODAY = "2026-09-28"


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1", BRAIN_TODAY=TODAY)
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


def daily(day: str) -> str:
    return (f"---\ntype: daily\ntitle: {day}\ndate: {day}\n---\n\n# {day}\n\n## Brief\n\n"
            "### Decide today (2)\n- **Globex fallback.** Name an owner.\n- **Acme QR.** Confirm tested.\n- **Initech.** Legal.\n\n"
            "### FYI (1)\n- one line\n\n"
            "## Log\n\n"
            "### Evening processing\n- Closed 2 from Sent.\n- Standup filed.\n- Top 3 reviewed.\n"
            "<!-- ran: evening 2026-09-20T19:30:00+05:30 ok -->\n\n"
            "### Something else\n- not a routine\n- still not\n- nope\n")


class SampleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        m = self.tmp / "memory"
        for d in ("daily", "meetings", "decisions", "inbox"):
            (m / d).mkdir(parents=True)
        shutil.copytree(REPO / "templates", self.tmp / "templates")
        for day in ("2026-09-20", "2026-09-21", "2026-09-22", "2026-08-01"):
            (m / "daily" / f"{day}.md").write_text(daily(day), encoding="utf-8")
        (m / "meetings" / "2026-09-21-acme.md").write_text(
            "---\ntype: meeting\ntitle: Acme\ndate: 2026-09-21\n---\n\n# Acme\n\n## Summary\n\nWe met.\nThey want dates.\nWe owe a deck.\n",
            encoding="utf-8")
        (m / "decisions" / "2026-09-22-pricing.md").write_text(
            "---\ntype: decision\ntitle: Pricing\ndate: 2026-09-22\n---\n\n# Pricing\n\nTwo layers.\nBecause of X.\nRevisit in Q1.\n",
            encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_every_kind_gets_a_turn(self):
        out = run(self.tmp, "sample", "-n", "6").stdout
        for kind in ("brief", "evening run", "meeting note", "decision"):
            self.assertIn(kind, out)
        self.assertNotIn("Something else", out)   # not a routine's output
        self.assertNotIn("FYI", out)              # too short to judge
        self.assertNotIn("2026-08-01", out)       # outside the window

    def test_same_month_same_picks(self):
        a = run(self.tmp, "sample", "-n", "4", "--month", "2026-09").stdout
        b = run(self.tmp, "sample", "-n", "4", "--month", "2026-09").stdout
        self.assertEqual(a, b)

    def test_sheet_is_written_once_and_notes_come_back(self):
        r = run(self.tmp, "sample", "-n", "5", "--write")
        self.assertEqual(r.returncode, 0, r.stderr)
        sheet = self.tmp / "memory" / "inbox" / "review-2026-09.md"
        text = sheet.read_text(encoding="utf-8")
        self.assertEqual(text.count("\nNote:\n"), 5)
        self.assertNotIn("ran: evening", text)       # run markers stay out of excerpts

        again = run(self.tmp, "sample", "--write")
        self.assertEqual(again.returncode, 1)
        self.assertIn("Not overwritten", again.stderr)

        # The owner writes two notes, one over two lines, and leaves the rest empty.
        parts = text.split("\nNote:\n")
        parts[0] += "\nNote: Wrong person. That was Grace, not Ada.\n"
        parts[2] += "\nNote: Too long.\nCut it to three bullets.\n"
        sheet.write_text("".join(parts), encoding="utf-8")
        notes = json.loads(run(self.tmp, "sample", "--notes", str(sheet), "--json").stdout)
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0]["note"], "Wrong person. That was Grace, not Ada.")
        self.assertEqual(notes[1]["note"], "Too long.\nCut it to three bullets.")
        self.assertTrue(all("#" in n["sample"] for n in notes))

    def test_month_must_be_a_month(self):
        # Found in review 2026-11-22: --month went straight into the file name.
        for bad in ("../../outside/escaped", "Nov", "2026-9"):
            r = run(self.tmp, "sample", "-n", "3", "--write", "--month", bad)
            self.assertEqual(r.returncode, 1, bad)
            self.assertIn("YYYY-MM", r.stderr)
        self.assertEqual([p.name for p in (self.tmp / "memory" / "inbox").iterdir()], [])
        self.assertFalse((self.tmp.parent / "outside").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
