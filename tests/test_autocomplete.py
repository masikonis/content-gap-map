from pathlib import Path

from cgm.autocomplete import expand, parse
from cgm.profiles import B2B_SOFTWARE, SERVICES, profile
from cgm.client import load_client


def test_expand_covers_seed_question_words_and_alphabet():
    queries = expand("piano lessons")
    assert len(queries) == 1 + len(SERVICES.before) + len(SERVICES.after) + 26
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


def test_each_site_type_gets_its_own_words_and_unknown_types_fall_back():
    assert "piano software alternatives" in expand("piano software", B2B_SOFTWARE)
    assert "best piano software" in expand("piano software", B2B_SOFTWARE)
    assert profile("publisher") == profile("generic")


def test_decode_reads_a_reply_in_the_charset_google_declares():
    import httpx
    from cgm.autocomplete import decode
    body = '["piano", ["piano à queue"], [], {}]'.encode("iso-8859-1")
    response = httpx.Response(200, content=body, headers={"content-type": "text/javascript; charset=ISO-8859-1"})
    assert decode(response)[1] == ["piano à queue"]


def test_an_unknown_site_type_is_refused(tmp_path):
    import pytest
    example = Path(__file__).parent.parent / "examples" / "client.example.toml"
    (tmp_path / "client.toml").write_text(example.read_text().replace('"services"', '"servicez"'))
    with pytest.raises(SystemExit, match="servicez"):
        load_client(tmp_path)
