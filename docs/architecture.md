# Architecture: open options

The parts of the tool that are not decided yet, each with its options, pros and cons. Each part is
decided when the build reaches it, using what the earlier parts showed. A decided part leaves this
page, and its choice is in [decisions.md](decisions.md).

Decided so far: where questions come from, the backend language and its tooling, how the
pipeline calls Claude, which model does each step, traces, how runs are stored, how evals work,
the command-line shape, and two constraints behind every option below (free software and data
only; AI through Claude Code). Crawling is always polite: robots.txt, rate limits and an honest
crawler name.

Sites are read in rungs (see [decisions.md](decisions.md)), so not every part is needed at once.
The first version, at rung 1 (sitemap), needs grouping (8) and a viewer (9). The crawler and
JavaScript pages (1, 2) join at rung 2. Text extraction, splitting and passage search (3 to 5) join
at rung 3. The embedding model and vector storage (6, 7) join at rung 3, or at rung 1 if grouping
uses embeddings.

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

## 9. Frontend libraries

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
