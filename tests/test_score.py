import csv

from cgm.client import Client, Site
from cgm.score import accuracy, check, load_answer_key, summarize

QUESTIONS = ["How much do piano lessons cost?", "Can adults learn piano?"]
PHRASES = ["piano lessons cost", "piano lessons near me"]


def test_check_turns_phrase_numbers_into_phrases():
    results = [{"id": 1, "found": True, "phrases": [1, 2], "reason": "same cost question"},
               {"id": 2, "found": False, "phrases": [], "reason": "no adult phrase"}]
    rows = check(results, QUESTIONS, PHRASES)
    assert [r["found"] for r in rows] == [True, False]
    assert rows[0]["matches"] == ["piano lessons cost", "piano lessons near me"]


def test_check_turns_a_phrase_number_outside_the_list_into_a_miss():
    results = [{"id": 1, "found": True, "phrases": [3], "reason": "same"}]
    rows = check(results, QUESTIONS, PHRASES)
    assert rows[0]["found"] is False
    assert rows[0]["reason"] == "phrase numbers not in the list"
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
        return [{"question": q, "found": f, "matches": ["p"] if f else []} for q, f in zip("abcd", found)]
    passes = {"judge pass 1": rows(True, False, True, True),
              "judge pass 2": rows(True, True, True, True),
              "second judge": rows(True, False, False, True)}
    tags = {"a": {"buyer": True}, "b": {"buyer": True}, "c": {"buyer": False}, "d": {"buyer": True}}
    summary = summarize(passes, tags, {"p": {"autocomplete"}})
    assert summary["buyer_questions"] == 3
    assert summary["share_found_buyer"] == 0.667
    assert summary["share_found_all"] == 0.75
    assert summary["flip_rate"] == 0.25
    assert summary["judge_agreement"] == 0.75
    assert summary["disagreements"] == 1


def test_summarize_credits_each_source_and_keeps_unverified_apart():
    first = [{"question": "a", "found": True, "matches": ["typed"]},
             {"question": "b", "found": True, "matches": ["written"]},
             {"question": "c", "found": True, "matches": ["unchecked"]}]
    passes = {"judge pass 1": first, "judge pass 2": first, "second judge": first}
    tags = {q: {"buyer": True} for q in "abc"}
    sources = {"typed": {"autocomplete"}, "written": {"websearch"}, "unchecked": {"websearch-unverified"}}
    summary = summarize(passes, tags, sources)
    assert summary["share_found_buyer"] == 0.667
    assert summary["share_found_buyer_by_source"]["all sources, with unverified"] == 1.0
    assert summary["share_found_buyer_by_source"]["autocomplete"] == 0.333
    assert summary["buyer_questions_only_one_source_found"] == {
        "autocomplete": ["a"], "searchconsole": [], "searchconsole, AI searches": [],
        "websearch, with unverified": ["b", "c"], "predicted": []}


def test_accuracy_counts_only_reviewed_questions():
    rows = [{"question": "a", "found": True}, {"question": "b", "found": False},
            {"question": "c", "found": True}]
    assert accuracy(rows, {"a": True, "b": True}) == 0.5


def test_shortlists_keep_seed_phrases_plus_close_wordings():
    from cgm.score import shortlists
    phrases = ["piano lessons cost", "piano lessons near me", "piano tuning",
               "guitar lessons cost", "violin lessons", "cheapest music teacher"]
    key = {"How much do piano lessons cost?": ["piano lessons"],
           "Who is the cheapest music teacher?": ["piano lessons"]}
    lists = shortlists(key, phrases, ["piano lessons", "guitar lessons"])
    base, extra = lists["How much do piano lessons cost?"]
    # "piano" is rarer than "lessons", so the seed list holds the piano phrases only.
    assert base == ("piano lessons cost", "piano lessons near me", "piano tuning")
    # A close wording without the seed's word still reaches the judge through the extras.
    assert "cheapest music teacher" in lists["Who is the cheapest music teacher?"][1]
    assert "cheapest music teacher" not in lists["Who is the cheapest music teacher?"][0]


def test_stem_joins_singular_and_plural():
    from cgm.text import stem
    assert stem("prices") == stem("price") == stem("pricing")
    assert stem("alternatives") == stem("alternative")
    assert stem("boxes") == "box" and stem("class") == "class" and stem("cleaning") == "clean"


def test_accuracy_is_none_when_no_question_was_reviewed():
    assert accuracy([{"question": "a", "found": True}], {}) is None


def test_headline_uses_real_phrases_and_predicted_shares_use_the_extended_pass():
    real = [{"question": "a", "found": True, "matches": ["typed"]},
            {"question": "b", "found": False, "matches": []}]
    extended = [{"question": "a", "found": True, "matches": ["typed"]},
                {"question": "b", "found": True, "matches": ["guessed"]}]
    passes = {"judge pass 1": real, "judge pass 2": real, "second judge": real,
              "with predicted and unverified": extended}
    tags = {"a": {"buyer": True}, "b": {"buyer": True}}
    summary = summarize(passes, tags, {"typed": {"autocomplete"}, "guessed": {"predicted"}})
    assert summary["share_found_buyer"] == 0.5
    assert summary["share_found_buyer_by_source"]["all sources, with predicted"] == 1.0
    assert summary["buyer_questions_only_one_source_found"]["predicted"] == ["b"]
