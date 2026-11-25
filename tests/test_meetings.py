#!/usr/bin/env python3
"""Fixtures for `bin/brain meetings`. Run: python3 tests/test_meetings.py

A throwaway library (BRAIN_ROOT) with one meeting note, one daily line that
already carries a team call's id, and a Pricing topic. A brain.json says the
owner is Ada Lovelace. The Fathom listing is the connector's own text shape,
including a title with a pipe in it.
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

FATHOM = """Found 7 meeting(s).

- Acme <> Grace | 2026-09-04 | id: 100000001 | url: https://fathom.video/calls/900000001 | recorded by Alan Turing | Ada Lovelace, Grace Hopper
- Grace <>Linus | 2026-09-05 | id: 100000002 | url: https://fathom.video/calls/900000002 | recorded by Linus Pauling | Alan Turing, Grace Hopper
- Events stand up | 2026-09-07 | id: 100000003 | url: https://fathom.video/calls/900000003 | recorded by Katherine Johnson | Ada Lovelace, Edsger Dijkstra
- Pricing discussion  | 2026-09-15 | id: 100000004 | url: https://fathom.video/calls/900000004 | recorded by Emmy Noether | Linus Pauling, Alan Turing
- Globex GTC | Acme | 2026-09-21 | id: 100000005 | url: https://fathom.video/calls/900000005 | recorded by Emmy Noether | Hedy Lamarr (GLOBEX)
- Impromptu Google Meet Meeting | 2026-09-11 | id: 100000006 | url: https://fathom.video/calls/900000006 | recorded by Emmy Noether
- Hedy<>Acme | 2026-09-14 | id: 100000007 | url: https://fathom.video/calls/900000007 | recorded by Alan Turing | Hedy Lamarr
"""

CALENDAR = {
    "events": [
        {"summary": "1-1 Ada <> Grace", "start": {"dateTime": "2026-09-15T11:00:00+05:30"},
         "attendees": [{"email": "ada@example.com", "self": True, "responseStatus": "accepted"},
                       {"email": "grace@example.com", "displayName": "Grace"}]},
        {"summary": "Pricing discussion", "start": {"dateTime": "2026-09-15T15:00:00+05:30"},
         "attendees": [{"email": "ada@example.com", "self": True}, {"email": "linus@example.com"}]},
        {"summary": "Standup - Engineering", "start": {"dateTime": "2026-09-15T09:30:00+05:30"},
         "attendees": [{"email": "ada@example.com", "self": True}, {"email": "edsger@example.com"}]},
        {"summary": "Vendor pitch", "start": {"dateTime": "2026-09-16T12:00:00+05:30"},
         "attendees": [{"email": "ada@example.com", "self": True, "responseStatus": "declined"},
                       {"email": "x@vendor.example"}]},
        {"summary": "Focus", "start": {"dateTime": "2026-09-16T14:00:00+05:30"}, "eventType": "focusTime",
         "attendees": [{"email": "ada@example.com", "self": True}, {"email": "y@example.com"}]},
    ]
}

# Whose library this is. The owner shows up in Fathom as "Ada".
CONFIG = {"name": "Ada Lovelace", "email": "ada@example.com", "timezone": "Asia/Kolkata", "hespia_org": "acme"}


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1")
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


class MeetingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        mem = self.tmp / "memory"
        for d in ("meetings", "daily", "topics"):
            (mem / d).mkdir(parents=True)
        shutil.copytree(REPO / "templates", self.tmp / "templates")
        (self.tmp / "brain.json").write_text(json.dumps(CONFIG), encoding="utf-8")
        (mem / "meetings" / "2026-09-14-hedy-lamarr-and-acme.md").write_text(
            "---\ntype: meeting\ntitle: Hedy Lamarr and Acme\ndate: 2026-09-14\n"
            "source: https://fathom.video/calls/900000007\n---\n\n# Hedy\n", encoding="utf-8")
        (mem / "daily" / "2026-09-05.md").write_text(
            "---\ntype: daily\ndate: 2026-09-05\n---\n\n## Log\n- Grace <> Linus (id 100000002). Not theirs.\n",
            encoding="utf-8")
        (mem / "topics" / "pricing.md").write_text(
            "---\ntype: topic\ntitle: Pricing\ndate: 2026-09-01\ncompiled: 2026-09-01\naliases: [credits]\n---\n\n# Pricing\n",
            encoding="utf-8")
        (self.tmp / "fathom.txt").write_text(FATHOM, encoding="utf-8")
        (self.tmp / "cal.json").write_text(json.dumps(CALENDAR), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rows(self, *extra) -> dict:
        r = run(self.tmp, "meetings", str(self.tmp / "fathom.txt"), "--json", *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return {row["title"]: row for row in json.loads(r.stdout)}

    def test_their_meeting_recorded_by_someone_else_is_full(self):
        row = self.rows()["Acme <> Grace"]
        self.assertEqual(row["action"], "full")
        self.assertEqual(row["why"], "they were on it")

    def test_id_in_daily_note_counts_as_filed(self):
        self.assertEqual(self.rows()["Grace <>Linus"]["action"], "done")

    def test_source_url_counts_as_filed(self):
        self.assertEqual(self.rows()["Hedy<>Acme"]["action"], "done")

    def test_their_standup_is_light(self):
        self.assertEqual(self.rows()["Events stand up"]["action"], "light")

    def test_team_call_on_a_topic_is_full(self):
        row = self.rows()["Pricing discussion"]
        self.assertEqual(row["action"], "full")
        self.assertEqual(row["why"], "topic pricing")

    def test_pipe_in_title_parses(self):
        self.assertEqual(self.rows()["Globex GTC | Acme"]["action"], "line")

    def test_impromptu_not_theirs_is_skipped(self):
        self.assertEqual(self.rows()["Impromptu Google Meet Meeting"]["action"], "skip")

    def test_calendar_meeting_with_no_recording(self):
        rows = self.rows("--calendar", str(self.tmp / "cal.json"))
        untraced = [t for t, r in rows.items() if r["action"] == "no-trace"]
        self.assertEqual(untraced, ["1-1 Ada <> Grace"])  # not the recorded, standup, declined or focus ones

    def test_calendar_only_uses_evening_log_not_brief(self):
        (self.tmp / "memory" / "daily" / "2026-09-15.md").write_text(
            "---\ntype: daily\ndate: 2026-09-15\n---\n\n## Brief\n\n### 11:00 1-1 Ada <> Grace\n"
            "### 15:00 Pricing discussion\n\n## Log\n\n### Morning brief\n- 1-1 Ada <> Grace prepped\n\n"
            "### Evening processing\n- Pricing discussion: no recording, card notes copied below.\n",
            encoding="utf-8")
        r = run(self.tmp, "meetings", "--calendar", str(self.tmp / "cal.json"), "--json")
        rows = {row["title"]: row["action"] for row in json.loads(r.stdout)}
        self.assertEqual(rows, {"1-1 Ada <> Grace": "no-trace"})

    def test_text_summary_line(self):
        r = run(self.tmp, "meetings", str(self.tmp / "fathom.txt"))
        self.assertIn("full 2  light 1  no-trace 0  line 1  skip 1  done 2", r.stdout)
        self.assertNotIn("Hedy<>Acme", r.stdout)

    # found in review 2026-11-22 ------------------------------------------------

    def test_a_second_call_that_day_is_not_hidden_behind_the_first_note(self):
        # Two interviews on one day. One has a note. The other must still need one.
        (self.tmp / "memory" / "meetings" / "2026-09-18-interview-linus.md").write_text(
            "---\ntype: meeting\ntitle: Interview Linus\ndate: 2026-09-18\n"
            "source: https://fathom.video/calls/900000001\n---\n\n# Interview\n", encoding="utf-8")
        (self.tmp / "fathom.txt").write_text(
            "- Interview Linus | 2026-09-18 | id: 1 | url: https://fathom.video/calls/900000001 | recorded by Ada Lovelace | Linus\n"
            "- Interview Edsger | 2026-09-18 | id: 2 | url: https://fathom.video/calls/900000002 | recorded by Ada Lovelace | Edsger\n",
            encoding="utf-8")
        rows = self.rows()
        self.assertEqual(rows["Interview Linus"]["action"], "done")
        self.assertNotEqual(rows["Interview Edsger"]["action"], "done")

    def test_json_listing_is_filed_under_its_local_date(self):
        # 21:00 UTC on the 20th is 02:30 on the 21st in the fixture's timezone.
        (self.tmp / "fathom.txt").write_text(json.dumps([{
            "title": "Late call", "created_at": "2026-09-20T21:00:00Z", "recording_id": 7,
            "url": "https://fathom.video/calls/900000007", "recorded_by": {"name": "Ada Lovelace"},
            "calendar_invitees": [{"name": "Ada Lovelace"}]}]), encoding="utf-8")
        self.assertEqual(self.rows()["Late call"]["date"], "2026-09-21")

    def test_a_broken_listing_is_one_line_not_a_traceback(self):
        (self.tmp / "fathom.txt").write_text("[{broken", encoding="utf-8")
        for args in ((str(self.tmp / "fathom.txt"),), (str(self.tmp / "nope.txt"),)):
            r = run(self.tmp, "meetings", *args)
            self.assertEqual(r.returncode, 1)
            self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
