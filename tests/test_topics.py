from cgm.topics import apply_merges, assign, merge_variants, nearest_seed, pair_test


def test_merge_variants_joins_rewordings_and_ignores_years():
    variants = merge_variants(["cost piano lessons", "piano lessons cost", "piano lesson costs 2025",
                               "piano lessons for adults"])
    assert variants == {"cost piano lessons": ["cost piano lessons", "piano lesson costs 2025",
                                               "piano lessons cost"],
                        "piano lessons for adults": ["piano lessons for adults"]}


def test_assign_keeps_the_first_topic_and_rescues_phrases_left_out():
    phrases = ["piano lessons cost", "piano lesson prices", "piano lessons for adults", "piano tuning"]
    answer = [{"name": "Cost?", "phrases": [1, 2, 9]}, {"name": "Adults?", "phrases": [2, 3]}]
    topics, missing = assign(answer, phrases)
    assert topics == [("Cost?", ["piano lessons cost", "piano lesson prices"]),
                      ("Adults?", ["piano lessons for adults"]), ("piano tuning", ["piano tuning"])]
    assert missing == 1


def test_apply_merges_joins_each_topic_once_under_the_new_name():
    topics = [("A?", ["a"]), ("B?", ["b"]), ("C?", ["c"])]
    merges = [{"topics": [1, 3], "name": "AC?"}, {"topics": [3, 2], "name": "CB?"}]
    assert apply_merges(topics, merges) == [("AC?", ["a", "c"]), ("B?", ["b"])]


def test_nearest_seed_picks_the_seed_sharing_most_words():
    seeds = ["piano lessons", "piano lessons for adults"]
    assert nearest_seed("best piano lessons for adults", seeds) == "piano lessons for adults"
    assert nearest_seed("guitar tuning", seeds) == "piano lessons"


def test_pair_test_scores_against_a_random_baseline():
    topic_of = {"a1": 1, "a2": 1, "b1": 2, "b2": 1}
    result = pair_test(topic_of, [{"a1", "a2"}, {"b1", "b2"}])
    assert result["share_together"] == 0.5
    assert result["share_together_per_question"] == 0.5
    assert result["share_apart"] == 0.5
    assert set(result["random_baseline"]) == {"share_together", "share_together_per_question", "share_apart"}


def test_lump_sample_skips_single_phrase_topics_and_is_repeatable():
    from cgm.topics import lump_sample
    topics = [(f"t{n}?", ["a", "b"] if n % 2 else ["a"]) for n in range(1, 161)]
    # Every fourth odd topic is learning stage, so it is dropped and never picked.
    marked = ["learning" if n % 8 == 1 else "comparing" for n in range(1, 161)]
    picked = lump_sample(topics, marked)
    assert len(picked) == 40 and picked == lump_sample(topics, marked)
    assert all(n % 2 and n % 8 != 1 for n in picked)


def test_lump_check_counts_a_missing_verdict_as_a_fail(monkeypatch, tmp_path):
    from cgm import topics as t
    many = [(f"t{n}?", ["a", "b"]) for n in range(1, 41)]
    answer = {"topics": [{"id": i, "one_page": i not in (2, 3, 4), "reason": "r"} for i in range(1, 40)]}
    monkeypatch.setattr(t.claude, "ask", lambda *a, **k: answer)
    result = t.lump_check(many, ["choosing"] * 40, tmp_path / "trace.jsonl")
    assert result["one_page"] == 36 and result["passes"] is True
    assert [f["reason"] for f in result["not_one_page"]] == ["r", "r", "r", "no verdict"]


def test_apply_splits_moves_phrases_once_and_drops_emptied_topics():
    from cgm.topics import apply_splits
    topics = [("Cost?", ["a", "b", "c"]), ("Hours?", ["d"])]
    splits = [{"topic": 1, "phrases": [2, 3, 9], "name": "Worth it?"},
              {"topic": 1, "phrases": [3, 1], "name": "Other?"},
              {"topic": 2, "phrases": [1], "name": "Opening?"},
              {"topic": 5, "phrases": [1], "name": "Bad?"}]
    result, made = apply_splits(topics, splits)
    assert result == [("Worth it?", ["b", "c"]), ("Other?", ["a"]), ("Opening?", ["d"])]
    assert made == 3


def test_stage_check_counts_keep_or_drop_agreement(monkeypatch, tmp_path):
    from cgm import topics as t
    many = [(f"t{n}?", ["a"]) for n in range(1, 41)]
    marked = ["learning"] * 10 + ["comparing"] * 30
    # The judge marks 1..39 choosing and gives no verdict for 40.
    def ask(prompt, schema, model, trace, label):
        return {"stages": [{"id": i, "stage": "choosing"} for i in range(1, 40)]}
    monkeypatch.setattr(t.claude, "ask", ask)
    result = t.stage_check(many, marked, tmp_path / "trace.jsonl")
    # It differs on the 10 learning topics, and the missing verdict counts as a difference.
    assert result["same_keep_or_drop"] == 29 and result["passes"] is False
    assert result["same_stage"] == 0


def test_stage_mark_keeps_an_item_with_no_verdict(monkeypatch, tmp_path):
    from cgm import stage
    monkeypatch.setattr(stage.claude, "ask", lambda *a, **k: {"stages": [{"id": 1, "stage": "learning"},
                                                                          {"id": 9, "stage": "choosing"}]})
    marks = stage.mark(["what is x", "x pricing"], "sonnet", tmp_path / "trace.jsonl", "test")
    assert marks == ["learning", "unknown"]
    assert [stage.kept(m) for m in marks] == [False, True]


def test_vote_keeps_pairs_most_groupings_agree_on():
    from cgm.topics import vote
    first = [("Cost?", ["cost", "price", "fees"]), ("Near me?", ["near me"])]
    second = [("Cost?", ["cost", "price"]), ("Fees?", ["fees", "near me"])]
    third = [("Price?", ["cost", "price"]), ("Fees?", ["fees"]), ("Near me?", ["near me"])]
    topics = sorted(vote([first, second, third]))
    # cost and price agree in all three; fees joins nothing in two of three, near me neither.
    assert topics == [("Cost?", ["cost", "price"]), ("Fees?", ["fees"]), ("Near me?", ["near me"])]
