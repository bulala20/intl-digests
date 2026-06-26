# -*- coding: utf-8 -*-
"""Fetch finance news from RSS feeds (domestic + international), classify, render.

Data sources (all free, official RSS — domestic + international):
Domestic (国内):
- 中新网财经 (官方 RSS, stable)
- 人民网国际 (官方 RSS)
International (国外):
- CNBC Top News (official RSS)
- Investing.com News (official RSS)
- MarketWatch (official RSS)
- BBC Business (official RSS)
- Financial Times (official RSS)

RSSHub public instance (rsshub.app) is unreliable (403), so we use official RSS only.
"""
from __future__ import annotations
import sys
from common import (fetch_rss, fmt_beijing, today_str, now_beijing, classify,
                    render_dashboard, save_dashboard, write_meta)
from datetime import timedelta

FEEDS = [
    # 国内 Domestic (official RSS, stable)
    ("https://www.chinanews.com.cn/rss/finance.xml",                "中新网·财经"),
    ("https://www.chinanews.com.cn/rss/scroll-news.xml",            "中新网·即时"),
    ("http://www.people.com.cn/rss/world.xml",                      "人民网·国际"),
    # 国外 International (official RSS)
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html",       "CNBC Top News"),
    ("https://www.investing.com/rss/news_1.rss",                    "Investing.com"),
    ("http://feeds.marketwatch.com/marketwatch/topstories/",        "MarketWatch"),
    ("http://feeds.bbci.co.uk/news/business/rss.xml",               "BBC Business"),
    ("https://www.ft.com/rss/home",                                 "Financial Times"),
]

SECTION_ORDER = ["股市行情", "央行与货币政策", "大宗商品", "汇率与债市", "要闻与机构观点"]
SECTION_META = {
    "股市行情":         ("stocks",  "#dc2626", "Stocks"),
    "央行与货币政策":   ("central", "#0e7490", "Central Banks"),
    "大宗商品":         ("commod",  "#ca8a04", "Commodities"),
    "汇率与债市":       ("fxbond",  "#4338ca", "FX & Bonds"),
    "要闻与机构观点":   ("watch",   "#be185d", "Market Watch"),
}

# Keyword classification rules. Order matters; first match wins.
CLASSIFY_RULES = [
    ("央行与货币政策", ["美联储", "Fed", "央行", "利率", "LPR", "加息", "降息", "议息", "BoJ", "日央行", "欧央行", "ECB", "货币政策", "PCE", "通胀"]),
    ("大宗商品",       ["黄金", "金价", "原油", "油价", "布伦特", "WTI", "铜", "铝", "金属", "大宗", "白银", "天然气"]),
    ("汇率与债市",     ["美元", "美债", "国债", "收益率", "人民币", "汇率", "美元指数", "在岸", "离岸", "日元", "欧元", "债券", "信用债"]),
    ("股市行情",       ["美股", "A股", "上证", "深证", "创业板", "纳指", "纳斯达克", "道指", "道琼斯", "标普", "恒生", "日经", "指数", "市值", "熔断", "KOSPI", "股市", "收盘", "大涨", "暴跌"]),
]


def fetch_all_feeds():
    items = []
    for url, src in FEEDS:
        print(f"  fetching {src} ...")
        got = fetch_rss(url, limit=40, source_name=src)
        print(f"    -> {len(got)} items")
        items.extend(got)
    return items


def filter_recent(items, days=2):
    """Keep only items published within last `days` days (by pub_date if available)."""
    cutoff = now_beijing() - timedelta(days=days)
    out = []
    for it in items:
        if not it["pub_date"]:
            out.append(it)  # keep if no date
            continue
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(it["pub_date"].replace("Z", "+00:00"))
            if dt.astimezone(timezone.utc) >= cutoff:
                out.append(it)
        except Exception:
            out.append(it)
    return out


def build_sections(items):
    buckets = {s: [] for s in SECTION_ORDER}
    seen_titles = set()
    for it in items:
        title = it["title"]
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        text = f"{title} {it['summary']}"
        cat = classify(text, CLASSIFY_RULES, "要闻与机构观点")
        buckets[cat].append({
            "date_label": it["pub_label"] or "近期",
            "title": title,
            "summary": it["summary"],
            "source": it["source"],
            "url": it["link"] or "#",
        })
    # Cap each section to 20; reserve at least 5 slots for international sources
    DOMESTIC = {"中新网·财经", "中新网·即时", "人民网·国际"}
    for s in SECTION_ORDER:
        domestic = [it for it in buckets[s] if it["source"] in DOMESTIC]
        intl = [it for it in buckets[s] if it["source"] not in DOMESTIC]
        buckets[s] = (domestic[:15] + intl[:5])[:20]
    out = []
    for s in SECTION_ORDER:
        sid, color, en = SECTION_META[s]
        out.append({"id": sid, "zh": s, "en": en, "color": color, "items": buckets[s]})
    return out


def main():
    print("[FINANCE] fetching RSS feeds...")
    items = fetch_all_feeds()
    if not items:
        print("[FINANCE] no items fetched, abort")
        return 1
    items = filter_recent(items, days=2)
    print(f"[FINANCE] recent items: {len(items)}")
    sections = build_sections(items)
    total = sum(len(s["items"]) for s in sections)
    today = today_str()
    date_range = f"{today.replace('-', '.')}（滚动近2日）"

    html_str = render_dashboard(
        title="国际金融日报 · 今日速览",
        tag="GLOBAL FINANCE · DAILY DIGEST",
        subtitle="每日汇总国内外财经要闻：股市行情、央行政策、大宗商品、汇率债市与机构观点。",
        gradient="linear-gradient(135deg,#064e3b 0%,#0f766e 50%,#155e75 100%)",
        date_range=date_range,
        period_label="更新日期",
        sections=sections,
        footer_source="中新网 / 人民网 / CNBC / Investing.com / MarketWatch / BBC / FT 等 RSS 源",
        footer_note="⚠️ 风险提示：本报告仅汇总公开财经资讯与市场数据，不构成任何投资建议。股市、商品、汇率波动存在风险，据此操作风险自担。",
    )
    save_dashboard("finance", html_str, today)

    write_meta("finance", {
        "name": "finance",
        "title": "国际金融日报",
        "en": "Global Finance Daily",
        "date": today,
        "date_range": date_range,
        "total": total,
        "sections": [{"zh": s["zh"], "en": s["en"], "count": len(s["items"])} for s in sections],
        "gradient": "linear-gradient(135deg,#064e3b 0%,#0f766e 50%,#155e75 100%)",
        "tag": "GLOBAL FINANCE · DIGEST",
    })
    print(f"[FINANCE] done. total={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
