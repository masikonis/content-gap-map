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
