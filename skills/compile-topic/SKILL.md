---
name: compile-topic
description: Build or refresh a topic page in memory/topics/. One page per big theme (pricing, fundraise), summing up what the library knows across every project, meeting, decision and daily note, with every claim linked to its source. Use when the owner asks "where are we on X", asks for a topic page or wiki page, when a theme keeps coming up with no page, and when the Friday review finds a stale topic.
---

# Compile topic

A topic page is the library's answer to "where are we on X", written once and kept
fresh. Without it, every question rebuilds the picture from 20 files.

The page summarises and points. It never becomes the source of truth. A fact lives in
its project, meeting or decision note. The topic page says it in one line and links it.

## When a theme earns a page

- It spans three or more projects, decisions or meetings. Or it came up in five or more
  notes across two or more weeks.
- A project file is enough when the theme is one thread of work. Don't make a topic
  page that only restates one project.
- Keep the set small. Ten live pages that stay fresh beat forty that rot.

## Steps

1. **Find or create the page.**

   ```bash
   bin/brain topics pricing            # exists? what moved since the last compile
   bin/brain new topic "Pricing"       # if not
   ```

   Set `aliases:` to the other words the owner uses for it: `[plans, tiers, price
   increase]`. These are how `bin/brain topics` spots new notes that aren't linked yet.

2. **Gather. Search, don't browse.**

   - First build: `bin/brain search` on the title and every alias. Then `--type decision`,
     `--type meeting`, `--type project` for each. `--loose` for question-shaped words.
     Three or more phrasings. One query is not a search.
   - `bin/brain links` on each project and decision you find. The answer is often one hop
     away.
   - `bin/brain who` for the two or three people who matter most here.
   - Refresh: `bin/brain topics <slug>` lists the changed sources and the new unlinked
     mentions. Read those, plus the page as it stands. Rebuild from scratch only when
     more than half the sources moved.

   Read the notes you will cite. Search snippets are not enough to summarise from.

3. **Write each section.** Follow the template's prompts. Rules for every section:

   - **Every bullet ends with a link.** `[[projects/new-pricing]]`. A claim with
     no link does not go on the page.
   - **Newest truth wins.** When two notes disagree, the page says what's true now and
     names the older view in Timeline, both dated.
   - **Decided, discussed, considered are different.** Never promote a discussion to a
     decision. "What we decided" holds only things someone decided.
   - **Mark a guess as a guess** in "What we believe". Say what evidence would settle it.
   - **Compress.** One line per point. If the owner needs detail, the link has it.
   - **Sensitive content: the fact, not the detail.** Same rule as CLAUDE.md. Comp,
     legal, health and personnel numbers stay in their source, or out of the library.

4. **Write the gaps. This is how the library grows.** For each thing the page should
   know but can't, name where the answer lives:

   ```
   - No decision file for the new tier's price. Said in the 2026-09-18 call
     with Ada. Write it as a decision. [[meetings/2026-09-18-ada-pricing]]
   - Nothing on how Vendor X prices. Capture their pricing page with Firecrawl.
   - Whether Grace agreed to the new tier. Ask the owner.
   ```

   A gap that names a meeting or a note: fix it now if it takes under five minutes
   (write the decision file, link the person). The rest stay on the page. The Friday
   review reads them.

5. **Link the new mentions.** Every note from `bin/brain topics <slug>` under "new" that
   really belongs gets cited on the page. The ones that just use the word don't.

6. **Stamp it.** Set `compiled:` to today. Add a line to `## Compile log`:
   `- 2026-09-23: refreshed from 4 changed sources and 2 new mentions. 3 gaps open.`

7. **Check.**

   ```bash
   bin/brain lint --path memory/topics/pricing.md   # zero em dashes
   bin/brain topics pricing                         # 0 changed, 0 new
   bin/brain lint --structure | grep topics/        # no dangling links from the page
   ```

8. **Confirm in one line**: which page, how many sources, how many gaps.

## Reading a topic page

The recall skill reads the topic page first for orientation. Then it opens the linked
sources for anything it will cite. An answer cites the source note, not the topic page.
If `bin/brain topics` shows the page stale, say so, or refresh it first.

## Rules

- One theme, one page. Search `memory/topics/` before creating. Merge, don't fork.
- Never delete a topic page. A dead theme gets `status: done` in frontmatter and a last
  line in the compile log. `bin/brain retire` if it truly must go.
- Never fill the page from general knowledge. If the library has nothing on a section,
  the section says so and the gap names where to look.
- No em dashes. Short sentences. The owner reads these pages fast or not at all.
