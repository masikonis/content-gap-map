from cgm.score import check, summarize

QUESTIONS = ["How much do piano lessons cost?", "Can adults learn piano?"]
PHRASES = ["piano lessons cost", "piano lessons near me"]


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


def test_summarize_reports_share_and_flips():
    first = [{"seed": "a", "found": True}, {"seed": "a", "found": False},
             {"seed": "b", "found": True}, {"seed": "b", "found": True}]
    second = [{"seed": "a", "found": True}, {"seed": "a", "found": True},
              {"seed": "b", "found": True}, {"seed": "b", "found": True}]
    summary = summarize([first, second])
    assert summary["share_found"] == 0.75
    assert summary["per_seed"] == {"a": "1/2", "b": "2/2"}
    assert summary["flip_rate"] == 0.25
