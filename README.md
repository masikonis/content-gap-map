# Content Gap Map

Commercial buyer questions your site misses.

Your buyers ask hundreds of questions before they contact you: on Google, in AI assistants, in
forums. When your site doesn't answer one, a competitor's page does, or an AI answer built from
it does, and you lose that buyer before you know they existed.

Content Gap Map takes your site and your top competitors, collects the real questions buyers ask,
and shows which questions you answer, which only your competitors answer, and which nobody answers
well. Every verdict links to the evidence behind it, so you can check the work. You end with a
short list of the pages worth writing next, based on real questions instead of guesses.

**It only covers questions that lead to a sale.** That means questions buyers ask while comparing
options ("best email automation tools", "Brevo vs MailerLite"), the middle of the funnel, and while
choosing a provider ("Mailchimp pricing", "Mailchimp alternatives"), the bottom. Questions asked
while still learning about a subject ("what is email automation"), the top of the funnel, are left
out on purpose, even when nobody answers them. AI assistants now answer those directly, so a page
written for them rarely brings a visit, let alone a buyer.

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
2. **Clear topics.** Group the questions that mean the same thing, the way a person would, and keep
   only the ones asked while comparing or choosing.
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

Milestone 2 groups the collected buyer phrases into topics and keeps the commercial ones. A topic
is what one good page would answer, so a page can be matched to it later. On the demo, Claude
tagged 837 of the 1,473 collected phrases as buyer phrases, plain code merged rewordings down to
763, and Claude grouped them into 217 named topics. Claude then marked each topic's funnel stage:
84 comparing and 42 choosing are kept (126 topics, 558 phrases), and 91 learning topics (279
phrases) are dropped, such as "What is a transactional email?". The full list, with each topic's
stage, is in [topics.csv](demo/email-marketing/runs/2026-10-30-0946/topics.csv).

The topics are a working list for the tool, not the result a person reads: the report will rank
them into a short list of the gaps most worth a page. So the number of topics doesn't matter, and
94 of them hold a single phrase. What matters is that each topic is one page's worth and marked
with the right stage, checked three ways on every run:

| Check | Pass mark | Published run | Random grouping |
|---|---|---|---|
| Not split: same-question pairs that share a topic, per question | 85% | **82%** | 1% |
| Not lumped: random topics one page could answer, judged blind | 36 of 40 | 38 | |
| Right stage: random topics where a blind judge agrees on keep or drop | 36 of 40 | 36 | |

**How to read it.** Milestone 2 has not passed yet: it needs every check to pass on two runs in a
row. Lumping and stage pass. Splitting swings around its pass mark from run to run on the same
code and phrases (82% to 88% over the last four runs), because Claude's grouping varies. Where the
stage judge disagreed, it was on small vendor topics, such as "Does Hetzner offer transactional
email?".

**What the checks measure.**
- *Not split* uses the 25 answer-key questions the milestone 1 review marked found, and the
  phrases the judges matched to them (885 pairs). Random grouping into topics of the same sizes
  scores 1%, so the grouping is doing real work.
- *Not lumped:* 40 topics with two or more phrases are picked with a fixed seed, and Claude Fable,
  a different model from the one that grouped them, judges each one from its phrases alone. It
  never sees the names or the scores.
- *Right stage:* 40 topics are picked with a fixed seed, and Claude Fable marks each one's stage
  from its phrases alone, without seeing the first mark. What counts is agreement on keep or drop.

**What is still weak.** Some topics are near-duplicates, such as "What are the best email
automation tools?" next to "What are the best email automation tools and platforms?". Part of the
split score is lost by design: a question about one vendor ("transactional vs marketing email in
HubSpot") keeps its own topic even when the answer-key question it matched was general. No person
has checked the topics.

**How it got here.**
- The first version asked for one question per topic, read strictly, and judged 20 topics. It
  failed (14 of 20), and splitting topics further to satisfy it broke the split check too (12 and
  15 of 20, with 83% and 80%).
- The rule changed to one page per topic, closer to what the next milestone needs, and the sample
  grew to 40 topics to cut the noise. The lump check then passed once (39) and missed once (34),
  with the same lumps recurring.
- A split pass now moves out phrases that a page answering the rest of a topic would not answer.
  The lump check passed on both runs after it. Running the merge pass again after the split fixed
  splitting (89% and 87%) but put the lumps back (29 and 34 of 40), so it was dropped.
- Funnel stage marking came last. Its first check missed by one (35 of 40), every disagreement
  a how-to question about one tool ("how does email automation work in Wix"); those now count as
  learning, since they are support rather than a buying decision.
- The rule and the sample size changed after seeing the results. Claude Fable also reviewed the
  topics twice along the way.

**Cost.** 18 Claude calls, about 4.5 minutes, $0.85 at list price (covered by a Claude
subscription), of which $0.24 is the lump check and $0.20 the stage marking and its check. Every
call is in [trace.jsonl](demo/email-marketing/runs/2026-10-30-0946/trace.jsonl).

## Status

Early. Milestone 1 sits on its target line on the public demo (above). Question collection (Google
autocomplete, and Search Console for your own site) and its scorer are built, with Claude web search
and predicted questions as optional extras. Grouping into commercial topics is built and close to
its target (above). Site reading and the report are not built yet. It is built in public, one step
at a time. The choices made so far and the reasons for them are in
[docs/decisions.md](docs/decisions.md); the parts still open, with their options, are in
[docs/architecture.md](docs/architecture.md).

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
