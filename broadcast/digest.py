"""卸载（Offload）：把『今日播报』写到上下文窗口之外的文件 digest.md；
明天重跑时读回来，对已经播过的条目去重——避免同一条新闻连续几天重复播报。

核心直觉：agent 的『记性』不在模型里，在你给它的这个文件里。删了它，它就失忆。
"""
import os
import re
import datetime

DIGEST_PATH = os.path.join(os.path.dirname(__file__), "..", "digest.md")


def _key(line: str) -> str:
    """用 URL 当条目指纹做去重。"""
    m = re.search(r"https?://\S+", line)
    return m.group(0).rstrip(").,，。") if m else line.strip()


def load_seen() -> set:
    """卸载：从窗口外的 digest.md 把『已经播过的链接』读回来。"""
    if not os.path.exists(DIGEST_PATH):
        return set()
    seen = set()
    with open(DIGEST_PATH, encoding="utf-8") as f:
        for line in f:
            if "http" in line:
                seen.add(_key(line))
    return seen


def dedup(summary_text: str, seen: set) -> str:
    """去掉已经播过的条目（按 URL 指纹）。"""
    kept = [ln for ln in summary_text.splitlines() if not ("http" in ln and _key(ln) in seen)]
    return "\n".join(kept).strip()


def append(title: str, body: str) -> None:
    """卸载：把今天的播报写回窗口外，明天读回来续上。"""
    stamp = datetime.date.today().isoformat()
    with open(DIGEST_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n\n## {stamp} · {title}\n\n{body}\n")
