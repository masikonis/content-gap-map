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
- `src/cgm/client.py`: loads `private/<client>/client.toml` (template: `examples/client.example.toml`).
- `src/cgm/autocomplete.py`: Google autocomplete collector. Plain code, raw replies kept.
- `src/cgm/websearch.py`: Claude web search for questions people wrote, then a plain-code check
  that each question is on its page.
- `src/cgm/claude.py`: the only place Claude is called. Trimmed `claude -p` with a JSON schema;
  every call appends a line to the run's `trace.jsonl`.
- `src/cgm/score.py`: milestone 1 scorer. Buyer tags, two judges, per-source shares, accuracy
  against reviewed verdicts.
- `tests/`: made-up data only, never a live service.

## Running it

```
uv run pytest                          # tests
uv run cgm autocomplete <client>       # starts a new run folder
uv run cgm websearch <client>          # adds to the latest run (or --run <name>)
uv run cgm score <client>              # scores the latest run against the answer key
```

## Private data layout (gitignored)

```
private/blocklist.txt                  terms the local pre-commit hook refuses to commit
private/<client>/client.toml           sites, seeds, language, country, site type
private/<client>/decisions.md          decisions and findings about this client
private/<client>/answer-key/           "People also ask" questions, and buyer-tags.csv
private/<client>/runs/<date-time>/     autocomplete.csv, responses/, websearch.csv, trace.jsonl,
                                       score.csv, score-summary.json, disagreements.csv, reviewed.csv
```

## Code conventions

- Plain code for exact parts, Claude for judgment, and every Claude call goes through `claude.ask`.
- Requests are polite: `USER_AGENT` and `PAUSE` in `autocomplete.py`, robots.txt for page fetches.
  A refusal is reported, never worked around.
- URLs from Claude or the web are untrusted: page fetches go to public addresses only, redirects
  are followed by hand and re-checked, and at most 2 MB is read (`Verifier` in `websearch.py`).
- Any code check on a Claude answer (a phrase number, a quote on a page) turns a failed check
  into a miss, never a pass.
