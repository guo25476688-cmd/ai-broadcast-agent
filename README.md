# 📡 ai-broadcast-agent

一个每天自动跑的多源 AI 资讯播报 Agent —— 附带一组**可量化的 context engineering 对照实验**。

它不只是"抓新闻 + 调 LLM 总结"，核心是回答一个具体的工程问题：**同样一份"今日 AI 资讯播报"，主上下文的 token 消耗能差多少？差在哪几个技巧上？**

[![tests](https://github.com/guo25476688-cmd/ai-broadcast-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/guo25476688-cmd/ai-broadcast-agent/actions/workflows/tests.yml)
[![daily-broadcast](https://github.com/guo25476688-cmd/ai-broadcast-agent/actions/workflows/daily.yml/badge.svg)](https://github.com/guo25476688-cmd/ai-broadcast-agent/actions/workflows/daily.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 项目故事

这个项目最初是一次 context engineering 练习的产物：写一个每日播报 agent，顺手把"隔离 / 按需检索 / 压缩 / 卸载"这几个 context 工程技巧的效果量出来。练习本身跑通之后，我觉得这套流水线值得当成一个真正在用的工具，于是继续往下做了几件事：

- 把 LLM 后端从练习用的内部网关换成了 **DeepSeek**（OpenAI 兼容协议）——别人 clone 下来配一个自己的 key 就能真的跑起来，而不是对着一套只有我能访问的接口看代码；
- 加了一个新的数据源 **Reddit**（第 4 个源，复用同一套"轻量抓取 → 子 agent 摘要"的隔离流水线，验证这套架构确实能横向扩展）；
- 加了一个**静态历史播报页**（`web/`），把 `digest.md` 这份纯文本记忆渲染成可以直接打开浏览的页面；
- 补了单元测试、CI、`.gitignore`、`.env.example`、LICENSE 这些原来没有的工程基本功。

下面的内容按现在的样子写，不是练习时的样子。

## 这个项目在做什么

每天自动从四个信息源拉取内容：

- **arXiv**（cs.AI / cs.CL / cs.LG 最新论文）
- **Hacker News**（按关键词 + 最低分数过滤的热帖）
- **GitHub Trending**（按语言 / 周期）
- **Reddit**（指定 subreddit 的当日热帖，公开 JSON 端点，无需 OAuth）

拉回来之后，不是简单拼接丢给一个大模型了事，而是走一套有意识设计的流水线：

```
              ┌─────────────┐   ┌───────────────┐   ┌──────────────┐
  arXiv    →  │  轻量抓取    │ → │  子 Agent 摘要 │ → │              │
  HN       →  │ (标题/链接/  │ → │ (各源独立窗口, │ → │  主编排合成   │
  GitHub   →  │  元数据，    │ → │  只回传摘要，  │ → │  → 去重      │ → 投递（邮件/飞书/本地）
  Reddit   →  │  不抓正文)   │   │  预算封顶)     │   │              │
              └─────────────┘   └───────────────┘   └──────────────┘
```

对应四个 context engineering 技巧：

| 技巧                               | 在项目里的落地                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------- |
| **按需检索**（Just-in-time retrieval） | 第一轮只抓标题/链接/元数据这些轻量条目，不抓整页正文                                                           |
| **隔离**（Isolation）                | 每个数据源派一个独立的子 Agent，在干净上下文里读条目、只回传一段摘要——原文从不进入主上下文                                     |
| **压缩**（Compaction）               | 每个子 Agent 的摘要有硬性 token 预算（`config.yaml` 里的 `per_source_summary_tokens`），逼着它做取舍而不是有闻必录 |
| **卸载**（Offloading）               | 播报历史落盘到 `digest.md`，下一次运行读回来做跨天去重——"记忆在文件里，不在模型的上下文里"                                 |

## 播报内容、选取逻辑、适合谁看

**播报什么**：每天的内容都是围绕 `config.yaml` 里 `interests.keywords` 这几个关键词（默认是 `LLM agent`、`context engineering`、`MCP`、`RAG`、`agent`）筛出来的——具体到条目，大概是这几类：

- 新发的 arXiv 论文（agent 可靠性、评估方法、RAG 相关的研究）
- Hacker News 上的热门讨论（工程实践、社区争论）
- GitHub Trending 上冒出来的新项目（今天在被大家攒 star 的工具）
- Reddit（默认 r/LocalLLaMA）上的当日热帖（更偏爱好者/实践者视角，比如本地部署、跑分、踩坑记录）

**为什么选这四个源、这几个关键词**：不是照抄某个"AI 资讯榜单"，而是我自己想每天看到的东西——我在跟进 agent 工程这个方向，关心的不是"又发布了一个新模型"这种大众新闻，而是具体的工程做法（怎么设计上下文、怎么做工具调用、怎么评估 agent 是否真的完成了任务）。四个源刻意选得视角不同：arXiv 给"学术前沿在研究什么"，Hacker News 给"工程师社区在讨论什么"，GitHub Trending 给"大家实际在用什么新工具"，Reddit 给"动手做的人踩了什么坑"——单独看任何一个源都会有偏向，合在一起才是相对完整的一天。这套关键词/源的组合完全是我自己的偏好，换成你关心的方向（比如前端性能、Rust、量化交易），改 `config.yaml` 就行，不用碰代码。

**适合谁用**：

- 想每天花几分钟跟进 LLM agent / context engineering 这个细分领域进展，又不想手动刷四五个网站的人
- 更广义地说：任何想要"每天自动汇总某个细分主题、跑在自己 GitHub 仓库里、完全自己掌控关键词和投递方式"的人——这个项目本质是一个可以套壳换主题的模板，agent 工程只是我自己套的第一层壳

## 用数字说话：naive vs 正确版

项目自带一个对照实验，两条命令跑同一份数据，对比主上下文的 `input_tokens`：

```bash
# 反面教材：把每条链接的整页正文都塞进主上下文
python run_broadcast.py --naive

# 正确版：隔离 + 按需检索，主上下文只看得到摘要
python run_broadcast.py
```

| 模式        | 主上下文能看到什么           | 主上下文 input_tokens |
| --------- | ------------------- | ----------------- |
| `--naive` | 每条链接的整页正文（去标签后的粗文本） | **11653**         |
| 默认（正确版）   | 只有各源子 Agent 回传的摘要   | **654**           |

> 同一份 arXiv / HN / GitHub Trending 数据，正确版的主上下文 input_tokens 只有 naive 版的 **5.6%**（省了 94%）。子 Agent 在各自窗口里另外烧了 1754 token 读原始条目，但这些 token 从没进过主上下文——隔离的意义就在这里：贵的部分被隔离在子窗口里，主编排只看得到浓缩后的摘要。（实测环境：`config.yaml` 默认配置，未接入 Reddit 源。）

这个对比是本项目最想讲清楚的一件事：**上下文工程不是玄学，是可以用同一份数据、同一个任务，跑出两个数字来对比的**。

## 架构

```
run_broadcast.py         # 主编排：抓取 → 隔离摘要 → 合成 → 去重 → 投递
cron_entry.py             # 无人值守入口，GitHub Actions 每天调用它
config.yaml               # 关注的关键词 / 数据源开关 / 投递渠道
digest.md                 # 播报历史（跨天去重用，也是 web/ 页面的数据源）
broadcast/
  agent_llm.py             # LLM 调用封装（complete / text_of），默认接 DeepSeek
  sources/
    arxiv.py                # arXiv API
    hackernews.py            # HN Algolia 搜索 API
    github_trending.py       # GitHub Trending 页面解析
    reddit.py                # Reddit 公开 JSON 端点
  summarize.py              # 隔离：每源一个子 Agent，只回传摘要
  digest.py                  # 卸载 + 压缩：落盘、跨天去重
  deliver/
    __init__.py               # 按 config 的 channel 分发投递
    mailer.py                  # Gmail / SMTP
    feishu.py                  # 飞书自定义机器人 webhook
web/
  render.py                 # 把 digest.md 渲染成静态历史播报页 web/index.html
tests/                     # pytest 单元测试（数据源解析、去重逻辑、LLM 封装）
.github/workflows/
  daily.yml                  # 每日定时任务：跑播报 → 渲染页面 → 提交回仓库
  tests.yml                   # push / PR 时跑一遍 pytest
```

## 快速开始

```bash
git clone https://github.com/guo25476688-cmd/ai-broadcast-agent.git
cd ai-broadcast-agent
pip install -r requirements.txt
cp .env.example .env   # 填入 LLM_API_KEY，以及 SMTP / 飞书 webhook（按需）
python run_broadcast.py
```

`LLM_API_KEY` 默认接 [DeepSeek](https://platform.deepseek.com)：国内直连不用挂梯子，价格便宜（具体单价以官网当前定价为准），申请一个 key 填进 `.env` 就能跑通全部功能，包括下面的 naive/正确版对照实验。想换别的 OpenAI 兼容服务（Kimi / 通义 / 自建网关），改 `.env` 里的 `LLM_BASE_URL` / `LLM_MODEL` 即可，不用碰代码。

在 `config.yaml` 里改你关心的关键词、数据源开关和投递渠道，也不用改代码：

```yaml
interests:
  keywords: ["LLM agent", "context engineering", "MCP", "RAG", "agent"]
sources:
  arxiv: { enabled: true, max_results: 8 }
  hackernews: { enabled: true, top_n: 15, min_points: 50 }
  github_trending: { enabled: true, language: "python", since: "daily", top_n: 10 }
  reddit: { enabled: true, subreddit: "LocalLLaMA", top_n: 10, min_score: 30 }
delivery:
  channel: feishu   # gmail / feishu / local
```

## 查看历史播报

`digest.md` 是纯文本记忆，`web/render.py` 把它渲染成一个可以直接双击打开的静态页面——不需要数据库、不需要后端，数据源始终是仓库里的这一份文件：

```bash
python web/render.py                  # 生成 web/index.html
python -m http.server 8000 -d web     # 或者本地起个静态服务器打开
```

GitHub Actions 每天跑完播报后会自动重新渲染并提交这个页面，所以仓库里的 `web/index.html` 始终是最新的。

**在线看（不用 clone）**：仓库里配好了 `.github/workflows/pages.yml` 和 `daily.yml` 里的部署步骤，会自动把 `web/` 发布到 GitHub Pages。首次使用需要在自己仓库的 Settings → Pages → Build and deployment → Source 里选一次 **GitHub Actions**（一次性设置，仓库 owner 才能改，所以工具帮不了这一步）；开完之后地址是：

```
https://guo25476688-cmd.github.io/ai-broadcast-agent/
```

之后每次 push 到 `web/**`，或者每天的定时任务跑完，页面都会自动更新。

## 自动化部署

`.github/workflows/daily.yml` 配置了每日定时任务：push 到自己的仓库、在 Settings → Secrets 配好 `LLM_API_KEY` 和投递渠道凭据，就能免费每天自动跑，本地关机也不影响。`tests.yml` 则在每次 push / PR 时跑一遍单元测试。

⚠️ Reddit 对数据中心出口 IP 封锁得比较激进，GitHub Actions 环境偶尔会抓不到 Reddit（`gather()` 对每个源都做了异常隔离，单源失败不影响其它源正常播报）。本地家庭网络运行通常没有这个问题。

## 工程规范

- `tests/` + `tests.yml`：数据源解析、去重逻辑、LLM 封装都有单元测试覆盖，用 `pytest -q` 跑
- `.env.example`：所有需要的环境变量都在这里列清楚，凭据本身走 `.env`（已 `.gitignore`）
- `LICENSE`：MIT

## 技术栈

Python · httpx · PyYAML · python-dotenv · OpenAI SDK（接 DeepSeek）· BeautifulSoup · feedparser · Markdown · pytest · GitHub Actions

## 示例输出

摘自 `digest.md` 里某一天的真实播报（完整历史见 [digest.md](digest.md) 或 `web/index.html`）：

```
# 今日 AI Agent 播报

> 去重合并后共 8 条，按重要性排序

## 🔬 研究与评估

1. 量化前沿 LLM Agent 的虚报倾向
首个系统量化 agent 虚报任务完成（overclaiming）的实证研究，直指长时自主 agent 的可信度
与输出验证核心问题，是 agent 评估领域的重要基准。
→ arxiv 论文

## 🛠️ 框架与工具

3. Strands Agents Harness SDK ⭐ GitHub Trending
生产级 agent 框架，支持 Python & TypeScript、任意模型/云，提供端到端 agent harness 控制。
→ GitHub
```

---

*灵感来自一次 context engineering 练习，此后按自己的想法独立迭代扩展。*
