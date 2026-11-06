# Milestone 3: the right content

[Back to the README](../../README.md)

Milestone 3 reads each compared site and keeps the pages that could answer a commercial buyer, so
the next milestone can match them to topics. This first version reads at rung 1: each site's
sitemap, judged by page address alone.

## Result (2026-11-06)

| Measure | Pass mark | Run 1 | Run 2 (published) |
|---|---|---|---|
| Google's first-ranked pages the tool kept | 90% | **93%** (56 of 60) | **92%** (55 of 60) |

**Milestone 3 passes:** the tool kept at least 90% of the key's pages on two runs in a row with
the same code and the same sitemaps.

**What was measured.** Each of milestone 1's 20 commercial "People also ask" questions was searched
on each compared site in Google (`site:mailchimp.com <question>`), and the first result is the
page the tool must keep: 60 searches, 35 different pages. The key was collected in a real Chrome
session and committed before the tool read any sitemap
([site-search key](../../demo/email-marketing/answer-key/site-search-2026-11-04.csv)).

**What the tool read and kept (published run).**

| Site | Sitemap pages | Other-language pages (code) | Kept by Claude |
|---|---|---|---|
| Mailchimp | 5,416 | none | 1,113 |
| Brevo | 7,126 | 5,307 | 563 |
| MailerLite | 3,446 | 1,577 | 397 |

Every one of the 35 key pages is in a sitemap, so reading loses nothing. One Mailchimp sitemap
file couldn't be read and is named in
[sitemaps-summary.json](../../demo/email-marketing/runs/2026-10-30-0946/sitemaps-summary.json).
Every address, kept or dropped, with its reason, is in
[pages.csv](../../demo/email-marketing/runs/2026-10-30-0946/pages.csv). Two addresses on a
compared site's public blog contain a term on the lab's private blocklist and show
"[withheld]" in its place.

**How to read it.** The key is lenient on purpose: losing a page that answers a buyer turns into a
false gap later, so recall is what is tested, and the tool is told to keep a page when unsure. The
number of pages kept varies more than the key score: Mailchimp 1,283 then 1,113, Brevo 666 then
563, between two runs of the same code.

**What it misses.** Of the five misses on the published run, two are weak picks by Google: an
article on email list churn for "Why are people leaving Mailchimp?", and email design tips for
"Are newsletters still relevant?". One is Mailchimp's newsletter-examples gallery for "What is the
best software to create a newsletter?", which the rule drops on purpose. One is a "what is email
marketing" post for "Is email marketing still worth it?". The last, Brevo's AI email marketing
guide, was kept on one run and dropped on the other.

**How it got here.**
- The first run kept 85% (51 of 60). Six misses were trend and overview posts for "Is email
  marketing still worth it?" and "Are newsletters still relevant?", which the keep rule dropped as
  teaching the subject, though the stage rule counts "is it worth it" as comparing. The keep rule
  was aligned with the stage rule after that result.
- One rerun read sitemap files that had already been masked for privacy, which merged two
  addresses into one. It was discarded; the steps now run on raw data and masking comes last.

**Cost.** One run of the keep step: 19 Claude calls, about 3 minutes of model time, $1.27 at list
price (covered by a Claude subscription); a rerun soon after costs less, because Claude reuses
cached input ($0.24). Reading the three sitemaps takes 17 requests at the polite pace. Every call
is in [trace.jsonl](../../demo/email-marketing/runs/2026-10-30-0946/trace.jsonl).
