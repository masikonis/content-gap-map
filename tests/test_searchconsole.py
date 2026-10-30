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


def test_ai_demand_reports_the_ai_share(tmp_path):
    from cgm.client import Client, Site
    from cgm.searchconsole import ai_demand
    client = Client(tmp_path, "x", "services", "en", "us", [], Site("Example Piano School", "https://example.com"), [])
    rows = [{"query": "piano lessons cost", "clicks": "5", "impressions": "300", "ai": False},
            {"query": "piano lesson prices explained -filetype:pdf", "clicks": "0", "impressions": "100", "ai": True}]
    report = ai_demand(client, rows, [tmp_path / "piano.zip"])
    assert "**50% look typed by an AI assistant**" in report
    assert "**25% of the impressions**" in report
