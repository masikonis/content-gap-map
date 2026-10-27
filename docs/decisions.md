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

## 2026-10-23: "Services" means service businesses

**Chose:** the services profile is for businesses that sell a service to local or individual
customers: an exterior cleaning company, a law firm, a language school.

**Alternatives:** professional B2B services such as agencies and consultancies.

**Why:** these businesses get many buyer questions (price, process, trust, area served) that
their sites often don't answer, and they are a large share of the sites this tool will be run on.
B2B agencies can use the B2B software profile or the generic one.

## 2026-10-23: English by default, any language as an input

**Chose:** language and country are inputs to every run, with English as the default. Each run
uses one language. Other languages run but are marked untested until they have their own test set.

**Alternatives:** English only; claim every language works from the start.

**Why:** the AI models and data sources handle many languages, so blocking them costs nothing.
Claiming they work would need a labelled test set per language, which we don't have yet.

## 2026-10-27: Milestone 1 is proven against a hand-collected answer key

**Chose:** milestone 1 ("real questions") counts as done when an automated collector finds the
questions in an answer key collected by hand. The answer key has two parts: Google's "People also
ask" questions for each seed, collected in a browser by a person, and the question-shaped searches
from the site's own Search Console. The score is the share of answer-key questions the collector
finds, matched by meaning rather than exact words. The target is set after the first scored run.

**Alternatives:** no answer key, judging the collector's output by reading it; Search Console
alone, which is free and already collected but only covers searches where the site already
appears, so it is blind to the gaps the tool is meant to find.

**Why:** "it works" needs a number, and every later milestone stands on this one. "People also
ask" is the closest public view of what buyers ask, but it can't be collected automatically
within Google's rules, which makes it a good independent test of any collector we can automate.
