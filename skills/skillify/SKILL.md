---
name: skillify
description: Turn work just completed into a reusable skill file, so the same thinking never has to happen twice. Use after finishing any multi-step task that took real judgment and could recur, and whenever the owner says "remember how to do this" or "make this a skill".
---

# Skillify

This is the compounding loop. Without it, every session starts from zero and the system is
just a chatbot with a filesystem.

## When it's worth it

Write a skill when **all three** hold:

- It took more than a couple of steps of real thinking.
- It will happen again. Weekly, monthly, or every time some trigger fires.
- Getting it wrong has a cost, so the order and the rules matter.

Don't write one for a one-off, and don't write one for something a single CLI command
already does. A skill nobody runs is clutter, and clutter makes the real skills harder
to find.

## Steps

1. **Reconstruct what you actually did.** Not the tidy version. The real sequence,
   including the dead ends. Where did you have to make a judgment call? Where did you
   nearly get it wrong? Those become the rules.

2. **Name the trigger precisely.** The `description` is the whole retrieval mechanism.
   It decides whether this skill ever gets used again. Write it as when to use this,
   in the words the owner would actually say. "Use when the owner asks about churn
   numbers" beats "Analytics skill".

3. **Write `skills/<name>/SKILL.md`:**

   ```markdown
   ---
   name: kebab-case-name
   description: What it does + when to use it, in the owner's words.
   ---

   # Title

   One line on what "done" looks like.

   ## Steps
   1. Numbered. Concrete. Name the actual tools and commands.

   ## Rules
   - The judgment calls, the failure modes, the things never to do.
   ```

   Write it for any owner. Owner facts (name, email, timezone, Hespia org) come from
   `brain.json`; priorities and voice come from `memory/profile.md`. Never hard-code
   them in the skill.

4. **Test the standard.** If a smart intern could follow it, an agent can run it. Read it
   back cold, with no memory of today. Any step where you'd have to ask a question is a
   step that isn't written yet.

5. **Keep the deterministic parts out of prose.** If the skill says "count them" or "find
   all the X", that belongs in `bin/brain` as a command, not in a paragraph the model has
   to re-derive every time. Add the subcommand and reference it.

6. **Lint it.** `bin/brain lint --path skills/<name>/SKILL.md`. Fix every em dash it
   finds.

7. **Commit it** with a message saying what it captures. Skills are the asset. They go in
   git, and they stay the owner's.

8. **Strike the ledger line.** If the work came from `memory/improvements.md`, strike
   that item with the date and the skill name. If it did not, it should have: anything
   done twice by hand goes into the ledger first, with `seen YYYY-MM-DD` for each
   time. `bin/brain improvements` shows what is waiting and what git may already have
   fixed. The Friday review reads it. A candidate that lives only in a review
   paragraph gets listed again next week and never built.

## Rules

- One skill, one job. If it needs "if the owner asks for A do this, if B do that",
  it's two skills.
- Rewrite existing skills rather than adding near-duplicates. Two skills that both sort of
  cover meeting prep means neither gets picked reliably.
- Concrete beats complete. A short skill that runs beats a thorough one that's ignored.
- Every skill that touches the outside world states plainly what it must never do
  (send, publish, delete, share). Write that line before you write the steps.
- Unattended runs never write a skill. They draft it as `skills/<name>/SKILL.md.draft`
  and say so. The owner promotes it.
