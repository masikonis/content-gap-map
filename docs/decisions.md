# Decisions

The current decisions about the tool. Each entry: what we chose, the alternatives, and why. When a
decision changes, its entry is rewritten, so this page always shows the current state.

## 2026-10-23: "Answered" has three levels

**Chose:** when the tool reads a site's full passages, each question gets one of three verdicts
per site: answered, partly answered, or not answered, with the URL and passage as evidence. At
lighter reading depths the verdict is topic-level (see the next entry).

**Alternatives:** yes or no; a score from 0 to 100.

**Why:** "partly" is the most useful case, because it means improving an existing page rather
than writing a new one. Yes or no hides it. A 0 to 100 score looks precise, but a person can't
label it consistently, so we couldn't test it.

## 2026-10-28: Sites are read in rungs, starting with the sitemap

**Chose:** the same pipeline reads a site at one of three depths, and each depth earns a stronger
verdict:

| Rung | Reads | Verdict |
|---|---|---|
| 1. Sitemap | Page addresses | Has a page on this topic, or no page |
| 2. Page outlines | Each page's title, description and headings | The same, more reliable |
| 3. Passages | The page text | Answered, partly answered or not, with the quote |

The first version runs at rung 1 only. Every report states the rung it ran at. Matching topics to
page addresses is a judgment step, done by Claude.

**Alternatives:** read full passages from the start; a sitemap-only tool that claims "answered".

**Why:** a sitemap gives a working report within seconds per site, and "no page on this topic" is
already a reliable, useful gap. Each later rung adds to the same report instead of replacing it.
A page address can show that a site covers a topic but not that it answers a question, so the
stronger verdict waits for the rung that can prove it. Sites with unreadable addresses (such as
`/?p=123`) need rung 2 straight away.

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

## 2026-10-27: Milestone 1 is proven against a "People also ask" answer key

**Chose:** milestone 1 ("real questions") counts as done when an automated collector finds the
questions in an answer key: Google's "People also ask" questions for each seed. The key is
collected once per test client in a real browser session, one search at a time, by Claude in
Nerijus's Chrome, never by the tool itself. Questions that appear under several seeds count once.
Each question is tagged as a buyer question or not, and the headline score is the share of buyer
questions the collector finds, matched by meaning rather than exact words, with the share of all
questions reported next to it. The target is set once the scorer itself has been checked.

**Alternatives:** no answer key, judging the collector's output by reading it; the site's own
Search Console searches as the answer key; scoring all questions alike.

**Why:** "it works" needs a number, and every later milestone stands on this one. "People also
ask" is the closest public view of what buyers ask, and none of the collector's sources can see
it, which keeps the test independent. Search Console fails that test, because the collector uses
it as a source, and it only covers searches where the site already appears. About one in five
"People also ask" questions are not from buyers (do-it-yourself tips, or other businesses pricing
their own work), and the tool filters those out anyway, so counting them would blur the number
that matters.

## 2026-10-28: The collector uses autocomplete and Search Console; web search is optional

**Chose:** two sources run by default:
- **Google autocomplete,** each seed expanded with question words and a to z. Plain code, close to
  what people type, about the same result every run.
- **Search Console,** through its API, for sites we have access to. The best real demand data,
  including questions typed by AI assistants.

**Claude web search** stays as an optional step (`cgm websearch`), off by default: it finds
questions people wrote out in full, each verified on its page.

