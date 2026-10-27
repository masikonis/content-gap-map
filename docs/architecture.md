# Architecture: open options

The parts of the tool that are not decided yet, each with its options, pros and cons. Each part is
decided when the build reaches it, using what the earlier parts showed. A decided part leaves this
page, and its choice is in [decisions.md](decisions.md).

Decided so far: where questions come from, the backend language and its tooling, and two
constraints behind every option below (free software and data only; AI through Claude Code).
Crawling is always polite: robots.txt, rate limits and an honest crawler name.

Facts below came from web research on 2026-10-23. Some are not verified yet: a few model
licences, speeds on a typical laptop, and whether the Claude Agent SDK can use a subscription.

## 1. Crawler

| Option | Pros | Cons |
|---|---|---|
| **A. Our own small crawler** (httpx, plus Protego for robots.txt) | A few hundred lines, all readable. Exactly the polite rules we want. | We write sitemap reading, caching and retries ourselves. |
| **B. Scrapy** | Mature. Robots.txt, rate limiting and caching built in. | A whole framework for 3 or 4 sites. |
| **C. Crawlee** (Python or JS) | Switches easily between plain fetching and a real browser. | Built for getting around blocks, which goes against the polite rule. |
| **D. crawl4ai** | Popular, outputs clean Markdown, handles JavaScript pages. | Big, changes fast, carries AI features we won't use. |

Ruled out:
- **Firecrawl:** the self-hosted version needs several services, and AGPL clashes with MIT.

## 2. JavaScript-heavy pages

| Option | Pros | Cons |
|---|---|---|
| **A. Ignore them in v1** | Nothing to install. Most business sites don't need it. | Some competitor sites will come out thin or empty. |
| **B. Playwright, only when a page returns too little text** | Automatic and repeatable. | A large install (a whole browser). |
| **C. Chrome connector, by hand, for the odd page** | Nothing to install. Works on tricky pages. | Slow and manual. Not part of a repeatable run. |

## 3. Pulling the main text out of a page

