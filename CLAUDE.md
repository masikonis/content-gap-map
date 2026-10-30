# content-gap-map

## Working rules

- Work one step at a time: explain each concept, offer options, and wait for the decision.
- Log every decision: what we chose, the alternatives, and why. Decisions about the tool go in
  `docs/decisions.md`. Decisions about a client (its seeds, sites, settings, findings) go in
  `private/<client>/decisions.md`. When a decision changes, rewrite its entry so the log shows
  the current state; git history keeps the trail. A decided part leaves `docs/architecture.md`.
- Public repo. Client data never reaches git in any form: no client names, domains, crawled
  pages, traces, labels or reports in files, tests, examples, docs or commit messages. It lives
  only in the gitignored `private/` folder. Code reads it from there by path.
- The test for anything committed: could someone who knows the lab works with real clients work
  out which one this is? If yes, it stays private. Public docs, examples and commit messages use
  made-up examples, never facts drawn from a client.
- If client data is ever committed by mistake, remove that commit from history before anything
  else and tell Nerijus at once. If it was pushed, rewrite the remote history too.
- Keep this file current: when code, commands or the data layout change, update the sections
  below in the same commit.

## Where things are

- `docs/decisions.md`: every current decision and why. Read it before changing behaviour.
- `docs/architecture.md`: the parts not decided yet, with their options.
- `src/cgm/cli.py`: the `cgm` command and its steps.
- `src/cgm/client.py`: loads a client file (template: `examples/client.example.toml`) and refuses
  an unknown site type.
- `src/cgm/profiles.py`: site-type profiles (services, b2b-software, generic): autocomplete
  expansion words, the buyer-question rule, and predicted-question angles.
- `src/cgm/fetch.py`: polite, safe web requests for every step: the crawler name, the pause, and
  `PageFetcher` for untrusted URLs (public addresses only, robots.txt, redirects re-checked,
  2 MB cap).
- `src/cgm/files.py`: reads a run's CSV files as UTF-8.
- `src/cgm/autocomplete.py`: Google autocomplete collector. Plain code, raw replies kept.
- `src/cgm/searchconsole.py`: imports Search Console CSV exports (client's own site only) into a
  run. Exports are made by hand or with the Chrome connector, one per filter, each under 1,000 rows.
  Marks queries that look typed by an AI assistant (`ai_style`) and writes `ai-demand.md`, a
  client-facing summary of the AI-assistant share of search demand.
- `src/cgm/predicted.py`: Claude-written questions in the way people ask AI assistants. Saved apart
  and never counted as demand.
- `src/cgm/websearch.py`: optional source, off by default. Claude web search for questions people
  wrote, then a plain-code check that each question is on its page.
- `src/cgm/topics.py`: milestone 2. Tags buyer phrases, merges rewordings, groups them into named
  topics with Claude, and runs the pair test when the run has reviewed verdicts.
- `src/cgm/text.py`: plain-code word matching (stems, seed words) shared by scoring and grouping.
- `src/cgm/claude.py`: the only place Claude is called. Trimmed `claude -p` with a JSON schema;
  every call appends a line to the run's `trace.jsonl`.
- `src/cgm/score.py`: milestone 1 scorer. Seed-word shortlists per question, buyer tags, two
  judges, per-source shares, accuracy against reviewed verdicts.
- `demo/email-marketing/`: the public demo (Mailchimp vs Brevo and MailerLite). Public data only;
  every command takes `demo/email-marketing` in place of a client name.
- `tests/`: made-up data only, never a live service.

## Running it

```
uv run pytest                          # tests
uv run cgm autocomplete <client>       # starts a new run folder
uv run cgm searchconsole <client>      # merges the client's Search Console zips into the latest run
uv run cgm websearch <client>          # optional: adds to the latest run (or --run <name>)
uv run cgm predicted <client>          # optional: predicted AI-style questions, never demand
uv run cgm score <client>              # scores the latest run against the answer key
uv run cgm topics <client>             # groups the latest run's buyer phrases into topics
```

## Data layout

Client data lives under `private/` (gitignored); the public demo uses the same layout under
`demo/<name>/`.

```
private/blocklist.txt          terms the local pre-commit hook refuses to commit
<client>/client.toml           sites, seeds, language, country, site type
<client>/decisions.md          decisions and findings about this client (private clients only)
<client>/answer-key/           "People also ask" questions, and buyer-tags.csv
<client>/search-console/       Search Console export zips, one per filter (own site only)
<client>/runs/<date-time>/     one folder per run:
    autocomplete.csv, responses/       collected suggestions and Google's raw replies
    searchconsole.csv, ai-demand.md    Search Console queries and the client-facing AI summary
    websearch.csv, predicted.csv       optional sources
    score.csv, score-summary.json,     verdicts, summary and judge disagreements
    disagreements.csv
    trace.jsonl                        every Claude call
    reviewed.csv, reviewed-summary.json   the reviewed verdicts, once a review is done
    topics.csv, topics-summary.json    buyer phrases grouped into topics, and the pair test
    first-score/                       a score kept as published, when a later one replaces it
```

`reviewed.csv` needs `question` and `found` (True or False) on every row. Optional columns:
`buyer` (the reviewed tag), `sources` (which sources the review covered, joined with "; ";
autocomplete if absent), and the evidence and notes behind each change.

## Code conventions

- Plain code for exact parts, Claude for judgment, and every Claude call goes through `claude.ask`.
- Every web request goes through `fetch.py`: an honest crawler name, a pause between requests, and
  for URLs from Claude or the web, `PageFetcher`. A refusal is reported, never worked around.
- Files are read and written as UTF-8 (`files.read_rows` for CSV).
- Any code check on a Claude answer (a phrase number, a quote on a page) turns a failed check
  into a miss, never a pass.
