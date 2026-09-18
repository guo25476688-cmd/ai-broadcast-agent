"""数据源的 fetch() 用 monkeypatch 掉网络请求，只测『抓回来的数据解析对不对』——
不发真实请求，避免测试因为外部服务限流/封禁（Reddit 对云端出口 IP 尤其敏感）而变得不稳定。
"""
from broadcast.sources import arxiv, hackernews, github_trending, reddit


class FakeResponse:
    def __init__(self, text="", json_data=None, status_code=200):
        self.text = text
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


ARXIV_FEED = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2609.00001v1</id>
    <title>  A Great   Paper  </title>
    <summary>  This is the   abstract.  </summary>
  </entry>
</feed>"""


def test_arxiv_fetch_parses_entries(monkeypatch):
    monkeypatch.setattr(arxiv, "_polite", lambda: None)
    monkeypatch.setattr(arxiv._client, "get", lambda url: FakeResponse(text=ARXIV_FEED))
    cfg = {"interests": {"arxiv_categories": ["cs.AI"]}, "sources": {"arxiv": {"max_results": 5}}}
    items = arxiv.fetch(cfg)
    assert len(items) == 1
    assert items[0]["title"] == "A Great Paper"
    assert items[0]["meta"]["abstract"] == "This is the abstract."


def test_hackernews_fetch_builds_items(monkeypatch):
    hits = {
        "hits": [
            {"objectID": "1", "title": "HN Story", "url": "https://example.com/x", "points": 120, "num_comments": 4}
        ]
    }
    monkeypatch.setattr(hackernews._client, "get", lambda url, params=None: FakeResponse(json_data=hits))
    cfg = {"interests": {"keywords": ["agent"]}, "sources": {"hackernews": {"min_points": 50, "top_n": 10}}}
    items = hackernews.fetch(cfg)
    assert items[0]["title"] == "HN Story"
    assert items[0]["meta"]["points"] == 120


def test_hackernews_fetch_falls_back_to_hn_link(monkeypatch):
    hits = {"hits": [{"objectID": "42", "title": "No URL", "url": None, "points": 10, "num_comments": 0}]}
    monkeypatch.setattr(hackernews._client, "get", lambda url, params=None: FakeResponse(json_data=hits))
    cfg = {"interests": {"keywords": []}, "sources": {"hackernews": {"min_points": 0, "top_n": 10}}}
    items = hackernews.fetch(cfg)
    assert items[0]["url"] == "https://news.ycombinator.com/item?id=42"


GITHUB_TRENDING_HTML = """
<html><body>
<article class="Box-row">
  <h2><a href="/foo/bar">  foo /   bar  </a></h2>
  <p>A cool repo</p>
  <span class="d-inline-block float-sm-right"> 123 stars today </span>
</article>
</body></html>
"""


def test_github_trending_fetch_parses_cards(monkeypatch):
    monkeypatch.setattr(github_trending._client, "get", lambda url: FakeResponse(text=GITHUB_TRENDING_HTML))
    cfg = {"sources": {"github_trending": {"language": "python", "since": "daily", "top_n": 10}}}
    items = github_trending.fetch(cfg)
    assert items[0]["title"] == "foo / bar"
    assert items[0]["url"] == "https://github.com/foo/bar"
    assert "123 stars today" in items[0]["meta"]["stars_today"]


def test_reddit_fetch_filters_by_min_score(monkeypatch):
    payload = {
        "data": {
            "children": [
                {"data": {"title": "Low score", "score": 5, "is_self": False, "url": "https://x.example/1", "permalink": "/r/x/1"}},
                {"data": {"title": "High score", "score": 500, "is_self": True, "url": None, "permalink": "/r/x/2", "selftext": "body"}},
            ]
        }
    }
    monkeypatch.setattr(reddit._client, "get", lambda url, params=None: FakeResponse(json_data=payload))
    cfg = {"sources": {"reddit": {"subreddit": "test", "top_n": 10, "min_score": 30}}}
    items = reddit.fetch(cfg)
    assert len(items) == 1
    assert items[0]["title"] == "High score"
    assert items[0]["url"] == "https://www.reddit.com/r/x/2"
