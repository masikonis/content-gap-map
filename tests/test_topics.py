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
