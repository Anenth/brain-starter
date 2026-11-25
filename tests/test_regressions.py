#!/usr/bin/env python3
"""One test per bug found in the 2026-11-22 review of bin/brain's brief loops.
Run: python3 tests/test_regressions.py

Each one failed on the code as it was. A throwaway library (BRAIN_ROOT), clock pinned.
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
TODAY = "2026-11-20"  # a Friday


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, BRAIN_ROOT=str(root), NO_COLOR="1", BRAIN_TODAY=TODAY)
    return subprocess.run([sys.executable, str(BRAIN), *args], env=env, capture_output=True, text=True)


class Regressions(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain-test-"))
        for d in ("daily", "people", "meetings"):
            (self.tmp / "memory" / d).mkdir(parents=True)
        shutil.copytree(REPO / "templates", self.tmp / "templates")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def daily(self, day: str, brief: str, log: str = "", carried: str = "") -> Path:
        p = self.tmp / "memory" / "daily" / f"{day}.md"
        tail = f"\n## Carried forward\n\n{carried}\n" if carried else ""
        p.write_text(f"---\ntype: daily\ntitle: {day}\ndate: {day}\n---\n\n# {day}\n\n## Brief\n\n{brief}\n{tail}"
                     f"\n## Log\n\n{log}\n", encoding="utf-8")
        return p

    # top3 ---------------------------------------------------------------------

    def test_a_done_verdict_survives_being_struck_by_close(self):
        self.daily("2026-11-19", "### Top 3\n1. **Reply to Ravi.** Send it. <!-- hespia:T1 -->\n",
                   "### Top 3 review\n- done  Reply to Ravi. <!-- hespia:T1 -->\n")
        self.assertIn("1 of 1 Top 3 slot(s) done", run(self.tmp, "top3", "--days", "3").stdout)
        self.assertEqual(run(self.tmp, "close", "--hespia", "T1").returncode, 0)
        self.assertIn("1 of 1 Top 3 slot(s) done", run(self.tmp, "top3", "--days", "3").stdout)

    def test_a_pick_with_a_gmail_tag_first_still_counts(self):
        self.daily("2026-11-19", "### Top 3\n"
                   "1. **One.** x <!-- gmail:g1 --> <!-- hespia:T1 -->\n"
                   "2. **Two.** x <!-- hespia:T2 -->\n"
                   "3. **Three.** x <!-- gmail:g3 --> <!-- hespia:T3 -->\n")
        out = run(self.tmp, "top3", "--days", "3").stdout
        self.assertNotIn("in the Top 3, not 3", out)
        self.assertIn("3 task(s)", out)

    # carried and repeats --------------------------------------------------------

    def test_carried_forward_is_read_when_the_brief_ends_on_fyi(self):
        self.daily("2026-11-19", "### Needs you\n- **Acme.** Sign it. <!-- gmail:a1 -->\n\n### FYI (1)\n- one line\n",
                   carried="- **Globex.** Still waiting. <!-- gmail:b2 -->\n")
        out = run(self.tmp, "carried", "--days", "7").stdout
        self.assertIn("Acme", out)
        self.assertIn("Globex", out)

    def test_carried_keeps_bullets_that_share_a_bold_lead(self):
        due = ("### Due (3)\n- **Fri 20 Nov.** Send the deck to Acme.\n- **Fri 20 Nov.** Pay the vendor.\n"
               "- **Fri 20 Nov.** Renew the domain.\n")
        self.daily("2026-11-18", due)
        self.daily("2026-11-19", due.replace("- **Fri 20 Nov.** Pay the vendor.\n", ""))
        out = run(self.tmp, "carried", "--days", "7").stdout
        for text in ("Send the deck", "Pay the vendor", "Renew the domain"):
            self.assertEqual(out.count(text), 1, text)   # none dropped, none twice
        self.assertIn("(2d)", out)                       # first seen on the 18th

    def test_an_item_twice_in_one_brief_keeps_its_streak(self):
        for day in ("2026-11-17", "2026-11-18", "2026-11-19"):
            self.daily(day, "### Needs you\n- **Ravi.** Reply. <!-- hespia:T9 -->\n")
        self.daily("2026-11-20", "### Top 3\n1. **Ravi.** Reply. <!-- hespia:T9 -->\n\n"
                                 "### Needs you\n- **Ravi.** Reply. <!-- hespia:T9 -->\n")
        out = run(self.tmp, "repeats", "--days", "7", "--min", "3").stdout
        self.assertIn("4 briefs", out)

    # close ----------------------------------------------------------------------

    def test_two_ids_on_one_bullet_are_both_found(self):
        self.daily("2026-11-19", "### Needs you\n- **Ravi** wants the date. <!-- gmail:aaa111 --> <!-- hespia:T1 -->\n")
        r = run(self.tmp, "close", "--gmail", "aaa111", "--hespia", "T1")
        self.assertNotIn("not found", r.stdout + r.stderr)

    # chases ---------------------------------------------------------------------

    def test_chases_lint_points_at_the_real_line(self):
        text = ("---\ntype: chases\ntitle: Chases\ndate: 2026-11-01\n---\n\n# Chases\n\n"
                "<!-- one line each\n     dated -->\n\n## They owe you\n\n- [ ] Somebody owes a thing with no date\n")
        (self.tmp / "memory" / "chases.md").write_text(text, encoding="utf-8")
        want = text.splitlines().index("- [ ] Somebody owes a thing with no date") + 1
        out = run(self.tmp, "chases", "--lint").stdout
        self.assertIn(f"chases.md:{want}", out)

    # writes that could land in the wrong place ------------------------------------

    def test_retire_parks_a_file_never_a_folder(self):
        (self.tmp / "memory" / "people" / "x.md").write_text("---\ntype: person\ntitle: X\n---\n")
        for target in ("memory/people", "memory"):
            r = run(self.tmp, "retire", target)
            self.assertEqual(r.returncode, 1, target)
        self.assertTrue((self.tmp / "memory" / "people" / "x.md").exists())
        self.assertFalse((self.tmp / "_to_delete").exists())

    def test_new_date_must_be_a_date(self):
        for bad in ("2026/08/07", "../../escaped", "tomorrow", "2026-13-40"):
            r = run(self.tmp, "new", "meeting", "Acme QBR", "--date", bad)
            self.assertEqual(r.returncode, 1, bad)
        self.assertEqual(list((self.tmp / "memory" / "meetings").iterdir()), [])
        self.assertEqual(run(self.tmp, "new", "meeting", "Acme QBR", "--date", "2026-08-07").returncode, 0)

    def test_new_set_takes_a_backslash(self):
        r = run(self.tmp, "new", "person", "Dee Vee", "--set", r"role=R\D lead")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(r"role: R\D lead", (self.tmp / "memory" / "people" / "dee-vee.md").read_text())

    # who --------------------------------------------------------------------------

    def test_who_matches_the_name_not_the_folder(self):
        for slug, title in (("ravi-kumar", "Ravi Kumar"), ("ada-lovelace", "Ada Lovelace")):
            (self.tmp / "memory" / "people" / f"{slug}.md").write_text(
                f"---\ntype: person\ntitle: {title}\ndate: 2026-11-01\n---\n\n# {title}\n", encoding="utf-8")
        self.assertIn("no person file", run(self.tmp, "who", "md").stdout)      # ".md" is not a name
        self.assertIn("no person file", run(self.tmp, "who", "memo").stdout)    # nor is "memory/"
        self.assertIn("Ravi Kumar", run(self.tmp, "who", "ravi").stdout)
        self.assertNotIn("Traceback", run(self.tmp, "who", "?").stderr)

    # index --------------------------------------------------------------------------

    def test_searches_that_start_during_a_rebuild_all_answer(self):
        for i in range(150):
            (self.tmp / "memory" / "people" / f"p{i}.md").write_text(
                f"---\ntype: person\ntitle: Person {i}\ndate: 2026-11-01\n---\n\n# Person {i}\n\nlikes zebras\n")
        run(self.tmp, "index")
        (self.tmp / "memory" / "people" / "p0.md").write_text(
            "---\ntype: person\ntitle: Person 0\ndate: 2026-11-01\n---\n\n# Person 0\n\nlikes zebras a lot\n")
        env = dict(os.environ, BRAIN_ROOT=str(self.tmp), NO_COLOR="1", BRAIN_TODAY=TODAY)
        procs = [subprocess.Popen([sys.executable, str(BRAIN), "search", "zebras"], env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
        results = [(p.communicate(), p.returncode) for p in procs]
        for (out, err), code in results:
            self.assertEqual(code, 0, err[-300:])
            self.assertIn("zebras", out)


if __name__ == "__main__":
    unittest.main()
