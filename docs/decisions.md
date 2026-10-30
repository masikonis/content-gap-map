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
profile in `src/cgm/profiles.py` holding the words that expand a seed for autocomplete, the rule
for what counts as a buyer question, and the angles for predicted questions. Any other site type
runs on the generic profile. Built so far: services, B2B software and generic; publishers use
generic until they get their own. Seeds should be short category phrases ("cloud phone system",
"voip"), because autocomplete only grows suggestions from the start of a phrase.

**Alternatives:** one site type only (the simplest start); one generic approach for every site.

**Why:** buyers on these sites ask different kinds of questions and get answers on different kinds
of pages, so treating them alike gives weaker results. The second test showed it: a services
setup run on a B2B software site found 56% of buyer questions. Its buyer rule asked about hiring,
so it dropped software research questions such as "what does unified communications do"; its
expansion words missed "best", "types", "alternatives" and "pricing"; and its long seeds missed
short searches like "voip disadvantages". The B2B software profile was written from that test, so
it counts as proven only once it scores on a third site it wasn't written from. Keeping the
differences in profiles keeps the core small and makes new types cheap to add.

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
questions reported next to it. **The target is 75% of buyer questions,** found by the default
sources together, on a score a person has reviewed. Predicted questions never count toward it.

**Alternatives:** no answer key, judging the collector's output by reading it; the site's own
Search Console searches as the answer key; scoring all questions alike.

**Why:** "it works" needs a number, and every later milestone stands on this one. "People also
ask" is the closest public view of what buyers ask, and none of the collector's sources can see
it, which keeps the test independent. Search Console fails that test, because the collector uses
it as a source, and it only covers searches where the site already appears. About one in five
"People also ask" questions are not from buyers (do-it-yourself tips, or other businesses pricing
their own work), and the tool filters those out anyway, so counting them would blur the number
that matters. The target was first set at 80% and lowered to 75% after the first test, by
Nerijus's call. That test showed what the real sources can reach: autocomplete and Search
Console together found about 75%, and nearly every miss was a conversational "why" or "what
happens if" question that people ask AI assistants rather than type as searches. No real,
free source holds those, so a higher bar would measure the limits of search data rather than of
the tool. The AI-style gap is covered by predicted questions, reported separately.

## 2026-10-28: The collector uses autocomplete and Search Console; web search is optional

**Chose:** two sources run by default:
- **Google autocomplete,** each seed expanded with question words and a to z. Plain code, close to
  what people type, about the same result every run.
- **Search Console,** for the client's own site only (competitors' data is never available). The
  best real demand data, including questions typed by AI assistants. It comes from Search
  Console's own CSV export, 12 months, one export per service narrowed to question- and
  cost-shaped searches so each stays under the export's 1,000-query cap; `cgm searchconsole`
  merges the exports into a run.

**Claude web search** stays as an optional step (`cgm websearch`), off by default: it finds
questions people wrote out in full, each verified on its page.

**Alternatives:** the Search Console API (needs a Google Cloud login setup, more than an internal
tool is worth; the export is a few clicks); one export of every query (hits the 1,000 cap and cuts
off the rare searches); web search on by default; cutting web search entirely; Bing autocomplete;
the Stack Exchange and Hacker News APIs; the WildChat dataset of real AI chats; Google driven
through a browser; questions written by Claude and kept only if autocomplete confirms them. Ruled
out: scraping "People also ask" (Google's robots.txt disallows it), Reddit (closed to new
developers), Quora and review sites (their terms forbid scraping), and paid search data APIs.

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
- **What it compares:** each unique answer-key question against a shortlist of what the sources
  found: every phrase containing the most specific word (the one fewest phrases use) of one of the
  question's seeds, or of a seed whose word the question mentions, plus the 100 phrases that share
  the most words with the question itself, rare words counting more. Questions that share a seed
  list are judged together, 5 per call.
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
the main judge; matches quoted as text; every phrase in every call; a shortlist of the phrases
sharing the most words with each question; a person checking a sample of verdicts without a
second judge.

