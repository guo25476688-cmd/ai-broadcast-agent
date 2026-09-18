"""Reddit 源 —— 用公开只读 JSON 端点（`.json` 后缀），不需要 OAuth。

  · 只读公开数据不用注册 app / 走 OAuth，比 arXiv、GitHub Trending 都省事；
  · 但 Reddit 对没有自定义 User-Agent 的请求很敏感，容易被 429/403，务必带一个具体的 UA；
  · t=day 只看今天的热帖，min_score 过滤掉热度不够的噪声。

⚠️ Reddit 对数据中心 / 云环境的出口 IP 封锁得很激进（包括不少 CI 环境），
   本地家庭网络运行通常没问题；若在 GitHub Actions 里遇到 403，属已知限制——
   run_broadcast.py 的 gather() 会捕获单源异常并跳过，不影响其它源正常播报。
"""
import httpx

_client = httpx.Client(
    timeout=30,
    follow_redirects=True,
    headers={"User-Agent": "ai-broadcast-agent/1.0 (daily digest bot)"},
)


def fetch(cfg):
    c = cfg["sources"]["reddit"]
    sub = c.get("subreddit", "LocalLLaMA")
    n = c.get("top_n", 10)
    min_score = c.get("min_score", 0)
    url = f"https://www.reddit.com/r/{sub}/top.json"
    params = {"limit": n, "t": "day"}
    r = _client.get(url, params=params)
    r.raise_for_status()
    items = []
    for child in r.json().get("data", {}).get("children", []):
        d = child.get("data", {})
        score = d.get("score", 0)
        if score < min_score:
            continue
        permalink = d.get("permalink", "")
        # 纯文字帖（selftext）没有外链，退回帖子本身在 reddit 上的链接
        link = d.get("url") if not d.get("is_self") else f"https://www.reddit.com{permalink}"
        items.append(
            {
                "source": f"Reddit r/{sub}",
                "title": d.get("title") or "(no title)",
                "url": link or f"https://www.reddit.com{permalink}",
                "meta": {"desc": (d.get("selftext") or "")[:300], "points": score},
            }
        )
    return items
