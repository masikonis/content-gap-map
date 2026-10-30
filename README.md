# Content Gap Map

Buyer questions your site misses.

Your buyers ask hundreds of questions before they contact you: on Google, in AI assistants, in
forums. When your site doesn't answer one, a competitor's page does, or an AI answer built from
it does, and you lose that buyer before you know they existed.

Content Gap Map takes your site and your top competitors, collects the real questions buyers ask,
and shows which questions you answer, which only your competitors answer, and which nobody answers
well. Every verdict links to the evidence behind it, so you can check the work. You end with a
short list of the pages worth writing next, based on real questions instead of guesses.

It reads each site at one of three depths, and the report says which one it used:

1. **Sitemap:** which topics each site has a page for, and which it has none for. Fast, and
   enough to find the clearest gaps.
2. **Page outlines:** the same, from each page's title and headings, so it's more reliable.
3. **Passages:** whether each page actually answers each question, partly answers it or misses
   it, with the passage quoted.

It is built for B2B software, service businesses and publishers, and can run on other sites too.
English first; other languages are accepted as input but stay untested until they have their
own test set.

## How we'll know it works

Success comes in milestones. Each one has to work reliably before the next one is worth building:

1. **Real questions.** Collect the questions real buyers ask, not ones a machine made up.
2. **Clear topics.** Group the questions that mean the same thing, the way a person would.
3. **The right content.** Read your site and your competitors' sites at each depth, starting with
   the sitemap, and keep what could answer a buyer.
4. **Honest verdicts.** Give each site the verdict its depth can prove, and show the proof.
5. **Gaps worth acting on.** A short list of missing answers that a person agrees are real and
   worth a page.

Each milestone is checked against a fixed test set that the tool never sees while it runs, with a
person reviewing the cases where the checks disagree. The scores, cost and run time are published
here.

## First result: milestone 1 on a public demo

Milestone 1 asks whether the tool collects the questions real buyers ask. The public demo is email
marketing software: Mailchimp, with Brevo and MailerLite as competitors, US English, five seed
phrases (email marketing software, newsletter software, email automation, transactional email,
email marketing for small business).

| Measure | Result |
|---|---|
| Buyer questions in the answer key that the tool found, after review | **74%** (26 of 35) |
| The same, counting paraphrased questions once | **75%** (24 of 32) |
| Automated judges alone, before review | 71% (68% after removing one wrong match) |
| Target | 75% |

**How to read it.** The result sits on the target line, not clearly above it. With 35 questions,
the honest range is roughly 60% to 90%, so this is one encouraging data point, not proof. It is one
run, on one market, against one snapshot of Google's results.

**What was measured.** The tool collected 1,473 unique Google autocomplete phrases (305 requests, 11
minutes). The answer key is the 57 unique questions in Google's "People also ask" box for the same
seeds, collected on 2026-10-30 in a real Chrome session, signed in to Google and set to US English,
so the results may be personalised. 35 of them are buyer questions: ones a person asks while
choosing, buying or switching email software, including whether the channel is worth it and which
tools to compare. The rest, such as "What is the 12 second rule for emails?", are left out.

