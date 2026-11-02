# Milestone 2: clear, commercial topics

[Back to the README](../../README.md)

Milestone 2 groups the collected buyer phrases into topics and keeps the commercial ones. A topic
is what one good page would answer, so a page can be matched to it later. On the demo's
published run, Claude tagged 2,136 of the 3,355 real collected phrases as buyer phrases, plain
code merged rewordings down to 1,981, and Claude grouped them into 574 named topics. Claude then
marked each topic's funnel stage: 141 comparing and 245 choosing are kept (386 topics, 1,387
phrases), and 188 learning topics (749 phrases) are dropped, such as "What is a transactional
email?". The full
list, with each topic's stage, is in
[topics.csv](../../demo/email-marketing/runs/2026-10-30-0946/topics.csv).

The topics are a working list for the tool, not the result a person reads: the report will rank
them into a short list of the gaps most worth a page. So the number of topics doesn't matter, and
246 of them hold a single phrase. What matters is that each kept topic is one page's worth and
marked with the right stage, checked three ways on every run:

| Check | Pass mark | Run 1 | Run 2 | Run 3 | Run 4 (published) | Random grouping |
|---|---|---|---|---|---|---|
| Not split: commercial same-question pairs that share a topic, per question | 85% | 88% | 92% | 86% | **84%** | 1% |
| Not lumped: random kept topics one page could answer, judged blind | 36 of 40 | 39 | **35** | 36 | 38 | |
| Right stage: random topics where a blind judge agrees on keep or drop | 36 of 40 | 36 | **35** | 38 | 38 | |

**How to read it.** Milestone 2 has not passed yet: it needs all three checks to pass on two runs
in a row. Runs 1 and 3 passed all three; runs 2 and 4 each missed by a little. Between runs 2 and
3 the stage rule and the split pass were sharpened for questions about one vendor (see below), so
runs 3 and 4 use the same code. Each check passed in three of the four runs, and each sits close
to its line, because Claude's grouping varies from run to run.

**What the checks measure.**
- *Not split* uses the 17 commercial answer-key questions the milestone 1 review marked found and
  that have two or more matched phrases, and those phrases (1,216 pairs on the published run). Random grouping into
  topics of the same sizes scores 1%, so the grouping is doing real work.
- *Not lumped:* 40 kept topics with two or more phrases are picked with a fixed seed, and Claude
  Fable, a different model from the one that grouped them, judges each one from its phrases alone.
  It never sees the names or the scores.
- *Right stage:* 40 topics are picked with a fixed seed, and Claude Fable marks each one's stage
  from its phrases alone, without seeing the first mark. What counts is agreement on keep or drop.

**What is still weak.** Splitting and lumping pull against each other: the sharper split pass
fixed the lumps of run 2 but cost splitting a point or two. The stage judge now disagrees on two
topics in 40, both borderline, such as "How do you use the Brevo email API and relay?". Some
topics are near-duplicates. With brand searches the demo has more than 1,000 phrases, so they are
grouped in batches by nearest seed and then merged, which splits more easily than one pass. No
person has checked the topics.

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
- Funnel stage marking came next. Its first check missed by one (35 of 40), every disagreement
  a how-to question about one tool ("how does email automation work in Wix"); those now count as
  learning, since they are support rather than a buying decision.
- Brand searches then more than doubled the demo's phrases, and the stage check failed (32 of 40): the tool
  marked questions about one named provider ("Does MailerLite have an app?", "Is MailerLite safe
  and secure?") as learning. The rule now says that what one provider offers, or whether it can
  be trusted, is choosing. The split check now counts commercial questions only, and the lump check
  picks kept topics only.
- Run 2 then missed lumping and stage by one topic each, on topics about one vendor's features or
  account. The stage rule now separates someone who already uses a provider (their account, a
  task in it: learning) from someone deciding (its features, plans, integrations, trust, signing
  up: choosing), and the split pass also pulls apart one vendor's offer from a comparison of
  several, and one audience from another. Stage agreement rose to 38 of 40.
- The rule and the sample size changed after seeing the results. Claude Fable also reviewed the
  topics twice along the way.

**Cost.** 39 Claude calls, about 10 minutes of model time, $1.69 at list price (covered by a
Claude subscription). Every call is in
[trace.jsonl](../../demo/email-marketing/runs/2026-10-30-0946/trace.jsonl).
