# content-gap-map

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
