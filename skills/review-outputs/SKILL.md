---
name: review-outputs
description: Monthly read-through of what the routines wrote. Code picks about 15 outputs into a sheet, the owner writes plain notes on the wrong ones, and this skill sorts the notes into mistake types and feeds the improvements ledger and the test cases. Use when a review sheet has notes, or when the owner asks to check how the briefs and notes are doing.
---

# Review outputs

The routines write briefs, meeting notes, triage and sweeps every day. Nobody checks
them on purpose. Mistakes get caught only by chance. This is the on-purpose check.

The idea comes from how evals are done well: **read real
outputs first, name the mistakes you actually see, then fix.** Never start from a
list of mistakes you imagine.

**The owner notices. You organise.** They write plain notes. They never pick a
category, fill a form or give a score. Sorting is your job.

## Part 1. Make the sheet (first Friday of the month, unattended)

1. `bin/brain sample --write`. It picks 15 outputs from the last 30 days, by code:
   every kind gets a turn, the rest at random. It writes
   `memory/inbox/review-YYYY-MM.md` and never overwrites one.
2. Post one Hespia `send_message`, `kind: update`, `from: review-outputs`. Title:
   "15 things to read this month". Body: two lines. Where the sheet is, and "write a
   note under anything wrong, leave the rest empty, stop when you like". No tasks.
3. That's all. Do not read the sheet for them. Do not pre-fill notes.

## Part 2. Read the notes back (any run that finds notes, or when the owner asks)

1. `bin/brain sample --notes memory/inbox/review-YYYY-MM.md`. Code pulls out each
   note with the sample it belongs to. No notes yet: stop, say nothing.
2. **Read the sample in full** before sorting its note. The excerpt is cut at 15
   lines. The note may be about a line past the cut.
3. **Sort each note into a mistake type.** Name the type by what went wrong in
   the system, not by a textbook label. Good: "suggestion filed as a decision", "wrong
   person named", "chase for an item someone else owns". Bad: "hallucination",
   "quality issue". Reuse a type already in `memory/improvements.md` when it fits.
4. **Look for more of the same.** Once a type has a clear example, search the last
   30 days for other instances: `bin/brain search`, `bin/brain lint`. Two or three
   more is enough. You are finding kinds of mistake, not counting them.
5. **Decide the fix for each type.** In this order. Stop at the first that works:
   - **The rule never asked for it.** Add one line to the skill or routine. Most
     mistakes are this.
   - **Code can check it.** Propose a check in `bin/brain lint`, like the name and
     tag checks in "known mistakes". Code first, always.
   - **It needs judgment.** Propose a test case in `tests/cases/`, with the real bad
     output as the Fail example. See `tests/cases/README.md`.
6. **Write it down.**
   - `memory/improvements.md`: one line per type, `seen YYYY-MM-DD`, "review
     sheet YYYY-MM" as the source. An existing item gets another `seen` date.
   - A wrong fact in the library gets corrected in place, struck through and dated,
     same as always.
   - Unattended, never edit `bin/brain` or a skill. Draft it and say so.
7. **Close the sheet.** Under each note, add `Sorted: <type> → <where it went>`.
   Then `bin/brain retire memory/inbox/review-YYYY-MM.md`. The owner removes it.
8. **Say it back.** One short block in today's log, `### Output review YYYY-MM`:
   how many samples the owner read, how many notes, the types, the fixes. Pick first.

## Rules

- **Diversity over counting.** 15 samples find kinds of mistake. They do not
  measure how often. Never write "7% of briefs are wrong" from a sheet.
- **One note can be two types.** Split it.
- **The owner's note wins.** If the note and the file disagree, the note is right
  unless the file cites a source the owner did not see. Then ask, once.
- **No new sheet while one has open notes.** Sort the old one first.
- A type seen in two months running is a rule that did not work. Say so plainly.
- Write the way `memory/profile.md` says. Short sentences, no em dashes, no italics.
