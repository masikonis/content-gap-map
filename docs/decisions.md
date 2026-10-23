# Decisions

Newest last. Each entry: what we chose, the alternatives, and why.

## 2026-10-23: "Answered" has three levels

**Chose:** each question gets one of three verdicts per site: answered, partly answered, or not
answered, with the URL and passage as evidence.

**Alternatives:** yes or no; a score from 0 to 100.

**Why:** "partly" is the most useful case, because it means improving an existing page rather
than writing a new one. Yes or no hides it. A 0 to 100 score looks precise, but a person can't
label it consistently, so we couldn't test it.

## 2026-10-23: Site types are profiles, with a generic fallback

**Chose:** version one targets B2B software, services and publishers. Each site type is a small
profile that the core reads; any other site runs on a generic profile that works, but less well.
Adding a site type means adding one profile, not changing the core.

**Alternatives:** one site type only (the simplest start); one generic approach for every site.

**Why:** buyers on these sites ask different kinds of questions and get answers on different kinds
of pages, so treating them alike gives weaker results. Keeping the differences in profiles keeps
the core small and makes new types cheap to add.
