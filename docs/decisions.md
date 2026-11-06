# Decisions

The current decisions about the tool. Each entry: what we chose, the alternatives, and why. When a
decision changes, its entry is rewritten, so this page always shows the current state.

## 2026-10-23: "Answered" has three levels

**Chose:** when the tool reads a site's full passages, each question gets one of three verdicts
per site: answered (in detail, with proof of expertise), partly answered (in general terms, or
only part of the question), or not answered, with the URL and passage as evidence. At lighter
reading depths the verdict is topic-level (see the next entry).

**Alternatives:** yes or no; a score from 0 to 100.

**Why:** "partly" is the most useful case, because it means improving an existing page rather
than writing a new one. Yes or no hides it. A 0 to 100 score looks precise, but a person can't
label it consistently, so we couldn't test it. What counts as answered follows the proof rule
(see "Only commercial topics count, and an answer needs proof").

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
Each question is tagged as a buyer question or not, and each buyer question's funnel stage is
marked by Claude Sonnet and, blind, by Claude Fable (saved in `answer-key/stage-tags.csv`). The
headline score is the share of commercial buyer questions (comparing or choosing, by Sonnet's
marks) the collector finds, matched by meaning rather than exact words, with the share under
Fable's marks and the share of all buyer questions reported next to it. **The target is 75% of
commercial buyer questions,** found by the default sources together, on a reviewed score.
Predicted questions never count toward it.

**Alternatives:** no answer key, judging the collector's output by reading it; the site's own
Search Console searches as the answer key; scoring all questions alike; scoring buyer questions
at every stage, as the first published result did.

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
the tool. The AI-style gap is covered by predicted questions, reported separately. The target
moved from all buyer questions to commercial ones when the tool dropped the learning stage, so
that milestone 1 measures what the tool is for; it was not raised, though the result rose.

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
- **Brand searches:** each compared business's name from the client file (the client's and its
  competitors'), with question words before it, the profile's brand words after it ("pricing",
  "alternatives", "vs", "reviews") and a to z. About 54 requests per business. `cgm brands` adds
  them to a run collected before they existed.
- **Pace and identity:** one request every 2 seconds, an honest crawler name with a link to this
  repository, backing off when asked to slow down, and stopping with a "blocked" report rather
  than working around a block.
- **Raw collection:** every suggestion is saved. Filtering for questions, buyer intent and
  location is a separate later step.
- **Output:** one folder per run in the client's private folder, holding a CSV with one row per
  suggestion (seed, query sent, suggestion, rank, relevance, time) and Google's raw replies.
- **Running it:** one command, `uv run cgm autocomplete <client>`, which later steps join as
  sub-commands.

**Alternatives:** brand seeds listed by hand in the client file; the "firefox" format (10
suggestions, no scores); the seed alone, or question
words without a to z; expanding the best suggestions again; faster requests or a browser-like
identity; filtering while collecting; JSON lines instead of CSV; a standalone script.

**Why:** more suggestions per request means fewer requests. A to z expansion is the standard way
to reach the long tail, and about 450 requests for 8 seeds is still small. Polite, honest
requests are a lab rule, and a block is reported rather than hidden. Keeping the raw data means a
bad filter can't silently drop real questions. CSV matches the answer key and opens anywhere. A
single command keeps every step of the tool in one place. Two test calls showed that the country
setting is only a hint: suggestions for other countries come back too, so location filtering
belongs in the later filtering step. Category seeds alone never reached choosing-stage searches
such as "mailchimp pricing": the first demo collection missed every question that named the
client. Brand searches come from the names already in the client file, so a client needs nothing
extra; Claude picked this when Nerijus asked for the fix, as the simplest version, and it can
change.

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
  (Sonnet) tags each one as a buyer phrase or not under the site's profile rule. Phrases in another
  language, logins, downloads, phrases with a dollar amount and far-away places are left out as
  junk. Only buyer phrases are grouped.
