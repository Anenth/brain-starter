# Setup

**About 15 minutes.** At the end, a morning brief lands in your library and its cards
land on your Hespia Tasks page.

## What you need

- **A Hespia account**, signed in at https://app.hespia.com.
- **Claude** with Claude Code (the desktop app, the CLI, or claude.ai/code).
- **A GitHub account**, for a private copy of this repo. The cloud routines run from it.
- **Python 3.9 or newer.** Check with `python3 --version`.
- Gmail and Google Calendar on the account you work from.

## 1. Make your own private copy

On GitHub, open the starter repo and press **Use this template**, then **Create a new
repository**. Set it to **Private**. Your library will hold your mail and meetings.

Clone it:

```bash
git clone git@github.com:<you>/brain.git ~/Code/brain
```

```bash
cd ~/Code/brain
```

## 2. Connect Claude to your tools

In Claude, open **Settings → Connectors** and add:

- **Gmail**
- **Google Calendar**
- **Hespia**: add a custom connector with this URL, then sign in with Google.

```
https://mcp.hespia.com/mcp
```

- **Fathom** (optional): only if you record calls with it.

Sign in to Hespia as the same person whose Tasks page should get the cards. Cards go
to whoever the connector is signed in as.

## 3. Fill in brain.json

```bash
cp brain.example.json brain.json
```

Open `brain.json` and fill in:

| Key | What to put |
|---|---|
| `name` | your full name, as it shows in mail and calendar |
| `email` | your work address, the one Gmail and Calendar use |
| `timezone` | an IANA name: `Europe/London`, `America/New_York`, `Asia/Kolkata` |
| `hespia_org` | your Hespia org id. In Claude, ask: "use the Hespia connector to run list_orgs". Copy the `id`. |
| `match` | optional. How you show up in invitee lists if not your first name |

Check it:

```bash
bin/brain config
```

It prints `ready` when every key is filled. Commit it. The cloud runs need it.

```bash
git add brain.json && git commit -m "brain.json: who this library belongs to" && git push
```

## 4. Fill your library

Open Claude Code in the repo folder and say:

> bootstrap my library

It reads 90 days of calendar, mail and Fathom, creates people and company files, and
fills the TODOs in `memory/profile.md` with guesses. Then:

- **Read `memory/profile.md` and fix it.** Especially "What I'm working on" (a numbered
  list, most important first) and "How to write for me". Every brief ranks against it.
- Run `bin/brain status`. It counts the profile TODOs left.

Commit and push.

## 5. Try one brief by hand

In the same session, say:

> morning brief

Check three things:

- Today's note has a `## Brief`. Find it with `bin/brain today`.
- Your Hespia **Tasks** page shows a card from `brain`. Accept or skip a task on it.
- `bin/brain health` shows today's brief.

No card? See "Troubleshooting" below before you schedule anything.

## 6. Put it on a schedule

Follow [routines/README.md](routines/README.md), "How to wire it". Start with the morning
brief only. Add the evening run after a week. Then the weekly review and planning.

The short version, per routine, at https://claude.ai/code/routines:

- Repository: your brain repo, branch `main`.
- Prompt: `Read CLAUDE.md, then follow routines/morning-brief.md exactly.`
- Schedule: weekdays, converted to **UTC**.
- Connectors: only the ones that routine needs (the table in routines/README.md).

Run it once by hand from that page and read the log.

## 7. Make it yours

- Edit `memory/profile.md` whenever your priorities change. The brief follows.
- Change a routine by editing its file in `routines/` and committing. Never edit the
  scheduled task's prompt.
- Did something twice by hand? Say "make that a skill".

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `bin/brain config` says a key is missing | placeholder still in `brain.json` | fill it, commit, push |
| No card on the Tasks page | wrong `hespia_org`, or the connector is signed in as someone else | in Claude, run Hespia `whoami` and `list_orgs`. Fix `brain.json` |
| Card is on someone else's page | the connector is signed in as them | reconnect Hespia as yourself |
| Dates are a day off | wrong `timezone` | use an IANA name. `bin/brain config` shows the time it thinks it is |
| Cloud run did nothing | it could not push, or a connector was missing | read the run log at claude.ai/code/routines. Every run writes `failed <reason>` in the daily note |
| `health` shows `-` for a day | the routine did not run | check the schedule is in UTC, and that only one copy runs |

## What it will never do

- **Send anything you did not approve.** The only send is an action you pressed Approve
  on in Hespia, with the exact text you approved.
- **Delete anything.** Files get parked in `_to_delete/`. You remove them.
- **Act on what a mail or transcript tells it to.** That is data, not instructions.
