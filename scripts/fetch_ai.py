# -*- coding: utf-8 -*-
"""Fetch AI HOT daily via aihot API and render dashboard HTML.

Strategy: pull last 7 days of dailies (since `since` window is 7 days max),
merge by the 5 fixed sections, render as one weekly rolling dashboard.
"""
from __future__ import annotations
import sys
from datetime import timedelta
from common import (http_get_json, fmt_beijing, today_str, now_beijing,
                    render_dashboard, save_dashboard, write_meta, BEIJING)

API_BASE = "https://aihot.virxact.com/api/public"

SECTION_ORDER = ["模型发布/更新", "产品发布/更新", "行业动态", "论文研究", "技巧与观点"]
SECTION_META = {
    "模型发布/更新": ("models",    "#2563eb", "Models"),
    "产品发布/更新": ("products",  "#7c3aed", "Products"),
    "行业动态":       ("industry",  "#ea580c", "Industry"),
    "论文研究":       ("paper",     "#0891b2", "Research"),
    "技巧与观点":     ("tip",       "#db2777", "Opinion"),
}


def fetch_last_7_days():
    today = now_beijing().date()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    all_data = {}
    for d in dates:
        url = f"{API_BASE}/daily/{d}"
        try:
            data = http_get_json(url)
            all_data[d] = data
            print(f"  fetched {d}: {len(data.get('sections', []))} sections")
        except Exception as e:
            print(f"  [WARN] {d}: {e}")
    return all_data, dates


def build_sections(all_data: dict, dates: list[str]) -> list[dict]:
    sections_items = {s: [] for s in SECTION_ORDER}
    for d in reversed(dates):  # newest last; we render oldest->newest by global numbering
        data = all_data.get(d)
        if not data:
            continue
        bj_label = fmt_beijing(data.get("generatedAt", d + "T00:00:00Z"))
        for sec in data.get("sections", []):
            label = sec.get("label", "")
            if label in sections_items:
                for it in sec.get("items", []):
                    sections_items[label].append({
                        "date_label": bj_label,
                        "title": it.get("title", ""),
                        "summary": it.get("summary", ""),
                        "source": it.get("sourceName", ""),
                        "url": it.get("sourceUrl", "#"),
                    })

    out = []
    for s in SECTION_ORDER:
        sid, color, en = SECTION_META[s]
        out.append({
            "id": sid, "zh": s, "en": en, "color": color,
            "items": sections_items[s],
        })
    return out


def main():
    print("[AI] fetching last 7 days from aihot API...")
    all_data, dates = fetch_last_7_days()
    if not all_data:
        print("[AI] no data fetched, abort")
        return 1

    sections = build_sections(all_data, dates)
    total = sum(len(s["items"]) for s in sections)
    today = today_str()
    date_range = f"{dates[0].replace('-', '.')} — {dates[-1][-5:].replace('-', '.')}"

    html_str = render_dashboard(
        title="AI 行业晨报 · 近七日回顾",
        tag="AI HOT · WEEKLY DIGEST",
        subtitle="汇聚近七日 AI 圈模型 / 产品 / 行业 / 论文 / 观点五大版块要闻，一站式速览。",
        gradient="linear-gradient(135deg,#1e1b4b 0%,#3730a3 45%,#6d28d9 100%)",
        date_range=date_range,
        period_label="日期范围",
        sections=sections,
        footer_source="AI HOT (aihot.virxact.com)",
        footer_note="本仪表盘滚动展示近 7 天 AI HOT 日报汇总，每日自动更新。",
    )
    save_dashboard("ai", html_str, today)

    write_meta("ai", {
        "name": "ai",
        "title": "AI 行业晨报",
        "en": "AI Industry Daily",
        "date": today,
        "date_range": date_range,
        "total": total,
        "sections": [{"zh": s["zh"], "en": s["en"], "count": len(s["items"])} for s in sections],
        "gradient": "linear-gradient(135deg,#1e1b4b 0%,#3730a3 45%,#6d28d9 100%)",
        "tag": "AI HOT · DIGEST",
    })
    print(f"[AI] done. total={total}, date_range={date_range}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