- **The topic rule:** a topic is what one good page on a site would answer, so one page could
  fully answer every phrase in it. A variation that page would cover in a section (a year, "free",
  "best", a device) stays in the topic. Three kinds of phrase need different pages even on one
  subject: asking about the activity itself ("is email marketing hard"), how to do it yourself,
  and choosing a provider. A phrase about one named vendor, compared or not, is its own topic.
- **How:** plain code first merges rewordings: the same words in any order or form, ignoring years
  and the words reddit, quora and youtube. Claude then groups the rest under the topic rule. Up to
  2,500 phrases go in one call, so a question is never split across calls; a longer list is split
  by its nearest seed (seeds and compared brands). Each topic is named as a question ending in
  "?". The limit was 1,000 until brand searches pushed the demo to about 1,900 phrases: grouped
  seed by seed, each check passed most runs but never two in a row; in one call, the next two
  runs passed all three. What it costs: the one call's answer reached 54,000 tokens, close to
  Claude's output limit, so a much longer list falls back to seed batches.
- **Merge pass, always:** a second call sees every topic with its phrases and joins topics one
  page could answer under a new name, without folding a vendor topic into a general one. It also
  catches the phrases the first call left out, which code keeps as their own topics and counts.
- **Split pass, always:** a third call sees every topic of two or more phrases and moves out the
  phrases a page answering the rest would not fully answer, into new named topics.
- **Checks in code:** a phrase assigned twice keeps its first topic; each topic joins at most one
  merge; a split moves a phrase at most once, and a topic it empties disappears; a name that is not
  a question is sent back to be renamed; a last call lists topic pairs
  that may still be duplicates, reported and not acted on.

**Alternatives:**
- One question per topic, read strictly (one answer satisfies every phrase). An outside judge then
  failed topics one page answers easily, such as newsletter software for Windows or Mac, and
  splitting further to satisfy it broke the split check: both checks failed.
- A majority vote of three groupings, to steady Claude's run-to-run variation: three times the
  grouping calls and about 40 lines of code, kept in reserve since one call was enough.
- Starting each run from the last run's topics: the most stable, and useful for tracking a client
  month to month, but a run would then test placing phrases rather than grouping them.
- Running the merge pass again after the split, to rejoin near-duplicate topics the split makes.
  It fixed splitting (89% and 87%) but put the lumps back (29 and 34 of 40), so it was dropped.
- Folding other vendors into the general question: fewer topics, but a general page rarely answers
  a question about one named vendor, and the lump check failed those topics.
- Grouping everything collected; Claude alone without the code merge; grouping one seed at a time,
  which split the same question across seeds and needed a merge that lumped unrelated topics; a
  merge pass only for long lists; an embedding model with clustering code, which would need an AI
  model running on the local machine.

**Why:** milestone 3 matches pages to topics, so the topic should be the size of a page. Merging
exact rewordings is a job for code; deciding what one page answers is a job for Claude. Vendor
topics and one-phrase topics cost nothing, since the report ranks them low. Claude Fable reviewed
the topics twice; the one-pass grouping, the always-on merge, question names and the random
baseline came from those reviews. The split pass came from the lump check: the same lumps
(asking whether email marketing is cheap next to choosing the cheapest tool) came back on every
run even with the grouping rule naming them, and grouping alone passed the lump check once in two
runs. What it costs: topics are less precise than one question, so a
page matched to a topic may cover some of its phrases better than others.

## 2026-10-30: Topics are a full working list; the report ranks them later

**Chose:** milestone 2 keeps every topic, however many there are, as a working list for the tool.
A person never reads it as the result. Matching pages (milestone 3) and verdicts (milestone 4) run
on the full list, and milestone 5 ranks it into the short list a person reads: the 10 to 20 gaps
most worth a page, by how many buyers ask and whether only competitors answer. The full list stays
in the run folder as evidence.

**Alternatives:** shrinking the topics now into 20 to 30 broad themes, readable at once but lumping
questions so that one page can't be matched to a topic; the full list plus broad theme headings in
the report, for display only, left out until a real report shows it is needed.

