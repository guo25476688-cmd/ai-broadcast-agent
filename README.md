# 📡 ai-broadcast-agent

一个每日多源 AI 资讯聚合与播报 Agent —— 附带一组**可量化的 context engineering 对照实验**。

它不只是"抓新闻 + 调 LLM 总结",核心目的是回答一个工程问题：**同样一份"今日 AI 资讯播报"，主上下文的 token 消耗能差多少？差在哪四个技巧上？**

---

## 这个项目在做什么

每天自动从三个信息源拉取内容：

- **arXiv**（cs.AI / cs.CL / cs.LG 最新论文）
- **Hacker News**（按关键词 + 最低分数过滤的热帖）
- **GitHub Trending**（按语言 / 周期）

拉回来之后，不是简单拼接丢给一个大模型了事，而是走一套有意识设计的流水线：

```
              ┌─────────────┐   ┌───────────────┐   ┌──────────────┐
  arXiv    →  │  轻量抓取    │ → │  子 Agent 摘要 │ → │              │
  HN       →  │ (标题/链接/  │ → │ (各源独立窗口, │ → │  主编排合成   │
  GitHub   →  │  元数据，    │ → │  只回传摘要，  │ → │  → 去重      │ → 投递（邮件/飞书/本地）
              │  不抓正文)   │   │  预算封顶)     │   │              │
              └─────────────┘   └───────────────┘   └──────────────┘
```

对应四个 context engineering 技巧：

| 技巧                               | 在项目里的落地                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------- |
| **按需检索**（Just-in-time retrieval） | 第一轮只抓标题/链接/元数据这些轻量条目，不抓整页正文                                                           |
| **隔离**（Isolation）                | 每个数据源派一个独立的子 Agent，在干净上下文里读条目、只回传一段摘要——原文从不进入主上下文                                     |
| **压缩**（Compaction）               | 每个子 Agent 的摘要有硬性 token 预算（`config.yaml` 里的 `per_source_summary_tokens`），逼着它做取舍而不是有闻必录 |
| **卸载**（Offloading）               | 播报历史落盘到 `digest.md`，下一次运行读回来做跨天去重——"记忆在文件里，不在模型的上下文里"                                 |

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
| `--naive` | 每条链接的整页正文（去标签后的粗文本） | `<跑一次填进来>`        |
| 默认（正确版）   | 只有各源子 Agent 回传的摘要   | `<跑一次填进来>`        |

> 跑一次 `python run_broadcast.py --naive` 和 `python run_broadcast.py`，把打印出来的两行 `input_tokens` 数字填进上表，再算一下省了百分之多少——这就是"隔离 + 按需检索"实打实省下来的钱和注意力窗口。子 Agent 在各自窗口里另外消耗的 token 不计入主上下文，但会打印出来供参考。

这个对比是本项目最想讲清楚的一件事：**上下文工程不是玄学，是可以用同一份数据、同一个任务，跑出两个数字来对比的**。

## 架构

```
run_broadcast.py         # 主编排：抓取 → 隔离摘要 → 合成 → 去重 → 投递
config.yaml               # 关注的关键词 / 数据源开关 / 投递渠道
digest.md                 # 播报历史（跨天去重用）
broadcast/
  agent_llm.py             # LLM 调用封装（complete / text_of）
  sources/
    arxiv.py                # arXiv API
    hackernews.py            # HN Algolia 搜索 API
    github_trending.py       # GitHub Trending 页面解析
  summarize.py              # 隔离：每源一个子 Agent，只回传摘要
  digest.py                  # 卸载 + 压缩：落盘、跨天去重
  deliver/
    __init__.py               # 按 config 的 channel 分发投递
    mailer.py                  # Gmail / SMTP
    feishu.py                  # 飞书自定义机器人 webhook
.github/workflows/         # 每日定时任务（GitHub Actions）
```

## 快速开始

```bash
git clone https://github.com/guo25476688-cmd/ai-broadcast-agent.git
cd ai-broadcast-agent
pip install -r requirements.txt
cp .env.example .env   # 填入 API key / SMTP 或飞书 webhook（按需）
python run_broadcast.py
```

在 `config.yaml` 里改你关心的关键词、数据源开关和投递渠道即可，不用改代码：

```yaml
interests:
  keywords: ["LLM agent", "context engineering", "MCP", "RAG", "agent"]
sources:
  arxiv: { enabled: true, max_results: 8 }
  hackernews: { enabled: true, top_n: 15, min_points: 50 }
  github_trending: { enabled: true, language: "python", since: "daily", top_n: 10 }
delivery:
  channel: feishu   # gmail / feishu / local
```

## 自动化部署

`.github/workflows/` 里配置了每日定时任务，push 到自己的仓库、配好 Secrets（API key、投递渠道凭据）就能免费每天自动跑，本地关机也不影响。

## 技术栈

Python · httpx · PyYAML · python-dotenv · GitHub Actions

## 示例输出

（跑一次 `python run_broadcast.py`，把 `digest.md` 里最新一天的片段贴在这里，作为效果展示）

```
<粘贴一段真实的播报输出>
```

---

*这个项目最初源于一次 context engineering 的课堂练习，此后独立迭代扩展。*
