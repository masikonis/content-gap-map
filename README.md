# Content Gap Map

Buyer questions your site misses.

Your buyers ask hundreds of questions before they contact you: on Google, in AI assistants, in
forums. When your site doesn't answer one, a competitor's page does, or an AI answer built from
it does, and you lose that buyer before you know they existed.

Content Gap Map takes your site and your top competitors, collects the real questions buyers ask,
and shows which questions you answer, which only your competitors answer, and which nobody answers
well. Every verdict links to the evidence behind it, so you can check the work. You end with a
short list of the pages worth writing next, based on real questions instead of guesses.

It reads each site at one of three depths, and the report says which one it used:

1. **Sitemap:** which topics each site has a page for, and which it has none for. Fast, and
   enough to find the clearest gaps.
2. **Page outlines:** the same, from each page's title and headings, so it's more reliable.
3. **Passages:** whether each page actually answers each question, partly answers it or misses
   it, with the passage quoted.

It is built for B2B software, service businesses and publishers, and can run on other sites too.
English first; other languages are accepted as input but stay untested until they have their
own test set.

## How we'll know it works

Success comes in milestones. Each one has to work reliably before the next one is worth building:

1. **Real questions.** Collect the questions real buyers ask, not ones a machine made up.
2. **Clear topics.** Group the questions that mean the same thing, the way a person would.
3. **The right content.** Read your site and your competitors' sites at each depth, starting with
   the sitemap, and keep what could answer a buyer.
4. **Honest verdicts.** Give each site the verdict its depth can prove, and show the proof.
5. **Gaps worth acting on.** A short list of missing answers that a person agrees are real and
   worth a page.

Each milestone is checked against a fixed test set that the tool never sees while it runs, with a
person reviewing the cases where the checks disagree. The scores, cost and run time are published
here.

## Status

Early, working on milestone 1. Question collection (Google autocomplete, and Search Console for
your own site) and its scorer are built, with Claude web search as an optional extra source;
grouping, site reading and the report are not. It is built in public, one step at a time. The
choices made so far and the reasons for them are in [docs/decisions.md](docs/decisions.md); the
parts still open, with their options, are in [docs/architecture.md](docs/architecture.md).

## Run it

You need [uv](https://docs.astral.sh/uv/) and [Claude Code](https://claude.com/claude-code).
Copy `examples/client.example.toml` to `private/<name>/client.toml` and fill it in. The
`private/` folder is never committed.

```
uv run cgm autocomplete <name>   # collect autocomplete suggestions into a new run
uv run cgm searchconsole <name>  # add your Search Console exports from private/<name>/search-console/
uv run cgm websearch <name>      # optional: add questions people wrote online, checked on their pages
uv run cgm score <name>          # score the run against an answer key in private/<name>/answer-key/
```

## License

MIT
