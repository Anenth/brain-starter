---
name: recall
description: Answer a question from the library. What was decided, when, by whom, and why. Use for any question about the owner's own history, people, past decisions, or prior conversations ("what did we decide about X", "when did I last talk to Y", "why did we go with Z").
---

# Recall

The library answers, or it says it doesn't know. Those are the only two outcomes.

## Steps

1. **Search deterministically, more than once.** One query is not a search.

   ```bash
   bin/brain search "sso timeline"
   bin/brain search "single sign-on" --type decision
   bin/brain search "sso" --since 2026-01-01 -n 20
   ```

   Vary the phrasing. The way the owner wrote it down then is not the way they're
   asking now. Use `--type` to separate what was decided from what was discussed.
   On zero hits, try `--loose`, and take the spellings it suggests.

   If the question is about a big theme, check `bin/brain topics` first. A topic page
   is the fastest map of what the library knows. Use it to find the sources, then read
   and cite the sources, not the page. If it shows stale, say so.

2. **Follow the graph.** `bin/brain links <path>` on the best hits. The answer is often one
   hop away: the decision file explains the meeting note.

3. **Names get `who`.** `bin/brain who "<name>"` for every person in the question.

4. **Answer with citations.** Every claim traces to a file. Format:

   ```
   Decided 2026-06-02: no custom SSO work before Q1.

   Why: two engineers for six weeks against one deal, and the SAML path covered
   80% of asks. You said you'd revisit if a second enterprise deal hinged on it.
   → memory/decisions/2026-06-02-sso-scope.md

   Since then Ada Lovelace has raised it twice (2026-07-14, 2026-08-01). That
   second deal condition may now be met.
   → memory/meetings/2026-07-14-acme-sync.md

   Not in the library: nothing on SSO since 2026-08-01, two weeks ago. No note
   records what came of Ada's second raise. If that landed in a chat or a call,
   the library never saw it. Ask the owner before treating the 2026-06-02 call
   as current.
   ```

5. **Notice when it's stale.** If the answer rests on something months old that later notes
   contradict or complicate, say so. That's the difference between recall and judgment.

6. **Name the gap.** Step 5 is about what's there and conflicting. This is about what's
   missing. End every substantive answer with it.

   Three checks, in this order:

   - **Age.** Search output carries a date on every hit. Read the newest one. If the
     library has been quiet on the topic for weeks, say how long.
   - **Blind channels.** The library only knows what a skill wrote into it. Gmail,
     Google Calendar, Hespia, Fathom (if connected), and whatever the owner captured
     feed it. Chat apps, phone calls, DMs, and hallway conversations do not. If the
     answer plausibly moved through a channel the library can't see, say that. If the
     routines missed days, `bin/brain health --days 30` names them. A dark day is a
     blind spot too.
   - **Structural holes.** A decision with no reasoning. An action with no follow-up
     note. A person named in a meeting who has no file. Run `bin/brain links` on the
     best hit. A dead end there is usually the hole.

   Then write one short paragraph, labelled so the owner can skip it. Be specific:
   name the file that should exist, or the date range that's dark.

   Coverage can also be fine. If it is, say so in a line and move on:

   ```
   Coverage looks current. Last note 2026-08-14, and every action from it is closed out.
   ```

## Rules

- **Never fill a gap with general knowledge.** "The library doesn't have this" is a good
  answer. A confident invention is a catastrophic one. It poisons the thing that makes
  the library trustworthy.
- Distinguish decided from discussed from considered. Never promote a discussion to
  a decision.
- If the library contradicts itself, show both and their dates. Don't pick silently.
- Quote the owner's own words from the note when the exact wording matters.
- **The gap line is not a disclaimer.** "The library may be incomplete" is noise. It's
  true of every answer and tells the owner nothing. Name the missing file, the dark
  date range, or the channel that wasn't watched. If you can't name one, the coverage
  is fine; say so.
- **Never manufacture a gap** to sound careful. A wrong gap sends the owner chasing
  something that doesn't exist, which costs more than saying nothing.
