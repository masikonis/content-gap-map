import gzip

from cgm.client import Site
from cgm.sitemaps import parse, read_site

URLS = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://piano.example/pricing</loc><lastmod>2026-01-02</lastmod></url>
  <url><loc>https://piano.example/es/precios</loc></url>
</urlset>"""

INDEX = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://piano.example/pages.xml.gz</loc></sitemap>
  <sitemap><loc>https://piano.example/broken.xml</loc></sitemap>
</sitemapindex>"""


def test_parse_reads_pages_and_indexes_gzipped_or_not():
    assert parse(URLS) == ("urls", [("https://piano.example/pricing", "2026-01-02"),
                                    ("https://piano.example/es/precios", "")])
    assert parse(gzip.compress(URLS))[1][0][0] == "https://piano.example/pricing"
    assert parse(INDEX)[0] == "index"


class FakePages:
    """Serves made-up files; robots.txt names one sitemap index."""

    def __init__(self, files):
        self.files, self.robots, self.asked = files, {}, []

    def allowed(self, url):
        class Rules:
            def site_maps(self):
                return ["https://piano.example/index.xml"]
        self.robots["https://piano.example"] = Rules()
        return True

    def fetch_bytes(self, url, limit):
        self.asked.append(url)
        if url not in self.files:
            return 404, (b"", "utf-8")
        return 200, (self.files[url], "utf-8")


def test_read_site_follows_the_index_and_names_each_problem():
    pages = FakePages({"https://piano.example/index.xml": INDEX,
                       "https://piano.example/pages.xml.gz": gzip.compress(URLS),
                       "https://piano.example/broken.xml": b"<urlset><url>"})
    rows, summary = read_site(pages, Site("Piano", "https://piano.example"))
    assert [r["url"] for r in rows] == ["https://piano.example/pricing", "https://piano.example/es/precios"]
    assert summary["sitemaps_read"] == 3 and summary["pages"] == 2
    assert summary["problems"] == ["https://piano.example/broken.xml: not a readable sitemap (ParseError)"]


def test_a_billion_laughs_sitemap_is_refused_not_expanded():
    bomb = (b'<?xml version="1.0"?><!DOCTYPE lol [<!ENTITY lol "lol">'
            b'<!ENTITY lol2 "&lol;&lol;&lol;">]><urlset><url><loc>&lol2;</loc></url></urlset>')
    pages = FakePages({"https://piano.example/index.xml": bomb})
    rows, summary = read_site(pages, Site("Piano", "https://piano.example"))
    assert rows == [] and "not a readable sitemap" in summary["problems"][0]
