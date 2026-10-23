# content-gap-map

- Work one step at a time: explain each concept, offer options, and wait for the decision.
- Log every decision in `docs/decisions.md`: what we chose, the alternatives, and why.
- Public repo. Client data never reaches git in any form: no client names, domains, crawled
  pages, traces, labels or reports in files, tests, examples, docs or commit messages. It lives
  only in the gitignored `private/` folder. Code reads it from there by path.
- If client data is ever committed by mistake, remove that commit from history before anything
  else and tell Nerijus at once. If it was pushed, rewrite the remote history too.
