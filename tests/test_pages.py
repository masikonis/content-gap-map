import csv

from cgm.client import Client, Site
from cgm.pages import code_reason, judge, key_test


def test_code_drops_other_languages_sites_files_and_duplicates():
    seen = set()
    reason = lambda url: code_reason(url, "piano.example", "en", seen)
    assert reason("https://piano.example/pricing") is None
    assert reason("https://www.piano.example/pricing/") == "duplicate"
    assert reason("https://piano.example/fr/tarifs") == "other language"
    assert reason("https://piano.example/en-gb/pricing") is None
    assert reason("https://piano.example/guide.pdf") == "not a page"
    assert reason("https://other.example/pricing") == "other website"
    assert reason("https://help.piano.example/start") is None


def test_judge_drops_addresses_without_a_verdict(monkeypatch, tmp_path):
    from cgm import pages
    monkeypatch.setattr(pages.claude, "ask", lambda *a, **k: {"keep": [1, 7]})
    kept = judge("Piano", "Piano", "piano lessons", ["https://p.example/pricing", "https://p.example/jobs"],
                 tmp_path / "trace.jsonl")
    assert kept == {"https://p.example/pricing"}


def test_key_test_counts_first_ranked_pages_kept(tmp_path):
    (tmp_path / "answer-key").mkdir()
    with open(tmp_path / "answer-key" / "site-search-2026-01-01.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["site", "question", "rank", "url", "collected"])
        writer.writerow(["Piano", "How much?", "1", "https://www.p.example/pricing/", "2026-01-01"])
        writer.writerow(["Piano", "How much?", "2", "https://p.example/jobs", "2026-01-01"])
        writer.writerow(["Piano", "Best school?", "1", "https://p.example/best", "2026-01-01"])
    client = Client(tmp_path, "x", "services", "en", "us", [], Site("Piano", "https://p.example"), [])
    test = key_test(client, {("p.example", "/pricing"): True, ("p.example", "/best"): False})
    assert test["kept"] == 1 and test["share_kept"] == 0.5 and test["passes"] is False
    assert test["missed"][0]["url"] == "https://p.example/best"
