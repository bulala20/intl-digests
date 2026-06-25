# -*- coding: utf-8 -*-
"""Build the site index.html: three dashboard entry cards + recent archive list."""
from __future__ import annotations
import json
import os
from common import esc, SITE_DIR, DATA_DIR, ARCHIVE_DIR, today_str, now_beijing
from datetime import timedelta

DASHBOARDS = [
    ("ai",       "AI 行业晨报",        "AI Industry Daily",       "近7日 AI 圈模型/产品/行业/论文/观点汇总"),
    ("finance",  "国际金融日报",       "Global Finance Daily",    "全球股市/央行/商品/汇率债市/机构观点"),
    ("affairs",  "国际要闻日报",       "World This Week Daily",   "世界杯/科技太空/自然气候/会议展会/商业"),
]

# Read all metas
metas = {}
for name, _, _, _ in DASHBOARDS:
    path = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            metas[name] = json.load(f)


def render_entry_card(name: str, zh: str, en: str, desc: str) -> str:
    m = metas.get(name, {})
    total = m.get("total", 0)
    date_range = m.get("date_range", "")
    gradient = m.get("gradient", "linear-gradient(135deg,#3730a3,#6d28d9)")
    tag = m.get("tag", "")
    sections = m.get("sections", [])
    sec_chips = "".join(
        f'<span class="mini-chip">{esc(s["zh"])} {s["count"]}</span>'
        for s in sections
    )
    return f"""
  <a class="entry" href="{name}/index.html" style="--grad:{gradient}">
    <div class="entry-hero">
      <span class="entry-tag">{esc(tag)}</span>
      <h2>{esc(zh)}</h2>
      <div class="entry-en">{esc(en)}</div>
      <p class="entry-desc">{esc(desc)}</p>
    </div>
    <div class="entry-meta">
      <div class="entry-num"><b>{total}</b><span>条要闻</span></div>
      <div class="entry-range">{esc(date_range)}</div>
    </div>
    <div class="entry-chips">{sec_chips}</div>
    <div class="entry-cta">查看本期 →</div>
  </a>"""


def render_archive_list() -> str:
    if not os.path.isdir(ARCHIVE_DIR):
        return "<p class='empty'>暂无归档</p>"
    days = sorted(os.listdir(ARCHIVE_DIR), reverse=True)[:14]
    if not days:
        return "<p class='empty'>暂无归档</p>"
    rows = []
    for d in days:
        dpath = os.path.join(ARCHIVE_DIR, d)
        if not os.path.isdir(dpath):
            continue
        files = os.listdir(dpath)
        cells = []
        for name, zh, _, _ in DASHBOARDS:
            if f"{name}.html" in files:
                cells.append(f'<a class="arch-link" href="archive/{d}/{name}.html">{zh}</a>')
        cells_html = " · ".join(cells) if cells else "—"
        rows.append(f"""
      <tr>
        <td class="arch-date">{esc(d)}</td>
        <td class="arch-files">{cells_html}</td>
      </tr>""")
    return f"""
    <table class="arch-table">
      <thead><tr><th>日期</th><th>归档内容</th></tr></thead>
      <tbody>{''.join(rows)}
      </tbody>
    </table>"""


def build():
    cards_html = "".join(render_entry_card(name, zh, en, desc) for name, zh, en, desc in DASHBOARDS)
    archive_html = render_archive_list()
    today = today_str()
    now_label = now_beijing().strftime("%Y-%m-%d %H:%M 北京时间")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日国际要闻 · 仪表盘</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#f6f7fb;--ink:#1a1f36;--muted:#6b7280;--line:#e5e7eb}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.6;min-height:100vh}}
