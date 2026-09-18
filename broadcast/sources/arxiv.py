"""arXiv 源。

调 arXiv API 踩过的坑，写下来免得下次再踩：
  · 共享同一个 httpx.Client（别每次 new 一个，会把本地节流清零）
  · 带自定义 User-Agent（arXiv 建议标明来源）
  · 每次请求间隔 ≥ 3 秒（arXiv 官方限流要求）
  · 撞 429 就抛出来，别盲目重试 —— 让上层用离线兜底
"""
import time
import httpx
import feedparser

_UA = "ai-broadcast-agent/1.0 (+https://github.com/guo25476688-cmd/ai-broadcast-agent)"
_client = httpx.Client(headers={"User-Agent": _UA}, timeout=30, follow_redirects=True)  # 共享一个 client（follow_redirects：自动跟 301 http→https，否则会抛错跳过）
_last = [0.0]


def _polite() -> None:
    dt = time.time() - _last[0]
    if dt < 3:
        time.sleep(3 - dt)
    _last[0] = time.time()


def fetch(cfg):
    cats = cfg["interests"]["arxiv_categories"]
    n = cfg["sources"]["arxiv"]["max_results"]
    q = "+OR+".join(f"cat:{c}" for c in cats)
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query={q}&sortBy=submittedDate&sortOrder=descending&max_results={n}"
    )
    _polite()
    r = _client.get(url)
    r.raise_for_status()  # 429 直接抛，别盲目重试
    feed = feedparser.parse(r.text)
    items = []
    for e in feed.entries:
        items.append(
            {
                "source": "arXiv",
                "title": " ".join(e.title.split()),
                "url": getattr(e, "id", ""),
                # 摘要本身就是一份天然的「轻量信号」——正文(PDF)是重的，按需才取
                "meta": {"abstract": " ".join(e.summary.split())},
            }
        )
    return items
