from cgm.topics import apply_merges, assign, merge_variants, pair_test


def test_merge_variants_joins_rewordings_and_keeps_the_shortest():
    variants = merge_variants(["cost piano lessons", "piano lessons cost", "piano lesson costs",
                               "piano lessons for adults"])
    assert variants == {"cost piano lessons": ["cost piano lessons", "piano lesson costs", "piano lessons cost"],
                        "piano lessons for adults": ["piano lessons for adults"]}


def test_assign_keeps_the_first_topic_and_rescues_phrases_left_out():
    phrases = ["piano lessons cost", "piano lesson prices", "piano lessons for adults", "piano tuning"]
    answer = [{"name": "Cost", "phrases": [1, 2, 9]}, {"name": "Adults", "phrases": [2, 3]}]
    topics, missing = assign(answer, phrases)
    assert topics == [("Cost", ["piano lessons cost", "piano lesson prices"]),
                      ("Adults", ["piano lessons for adults"]), ("piano tuning", ["piano tuning"])]
    assert missing == 1


def test_apply_merges_joins_each_topic_once():
    topics = [("A", ["a"]), ("B", ["b"]), ("C", ["c"])]
    assert apply_merges(topics, [[1, 3], [3, 2]]) == [("A", ["a", "c"]), ("B", ["b"])]


def test_pair_test_scores_same_question_pairs_and_different_ones():
    topic_of = {"a1": 1, "a2": 1, "b1": 2, "b2": 1}
    result = pair_test(topic_of, [{"a1", "a2"}, {"b1", "b2"}])
    assert result["share_together"] == 0.5
    assert result["share_apart"] == 0.5
