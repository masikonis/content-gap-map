# Milestone 2: clear, commercial topics

[Back to the README](../../README.md)

Milestone 2 groups the collected buyer phrases into topics and keeps the commercial ones. A topic
is what one good page would answer, so a page can be matched to it later. On the demo, Claude
tagged 837 of the 1,473 collected phrases as buyer phrases, plain code merged rewordings down to
763, and Claude grouped them into 217 named topics. Claude then marked each topic's funnel stage:
84 comparing and 42 choosing are kept (126 topics, 558 phrases), and 91 learning topics (279
phrases) are dropped, such as "What is a transactional email?". The full list, with each topic's
stage, is in [topics.csv](../../demo/email-marketing/runs/2026-10-30-0946/topics.csv).

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
call is in [trace.jsonl](../../demo/email-marketing/runs/2026-10-30-0946/trace.jsonl).