**How it was checked.**
- The setup and answer key were committed before the run
  ([994fa80](https://github.com/masikonis/content-gap-map/commit/994fa80)). One earlier attempt
  crashed on a text-encoding bug and was thrown away
  ([5bd92e1](https://github.com/masikonis/content-gap-map/commit/5bd92e1)); the raw result was
  committed before any review ([700be12](https://github.com/masikonis/content-gap-map/commit/700be12)).
- Two AI judges (Claude Sonnet twice, Claude Opus once) decided which questions were found. A match
  means one answer would satisfy both the question and the collected phrase.
- Claude then reviewed every buyer tag and verdict against the full list of collected phrases, and
  two outside models, Claude Fable and OpenAI Codex, checked each change. Where either one objected,
  the stricter call was kept. No person reviewed the verdicts. Every change and its evidence is in
  [reviewed.csv](demo/email-marketing/runs/2026-10-30-0946/reviewed.csv).
- The method was developed on two earlier private tests. This answer key was not used to develop it.

**What it misses.** Four of the nine missed questions name Mailchimp ("How much does Mailchimp cost
per month?", "Why are people leaving Mailchimp?"). The seeds were category phrases, so autocomplete
never saw "mailchimp pricing". The other five ask about other tools (Word, ChatGPT, AI writers), the
easiest way to create a newsletter, and whether email marketing is declining.

**Flaws the reviews found, and what changed.** The shortlist that picks phrases for the judges was
keyed on each seed's rarest word, which for two seeds was generic ("software", "business"), so it
dropped two clear matches such as "cheapest email marketing"; it now also adds the 100 phrases
closest to each question. A word-matching bug split plurals from singulars ("prices" from "price");
it is fixed. And the predicted questions were in the phrase pool when the published score was
computed, where they could crowd out real phrases; the headline is now judged on real phrases only.
After these fixes the shortlist keeps every reviewed match. Rescored with all of them, the judges
agree with the reviewed verdicts on 32 to 33 of the 35 buyer questions and read 80 to 83% on their
own; the differences are the borderline calls where the review chose the stricter answer. The
published 74% stays the reviewed figure.

**Cost.** 42 Claude calls, about 290,000 tokens, under 5 minutes of model time, $1.42 at list price
(covered by a Claude subscription). Every call is in
[trace.jsonl](demo/email-marketing/runs/2026-10-30-0946/first-score/trace.jsonl).

## Second result: milestone 2 on the public demo

Milestone 2 groups the collected buyer phrases into topics, one topic per question a buyer wants
answered. On the demo, Claude tagged 837 of the 1,473 collected phrases as buyer phrases, plain
code merged rewordings down to 761, and Claude grouped them into 131 named topics, such as "What
is the best newsletter software?" (46 phrases) or "How much does transactional email cost?" (21).
The full list is in [topics.csv](demo/email-marketing/runs/2026-10-30-0946/topics.csv).

| Measure | Result | Random grouping |
|---|---|---|
| Phrase pairs matched to the same answer-key question that share a topic | **91%** | 2% |
| The same, averaged per question | **88%** | 2% |
| Phrase pairs matched to different questions that are kept apart | 99.7% | 98.2% |

**How to read it.** The test pairs come from the judges' matches on the 25 questions the milestone
1 review marked found (890 same-question pairs). Random grouping into topics of the same sizes is
the baseline: the first two rows are far above it, so the grouping is doing real work. The third
row is not: random grouping keeps almost every pair apart too, so it can't show lumping. No target
is set for milestone 2 yet, and no person checked the topics.

**What is still weak.** 33 topics hold a single phrase. "Which tools exist" and "which tool is
best" are still separate topics. Claude's last check flags 12 topic pairs as possible duplicates.
Buyer tagging varies a little between runs: two runs on the same phrases gave 820 and 837.

**How it was checked.** Claude Fable reviewed the topics twice. The first review found merged
topics that lumped unrelated questions, the same question split across several topics, names that
were not questions, junk such as bare prices, and a pair test with no baseline. Each was fixed and
the demo rerun; the second review judged the topics fit for matching to pages.

**Cost.** 14 Claude calls, about 4.5 minutes, $0.55 at list price (covered by a Claude
subscription). Every call is in [trace.jsonl](demo/email-marketing/runs/2026-10-30-0946/trace.jsonl).

## Status

Early. Milestone 1 sits on its target line on the public demo (above). Question collection (Google
autocomplete, and Search Console for your own site) and its scorer are built, with Claude web search
and predicted questions as optional extras, and grouping into topics works (above). Site reading and
the report are not built yet. It is built in public, one step at a time. The choices made so far and
the reasons for them are in [docs/decisions.md](docs/decisions.md); the parts still open, with their
options, are in [docs/architecture.md](docs/architecture.md).

## Run it

You need [uv](https://docs.astral.sh/uv/) and [Claude Code](https://claude.com/claude-code).
Copy `examples/client.example.toml` to `private/<name>/client.toml` and fill it in. The
`private/` folder is never committed. The public demo in `demo/email-marketing/` runs with the same
commands, using `demo/email-marketing` in place of a name.

```
uv run cgm autocomplete <name>   # collect autocomplete suggestions into a new run
uv run cgm searchconsole <name>  # add your own Search Console exports (see CLAUDE.md)
uv run cgm websearch <name>      # optional: questions people wrote online, checked on the page
uv run cgm predicted <name>      # optional: predicted AI-assistant questions, scored apart
uv run cgm score <name>          # score the run against an answer key in private/<name>/answer-key/
uv run cgm topics <name>         # group the run's buyer phrases into topics
```

## License

MIT