**Alternatives:** web search on by default; cutting web search entirely; Bing autocomplete; the
Stack Exchange and Hacker News APIs; the WildChat dataset of real AI chats; Google driven through
a browser; questions written by Claude and kept only if autocomplete confirms them. Ruled out:
scraping "People also ask" (Google's robots.txt disallows it), Reddit (closed to new developers),
Quora and review sites (their terms forbid scraping), and paid search data APIs.

**Why:** a source has to earn its place in the score. On the first scored test, autocomplete alone
found 73% of the answer key's buyer questions. Web search, limited to pages that can be verified,
added one more question while using about three times the rest of the run. Its questions are real
but mostly not the ones Google shows, which the answer key can't credit, so it is kept for trying
on other clients rather than cut. The other alternatives wait until the score shows something
missing.

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

## 2026-10-28: httpx for requests, pytest for tests

**Chose:** httpx for every HTTP request the tool makes, and pytest for tests. Tests use made-up
data only and never call a live service.

**Alternatives:** Python's built-in `urllib` and `unittest`, with no dependencies.

**Why:** httpx gives clear timeouts and status handling, and the crawler will need it at rung 2,
so one library serves the whole tool instead of being swapped in later. pytest is the standard
and keeps tests short.

## 2026-10-28: Python calls Claude Code in a trimmed mode, and every call is traced

**Chose:** Python runs the pipeline and calls `claude -p` for each judgment, with a fixed JSON
reply shape. Each call turns off Claude Code's tools, MCP servers and settings and uses a short
system prompt of our own. Every call adds one line to the run's `trace.jsonl`: the prompt, the
reply, tokens, time and Claude Code's list-price estimate.

**Alternatives:** Claude Code running the pipeline as a skill; the Claude Agent SDK; a dashboard
for traces (Langfuse self-hosted, PostHog).

**Why:** code stays in charge and every reply is checked against its shape. A test call carried
about 46,000 tokens of Claude Code's own setup before the question; the trimmed mode cut it to
1,270 and halved the time, which keeps a subscription's limits out of the way. A plain trace file
is free, works offline, and is what the README's cost and speed numbers are computed from. The
Agent SDK normally needs a paid API key.

## 2026-10-28: How milestone 1 is scored

**Chose:**
- **Who judges:** Claude (Sonnet) decides whether a collected item and an answer-key question are
  the same question.
- **The rule:** they match if one answer would satisfy both. Same topic is not enough, and neither
  is a phrase whose answer would only cover the question along the way.
- **What it compares:** each unique answer-key question against everything the collector found,
  across all seeds, 15 questions per call.
- **Buyer tags:** each question is tagged once as a buyer question or not (Sonnet), and the tags
  are saved beside the answer key so every later score uses the same ones.
- **Proof:** collected phrases are numbered, and every match names the number of the matching
  phrase. Plain code turns the number back into the phrase, and a number outside the list counts
  as a miss.
- **Checks on the scorer:** the main judge runs twice, and the share of verdicts that flip is
  reported. A second judge (Opus) runs once, and every question where the two judges disagree is
  listed for a person to review. Once a person has reviewed a run, every pass is also scored
  against those reviewed verdicts.
- **Output:** `score.csv` with every verdict, `disagreements.csv`, a summary (share of buyer
  questions found, share of all questions found, flip rate, agreement between judges), and the
  trace.

**Alternatives:** embedding similarity with a threshold; word overlap in plain code; a "same
topic" rule; checking each question only against its own seed's suggestions; Opus or Haiku as
the main judge; matches quoted as text; a plain-code shortlist of candidates before judging; a
person checking a sample of verdicts without a second judge.

**Why:** matching meaning is a judgment call, so it belongs to Claude; word overlap would miss
most paraphrases and embeddings would need labels we don't have to set a threshold. The strict rule
keeps the score from being inflated by loose topic matches. A question often appears under one seed
while its match was collected under another, so checking against everything avoids false misses.
Stable verdicts are not the same as correct ones: the flip rate shows stability, and the second
judge points a person at the verdicts most likely to be wrong, which keeps the review short.
Measured against a reviewed run: with phrases quoted as text, Sonnet was right on 83 to 89% of
verdicts and Opus on 96%, because Sonnet missed obvious matches in long lists and miscopied
phrases. Numbering the phrases brought Sonnet to 92% and Opus to 91 to 94%, and most of Opus's
remaining errors were generous matches. Adding the "covers it along the way" rule left Sonnet at
89 to 90% and Opus at 94%. Differences this small sit inside the 6% of verdicts that flip between
passes, so on its own the scorer is about 90% accurate, and a score is only final once a person has
reviewed the questions where the two judges disagree. With equal accuracy, Sonnet uses less than
half the subscription limit, and a strict judge understates the score rather than inflating it. A
shortlist before judging would cut usage further, but a shortlist that drops the right phrase
causes misses no judge can fix, so it waits until the limit matters.

## 2026-10-28: How the Claude web search source works

**Chose:**
- **What to find:** about 25 questions per seed, spread across the angles autocomplete misses: why,
  what happens if, when and when not, risks and worries, what is included, comparisons, and hiring
  versus doing it yourself.
- **Which pages count:** questions people asked in their own words on forums, Q&A sites, community
  threads and comments, preferably from people in the client's country. Businesses' own FAQ pages
  are excluded, and so are sites that forbid crawlers (such as Quora and Reddit), because their
  questions can't be checked.
- **Proof:** plain code fetches each URL politely (robots.txt respected, one request every 2
  seconds, an honest crawler name) and checks that the question appears on the page. It fetches
  public addresses only, re-checks every redirect, and reads at most 2 MB per page. Questions it
  can't check are kept but marked unverified.
- **Model and volume:** Sonnet, one call per seed, with only the web search and page reading
  tools allowed.
- **Output:** `websearch.csv` in the same run folder as the other sources, with the question, its
  URL, and whether it was verified, plus a trace line per call.
- **Scoring:** the scorer reads every source in the run and reports the share of buyer questions
  found by all sources together (verified questions only, and with unverified ones), by each
  source alone, and the questions only one source found.

**Alternatives:** one open request per seed with no angles; any page including FAQ pages; keeping
sites that forbid crawlers and counting their questions unverified in the headline; trusting
Claude's URLs, or having Claude re-read the page to confirm; Haiku; several calls per seed; a
separate run folder per source.

**Why:** autocomplete already finds most cost questions, so the angles point the search at what it
misses. FAQ pages hold questions someone already answers, so counting them would hide the gaps the
tool is meant to find. A question checked on its page in plain code is proof; Claude's word for it
is not. On the first run, more than half the questions came from Quora, whose robots.txt forbids
crawlers, and many verified ones came from forums in another country, so the search now skips
such sites and prefers the client's country. The URLs come from web content, so the checker
refuses private and local addresses and caps what it reads. Questions that still can't be checked
are reported apart rather than dropped. Reporting each source's own share and its
unique finds is how a source shows it earns its place.
