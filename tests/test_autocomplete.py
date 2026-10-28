from pathlib import Path

from cgm.autocomplete import AFTER, BEFORE, expand, parse
from cgm.client import load_client


def test_expand_covers_seed_question_words_and_alphabet():
    queries = expand("piano lessons")
    assert len(queries) == 1 + len(BEFORE) + len(AFTER) + 26
    assert queries[0] == "piano lessons"
    assert "how much piano lessons" in queries
    assert "piano lessons cost" in queries
    assert "piano lessons z" in queries
    assert len(set(queries)) == len(queries)


def test_parse_pairs_suggestions_with_relevance():
    reply = ["piano lessons", ["piano lessons near me", "piano lessons cost"], ["", ""], [],
             {"google:suggestrelevance": [900, 601]}]
    assert parse(reply) == [("piano lessons near me", 900), ("piano lessons cost", 601)]


def test_parse_handles_a_reply_without_relevance():
    reply = ["piano lessons", ["piano lessons near me"], [], {}]
    assert parse(reply) == [("piano lessons near me", None)]


def test_example_client_file_loads(tmp_path: Path):
    example = Path(__file__).parent.parent / "examples" / "client.example.toml"
    (tmp_path / "client.toml").write_text(example.read_text())
    client = load_client(tmp_path)
    assert client.seeds == ["piano lessons", "piano lessons springfield"]
    assert len(client.competitors) == 2
