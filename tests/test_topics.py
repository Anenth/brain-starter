#!/usr/bin/env python3
"""Fixtures for `bin/brain topics` and the topic checks in lint and who.
Run: python3 tests/test_topics.py

A throwaway library (BRAIN_ROOT) with one topic page. It links two sources: one
untouched since the compile, one with a newer log line. A third note names the
topic's alias after the compile without linking it. An old note that names it
before the compile must not count.
"""

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


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1")
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


class TopicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        mem = self.tmp / "memory"
        for d in ("topics", "projects", "meetings", "people", "daily"):
            (mem / d).mkdir(parents=True)
        shutil.copytree(REPO / "templates", self.tmp / "templates")
        (mem / "topics" / "pricing.md").write_text(
            "---\ntype: topic\ntitle: Pricing\ndate: 2026-09-01\ncompiled: 2026-09-10\n"
            "aliases: [credits, outcome based]\n---\n\n# Pricing\n\n## Where it stands\n"
            "- Moving to credits. [[projects/credits]]\n- Old plan held. [[projects/old-plan]]\n"
            "- Grace owns it. [[people/grace]]\n\n## Compile log\n- 2026-09-10: compiled\n",
            encoding="utf-8",
        )
        (mem / "projects" / "credits.md").write_text(
            "---\ntype: project\ntitle: Credits\ndate: 2026-08-01\nstatus: active\n---\n\n# Credits\n\n"
            "## Log\n- 2026-08-01: created\n- 2026-09-15: meter spec agreed\n",
            encoding="utf-8",
        )
        (mem / "projects" / "old-plan.md").write_text(
            "---\ntype: project\ntitle: Old plan\ndate: 2026-08-01\nstatus: reference\n---\n\n# Old plan\n\n"
            "## Log\n- 2026-08-01: created\n",
            encoding="utf-8",
        )
        (mem / "people" / "grace.md").write_text(
            "---\ntype: person\ntitle: Grace\ndate: 2026-08-01\n---\n\n# Grace\n\nRuns pricing.\n\n"
            "## History\n- 2026-08-01: first met\n",
            encoding="utf-8",
        )
        (mem / "meetings" / "2026-09-18-board.md").write_text(
            "---\ntype: meeting\ntitle: Board\ndate: 2026-09-18\n---\n\n# Board\n\n"
            "The board asked about credits burn. [[people/grace]]\n",
            encoding="utf-8",
        )
        (mem / "meetings" / "2026-09-02-early.md").write_text(
            "---\ntype: meeting\ntitle: Early\ndate: 2026-09-02\n---\n\n# Early\n\nFirst talk of credits.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_topics_counts(self):
        r = run(self.tmp, "topics")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pricing", r.stdout)
        self.assertIn("3 source(s)  1 changed  1 new mention(s)", r.stdout)

    def test_topic_detail_lists_paths(self):
        r = run(self.tmp, "topics", "pricing")
        self.assertIn("changed  2026-09-15  memory/projects/credits.md", r.stdout)
        self.assertIn("new      2026-09-18  memory/meetings/2026-09-18-board.md", r.stdout)
        self.assertNotIn("old-plan", r.stdout.split("new mention(s)")[1])
        self.assertNotIn("2026-09-02-early", r.stdout)

    def test_fresh_topic_not_stale(self):
        page = self.tmp / "memory" / "topics" / "pricing.md"
        page.write_text(page.read_text().replace("compiled: 2026-09-10", "compiled: 2026-09-20"))
        r = run(self.tmp, "topics", "--stale")
        self.assertIn("0 topic(s) to refresh", r.stdout)
        r = run(self.tmp, "lint", "--structure")
        self.assertNotIn("stale topic", r.stdout)

    def test_lint_flags_stale_topic(self):
        r = run(self.tmp, "lint", "--structure")
        self.assertIn("stale topic       memory/topics/pricing.md  compiled 2026-09-10, 1 source(s) changed, 1 new mention(s)", r.stdout)

    def test_who_last_seen_skips_topic(self):
        page = self.tmp / "memory" / "topics" / "pricing.md"
        page.write_text(page.read_text().replace("date: 2026-09-01", "date: 2026-09-30"))
        r = run(self.tmp, "who", "grace")
        self.assertIn("last seen  2026-09-18  memory/meetings/2026-09-18-board.md", r.stdout)

    def test_backfill_with_old_dates_is_caught_by_git(self):
        # Compiled after every date in the sources, so dates alone see nothing.
        page = self.tmp / "memory" / "topics" / "pricing.md"
        page.write_text(page.read_text().replace("compiled: 2026-09-10", "compiled: 2026-09-20"))
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                        cwd=self.tmp, capture_output=True, check=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "compile")
        r = run(self.tmp, "topics", "--stale")
        self.assertIn("0 topic(s) to refresh", r.stdout)
        # A backfilled note about 09-15, written after the compile, not committed yet.
        src = self.tmp / "memory" / "projects" / "credits.md"
        src.write_text(src.read_text() + "- 2026-09-15: board pushed back on the meter\n")
        (self.tmp / "memory" / "meetings" / "2026-09-15-credits-review.md").write_text(
            "---\ntype: meeting\ntitle: Credits review\ndate: 2026-09-15\n---\n\n# Credits review\n", encoding="utf-8")
        r = run(self.tmp, "topics", "pricing")
        self.assertIn("1 changed  1 new mention(s)", r.stdout)
        self.assertIn("memory/projects/credits.md", r.stdout)
        self.assertIn("memory/meetings/2026-09-15-credits-review.md", r.stdout)

    def test_gaps_lists_open_lines_only(self):
        page = self.tmp / "memory" / "topics" / "pricing.md"
        page.write_text(page.read_text().replace(
            "## Compile log",
            "## Gaps\n- No decision file for the credit price.\n  Said in the board call.\n"
            "- ~~Vendor X pricing.~~ captured 2026-09-20\n\n## Compile log"))
        r = run(self.tmp, "topics", "--gaps")
        self.assertIn("- No decision file for the credit price. Said in the board call.", r.stdout)
        self.assertNotIn("Vendor X", r.stdout)
        self.assertIn("1 open gap(s)", r.stdout)

    def test_new_topic_from_template(self):
        r = run(self.tmp, "new", "topic", "Fundraise")
        self.assertEqual(r.stdout.strip(), "memory/topics/fundraise.md")
        text = (self.tmp / "memory" / "topics" / "fundraise.md").read_text()
        self.assertIn("type: topic", text)
        self.assertIn("## Gaps", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
