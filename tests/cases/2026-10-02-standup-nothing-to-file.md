---
case: standup-status-is-not-an-action
date: 2026-10-02
seen: 2026-10-03
rules: routines/evening-processing.md
anchor: "- **light**:"
source: https://fathom.video/calls/900000123
---

# A status update filed as an action

This is an example case. The people and the call are made up.

The evening run read the Fathom summary of the 10-02 Initech daily standup. The
summary listed "Grace Hopper: check the build" under Action items. In the call Grace
only said the build was already green. Nobody asked for anything. The run filed it as
an owned action in Grace's history and wrote "1 action filed" in the log. The next
morning's brief chased Grace for a task that never existed.

## Task

You are running the evening routine's standup step on this one call. The rule you
follow is below under "Rule". Write the single line you would add to today's log for
this standup. Output that line only.

## Input

Fathom listing row:

- Initech daily stand up | 2026-10-02 | id: 100000123 | url: https://fathom.video/calls/900000123 | recorded by Alan Turing | Ada Lovelace, Grace Hopper

Fathom summary:

- Build status: The build is green.
- Action items:
  - Grace Hopper: check the build.

Transcript, 02:10 to 02:41:

[02:10] Alan Turing: Grace, where is the build?
[02:14] Grace Hopper: Green since this morning. I checked it before the call.
[02:20] Ada Lovelace: Good. Anything blocked?
[02:24] Grace Hopper: No, nothing pending on my side.
[02:31] Alan Turing: Same here. Nothing from me.
[02:41] Ada Lovelace: Okay, short one today. Thanks all.

## Must not match

- `(?i)\b[1-9]\d* actions?\b`

## Must match

- `(?i)nothing to file`
- `fathom\.video/calls/900000123`

## Checked

Not run against a model yet. It ships with the starter to show the format. Run it
once with `python3 tests/run_cases.py nothing-to-file` and write what you saw here.

## Judge

Does the line say the standup had nothing to file, with the call's URL?

PASS: One log line for this standup. It says nothing came out of it, in any words, and
it carries the Fathom URL or the id. It does not name an action or a decision.

FAIL: The line counts an action or a decision. Or it names Grace as owning a task. Or
it leaves out both the URL and the id.

Example, FAIL. This is what the run wrote on 10-02:
"- Standup, Initech daily stand up https://fathom.video/calls/900000123: 1 action filed (Grace to check the build)."
Critique: it takes the summary's action item at face value. In the transcript Grace
says the build is already green and nobody asks Grace for anything. Result: Fail

Example, PASS:
"- Standup, Initech daily stand up https://fathom.video/calls/900000123: nothing to file."
Critique: status updates only, no owned action, and the URL is there so the next run
sees the call as handled. Result: Pass