| Option | Pros | Cons |
|---|---|---|
| **A. trafilatura** | The reference tool. Multilingual. Keeps headings. Scores well on benchmarks. | Can drop content that isn't article-like, such as pricing grids and accordion FAQs. |
| **B. Readability** | Well known (Firefox's reader view). | Built for articles, so worse on service and pricing pages. |
| **C. Keep the whole page as Markdown** (markdownify) | Loses nothing. | Keeps menus, footers and other noise, so matching gets worse. |
| **D. crawl4ai's built-in Markdown** | Comes free with 1D. | Ties extraction to that crawler. |

Add-on for any option: **extruct** reads FAQ and schema data, which gives exact question and
answer pairs without AI.

## 4. Splitting pages into passages

| Option | Pros | Cons |
|---|---|---|
| **A. By heading**, with long sections split further | Follows how the page is written, so each passage stays on one topic. About 30 lines of code. | Pages with poor headings give uneven passages. |
| **B. Fixed size** (for example, every 400 words) | Simplest. | Cuts through the middle of answers. |
| **C. Semantic splitting** (AI decides where topics change) | Clean breaks in theory. | Studies show little gain over A, at more cost. |

## 5. Finding candidate passages for each question

Claude can't read every passage for every question, so code has to shortlist the top 10 or so
first.

| Option | Pros | Cons |
|---|---|---|
| **A. A small local embedding model** (search only, no reasoning) | Finds passages with the same meaning in different words ("how much is it" and "pricing"). Free, same result every run. | About a 1.2 GB download plus PyTorch. The one local model in the plan. |
| **B. Keyword search (BM25)** | Plain code, no AI, tiny, exact. | Misses paraphrases, so some real answers never reach Claude. |
| **C. A and B combined** | Usually finds more than either alone. | Two systems to tune. |
| **D. A free embedding API tier** (Voyage, Gemini) | No local install. | A SaaS account with free-tier limits that can change. |

## 6. Embedding model (only with 5A or 5C)

| Option | Pros | Cons |
|---|---|---|
| **A. Qwen3-Embedding-0.6B** | Strongest at its size, 100+ languages, Apache-2.0. | Questions need a one-line instruction in front. |
| **B. BGE-M3** | Solid, multilingual, MIT, no instruction needed. | A bit older and weaker. |
| **C. EmbeddingGemma-300m** | Smallest and fastest. | Google's own licence terms, not a standard open-source licence. |

## 7. Where vectors live (only with 5A or 5C)

| Option | Pros | Cons |
|---|---|---|
| **A. numpy files on disk** | Nothing to install. Millisecond search at our size. | No queries, just arrays. |
| **B. sqlite-vec** | Vectors in the same SQLite file as everything else. | Younger tool, clunkier queries. |
| **C. LanceDB** | Grows to large data. | Not needed at about 20,000 vectors. |
| **D. pgvector** | The industry standard, good to learn. | Needs a Postgres server, for no gain at this size. |

## 8. Grouping questions into topics

| Option | Pros | Cons |
|---|---|---|
| **A. Agglomerative clustering** (scikit-learn) | Same result every run. One threshold to tune. No need to pick the number of groups. | Needs embeddings (5A or 5C). |
| **B. HDBSCAN** | Finds groups of any shape. | Often throws a large share of short questions out as "noise". |
| **C. BERTopic** | All in one: groups and names topics. | Hides its settings, and results change between runs. |
| **D. Claude groups them directly** | No embeddings needed. Names come out in the same step. | Hard with thousands of questions at once, and less stable across runs. |

## 9. How the pipeline calls Claude

| Option | Pros | Cons |
|---|---|---|
| **A. Python runs the pipeline and calls `claude -p`** for each judging batch | Code stays in charge. `--json-schema` fixes the reply shape. `--output-format json` returns tokens and time, which feed the traces. | Each call starts a new Claude Code process, which is a bit slow. |
| **B. Claude Code runs the pipeline** (a skill that runs Python scripts and judges in between) | Natural in Claude Code. Can use subagents and the Chrome connector. | Less repeatable, harder to trace, and the line between code and AI blurs. |
| **C. Claude Agent SDK** | A clean programming interface. | Normally needs a paid API key rather than a subscription (not verified). |

## 10. Which Claude model per step

| Option | Pros | Cons |
|---|---|---|
| **A. Haiku for bulk steps, Sonnet or Opus for hard ones** | Uses the plan's weekly limit slowly. | Two models to compare in the evals. |
| **B. Sonnet everywhere** | One setting, strong quality. | Uses more of the limit. |
| **C. Opus everywhere** | Best quality. | Uses the limit fastest, and is slower. |

## 11. Storing runs and caching

| Option | Pros | Cons |
|---|---|---|
| **A. SQLite** for the cache and working data, plus one JSON file per run for the viewer | Built into Python. One file. Re-runs reuse cached pages and AI replies. | Some SQL to write. |
| **B. JSON files only** | Simplest, easy to read. | Gets messy as a cache. |
| **C. DuckDB** | Great for analysis. | Not needed at this size. |
| **D. Postgres** | Standard for a hosted service later. | A server to run, for nothing now. |

## 12. Evals

| Option | Pros | Cons |
|---|---|---|
| **A. pytest plus one script** that writes the scores into the README | Smallest, all readable. | We build the report format ourselves. |
| **B. Inspect** (UK AI Security Institute, MIT) | Good log viewer for AI-graded tests. | A framework to learn. |
| **C. promptfoo** | Popular, config-driven. | Now owned by OpenAI, with an uncertain future. |

Ruled out:
- **Ragas and DeepEval:** their scores are AI-graded and opaque, which doesn't fit tests against
  labels made by hand.

## 13. Traces and cost reporting

| Option | Pros | Cons |
|---|---|---|
| **A. One trace file per run** (each line is one AI call: prompt, reply, tokens, time) | Free, offline, can be committed as a public example. | No dashboard. |
| **B. Langfuse, self-hosted** | A web UI. | Docker plus Postgres to run. |
| **C. PostHog LLM analytics** | Dashboards with no setup. | Sends data off the machine. SaaS on a free tier. |

## 14. App shape

| Option | Pros | Cons |
|---|---|---|
| **A. A command-line tool writes files, and a static React viewer reads them** | Fewest moving parts. The demo can be hosted free on GitHub Pages. | No starting runs or labelling from the browser. |
| **B. A local API server plus a React app** | Start runs and label in the browser. | A server, two processes, more code. |

## 15. Frontend libraries

| Area | Options |
|---|---|
| **Tables** | (A) a plain `<table>`: nothing to learn, but sorting is our own code. (B) TanStack Table: headless, so we write the markup and it handles sorting and filtering. (C) AG Grid: everything included, but a big black box. |
| **Charts** | (A) Observable Plot: small and SVG-based, also covers a scatter map of the topics. (B) Recharts: made for React, but heavier. (C) visx: very flexible, but a lot to build by hand. |
| **Styling** | (A) CSS modules: plain CSS, nothing extra. (B) Tailwind: fast to write, but long class strings and a build plugin. |
| **Routing** | (A) none: a few views switched in state. (B) TanStack Router: typed URLs, good for filters. (C) React Router: the most common. |

## Projects worth studying

- **BERTopic:** a pipeline that embeds, clusters and names topics.
- **Apple Embedding Atlas:** a Python tool that does the work, plus a separate web viewer.
- **UMBRELA:** an open method for having an AI judge how well a passage answers a query. It is
  the closest prior art to our "answered" check.
- **open-seo:** keyword clustering.
- **Datasette:** a SQLite file plus a viewer.