**Why:** matching needs topics the size of one page. Whether a topic is worth a page depends on
what competitors answer, which only milestones 3 and 4 show, so ranking belongs at the end. A long
tail of one-phrase topics costs the reader nothing when it ranks low. What it costs: nobody sees a
readable result until milestone 5.

## 2026-10-30: The milestone 2 target, and how it is checked

**Chose:** each kept topic is what one page would answer, with the right funnel stage, checked
three ways on every run.
- **Not split:** in a reviewed run, phrases the judges matched to the same commercial answer-key
  question should share a topic. At least 85% of those pairs must, with each question counted
  equally, and the same share for a random grouping of the same topic sizes is reported next to
  it.
- **Not lumped:** at least 36 of 40 kept topics, picked with a fixed seed from topics of two or
  more phrases (a single phrase can't be lumped), must be ones one page could fully answer.
  Claude Fable judges them blind: it sees the phrases, not the names or scores. A missing verdict
  is a fail.
- **Right stage:** Claude Fable marks the stage of 40 topics picked with a fixed seed, without
  seeing the first marks; at least 36 must agree on keep or drop. A missing verdict is a fail.
- Milestone 2 passes when all three checks pass on two runs in a row, because Claude's grouping
  varies from run to run, and one lucky run would not show the tool works. Claude proposed this
  rule and Nerijus kept it when one run passed and the next missed by one topic on two checks.

**Alternatives:** the split check alone, which a tool that dumps everything into a few huge topics
would pass; judging 20 topics, too noisy (the same code scored 12 and 15 of 20 on two runs);
sampling every topic, where one-phrase topics pass automatically; a person checking topics, which
nobody has time for at each run; the share of different-question pairs kept apart, which random
grouping already scores 98% on, so it says little.

**Why:** lumping is the failure that would hurt the report most, since a lumped topic hides a
real gap, and the split check can't see it. An outside model that never sees the scores is the
cheapest honest judge. A wrong stage mark drops a commercial topic for good, so the stage needs
its own check. Learning topics never reach the report, so the split and lump checks look only at
commercial questions and kept topics. What it costs: about $0.45 per run for the two blind
checks, and the judge is still an AI.

The target was set after the first results and changed once: the first version asked for one
question per topic, judged 20 topics and needed 18 of them.

## 2026-11-02: Only commercial topics count, and an answer needs proof

**Chose:**
- **Commercial topics only.** The gap list covers topics a buyer asks while comparing options
  (middle of the funnel: "best email automation tools", "Brevo vs MailerLite") or while ready to
  choose a provider (bottom: "Mailchimp pricing", "Mailchimp alternatives"). Topics asked while
  still learning about the problem (top: "what is email automation") are left out entirely, even
  when nobody answers them. Every gap should tie to a business outcome: a buyer choosing a
  provider. Collection stays broad; the stage is marked right after grouping, and learning-stage
  topics stay in topics.csv as evidence but are dropped from every later step. How to do something
  in a tool the buyer already uses ("how to send transactional email in HubSpot") counts as
  learning: it is support, not a buying decision, and so does a question about one's own account.
  What one named provider offers before buying (features, plans, integrations, regions), whether
  it can be trusted, and how to sign up ("does MailerLite have an app", "is MailerLite safe")
  count as choosing. One
  rule (`stage.py`) marks both answer-key questions and topics, so milestones 1 and 2 count the
  same thing.
- **An answer counts only with proof.** A page answers a topic when it answers it in detail and
  backs it with expertise that can't be faked: case studies, project details, real prices, or
  other proof of having done the work. A page that answers in general terms is a gap too, and
  often the most useful one, since any competitor or AI answer can say the same.
- **What it is for:** a free addition to client work, run proactively, so a client sees the
  pages worth writing next without asking. The result is a short brief a client can act on.

**Alternatives:** keeping every buyer question, including the learning stage, as milestones 1 and
2 do now; dropping them only when ranking the gap list, which keeps everything until the end but
reads and judges pages for topics that will be thrown away; keeping how-to questions about one
tool as choosing, since a struggling user may switch, which fills the list with support pages;
counting any page that answers the question, however generic.

**Why:** a gap is worth a page only when it has commercial value and leads to a business outcome.
Learning-stage content makes little sense now that AI assistants answer those questions
directly. This is an opinionated choice, and the README says so up front.
Expertise backed by proof can't be faked, so it is what makes a page worth more than a generic
one. What it costs: judging proof needs each page's text, not just its sitemap or headings, and
the funnel stage is a Claude judgment that needs its own check.

## 2026-11-03: Milestone 3 is checked against Google's own pick of each site's page

**Chose:** milestone 3 ("the right content") reads each site's sitemap and keeps the pages that
could answer a commercial buyer topic. It is tested against an answer key built outside the tool:
each of milestone 1's 20 commercial "People also ask" questions is searched on each compared site
(`site:mailchimp.com How much does Mailchimp cost per month?`) in a real Chrome session, and the
first result is the page that matters. **The target is 90% of those pages kept,** with the
number of pages kept per site reported next to it, on two runs in a row, as for milestone 2,
since Claude's keep verdicts can vary from run to run. The key is committed before the tool runs.

**Alternatives:** checking only that every sitemap address was read and dropped by clear rules,
which proves the code reads files but not that it keeps the right pages; a person labelling a
sample of kept and dropped addresses, the truest test but 20 minutes of Nerijus's time per rerun;
building the key from milestone 2's topics, which would make the key depend on the tool's own
grouping.

**Why:** the costly mistake at this step is dropping a page that answers a buyer, since it turns
into a false gap later; keeping too many only costs time. Google's ranking doesn't depend on the
sitemap reader, and milestone 1's questions are already reviewed and public. What it costs:
Google's first result isn't always the best page, and the key takes a short Chrome session.

## 2026-11-03: Sitemaps are read by our own small reader

**Chose:** a sitemap reader built on the existing polite fetch code: robots.txt for the sitemap
locations, sitemap index files followed to their children, gzip handled, every request with the
honest crawler name and the pause.

**Alternatives:** a sitemap library such as ultimate-sitemap-parser, which handles odd formats
but brings its own fetching, outside the polite rules.

**Why:** the reader is small, and every request staying in `fetch.py` keeps the crawling rules in
one place.

## 2026-11-04: Pages are kept by code rules first, then Claude

**Chose:** from every sitemap address, plain code first drops the exact cases: pages in another
language than the client's (a language code as the first part of the path), other websites,
files that aren't pages (PDFs, images), and duplicates of the same address. Claude (Sonnet) then
reads the remaining addresses and keeps the ones whose page could answer a buyer who is comparing
options or choosing a provider, under the same stage rule as milestones 1 and 2. That includes
pages on whether the activity is worth doing at all (trends, statistics, results), which the stage
rule counts as comparing; the first run dropped them as teaching, missing 6 of 60 key pages, and
the rule was aligned after that result. Every address is
saved with the reason it was kept or dropped. A page Claude gives no verdict for is dropped and
counted, per the rule that a failed check is a miss.

**Alternatives:** code rules alone, exact and free but tuned per site, and unable to tell a buyer
guide from a how-to post; Claude alone on every address, one rule for any site but about twice the
calls, with Claude doing exact work code does better.

**Why:** code for what must be exact, AI for what must be judged. What it costs: Claude judges
from the address alone, so an address that says little (`/p/12345`) waits for rung 2, which reads
page outlines.

## 2026-11-06: Private terms in the public demo are masked, not dropped

**Chose:** before a demo run is committed, `cgm withhold` replaces every term on the private
blocklist in the run's text files with "[withheld]". The first sitemap run hit this: a compared
site's public blog has posts named after terms on the list, and the local pre-commit hook refused
the commit. The results page says how many were masked, without naming them.

**Alternatives:** dropping the matching rows, which would make the published counts disagree
with the files; keeping the sitemap and page lists out of git, which would leave 16,000 verdicts
uncheckable.

**Why:** nothing committed may let a reader link the demo to a client, and every other number
stays public and checkable. What it costs: a handful of public addresses show "[withheld]" where a
word was.
