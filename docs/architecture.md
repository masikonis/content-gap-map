# Architecture: initial research

**Status: early research, 2026-10-23. Nothing here is decided.**

This page lists the options I found for each part of the tool, with their pros and cons. I'm only
evaluating them for now. I'll go through the build one component at a time, look at each choice
again once I'm working on that part, and make the final call there. As that happens, options get
removed from this page and the choices move to [decisions.md](decisions.md).

Constraints behind the list:

- Free and open-source software and data only. No paid APIs, scrapers or SaaS.
- AI work goes through Claude Code on my existing subscription. No local language models.
- Crawl politely: respect robots.txt and site terms, rate-limit, identify the crawler.

Facts below came from web research on 2026-10-23. Some are not verified yet: a few model
licences, speeds on my machine, and whether the Claude Agent SDK can use a subscription.

## 1. Backend language

| Option | Pros | Cons |
|---|---|---|
| **A. Python** | The best text extraction and clustering libraries only exist here (trafilatura, scikit-learn). Most similar tools are built this way. | A second language next to the TypeScript frontend, and two sets of data types to keep in sync. |
| **B. TypeScript** (Node or Bun) | One language end to end. | Weaker extraction, thin clustering support (small single-author packages), so more code of our own. |
| **C. Python for the pipeline, TypeScript for the viewer** | Each side gets its best tools. The viewer only reads a results file, so the link between them is small. | Two languages and two toolchains. |

## 2. Where questions come from (several can be combined)

| Option | Pros | Cons |
|---|---|---|
| **A. Google autocomplete** | Real searches, any language and country, free, quick to code. | Google's terms forbid automated use, even polite. Could stop working without notice. No search volumes. |
| **B. Bing autocomplete** | Same as A, and different enough to act as a second opinion or held-out test set. | Same terms risk. Less data than Google. |
| **C. Search Console** (own or client site) | The best real data, with impressions and clicks. Free, official API. | Only for sites with access, so not for a public demo or for competitors. |
| **D. Claude web search** (finds real questions in forums, Q&A sites and community threads, keeps the source URL) | Real questions with proof. Covers the "why" and the objections that autocomplete misses. Included in the subscription. | Slower. Results vary from run to run. Coverage depends on what the search finds. |
| **E. Stack Exchange API** | Real, well-structured questions. Free key. | Mostly tech, legal and language topics. Little for local services. |
| **F. Hacker News search API** | Free, no key. Good for B2B software. | Tech topics only. |
| **G. WildChat dataset** (real ChatGPT chats, ODC-BY licence) | The only free, legal source of real questions asked to an AI. | Mostly coding and creative chats from 2023 to 2025. Few buyer questions. |
| **H. Claude-made seed phrases** | Fast, and covers angles nobody has typed yet. | Not real demand. Only usable as seeds that A or B then confirm. |
| **I. "People also ask" collected by hand** for about 10 seeds | Real Google data, fine because a person collects it. A strong test set. | About an hour of work, and it doesn't scale. |

Ruled out:
- **Scraping "People also ask":** Google's robots.txt disallows `/search`, and it shows CAPTCHAs.
- **Reddit:** closing to new developers on 2026-10-31.
- **Quora and review sites (G2, Capterra, Trustpilot):** their terms forbid scraping.
- **DataForSEO, SerpApi:** paid.

## 3. Crawler

| Option | Pros | Cons |
|---|---|---|
| **A. Our own small crawler** (httpx, plus Protego for robots.txt) | A few hundred lines, all readable. Exactly the polite rules we want. | We write sitemap reading, caching and retries ourselves. |
| **B. Scrapy** | Mature. Robots.txt, rate limiting and caching built in. | A whole framework for 3 or 4 sites. |
| **C. Crawlee** (Python or JS) | Switches easily between plain fetching and a real browser. | Built for getting around blocks, which goes against the polite rule. |
| **D. crawl4ai** | Popular, outputs clean Markdown, handles JavaScript pages. | Big, changes fast, carries AI features we won't use. |

Ruled out:
- **Firecrawl:** the self-hosted version needs several services, and AGPL clashes with MIT.

## 4. JavaScript-heavy pages

