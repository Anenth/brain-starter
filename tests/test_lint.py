#!/usr/bin/env python3
"""Fixtures for the known-mistake checks in `bin/brain lint`.
Run: python3 tests/test_lint.py

Each test is a mistake of a kind that happens in real runs:
- a person's name one or two letters off, used for weeks (Grace Harper for Grace Hopper)
- a Hespia message id in a `hespia:` task tag
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


def run(root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1", BRAIN_TODAY=TODAY)
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, input=stdin,
                          capture_output=True, text=True)


class LintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        for d in ("people", "companies", "meetings", "daily"):
            (self.tmp / "memory" / d).mkdir(parents=True)
        shutil.copytree(REPO / "templates", self.tmp / "templates")
        self.note("people/grace-hopper.md", "person", "Grace Hopper", "Runs events at Acme.\n" * 6)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def note(self, rel: str, kind: str, title: str, body: str, day: str = "2026-09-20") -> Path:
        p = self.tmp / "memory" / rel
        p.write_text(f"---\ntype: {kind}\ntitle: {title}\ndate: {day}\n---\n\n# {title}\n\n{body}\n",
                     encoding="utf-8")
        return p

    def known(self, *args: str) -> str:
        out = run(self.tmp, "lint", "--structure", *args).stdout
        return out.split("known mistakes", 1)[1]

    # names -----------------------------------------------------------------

    def test_misspelled_name_is_flagged(self):
        self.note("meetings/2026-09-20-acme.md", "meeting", "Acme sync",
                  "Grace Harper asked for the deck. Grace Harper will send dates.")
        out = self.known()
        self.assertIn('"Grace Harper" x2, file is memory/people/grace-hopper.md', out)

    def test_correct_name_and_other_people_pass(self):
        self.note("meetings/2026-09-20-acme.md", "meeting", "Acme sync",
                  "Grace Hopper asked for the deck. Grace Kelly joined late. Grand Hotel venue.")
        self.assertNotIn("name off by a letter", self.known())

    def test_correction_note_is_not_the_error(self):
        self.note("daily/2026-09-20.md", "daily", "2026-09-20",
                  "- **Grace Harper was never their name.** It is Grace Hopper.\n\n"
                  "- ~~Grace Harper to send dates~~ fixed")
        self.assertNotIn("name off by a letter", self.known())

    # hespia tags -----------------------------------------------------------

    def test_message_id_in_task_tag_is_flagged(self):
        self.note("daily/2026-09-27.md", "daily", "2026-09-27",
                  "## Brief\n\n"
                  "- Send Alan the DPA. <!-- hespia:TASK1 -->\n"
                  "- Prep for Acme. <!-- hespia:MSG1 -->\n"
                  "- ~~Old one~~ ticked 2026-09-26 <!-- hespia:GONE1 -->\n", day="2026-09-27")
        tasks = self.tmp / "tasks.json"
        tasks.write_text(json.dumps([{"id": "TASK1", "done": False}]), encoding="utf-8")
        out = self.known("--tasks", str(tasks))
        self.assertIn("not a task id     hespia:MSG1", out)
        self.assertNotIn("TASK1", out)
        self.assertNotIn("GONE1", out)  # struck lines are history, not open tasks

    def test_same_id_in_both_kinds_of_tag(self):
        self.note("daily/2026-09-27.md", "daily", "2026-09-27",
                  "- Acme card <!-- hespia-msg:X1 -->\n- Acme prep <!-- hespia:X1 -->", day="2026-09-27")
        self.assertIn("id in both tags   X1", self.known())

    def test_tags_in_backticks_are_docs_not_tags(self):
        self.note("daily/2026-09-27.md", "daily", "2026-09-27",
                  "Cards carry `<!-- hespia-msg:X1 -->` and tasks `<!-- hespia:X1 -->`.", day="2026-09-27")
        self.assertNotIn("id in both tags", self.known())

    # found in review 2026-11-22 ------------------------------------------------

    def test_path_that_is_not_there_does_not_read_as_clean(self):
        r = run(self.tmp, "lint", "--path", "memory/daily/2026-13-99.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no such file", r.stderr)
        self.assertNotIn("0 finding(s)", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
