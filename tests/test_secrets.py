#!/usr/bin/env python3
"""Fixtures for `bin/brain secrets`. Run: python3 tests/test_secrets.py

A throwaway git repo (BRAIN_ROOT). Every routine runs `secrets` and then `git add -A`,
so the scan must see files git has not been told about yet. Found in review
2026-11-22: it listed tracked files only, so a note written in that run was
committed unscanned.

Every key here is fake and is glued together at run time, so this file never
trips the scan it tests.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAIN = HERE.parent / "bin" / "brain"

A = "a1B2c3D4e5F6g7H8i9J0"
FAKES = {
    "google api key": "AI" + "za" + "x" * 35,
    "github token": "gh" + "p_" + A + A[:16],
    "api key field": "FATHOM_API" + "_KEY=" + A + A,
    "json pw field": '{"pass' + 'word": "hunter2hunter2"}',
    "json client secret": '{"client_' + 'secret": "' + A + '"}',
    "slack app token": "xap" + "p-1-" + A,
    "stripe key": "sk_" + "live_" + A,
    "jwt": "ey" + "J" + A + "." + A + "." + A,
}


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1")
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   cwd=root, capture_output=True, check=True)


class SecretsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        (self.tmp / "memory" / "inbox").mkdir(parents=True)
        (self.tmp / ".gitignore").write_text(".brain/\nignored/\n")
        (self.tmp / "memory" / "ok.md").write_text("Nothing to see. password policy is in the wiki.\n")
        git(self.tmp, "init", "-q")
        git(self.tmp, "add", "-A")
        git(self.tmp, "commit", "-qm", "start")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clean_repo_passes(self):
        r = run(self.tmp, "secrets")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 possible secret(s)", r.stdout)

    def test_a_new_untracked_file_is_scanned(self):
        (self.tmp / "memory" / "inbox" / "new-capture.md").write_text(FAKES["google api key"] + "\n")
        r = run(self.tmp, "secrets")
        self.assertEqual(r.returncode, 1)
        self.assertIn("memory/inbox/new-capture.md:1", r.stdout)

    def test_an_ignored_file_is_not(self):
        (self.tmp / "ignored").mkdir()
        (self.tmp / "ignored" / "token.json").write_text(FAKES["google api key"] + "\n")
        self.assertEqual(run(self.tmp, "secrets").returncode, 0)

    def test_every_shape_is_caught(self):
        for label, fake in FAKES.items():
            p = self.tmp / "memory" / "leak.md"
            p.write_text(fake + "\n")
            r = run(self.tmp, "secrets")
            self.assertEqual(r.returncode, 1, f"missed: {label}")


if __name__ == "__main__":
    unittest.main()