.site-hero{{background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 50%,#3730a3 100%);color:#fff;padding:64px 24px 56px;text-align:center;position:relative;overflow:hidden}}
.site-hero::before{{content:"";position:absolute;inset:0;background-image:radial-gradient(circle at 30% 20%,rgba(255,255,255,.10) 0,transparent 40%),radial-gradient(circle at 70% 70%,rgba(255,255,255,.08) 0,transparent 45%);pointer-events:none}}
.site-hero h1{{font-size:38px;font-weight:800;letter-spacing:1px;position:relative}}
.site-hero .sub{{font-size:16px;opacity:.85;margin-top:14px;position:relative}}
.site-hero .ts{{font-size:12px;opacity:.65;margin-top:18px;position:relative}}
.wrap{{max-width:1200px;margin:0 auto;padding:40px 20px}}
.entries{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:22px;margin-bottom:48px}}
.entry{{display:flex;flex-direction:column;text-decoration:none;color:inherit;background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;transition:.22s;position:relative}}
.entry:hover{{transform:translateY(-4px);box-shadow:0 16px 40px rgba(30,27,75,.16);border-color:transparent}}
.entry-hero{{background:var(--grad);color:#fff;padding:24px 22px 22px}}
.entry-tag{{display:inline-block;font-size:11px;letter-spacing:1.5px;background:rgba(255,255,255,.18);padding:4px 10px;border-radius:14px;margin-bottom:10px}}
.entry-hero h2{{font-size:22px;font-weight:800;margin-bottom:4px}}
.entry-en{{font-size:12px;opacity:.8;letter-spacing:1px}}
.entry-desc{{font-size:13px;opacity:.92;margin-top:14px;line-height:1.55}}
.entry-meta{{display:flex;justify-content:space-between;align-items:center;padding:16px 22px;border-bottom:1px solid var(--line)}}
.entry-num b{{font-size:30px;font-weight:800;color:#3730a3}}
.entry-num span{{font-size:12px;color:var(--muted);margin-left:4px}}
.entry-range{{font-size:12px;color:var(--muted);text-align:right;max-width:55%}}
.entry-chips{{padding:12px 22px;display:flex;flex-wrap:wrap;gap:6px;flex:1}}
.mini-chip{{font-size:11px;color:#4b5563;background:#f1f3f9;padding:3px 9px;border-radius:10px}}
.entry-cta{{padding:14px 22px;background:#fafbff;color:#3730a3;font-size:13.5px;font-weight:700;border-top:1px solid var(--line);text-align:center}}
.entry:hover .entry-cta{{background:#3730a3;color:#fff}}
.arch{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px 26px}}
.arch h3{{font-size:18px;font-weight:800;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.arch h3::before{{content:"";width:4px;height:18px;background:#3730a3;border-radius:2px}}
.arch-table{{width:100%;border-collapse:collapse}}
.arch-table th,.arch-table td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);font-size:13px}}
.arch-table th{{color:var(--muted);font-weight:600;font-size:12px}}
.arch-date{{font-weight:700;color:#3730a3;white-space:nowrap}}
.arch-link{{color:#3730a3;text-decoration:none;margin-right:6px}}
.arch-link:hover{{text-decoration:underline}}
.empty{{color:var(--muted);font-size:13px;padding:14px 0}}
.foot{{text-align:center;color:var(--muted);font-size:12px;padding:24px 20px 50px;border-top:1px solid var(--line);margin-top:40px}}
.foot a{{color:#3730a3;text-decoration:none}}
@media(max-width:720px){{.site-hero h1{{font-size:28px}}.entries{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header class="site-hero">
  <h1>每日国际要闻 · 仪表盘</h1>
  <div class="sub">AI 行业 · 国际金融 · 国际要闻 三联仪表盘，每日北京时间早 8 点自动更新</div>
  <div class="ts">最近更新：{now_label}</div>
</header>
<main class="wrap">
  <div class="entries">
{cards_html}
  </div>
  <div class="arch">
    <h3>历史归档（最近 14 期）</h3>
{archive_html}
  </div>
</main>
<footer class="foot">
  <p>本站由 GitHub Actions 每日自动抓取数据生成并部署到 Cloudflare Pages。</p>
  <p style="margin-top:6px">数据源：AI HOT API · RSS 订阅源（东方财富 / 财联社 / NASA / FourFourTwo 等）· 由 WorkBuddy 自动汇总</p>
</footer>
</body>
</html>"""
    out_path = os.path.join(SITE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[INDEX] -> {out_path}")


if __name__ == "__main__":
    build()
