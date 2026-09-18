"""把 digest.md 渲染成一个可以直接双击打开的静态历史播报页面。

digest.md 是卸载（Offload）落盘的『记忆』，本身只是给下一次运行做去重用的纯文本。
这个脚本额外做一件事：把同一份文件渲染成人能舒服浏览的页面——不用另起一个数据库或后端，
数据源永远是 digest.md 这一份文件，页面只是它的一个『视图』。

用法：
    python web/render.py          # 生成 web/index.html
    python -m http.server 8000 -d web   # 本地打开 http://localhost:8000
"""
import os
import re
import html
import datetime

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIGEST_PATH = os.path.join(ROOT, "digest.md")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

DAY_HEADER = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+·\s+(.+)$", re.M)


def parse_days(text: str) -> list[dict]:
    """按 `## YYYY-MM-DD · 标题` 切分成每天一段，最新的排前面。"""
    matches = list(DAY_HEADER.finditer(text))
    days = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        days.append({"date": m.group(1), "title": m.group(2).strip(), "body": text[start:end].strip()})
    days.sort(key=lambda d: d["date"], reverse=True)
    return days


def render(days: list[dict]) -> str:
    tabs = "\n".join(
        f'<button class="day-tab" data-idx="{i}">{d["date"]}</button>' for i, d in enumerate(days)
    )
    panels = "\n".join(
        f'<section class="day-panel" data-idx="{i}" {"" if i == 0 else "hidden"}>'
        f'<h2 class="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">{html.escape(d["title"])}</h2>'
        f'<div class="prose prose-slate dark:prose-invert max-w-none">{markdown.markdown(d["body"])}</div>'
        f"</section>"
        for i, d in enumerate(days)
    )
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>播报历史 · ai-broadcast-agent</title>
<script src="https://cdn.tailwindcss.com?plugins=typography"></script>
</head>
<body class="bg-slate-50 dark:bg-slate-900 min-h-screen">
  <div class="max-w-4xl mx-auto px-4 py-10">
    <header class="mb-8">
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">📡 播报历史</h1>
      <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
        数据源就是仓库里的 digest.md，这个页面只是它的一个只读视图 · 生成于 {generated}
      </p>
    </header>
    <nav class="flex flex-wrap gap-2 mb-8" id="tabs">
      {tabs}
    </nav>
    <main id="panels">
      {panels}
    </main>
  </div>
  <style>
    .day-tab {{
      padding: 0.375rem 0.875rem; border-radius: 9999px; font-size: 0.875rem;
      border: 1px solid rgb(203 213 225); color: rgb(71 85 105); background: white;
      cursor: pointer;
    }}
    .day-tab.active {{ background: rgb(15 23 42); color: white; border-color: rgb(15 23 42); }}
    @media (prefers-color-scheme: dark) {{
      .day-tab {{ background: rgb(30 41 59); color: rgb(203 213 225); border-color: rgb(51 65 85); }}
      .day-tab.active {{ background: white; color: rgb(15 23 42); }}
    }}
  </style>
  <script>
    const tabs = document.querySelectorAll('.day-tab');
    const panels = document.querySelectorAll('.day-panel');
    tabs.forEach(tab => tab.addEventListener('click', () => {{
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const idx = tab.dataset.idx;
      panels.forEach(p => p.hidden = p.dataset.idx !== idx);
    }}));
    if (tabs[0]) tabs[0].classList.add('active');
  </script>
</body>
</html>
"""


def main() -> None:
    if not os.path.exists(DIGEST_PATH):
        raise SystemExit(f"没找到 {DIGEST_PATH}，先跑一次 python run_broadcast.py 生成播报历史。")
    text = open(DIGEST_PATH, encoding="utf-8").read()
    days = parse_days(text)
    if not days:
        raise SystemExit("digest.md 里还没有可解析的播报记录。")
    html_out = render(days)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"✅ 已生成 {OUT_PATH}（共 {len(days)} 天记录）")


if __name__ == "__main__":
    main()