| Option | Pros | Cons |
|---|---|---|
| **A. Ignore them in v1** | Nothing to install. Most business sites don't need it. | Some competitor sites will come out thin or empty. |
| **B. Playwright, only when a page returns too little text** | Automatic and repeatable. | A large install (a whole browser). |
| **C. Chrome connector, by hand, for the odd page** | Nothing to install. Works on tricky pages. | Slow and manual. Not part of a repeatable run. |

## 5. Pulling the main text out of a page

| Option | Pros | Cons |
|---|---|---|
| **A. trafilatura** | The reference tool. Multilingual. Keeps headings. Scores well on benchmarks. | Can drop content that isn't article-like, such as pricing grids and accordion FAQs. |
| **B. Readability** | Well known (Firefox's reader view). | Built for articles, so worse on service and pricing pages. |
| **C. Keep the whole page as Markdown** (markdownify) | Loses nothing. | Keeps menus, footers and other noise, so matching gets worse. |
| **D. crawl4ai's built-in Markdown** | Comes free with 3D. | Ties extraction to that crawler. |

Add-on for any option: **extruct** reads FAQ and schema data, which gives exact question and
answer pairs without AI.

## 6. Splitting pages into passages

| Option | Pros | Cons |
|---|---|---|
| **A. By heading**, with long sections split further | Follows how the page is written, so each passage stays on one topic. About 30 lines of code. | Pages with poor headings give uneven passages. |
| **B. Fixed size** (for example, every 400 words) | Simplest. | Cuts through the middle of answers. |
| **C. Semantic splitting** (AI decides where topics change) | Clean breaks in theory. | Studies show little gain over A, at more cost. |

## 7. Finding candidate passages for each question

Claude can't read every passage for every question, so code has to shortlist the top 10 or so
first.

| Option | Pros | Cons |
|---|---|---|
| **A. A small local embedding model** (search only, no reasoning) | Finds passages with the same meaning in different words ("how much is it" and "pricing"). Free, same result every run. | About a 1.2 GB download plus PyTorch. The one local model in the plan. |
| **B. Keyword search (BM25)** | Plain code, no AI, tiny, exact. | Misses paraphrases, so some real answers never reach Claude. |
| **C. A and B combined** | Usually finds more than either alone. | Two systems to tune. |
| **D. A free embedding API tier** (Voyage, Gemini) | No local install. | A SaaS account with free-tier limits that can change. |

## 8. Embedding model (only with 7A or 7C)

| Option | Pros | Cons |
|---|---|---|
| **A. Qwen3-Embedding-0.6B** | Strongest at its size, 100+ languages, Apache-2.0. | Questions need a one-line instruction in front. |
| **B. BGE-M3** | Solid, multilingual, MIT, no instruction needed. | A bit older and weaker. |
| **C. EmbeddingGemma-300m** | Smallest and fastest. | Google's own licence terms, not a standard open-source licence. |

## 9. Where vectors live (only with 7A or 7C)

| Option | Pros | Cons |
|---|---|---|
| **A. numpy files on disk** | Nothing to install. Millisecond search at our size. | No queries, just arrays. |
| **B. sqlite-vec** | Vectors in the same SQLite file as everything else. | Younger tool, clunkier queries. |
| **C. LanceDB** | Grows to large data. | Not needed at about 20,000 vectors. |
| **D. pgvector** | The industry standard, good to learn. | Needs a Postgres server, for no gain at this size. |

## 10. Grouping questions into topics

| Option | Pros | Cons |
|---|---|---|
| **A. Agglomerative clustering** (scikit-learn) | Same result every run. One threshold to tune. No need to pick the number of groups. | Needs embeddings (7A or 7C). |
| **B. HDBSCAN** | Finds groups of any shape. | Often throws a large share of short questions out as "noise". |
| **C. BERTopic** | All in one: groups and names topics. | Hides its settings, and results change between runs. |
| **D. Claude groups them directly** | No embeddings needed. Names come out in the same step. | Hard with thousands of questions at once, and less stable across runs. |

## 11. How the pipeline calls Claude

| Option | Pros | Cons |
|---|---|---|
| **A. Python runs the pipeline and calls `claude -p`** for each judging batch | Code stays in charge. `--json-schema` fixes the reply shape. `--output-format json` returns tokens and time, which feed the traces. | Each call starts a new Claude Code process, which is a bit slow. |
| **B. Claude Code runs the pipeline** (a skill that runs Python scripts and judges in between) | Natural in Claude Code. Can use subagents and the Chrome connector. | Less repeatable, harder to trace, and the line between code and AI blurs. |
| **C. Claude Agent SDK** | A clean programming interface. | Normally needs a paid API key rather than a subscription (not verified). |

## 12. Which Claude model per step

| Option | Pros | Cons |
|---|---|---|
| **A. Haiku for bulk steps, Sonnet or Opus for hard ones** | Uses the plan's weekly limit slowly. | Two models to compare in the evals. |
| **B. Sonnet everywhere** | One setting, strong quality. | Uses more of the limit. |
| **C. Opus everywhere** | Best quality. | Uses the limit fastest, and is slower. |

## 13. Storing runs and caching

| Option | Pros | Cons |
|---|---|---|
| **A. SQLite** for the cache and working data, plus one JSON file per run for the viewer | Built into Python. One file. Re-runs reuse cached pages and AI replies. | Some SQL to write. |
| **B. JSON files only** | Simplest, easy to read. | Gets messy as a cache. |
| **C. DuckDB** | Great for analysis. | Not needed at this size. |
| **D. Postgres** | Standard for a hosted service later. | A server to run, for nothing now. |

## 14. Evals

| Option | Pros | Cons |
|---|---|---|
| **A. pytest plus one script** that writes the scores into the README | Smallest, all readable. | We build the report format ourselves. |
| **B. Inspect** (UK AI Security Institute, MIT) | Good log viewer for AI-graded tests. | A framework to learn. |
| **C. promptfoo** | Popular, config-driven. | Now owned by OpenAI, with an uncertain future. |

Ruled out:
- **Ragas and DeepEval:** their scores are AI-graded and opaque, which doesn't fit tests against
  my own hand labels.

## 15. Traces and cost reporting

| Option | Pros | Cons |
|---|---|---|
| **A. One trace file per run** (each line is one AI call: prompt, reply, tokens, time) | Free, offline, can be committed as a public example. | No dashboard. |
| **B. Langfuse, self-hosted** | A web UI. | Docker plus Postgres to run. |
| **C. PostHog LLM analytics** | Dashboards with no setup. | Sends data off the machine. SaaS on a free tier. |

## 16. App shape

| Option | Pros | Cons |
|---|---|---|
| **A. A command-line tool writes files, and a static React viewer reads them** | Fewest moving parts. The demo can be hosted free on GitHub Pages. | No starting runs or labelling from the browser. |
| **B. A local API server plus a React app** | Start runs and label in the browser. | A server, two processes, more code. |

## 17. Frontend libraries (written by hand)

| Area | Options |
|---|---|
| **Tables** | (A) a plain `<table>`: nothing to learn, but I write sorting myself. (B) TanStack Table: headless, so I write the markup and it handles sorting and filtering. (C) AG Grid: everything included, but a big black box. |
| **Charts** | (A) Observable Plot: small and SVG-based, also covers a scatter map of the topics. (B) Recharts: made for React, but heavier. (C) visx: very flexible, but a lot to build by hand. |
| **Styling** | (A) CSS modules: plain CSS, nothing extra. (B) Tailwind: fast to write, but long class strings and a build plugin. |
| **Routing** | (A) none: a few views switched in state. (B) TanStack Router: typed URLs, good for filters. (C) React Router: the most common. |

## 18. Python tooling (only with 1A or 1C)

| Option | Pros | Cons |
|---|---|---|
| **A. uv** | Fast, one tool for Python versions and packages. | Now owned by OpenAI. Stays open source, and the project file is standard, so it's easy to leave. |
| **B. pip + venv** | Built in, no new tool. | Slower and more manual. |
| **C. Poetry** | Mature. | Slower, and losing ground to uv. |

## Projects worth studying

- **BERTopic:** a pipeline that embeds, clusters and names topics.
- **Apple Embedding Atlas:** a Python tool that does the work, plus a separate web viewer.
- **UMBRELA:** an open method for having an AI judge how well a passage answers a query. It is
  the closest prior art to our "answered" check.
- **open-seo:** keyword clustering.
- **Datasette:** a SQLite file plus a viewer.
