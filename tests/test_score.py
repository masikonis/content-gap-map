import csv

from cgm.client import Client, Site
from cgm.score import check, load_answer_key, summarize

QUESTIONS = ["How much do piano lessons cost?", "Can adults learn piano?"]
PHRASES = {"piano lessons cost", "piano lessons near me"}


def test_check_keeps_a_match_whose_quote_exists():
    results = [{"id": 1, "found": True, "suggestion": "piano lessons cost", "reason": "same cost question"},
               {"id": 2, "found": False, "suggestion": "", "reason": "no adult phrase"}]
    rows = check(results, QUESTIONS, PHRASES)
    assert [r["found"] for r in rows] == [True, False]
    assert rows[0]["suggestion"] == "piano lessons cost"


def test_check_turns_an_invented_quote_into_a_miss():
    results = [{"id": 1, "found": True, "suggestion": "piano lesson prices", "reason": "same"}]
    rows = check(results, QUESTIONS, PHRASES)
    assert rows[0]["found"] is False
    assert rows[0]["reason"] == "quoted phrase not in the collected data"
    assert rows[1]["reason"] == "no verdict returned"


def test_answer_key_counts_a_question_once_across_seeds(tmp_path):
    (tmp_path / "answer-key").mkdir()
    with open(tmp_path / "answer-key" / "google-serp-2026-01-01.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "kind", "text"])
        writer.writerow(["piano lessons", "people_also_ask", "How much do piano lessons cost?"])
        writer.writerow(["piano teacher", "people_also_ask", "How much do piano lessons cost?"])
        writer.writerow(["piano lessons", "related_search", "piano lessons for kids"])
    client = Client(tmp_path, "x", "services", "en", "us", [], Site("x", "https://example.com"), [])
    assert load_answer_key(client) == {"How much do piano lessons cost?": ["piano lessons", "piano teacher"]}


def test_summarize_reports_buyer_share_flips_and_agreement():
    def rows(*found):
        return [{"question": q, "found": f} for q, f in zip("abcd", found)]
    passes = {"judge pass 1": rows(True, False, True, True),
              "judge pass 2": rows(True, True, True, True),
              "second judge": rows(True, False, False, True)}
    tags = {"a": {"buyer": True}, "b": {"buyer": True}, "c": {"buyer": False}, "d": {"buyer": True}}
    summary = summarize(passes, tags)
    assert summary["buyer_questions"] == 3
    assert summary["share_found_buyer"] == 0.667
    assert summary["share_found_all"] == 0.75
    assert summary["flip_rate"] == 0.25
    assert summary["judge_agreement"] == 0.75
    assert summary["disagreements"] == 1
