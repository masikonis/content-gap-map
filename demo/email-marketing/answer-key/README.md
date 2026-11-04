# Answer key (collected 2026-10-30)

`google-serp-2026-10-30.csv`: Google "People also ask" for the 5 seeds, searched in a real Chrome
session with `hl=en&gl=us`, one search at a time: the first 4 questions plus one expansion round.
Seed echoes removed. Questions that appear under several seeds count once when scoring.

`buyer-tags.csv` and `stage-tags.csv`: each question's buyer tag, and each buyer question's funnel
stage, marked by Claude Sonnet and, blind, by Claude Fable.

# Site-search key (collected 2026-11-03 and 2026-11-04)

`site-search-2026-11-04.csv`: the milestone 3 answer key. Each of the 20 commercial questions was
searched on each compared site (`site:mailchimp.com <question>`, `hl=en&gl=us`) in a real Chrome
session signed in to Google, one search at a time, and the top three results were saved. Rank 1
is the page the tool must keep. Google asked to verify a human after 41 searches; collection
stopped and the last 19 MailerLite searches were run the next day, 20 seconds apart. The key was
committed before the tool read any sitemap.
