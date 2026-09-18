"""服务端 cron 的入口。

手动跑一次就是『模拟 cron 叫醒它一次』：无人值守，跑完一整轮 + 推送 + 更新 digest。

  python cron_entry.py

调度（GitHub Actions 的 schedule，决定 WHEN）和执行（这个脚本，决定 WHAT）是分开的两层——
agent 本身没有时钟，闹钟必须在外面（见 .github/workflows/daily.yml）。

幂等（重跑安全）：cron 可能延迟/重复触发，digest 去重保证重跑一次也不会重复刷屏。
"""
import run_broadcast

if __name__ == "__main__":
    # 和手动跑同一条路径——区别只是『谁来叫醒它』。
    run_broadcast.main()