**Why:** matching meaning is a judgment call, so it belongs to Claude; word overlap would miss most
paraphrases and embeddings would need labels we don't have to set a threshold. The strict rule keeps
the score from being inflated by loose topic matches. A question often appears under one seed while
its match was collected under another, so checking against everything avoids false misses. Stable
verdicts are not the same as correct ones: the flip rate shows stability, and the second judge
points a person at the verdicts most likely to be wrong, which keeps the review short. The seed list
alone keys each seed on its rarest word, and for seeds like "email marketing software" that word is
generic ("software"), so right phrases were dropped before judging: the first public demo lost two
matches this way. Adding the 100 closest phrases per question fixes it: measured against both
reviewed sets, the shortlist then kept every confirmed match (56 of 56 and 26 of 26) with lists only
slightly longer, and still does after a plural-matching bug was fixed. Using the seeds' two rarest
words also kept them all but doubled the lists; dropping the shortlist did too, at the cost of long
lists the judges handle worse. Measured against a reviewed run: with phrases quoted as text, Sonnet
was right on 83 to 89% of verdicts and Opus on 96%, because Sonnet missed obvious matches in long
lists and miscopied phrases. Numbering the phrases brought Sonnet to 92% and Opus to 91 to 94%, and
most of Opus's remaining errors were generous matches. Adding the "covers it along the way" rule
left Sonnet at 89 to 90% and Opus at 94%. Differences this small sit inside the 6% of verdicts that
flip between passes, so on its own the scorer is about 90% accurate, and a score is only final once
a person has reviewed the questions where the two judges disagree. With equal accuracy, Sonnet uses
less than half the subscription limit, and a strict judge understates the score rather than
inflating it. A judge also misses more as lists grow: adding a second source took each call from
about 3,600 phrases to 5,100, and accuracy fell to 90 to 92%. A shortlist fixes that, but one that
drops the right phrase causes a miss no judge can fix, so each was tested against the reviewed
matches: the top 150 phrases by shared words kept only 46 of 56, because hundreds of near-identical
phrases crowd out the right one and synonyms share no words, while the seed-word shortlist kept 55
of 56 and cut lists to about 1,300 phrases.

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

## 2026-10-30: Questions asked to AI assistants: AI searches counted, predictions kept apart

**Chose:**
- **AI searches in Search Console:** a query counts as typed by an AI assistant searching for
  someone if it uses search commands people don't type (`filetype:`, `site:`, quotes), starts like
  a prompt ("context:", "question:"), or runs to 10 words or more. These are real demand and score
  as their own source.
- **AI demand as a client deliverable:** every Search Console import writes `ai-demand.md`, a
  plain-words page with the share of searches and impressions that come through AI assistants,
  their clicks, and the top AI searches. It is a strong, simple signal for any client, so it stands
  on its own rather than only feeding the score.
- **Predicted questions:** Claude writes 25 questions per seed in the way people talk to an
  assistant (`cgm predicted`). They are saved apart, reported as "with predicted", and never count
  in the headline score or toward the milestone target.

**Alternatives:** an AI-side answer key built from the follow-up questions AI assistants suggest
(dropped: Perplexity asks for an account after one search, Google AI Mode suggests no follow-ups,
and ChatGPT needs an account); paid prompt-volume products; ignoring AI assistants.

**Why:** fewer people type short searches; more ask assistants in full sentences, and what they
type there is private. The assistants' own searches do reach Search Console, so that part can be
measured. The rest can only be predicted, and a prediction must never be scored as demand. On
the first test the predicted questions covered most of the conversational "why" and "what
happens if" questions the real sources missed, but the prompt's angles were chosen after seeing
those misses, so that result is optimistic until it holds on a site it wasn't tuned on.

## 2026-10-30: The public demo: Mailchimp vs Brevo and MailerLite

**Chose:** the public test set is email marketing software: Mailchimp as the primary site, Brevo
and MailerLite as competitors, with the B2B software profile and five short seeds (email
marketing software, newsletter software, email automation, transactional email, email marketing
for small business). Everything lives in `demo/email-marketing/` and is public: the client file,
the answer key, the collected data and the scores. The setup and the answer key were committed
before the first run, the run is scored once, and the result is published as it comes out.

**Alternatives:** project management (Asana vs monday.com and ClickUp); online scheduling
(Calendly vs Acuity Scheduling and Cal.com); a client's site, which can't be published.

**Why:** the lab's readers are marketers, so this category speaks to them; its buyer questions are
about choosing and paying for software, which is what the B2B software profile claims to handle;
and no part of that profile was written from this category, so it is a fair test. Fixing the test
in git before running it shows the result wasn't picked after the fact.

## 2026-10-30: How a public result is reviewed and published

**Chose:** before a result goes in the README, Claude reviews every buyer tag and every verdict on a
buyer question against the full list of collected phrases, and two outside models (Claude Fable and
OpenAI Codex, at high reasoning) check each change independently. Where either objects, the stricter
call is kept. The raw result is committed before review, and every change is listed with its
evidence in the run's `reviewed.csv`. The README states who reviewed (no person, when none did),
the sample size and its rough range, the answer key's capture conditions, and any flaw the review
found.

