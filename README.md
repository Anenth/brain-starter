# brain

A personal intelligence. A library you own, procedures you wrote, agents that run them.
On your infra, in your repo, under your keys.

Every weekday morning it reads your calendar and mail, writes a brief, and posts the few
things that need you as cards on your **Hespia** Tasks page. You tap to accept a task,
answer a question, or approve a reply. The evening run carries out what you approved and
closes what you finished.

**New here? Start with [SETUP.md](SETUP.md).** About 15 minutes.

## How it works

```
            Gmail · Calendar · Fathom · Hespia
                          │
                      skills/            ← procedures, in markdown
                          │
                      memory/            ← the library. plain markdown. yours.
                          │
                     bin/brain           ← the exact layer. search, links, dates.
                          │
                Hespia Tasks page        ← where you act on it
```

Three ideas hold it up:

1. **Memory is files.** Markdown in git. No database you can't read, no service that can
   revoke it. If this repo survives, the intelligence survives.
2. **Judgment is latent, facts are deterministic.** The model decides what matters; SQLite
   decides what exists. Never the other way round.
3. **Work becomes skills.** Anything done twice by hand gets written down as a procedure,
   and the system gets permanently better at it. That loop is the whole point.

## Day to day

```bash
bin/brain config                        # is brain.json filled in
bin/brain status                        # what the library holds
bin/brain new person "Ada Lovelace"     # add someone
bin/brain search "pricing timeline"     # ask it something
bin/brain who "ada"                     # everything about a person
bin/brain health                        # did the routines run
```

Then, in a Claude Code session in this repo:

- **"bootstrap my library"**: backfill 90 days from calendar, mail and Fathom
- **"morning brief"**: the day, with context already attached
- **"prep me for the 2pm"**: who's in the room and what you owe them
- **"what did we decide about pricing?"**: recall, with citations
- **"make that a skill"**: so it never has to be figured out again

## Layout

| Path | What |
|---|---|
| `brain.json` | who this library belongs to: name, email, timezone, Hespia org |
| `CLAUDE.md` | how the agent behaves in this repo |
| `memory/` | the library: people, meetings, decisions, projects, daily notes |
| `skills/` | executable procedures. If a smart intern could follow it, an agent can run it |
| `bin/brain` | search, indexing, templates, the link graph. Python 3, no dependencies |
| `templates/` | the shape of each note type |
| `routines/` | what runs unattended, and how to wire it |
| `tests/` | `python3 tests/test_close.py` and friends |

## The one thing that makes it compound

Write down the decisions **with the reasoning**. Not what was decided. Why, what was
rejected, and what would change your mind. In six months that file is the only thing
standing between you and re-litigating a settled question. Everything else here is
plumbing for that.

Built after Garry Tan's ["Own Your Intelligence"](https://www.ycrootaccess.com/p/garry-tan-own-your-intelligence).
