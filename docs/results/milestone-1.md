# Milestone 1: real questions

[Back to the README](../../README.md)

Milestone 1 asks whether the tool collects the questions real buyers ask, and since the tool
covers only comparing and choosing, it is scored on those commercial questions. The public demo is
email marketing software: Mailchimp, with Brevo and MailerLite as competitors, US English, five
seed phrases (email marketing software, newsletter software, email automation, transactional
email, email marketing for small business).

## Current result: commercial questions (2026-11-02)

| Measure | Result |
|---|---|
| Commercial buyer questions in the answer key that the tool found, after review | **85%** (17 of 20) |
| The same, with the outside model's stage marks | 83% (19 of 23) |
| All buyer questions, any stage, after review | 80% (28 of 35) |
| Automated judges alone on commercial questions, before review | 95% (19 of 20) |
| Target | 75% of commercial questions |

**How to read it.** The result is above the target, but with 20 questions one question moves it
by 5 points, so it is still one market and one snapshot of Google's results.

**What changed since the first result.**
- **Commercial questions only.** Each of the answer key's buyer questions was marked learning,
  comparing or choosing by Claude Sonnet, and again by Claude Fable without seeing the first
  marks. Both are in [stage-tags.csv](../../demo/email-marketing/answer-key/stage-tags.csv). They
  disagree on keep or drop for 3 of 35 questions, such as "Can ChatGPT make a newsletter?"
  (learning for Sonnet, choosing for Fable); the headline uses Sonnet's marks, and Fable's are
  reported beside it. 15 of the 35 buyer questions are learning stage, such as "What is a
  transactional email?". The tool had found 11 of them, so dropping them changes what the
  score means more than the score itself: on the first collection, the commercial share was
  already 75% (15 of 20).
- **Brand searches.** The first collection searched category phrases only, so autocomplete never
  saw "mailchimp pricing". Collection now also searches each compared business's name with
  question words, words such as "pricing", "alternatives" and "vs", and a to z: 162 more requests
  (6 minutes), adding 2,007 unique phrases to the same run, for 3,480 in all. They were collected
  on 2026-11-02, three days after the rest; each row's time is in
  [autocomplete.csv](../../demo/email-marketing/runs/2026-10-30-0946/autocomplete.csv).
- **The review was updated only where a verdict changed.** Four commercial questions were missed
  before and matched now. Claude Fable checked each one, and where it objected, the stricter call
  was kept:

| Question | New match | Verdict |
|---|---|---|
| How much does Mailchimp cost per month? | "mailchimp cost per month" | Found |
| How much is Mailchimp every month? | "how much is mailchimp per month" | Found |
| Is there a better option than Mailchimp? | "mailchimp alternatives" | Still missed: a list of alternatives doesn't say which is better |
| Why are people leaving Mailchimp? | "why is mailchimp so bad" | Still missed: complaints are not the reasons people switch |

  Every change and its reason is in
  [reviewed.csv](../../demo/email-marketing/runs/2026-10-30-0946/reviewed.csv). No person reviewed
  the verdicts.

**What it misses.** Of the three missed commercial questions, two are the strict calls above, and
the third asks which AI is best for creating newsletters.

**Cost.** One full score run: 74 Claude calls, about 830,000 tokens, about 8 minutes of model time,
$3.63 at list price (covered by a Claude subscription). A rerun soon after costs less, because
Claude reuses cached input: the last one cost $0.79. Every call is in
[trace.jsonl](../../demo/email-marketing/runs/2026-10-30-0946/trace.jsonl).

## First published result (2026-10-30)

The first result scored every buyer question, at any stage, against the category searches alone.
It stays here as published.

| Measure | Result |
|---|---|
| Buyer questions in the answer key that the tool found, after review | 74% (26 of 35) |
| The same, counting paraphrased questions once | 75% (24 of 32) |
| Automated judges alone, before review | 71% (68% after removing one wrong match) |
| Target | 75% |

**How to read it (then).** The result sits on the target line, not clearly above it. With 35 questions,
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
