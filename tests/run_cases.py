#!/usr/bin/env python3
"""Replay real mistakes against the current skill and routine rules.

Run: python3 tests/run_cases.py            every case
     python3 tests/run_cases.py standup    cases whose file name has "standup"
     python3 tests/run_cases.py --show     print the prompts, call nothing
     python3 tests/run_cases.py --rev 643d746~1 standup   against the rule before the fix

Each file in tests/cases/ is one mistake a real run made. It holds the input the run
saw, the rule text it should follow (read live from the repo, so a rule change is
tested), and two kinds of check:

- Code first. "Must match" and "Must not match" are regexes on the output.
- Then one yes/no judge question, with the real bad output as the Fail example.
  Pass or Fail only. No scores.

A case passes only if every check passes. Run it after changing a skill or routine
that a case names in `rules:`. Needs the claude command, logged in. Costs a few
cents a case.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "tests" / "cases"
MODEL = "sonnet"  # the model the routines run on, near enough
JUDGE_MODEL = "sonnet"


def parse_case(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    parts = re.split(r"(?m)^## (.+)$", m.group(2))
    sections = {parts[i].strip().lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    regexes = lambda key: re.findall(r"(?m)^- `(.+)`\s*$", sections.get(key, ""))
    return {"name": path.stem, "meta": meta, "task": sections.get("task", ""),
            "input": sections.get("input", ""), "judge": sections.get("judge", ""),
            "must": regexes("must match"), "must_not": regexes("must not match")}


def rule_text(meta: dict, rev: str = "") -> str:
    """The rule block, read from the repo now, or as it was at a git rev. With an
    anchor, the lines from the anchor to the next sibling bullet at the same indent.
    Without one, the file."""
    if rev:
        text = subprocess.run(["git", "show", f"{rev}:{meta['rules']}"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout
    else:
        text = (REPO / meta["rules"]).read_text(encoding="utf-8")
    anchor = meta.get("anchor")
    if not anchor:
        return text
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if anchor in l), None)
    if start is None:
        raise SystemExit(f"anchor {anchor!r} not found in {meta['rules']}. The rule moved. Fix the case.")
    indent = len(lines[start]) - len(lines[start].lstrip())
    out = [lines[start]]
    for l in lines[start + 1:]:
        ind = len(l) - len(l.lstrip())
        if l.strip() and (ind < indent or (ind == indent and l.lstrip().startswith("- "))):
            break
        out.append(l)
    return "\n".join(out).rstrip()


def claude(prompt: str, model: str) -> str:
    # Outside the repo, so the call does not load the brain's CLAUDE.md.
    res = subprocess.run(["claude", "-p", "--model", model, "--output-format", "text"],
                         input=prompt, capture_output=True, text=True, timeout=300,
                         cwd=tempfile.gettempdir())
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip()[:300])
    return res.stdout.strip()


def run_prompt(case: dict, rev: str = "") -> str:
    return f"{case['task']}\n\n## Rule\n\n{rule_text(case['meta'], rev)}\n\n## Input\n\n{case['input']}\n"


def judge_prompt(case: dict, output: str) -> str:
    return ("You are checking one output for one failure. Answer Pass or Fail only.\n\n"
            f"## Criterion\n\n{case['judge']}\n\n"
            f"## What the run saw\n\n{case['input']}\n\n"
            f"## Output to check\n\n{output}\n\n"
            'Reply with JSON only: {"critique": "<what the output says, with evidence>", '
            '"result": "Pass" or "Fail"}. Write the critique first.')


def check(case: dict, output: str) -> list[str]:
    """Code checks. Each failure is one line. Empty means pass."""
    fails = [f"matched forbidden /{rx}/" for rx in case["must_not"] if re.search(rx, output)]
    fails += [f"did not match /{rx}/" for rx in case["must"] if not re.search(rx, output)]
    return fails


def judge(case: dict, output: str) -> tuple[str, str]:
    raw = claude(judge_prompt(case, output), JUDGE_MODEL)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        v = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        v = {}
    result = str(v.get("result", "")).strip().capitalize()
    if result not in ("Pass", "Fail"):
        return "Fail", f"judge gave no clear verdict: {raw[:200]}"
    return result, str(v.get("critique", ""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("filter", nargs="?", default="")
    ap.add_argument("--show", action="store_true", help="print the prompts, call nothing")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--rev", default="", help="read the rules as they were at this git rev. "
                    "Use the commit before a case's fix to see the case fail, so you know it has teeth")
    args = ap.parse_args()
    files = sorted(p for p in CASES.glob("*.md") if args.filter in p.stem and p.name != "README.md")
    if not files:
        print(f"no cases match {args.filter!r}")
        return 1
    if not args.show and not shutil.which("claude"):
        print("the claude command is not installed")
        return 1
    failed = 0
    for path in files:
        case = parse_case(path)
        prompt = run_prompt(case, args.rev)
        if args.show:
            print(f"===== {case['name']}\n{prompt}")
            continue
        print(f"{case['name']}")
        try:
            output = claude(prompt, args.model)
        except Exception as e:
            print(f"  ERROR  {e}")
            failed += 1
            continue
        print("  output  " + output.replace("\n", "\n          "))
        fails = check(case, output)
        for f in fails:
            print(f"  FAIL   code: {f}")
        verdict, critique = judge(case, output) if case["judge"] else ("Pass", "")
        print(f"  {verdict.upper():<6} judge: {critique}")
        ok = not fails and verdict == "Pass"
        failed += not ok
        print(f"  {'PASS' if ok else 'FAIL'}")
    if not args.show:
        print(f"\n{len(files) - failed} of {len(files)} case(s) pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
