import zipfile

from cgm.searchconsole import read_export


def test_read_export_takes_queries_from_the_zip(tmp_path):
    path = tmp_path / "piano-questions.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Queries.csv", "Top queries,Clicks,Impressions,CTR,Position\n"
                                  "how much do piano lessons cost,3,120,2.5%,8.1\n")
        z.writestr("Filters.csv", "Filter,Value\nDate,Last 12 months\n")
    assert read_export(path) == [{"query": "how much do piano lessons cost", "clicks": "3",
                                  "impressions": "120", "position": "8.1",
                                  "export": "piano-questions.zip"}]


def test_ai_style_spots_search_commands_prompts_and_long_queries():
    from cgm.searchconsole import ai_style
    assert ai_style("piano lesson prices explained -filetype:pdf")
    assert ai_style("context: location: united states. question: are piano lessons worth it?")
    assert ai_style("what should i look for when choosing a piano teacher for a nervous adult beginner")
    assert not ai_style("how much do piano lessons cost")
