# Decisions

The current decisions about the tool. Each entry: what we chose, the alternatives, and why. When a
decision changes, its entry is rewritten, so this page always shows the current state.

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
customers: a plumber, a law firm, a language school.

**Alternatives:** professional B2B services such as agencies and consultancies.

**Why:** these businesses get many buyer questions (price, process, trust, area served) that
their sites often don't answer, and they are a large share of the sites this tool will be run on.
B2B agencies can use the B2B software profile or the generic one.

## 2026-10-23: English by default, any language as an input

**Chose:** language and country are inputs to every run, with English as the default. Each run
uses one language. Other languages are accepted but marked untested until they have their own
test set.

**Alternatives:** English only; claim every language works from the start.

**Why:** the AI models and data sources handle many languages, so blocking them costs nothing.
Claiming they work would need a test set per language, which we don't have yet.

## 2026-10-23: Free software and data only; AI through Claude Code

**Chose:** every library, data source and service is free and open. Judgment steps run through
Claude Code on an existing subscription.

**Alternatives:** paid search data APIs (DataForSEO, SerpApi); paid model APIs; local open-weight
models.

**Why:** this is a lab experiment, and a tool anyone can run shouldn't need paid accounts. Claude
Code gives a strong model with structured output and usage reporting at no extra cost. Local models
strong enough to judge answers need far more memory than a typical laptop has.

## 2026-10-23: One file per client; client data never leaves a private folder

**Chose:** each client is one file holding its primary site, any number of competitors, its
language, country, site type and seeds. Everything that belongs to a client (that file, crawls,
traces, labels, reports and its own decisions) lives in a gitignored `private/<client>/` folder.
A public template is in `examples/client.example.toml`.

**Alternatives:** a separate private repository for client data; site lists in environment files.

**Why:** one folder per client makes adding clients trivial, and keeping it all out of git means
nothing about a client can be published by accident. A separate repository would add a second
place to keep in sync, and environment files suit secrets, not lists of sites.

## 2026-10-27: Milestone 1 is proven against "People also ask" collected by hand

**Chose:** milestone 1 ("real questions") counts as done when an automated collector finds the
questions in an answer key: Google's "People also ask" questions for each seed, collected in a
browser by a person. The score is the share of answer-key questions the collector finds, matched
by meaning rather than exact words. The target is set after the first scored run.

**Alternatives:** no answer key, judging the collector's output by reading it; the site's own
Search Console searches as the answer key.

**Why:** "it works" needs a number, and every later milestone stands on this one. "People also
ask" is the closest public view of what buyers ask, and it can't be collected automatically within
Google's rules, so no source the collector uses can see it. That keeps the test independent.
Search Console fails that test, because the collector uses it as a source, and it only covers
searches where the site already appears.

## 2026-10-27: The first collector uses autocomplete, Search Console and Claude web search

**Chose:** three sources, combined:
- **Google autocomplete,** each seed expanded with question words and a to z. Plain code, close to
  what people type, about the same result every run.
- **Search Console,** through its API, for sites we have access to. The best real demand data,
  including questions typed by AI assistants.
- **Claude web search,** for questions people wrote out in full on forums, Q&A pages and articles,
  each kept with its URL.

**Alternatives:** Bing autocomplete; the Stack Exchange and Hacker News APIs; the WildChat dataset
of real AI chats; Google driven through a browser; questions written by Claude and kept only if
autocomplete confirms them. Ruled out: scraping "People also ask" (Google's robots.txt disallows
it), Reddit (closed to new developers), Quora and review sites (their terms forbid scraping), and
paid search data APIs.

**Why:** together they cover what people search for and how they phrase it in their own words,
which is roughly what "People also ask" combines. Each run reports what every source found and
which questions only one of them found, so a source that adds nothing gets cut. The alternatives
wait until the score shows something missing.

## 2026-10-27: The backend is Python, managed with uv

**Chose:** the pipeline is written in Python. uv manages the Python version, the packages and the
lock file.

**Alternatives:** TypeScript end to end; pip with venv; Poetry.

**Why:** the hard parts still ahead, pulling the main text out of pages and grouping questions,
have their strongest libraries in Python (trafilatura, scikit-learn). Starting there costs less
than switching halfway. The frontend only reads a results file, so a second language stays at
arm's length. uv is one fast tool for everything Python needs; it is now owned by OpenAI, but it
stays open source and the project file is standard, so leaving it is easy.

## 2026-10-27: How the autocomplete collector works

**Chose:**
- **Format:** Google's "chrome" autocomplete format, which returns 15 suggestions per request,
  each with a relevance score.
- **Expansion:** each seed alone, with question words before and after it ("how much …",
  "… cost", "… vs"), and with a to z after it. About 55 requests per seed. Results are not
  expanded again.
- **Pace and identity:** one request every 2 seconds, an honest crawler name with a link to this
  repository, backing off when asked to slow down, and stopping with a "blocked" report rather
  than working around a block.
- **Raw collection:** every suggestion is saved. Filtering for questions, buyer intent and
  location is a separate later step.
- **Output:** one folder per run in the client's private folder, holding a CSV with one row per
  suggestion (seed, query sent, suggestion, rank, relevance, time) and Google's raw replies.
- **Running it:** one command, `uv run cgm autocomplete <client>`, which later steps join as
  sub-commands.

**Alternatives:** the "firefox" format (10 suggestions, no scores); the seed alone, or question
words without a to z; expanding the best suggestions again; faster requests or a browser-like
identity; filtering while collecting; JSON lines instead of CSV; a standalone script.

**Why:** more suggestions per request means fewer requests. A to z expansion is the standard way
to reach the long tail, and about 450 requests for 8 seeds is still small. Polite, honest
requests are a lab rule, and a block is reported rather than hidden. Keeping the raw data means a
bad filter can't silently drop real questions. CSV matches the answer key and opens anywhere. A
single command keeps every step of the tool in one place. Two test calls showed that the country
setting is only a hint: suggestions for other countries come back too, so location filtering
belongs in the later filtering step.