**Alternatives:** a person reviewing every verdict (the strongest check, but not available for the
first demo); reviewing only the judges' disagreements; publishing the judges' raw number.

**Why:** both outside reviewers found real problems in the first draft: a range presented as a
margin of error, an overstated claim about the misses, paraphrased questions counted twice, and the
need to disclose a signed-in browser. Checking misses against the full phrase list exposed a scorer
flaw the judges could not see. Keeping the stricter call where reviewers disagree stops a review
from leaning toward a higher score.

## 2026-10-30: Which Claude model does each step

**Chose:** Sonnet tags buyer questions, writes predicted questions, runs web search and is the main
judge. Opus is the second judge, run once per score to flag verdicts for review. Each module names
its model in a constant at the top.

**Alternatives:** Haiku for bulk steps; Sonnet everywhere; Opus everywhere.

**Why:** measured on a reviewed run, Sonnet with numbered phrases judged as accurately as Opus at
less than half the subscription usage, and it errs strict where Opus errs generous. Opus earns its
place as the second judge, because its different mistakes are what make disagreements worth a
person's look. Haiku was the weaker judge in every comparison.

## 2026-10-30: A run is a folder of plain files

**Chose:** each run is a folder named by date and time. Every step writes its own plain files
there: CSV for tables, JSON for summaries, JSON lines for traces, and the raw replies from Google.
No database and no cache.

**Alternatives:** SQLite as a cache and store; DuckDB; Postgres.

**Why:** a run holds a few thousand rows, so plain files are fast enough, readable in any editor or
spreadsheet, and diffable in git, which is how the public demo's results are published. Runs are
rare and each one is kept, so a cache would save little.

## 2026-10-30: Evals are the scorer plus a reviewed set; pytest tests the code

**Chose:** each milestone is measured by a `cgm` step (milestone 1: `cgm score`) against an answer
key, with a reviewed verdict file (`reviewed.csv`) as its ground truth once a review is done.
pytest checks the code on made-up data and never calls a live service.

**Alternatives:** Inspect (UK AI Security Institute); promptfoo; Ragas or DeepEval.

**Why:** the score has to be readable end to end and published in the README, and a small scorer
does that with nothing to learn. Ragas and DeepEval grade with opaque AI metrics, which don't fit
tests against verdicts a reviewer can check line by line.

## 2026-10-30: The tool is a command-line program that writes files

**Chose:** `cgm` runs each step from the command line and writes files into the run folder. A
viewer, when it comes, reads those files.

**Alternatives:** a local web server with a browser app that starts runs and records reviews.

**Why:** fewest moving parts, and the files are the record. A server would only pay off once
reviewing in a browser is needed often.

## 2026-10-30: How questions are grouped into topics (milestone 2)

**Chose:**
- **What gets grouped:** real collected phrases only (no predicted questions), after Claude
  (Sonnet) tags each one as a buyer phrase or not under the site's profile rule. Only buyer phrases
  are grouped.
- **How:** plain code first merges near-duplicates (the same words in any order or form). Claude
  then groups the rest into topics, one seed's phrases at a time, under the same rule as scoring:
  a topic is one question a buyer wants answered, so one answer would satisfy every phrase in it.
  Each topic gets a short plain name. A final pass merges topics that mean the same thing across
  seeds. Code checks every answer: a phrase assigned twice keeps its first topic, and a phrase left
  out becomes a topic of its own and is counted.
- **The test:** in a reviewed run, phrases the judges matched to the same answer-key question
  should land in the same topic. The score is the share of those pairs kept together. Pairs matched
  to different questions are reported too, as a rough check against topics that lump things
  together, since two different questions can still share a topic.

**Alternatives:** grouping everything collected; Claude alone without the duplicate merge; an
embedding model with clustering code, which would need an AI model running on the local machine.

**Why:** the report should only show topics buyers care about, and shorter, cleaner lists group
better. Merging exact rewordings is a job for code; deciding what means the same is a job for
Claude. Using the scoring rule as the topic rule keeps milestones 1 and 2 consistent, and the pair
test reuses data a review already checked, so it needs no new labelling.

First results: on the public demo, 863 buyer phrases became 194 topics; 77% of same-question pairs
landed together and 98% of different-question pairs were kept apart. On a private services client
with ten times the long tail, 96% and 88%, but with 1,116 topics, most of them a single phrase.
Known weak spots: some over-splitting ("best newsletter software" versus "best software for
creating a newsletter"), a few foreign-language phrases tagged as buyer phrases, and a long tail of
one-phrase topics that the report will need to fold away. No target is set for milestone 2 yet.
