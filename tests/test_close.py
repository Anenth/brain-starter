#!/usr/bin/env python3
"""Fixtures for `bin/brain close`. Run: python3 tests/test_close.py

Builds a throwaway library under a temp dir (BRAIN_ROOT) so the real one is
never touched. Three shapes: tag on the bullet line, tag on a continuation
line, tag alone on its own line. Plus: a tag under a heading must not strike
the bullet above it, and an unknown id must be reported. The library's brain.json
puts the owner in Asia/Kolkata, so "today" here is their date, not the machine's.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BRAIN = REPO / "bin" / "brain"
TZ = "Asia/Kolkata"


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1")
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


def library(root: Path) -> None:
    """The bare tree every test needs, with the owner's timezone in brain.json."""
    (root / "memory" / "daily").mkdir(parents=True)
    shutil.copytree(REPO / "templates", root / "templates")
    (root / "brain.json").write_text(json.dumps({"name": "Ada Lovelace", "timezone": TZ}), encoding="utf-8")


def owner_today() -> str:
    return datetime.now(ZoneInfo(TZ)).date().isoformat()


class CloseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        library(self.tmp)
        self.today = owner_today()
        self.note = self.tmp / "memory" / "daily" / f"{self.today}.md"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, body: str) -> None:
        self.note.write_text(f"---\ntype: daily\ntitle: {self.today}\ndate: {self.today}\n---\n\n# {self.today}\n\n## Brief\n\n{body}\n\n## Log\n", encoding="utf-8")

    def read(self) -> str:
        return self.note.read_text(encoding="utf-8")

    def test_tag_on_bullet_line(self):
        self.write("- **Grace** wants the date. <!-- gmail:abc123 -->\n- **Other** item stays. <!-- gmail:zzz -->")
        r = run(self.tmp, "close", "--gmail", "abc123")
        self.assertIn("1 item(s) closed", r.stdout)
        text = self.read()
        self.assertIn("- ~~**Grace** wants the date.~~ replied", text)
        self.assertIn("- **Other** item stays. <!-- gmail:zzz -->", text)

    def test_tag_on_continuation_line(self):
        self.write("- **Globex** fallback plan, 4 days late.\n  Nobody owns it. <!-- hespia:TASK1 -->")
        r = run(self.tmp, "close", "--hespia", "TASK1")
        self.assertIn("1 item(s) closed", r.stdout)
        text = self.read()
        self.assertIn("- ~~**Globex** fallback plan, 4 days late.", text)
        self.assertIn("Nobody owns it.~~ ticked", text)

    def test_tag_alone_on_line(self):
        self.write("- **Acme** single QR, still untested.\n  <!-- hespia:TASK2 -->")
        r = run(self.tmp, "close", "--hespia", "TASK2")
        self.assertIn("1 item(s) closed", r.stdout)
        text = self.read()
        self.assertIn("- ~~**Acme** single QR, still untested.~~ ticked", text)
        self.assertNotIn("\n~~ ticked", text)  # never a strike at column 0

    def test_tag_under_heading_does_not_strike_bullet_above(self):
        self.write("- **Live item** must survive. <!-- gmail:keep -->\n### 11:30 Product Discussion <!-- hespia:CARD9 -->\nSee needs you above.")
        r = run(self.tmp, "close", "--hespia", "CARD9")
        self.assertIn("skipped: tag not under a bullet", r.stderr)
        self.assertIn("0 item(s) closed", r.stdout)
        self.assertIn("- **Live item** must survive.", self.read())

    def test_message_tag_is_never_closed(self):
        self.write("- **Prep card** for the 1:1. <!-- hespia-msg:MSG1 -->")
        r = run(self.tmp, "close", "--hespia", "MSG1")
        self.assertIn("not found: hespia:MSG1", r.stdout)
        self.assertNotIn("~~", self.read())

    def test_unknown_id_is_reported(self):
        self.write("- **A** thing. <!-- gmail:one -->")
        r = run(self.tmp, "close", "--gmail", "one", "two")
        self.assertIn("not found: gmail:two", r.stdout)
        self.assertIn("1 item(s) closed", r.stdout)

    def test_dry_run_changes_nothing(self):
        self.write("- **A** thing. <!-- gmail:one -->")
        before = self.read()
        r = run(self.tmp, "close", "--gmail", "one", "--dry-run")
        self.assertIn("would strike", r.stdout)
        self.assertEqual(before, self.read())

    def test_already_struck_is_left_alone(self):
        self.write("- ~~**A** thing.~~ replied 2026-01-01 <!-- gmail:one -->")
        r = run(self.tmp, "close", "--gmail", "one")
        self.assertIn("0 item(s) closed", r.stdout)


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        library(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_run_marker_beats_heading(self):
        today = owner_today()
        note = self.tmp / "memory" / "daily" / f"{today}.md"
        note.write_text(
            f"---\ntype: daily\ndate: {today}\n---\n# {today}\n\n## Brief\n\nShort brief with an em dash \u2014 here.\n\n"
            f"## Log\n\n### Evening processing\nnothing\n<!-- ran: evening {today}T19:00+05:30 failed fathom down -->\n",
            encoding="utf-8",
        )
        r = run(self.tmp, "health", "--days", "1")
        self.assertIn("FAIL", r.stdout)
        self.assertIn("1 em dash(es) in brief", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
