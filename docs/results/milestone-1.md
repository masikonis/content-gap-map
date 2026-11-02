# Milestone 1: real questions

[Back to the README](../../README.md)

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
tools to compare. The rest, such as "What is the 12 second rule for emails?", are left out. Milestone 1 measures
collection, so it counts buyer questions at every stage; learning-stage topics are dropped later,
at milestone 2.

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
  [reviewed.csv](../../demo/email-marketing/runs/2026-10-30-0946/reviewed.csv).
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
[trace.jsonl](../../demo/email-marketing/runs/2026-10-30-0946/first-score/trace.jsonl).
