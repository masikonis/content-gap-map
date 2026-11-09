# Content Gap Map

Commercial buyer questions your site misses.

Your buyers ask hundreds of questions before they contact you: on Google, in AI assistants, in
forums. When your site doesn't answer one, a competitor's page does, or an AI answer built from
it does, and you lose that buyer before you know they existed.

Content Gap Map takes your site and your top competitors, collects the real questions buyers ask,
and shows which questions you answer, which only your competitors answer, and which nobody answers
well. You end with a short list of the pages worth writing next, based on real questions instead
of guesses. Every verdict links to its evidence, so you can check the work.

## What it leaves out, on purpose

**Only questions that lead to a sale count.** That means questions asked while comparing options
("best email automation tools", "Brevo vs MailerLite"), the middle of the funnel, and while
choosing a provider ("Mailchimp pricing", "Mailchimp alternatives"), the bottom. Questions asked
while still learning ("what is email automation"), the top of the funnel, are dropped even when
nobody answers them: AI assistants now answer those directly, so a page written for them rarely
brings a buyer.

**A generic answer doesn't count.** A page answers a question only when it answers in detail and
backs it with proof that can't be faked: case studies, project details, real prices. A page that
says what any competitor or AI answer could say is still a gap.

## How it reads a site

Each site is read at one of three depths, and the report says which one it used:

1. **Sitemap:** which topics each site has a page for. Fast, and enough to find missing pages.
2. **Page outlines:** the same, from each page's title and headings, so it's more reliable.
3. **Passages:** whether each page answers each question in detail and with proof, partly, or not
   at all, with the passage quoted.

It is built for B2B software, service businesses and publishers, and can run on other sites too.
English first; other languages are accepted as input but stay untested until they have their own
test set.

## Progress

Each milestone has to work reliably before the next one is worth building. The public demo is
email marketing software: Mailchimp, with Brevo and MailerLite as competitors.

| Milestone | What it proves | Status on the demo |
|---|---|---|
| 1. Real questions | It collects the questions real buyers ask, not ones a machine made up | Above target: 85% of the commercial questions in Google's "People also ask" found, against 75% ([details](docs/results/milestone-1.md)) |
| 2. Clear topics | It groups them into page-sized topics and keeps only commercial ones | Passed: all three checks (not split, not lumped, right stage) passed two runs in a row, with the phrases grouped three times and a majority vote ([details](docs/results/milestone-2.md)) |
| 3. The right content | It reads your site and competitors' sites, starting with the sitemap | Passed: kept 93% and 92% of the pages Google ranks first for each question, against 90% ([details](docs/results/milestone-3.md)) |
| 4. Honest verdicts | It gives each site the verdict its depth can prove, with the proof | Not started |
| 5. Gaps worth acting on | A short, ranked list of pages worth writing | Not started |

Milestone 1 is scored against a fixed answer key the tool never sees while it runs, and milestone
2 reuses it. AI judgments are checked by a different model, mostly blind, and each results page
says what no person has reviewed. Weak and failed results are published too. One demo run of
milestones 1 to 3 costs about $7.90 at list price, covered by a Claude subscription, and every AI
call is logged.

The choices made so far and why are in [docs/decisions.md](docs/decisions.md); the parts still
open, with their options, are in [docs/architecture.md](docs/architecture.md).

## Run it

You need [uv](https://docs.astral.sh/uv/) and [Claude Code](https://claude.com/claude-code).
Copy `examples/client.example.toml` to `private/<name>/client.toml` and fill it in. The
`private/` folder is never committed. The public demo in `demo/email-marketing/` runs with the same
commands, using `demo/email-marketing` in place of a name.

```
uv run cgm autocomplete <name>   # collect autocomplete suggestions into a new run
uv run cgm brands <name>         # add brand searches to a run collected before they existed
uv run cgm searchconsole <name>  # add your own Search Console exports (see CLAUDE.md)
uv run cgm websearch <name>      # optional: questions people wrote online, checked on the page
uv run cgm predicted <name>      # optional: predicted AI-assistant questions, scored apart
uv run cgm score <name>          # score the run against an answer key in private/<name>/answer-key/
uv run cgm topics <name>         # group the run's buyer phrases into commercial topics
uv run cgm sitemaps <name>       # read every compared site's sitemap into the run
uv run cgm pages <name>          # keep the pages that could answer a commercial buyer
```

## License

MIT
