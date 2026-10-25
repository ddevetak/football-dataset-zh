"""Football Charts API 快速上手：获取中超赛果，画出进球时间分布。

安装依赖后直接运行：
    pip install requests matplotlib
    python fc_api_quickstart_zh.py

不需要密钥（每天 300 次）。有免费密钥时（每天 5,000 次），先设置环境变量：
    export FC_API_KEY=fc_你的密钥        # Windows: set FC_API_KEY=fc_你的密钥

文档：https://www.football-charts.com/zh-cn/developers
数据来源：football-charts.com（使用数据时请注明 "Data by football-charts.com"）
"""
import os

import matplotlib.pyplot as plt
import requests
from matplotlib import font_manager

API = "https://footballcharts-backend.onrender.com/api/v1"
KEY = os.environ.get("FC_API_KEY", "").strip()
HEADERS = {"Authorization": f"Bearer {KEY}"} if KEY else {}


def get(path, **params):
    """GET 一个接口，返回 JSON；出错时打印错误码和说明。"""
    r = requests.get(f"{API}{path}", params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        err = r.json().get("error", {})
        raise SystemExit(f"HTTP {r.status_code} {err.get('code')}: {err.get('message')}")
    return r.json()


# 1. 联赛列表：联赛代码，以及每个联赛免费可查的赛季（当前赛季 + 上一赛季）
leagues = get("/leagues/")["leagues"]
csl = next(lg for lg in leagues if lg["league"] == "china")
print(f"{len(leagues)} 个联赛；中超（{csl['league']}）可查询赛季：{csl['seasons']}")

# 2. 中超 2025 赛季全部赛果：全场比分、半场比分、首个进球的分钟
#    中超是自然年赛制，赛季写作 "2025"；英超等跨年赛制写作 "2025-2026"
season = "2025"
res = get("/leagues/china/results/", season=season)
print(f"中超 {season}：{res['count']} 场比赛，赛季状态 {res['season_state']}")
for m in res["matches"][:3]:
    # 时间均为 UTC，北京时间 = UTC + 8 小时
    print(f"  {m['kickoff_utc']}  {m['homeTeam']} {m['score']} {m['awayTeam']}"
          f"  （半场 {m['ht_result']}，首球 {m['first_goal_time']} 分钟）")

# 3. 进球时间分布：每 15 分钟一段，"45+" 和 "90+" 是上下半场补时
gt = get("/leagues/china/goal-timing/", season=season)
bins, counts = gt["time_bins"], gt["stats"]["period_totals"]
total = sum(counts)
for b, n in zip(bins, counts):
    print(f"  {b:>6}  {n:4d}  {100 * n / total:4.1f}%")

# matplotlib 默认字体不含中文：使用系统里第一个可用的中文字体
installed = {f.name for f in font_manager.fontManager.ttflist}
for name in ("PingFang SC", "Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
             "Source Han Sans SC", "WenQuanYi Zen Hei", "Heiti TC", "Arial Unicode MS"):
    if name in installed:
        plt.rcParams["font.sans-serif"] = [name]
        break
plt.rcParams["axes.unicode_minus"] = False

colors = ["#f59e0b" if b.endswith("+") else "#3b82f6" for b in bins]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(bins, counts, color=colors)
ax.set_title(f"中超 {season} 赛季进球时间分布（{total} 球，橙色为补时）")
ax.set_xlabel("比赛分钟")
ax.set_ylabel("进球数")
fig.text(0.99, 0.01, "Data by football-charts.com", ha="right", fontsize=8, color="#64748b")
fig.tight_layout()
fig.savefig("csl_2025_goal_timing.png", dpi=150)
print("图已保存：csl_2025_goal_timing.png")
print("网页版：", gt["source_url"])
