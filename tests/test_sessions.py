#!/usr/bin/env python3
"""Fixtures for `bin/brain sessions`. Run: python3 tests/test_sessions.py

Builds fake Claude Code transcripts under a temp CLAUDE_PROJECTS_DIR. Checks: a
quiet branch is dropped, a fresh one is active, a routine run is hidden, a
one-question session is hidden, a merged PR (from the cache) is hidden, and two
sessions on one PR collapse to one line. gh is never called (--no-gh).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BRAIN = REPO / "bin" / "brain"


def iso(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def transcript(path: Path, prompts: list[str], days_ago: float, cwd: str, branch: str = "",
               title: str = "", pr: int | None = None, repo: str = "") -> None:
    sid = path.stem
    rows = []
    if title:
        rows.append({"type": "custom-title", "customTitle": title, "sessionId": sid})
    for i, text in enumerate(prompts):
        ts = iso(days_ago + (len(prompts) - i) * 0.01)
        rows.append({"type": "user", "timestamp": ts, "cwd": cwd, "gitBranch": branch,
                     "isSidechain": False, "sessionId": sid, "message": {"role": "user", "content": text}})
        rows.append({"type": "assistant", "timestamp": ts, "cwd": cwd, "gitBranch": branch,
                     "isSidechain": False, "sessionId": sid,
                     "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]}})
    if pr:
        rows.append({"type": "pr-link", "sessionId": sid, "prNumber": pr, "prRepository": repo,
                     "prUrl": f"https://github.com/{repo}/pull/{pr}", "timestamp": iso(days_ago)})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    stamp = (datetime.now() - timedelta(days=days_ago)).timestamp()
    os.utime(path, (stamp, stamp))


class SessionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-sessions-"))
        self.root = self.tmp / "brain"
        (self.root / "memory").mkdir(parents=True)
        (self.root / ".brain").mkdir()
        self.projects = self.tmp / "projects"
        fe = "/Users/x/Code/acme/acme-front-end"
        transcript(self.projects / "a" / "s1.jsonl", ["build the widget", "now polish it"], 6, fe,
                   "claude/widget-1", "Widget z-order")
        transcript(self.projects / "a" / "s2.jsonl", ["fix the flicker", "again"], 0.5, fe,
                   "claude/flicker-2", "List flickering")
        transcript(self.projects / "b" / "s3.jsonl", ["<scheduled-task name=\"x\"> run", "more"], 5,
                   "/Users/x/Code/brain", "", "Brain chat sweep")
        transcript(self.projects / "a" / "s4.jsonl", ["what changed on master"], 5, fe, "", "Changes")
        transcript(self.projects / "a" / "s5.jsonl", ["sso login", "plan it"], 9, fe, "claude/sso",
                   "SSO login", pr=101, repo="acme/acme-front-end")
        transcript(self.projects / "a" / "s6.jsonl", ["sso login again", "resolve"], 4, fe, "claude/sso-2",
                   "SSO login (fork)", pr=101, repo="acme/acme-front-end")
        transcript(self.projects / "a" / "s7.jsonl", ["magazine sizing", "ship"], 4, fe, "claude/mag",
                   "Report PDF", pr=102, repo="acme/acme-front-end")
        (self.root / ".brain" / "pr-state.json").write_text(json.dumps({
            "acme/acme-front-end#102": "merged", "acme/acme-front-end#101": "open"}))

    def run_brain(self, *args):
        env = dict(os.environ, BRAIN_ROOT=str(self.root), CLAUDE_PROJECTS_DIR=str(self.projects), NO_COLOR="1")
        return subprocess.run([sys.executable, str(BRAIN), "sessions", "--no-gh", *args],
                              env=env, capture_output=True, text=True)

    def test_buckets(self):
        out = self.run_brain("--days", "14").stdout
        dropped, active = out.split("Active", 1)
        self.assertIn("Widget z-order", dropped)
        self.assertIn("claude/widget-1", dropped)
        self.assertIn("List flickering", active)
        self.assertNotIn("Brain chat sweep", out)
        self.assertNotIn("Changes", out)
        self.assertNotIn("Report PDF", out)
        self.assertIn("1 done", out)

    def test_pr_collapses_and_idle_flag(self):
        rows = json.loads(self.run_brain("--days", "14", "--json").stdout)
        sso = [r for r in rows if r["pr"] and r["pr"]["number"] == 101]
        self.assertEqual(len(sso), 1)
        self.assertEqual(sso[0]["title"], "SSO login (fork)")
        self.assertTrue(sso[0]["dropped"])
        self.assertEqual(sso[0]["pr_state"], "open")
        self.assertEqual(sso[0]["repo"], "acme-front-end")
        fresh = [r for r in rows if r["title"] == "List flickering"][0]
        self.assertFalse(fresh["dropped"])

    def test_all_shows_done(self):
        out = self.run_brain("--days", "14", "--all").stdout
        self.assertIn("Report PDF", out)
        self.assertIn("PR #102 merged", out)

    def test_one_branch_name_in_two_repos_is_two_sessions(self):
        # Found in review 2026-11-22: the dedup key had no repo in it.
        transcript(self.projects / "c" / "s8.jsonl", ["port the importer", "go on"], 2,
                   "/Users/x/Code/acme/acme-server", "develop", "Importer port")
        transcript(self.projects / "c" / "s9.jsonl", ["tidy the tokens", "go on"], 3,
                   "/Users/x/Code/acme/acme-design", "develop", "Token tidy")
        titles = [r["title"] for r in json.loads(self.run_brain("--days", "14", "--json").stdout)]
        self.assertIn("Importer port", titles)
        self.assertIn("Token tidy", titles)


if __name__ == "__main__":
    unittest.main()
