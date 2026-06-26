# -*- coding: utf-8 -*-
"""Fetch international affairs (non-political) news from RSS feeds, classify, render.

Focus areas: World Cup/Sports, Science & Space, Climate, International Forums/Expos, Business.
Strictly excludes political conflicts / political figures / elections / government policies.

Data sources (domestic + international, all official RSS):
Domestic (国内): 中新网(国际/体育/社会), 人民网国际
International (国外): ESPN, Sky Sports, NASA, ESA, New Scientist, Nature, BBC, Carbon Brief
"""
from __future__ import annotations
import sys
from common import (fetch_rss, fmt_beijing, today_str, now_beijing, classify,
                    render_dashboard, save_dashboard, write_meta)
from datetime import timedelta, datetime, timezone

FEEDS = [
    # 国内 Domestic (official RSS, stable)
    ("https://www.chinanews.com.cn/rss/world.xml",                   "中新网·国际"),
    ("https://www.chinanews.com.cn/rss/sports.xml",                  "中新网·体育"),
    ("https://www.chinanews.com.cn/rss/society.xml",                 "中新网·社会"),
    ("http://www.people.com.cn/rss/world.xml",                       "人民网·国际"),
    # World Cup / Sports (international)
    ("https://www.espn.com/espn/rss/news",                           "ESPN News"),
    ("https://www.skysports.com/rss/0,20514,11661,00.xml",           "Sky Sports Football"),
    # Science & Space (international, official, stable)
    ("https://www.nasa.gov/rss/dyn/breaking_news.rss",               "NASA Breaking News"),
    ("https://www.esa.int/rssfeed/Our_Activities/Space_News",        "ESA Space News"),
    ("https://www.newscientist.com/section/news/feed/",              "New Scientist"),
    ("https://www.nature.com/nature.rss",                            "Nature"),
    # Climate & Environment (international, official)
    ("http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "BBC Science & Environment"),
    ("https://www.carbonbrief.org/feed",                             "Carbon Brief"),
    # General world news (BBC, excludes political by keyword filter)
    ("http://feeds.bbci.co.uk/news/rss.xml",                         "BBC News"),
    ("http://feeds.bbci.co.uk/news/world/rss.xml",                   "BBC World"),
]

SECTION_ORDER = ["世界杯赛况", "科技与太空", "自然与气候", "国际会议与展会", "商业与产业"]
SECTION_META = {
    "世界杯赛况":       ("sports",  "#ea580c", "World Cup"),
    "科技与太空":       ("science", "#1d4ed8", "Science & Space"),
    "自然与气候":       ("climate", "#047857", "Climate"),
    "国际会议与展会":   ("forums",  "#7c3aed", "Forums & Expos"),
    "商业与产业":       ("business","#b45309", "Business"),
}

CLASSIFY_RULES = [
    ("世界杯赛况", ["世界杯", "World Cup", "梅西", "Messi", "姆巴佩", "Mbappé", "C罗", "Ronaldo",
                  "哈兰德", "Haaland", "维尼修斯", "Vinicius", "比赛", "进球", "小组赛", "FIFA",
                  "足球", "Football", "Soccer"]),
    ("科技与太空", ["SpaceX", "星舰", "Starship", "NASA", "火箭", "Rocket", "太空", "Space",
                  "卫星", "Satellite", "登月", "Moon", "火星", "Mars", "AI", "论文", "Nature",
                  "Science", "科学", "发现", "Discovery", "技术", "Technology", "量子"]),
    ("自然与气候", ["气候", "Climate", "厄尔尼诺", "El Niño", "气温", "Temperature",
                  "极端天气", "暴雨", "洪水", "地震", "Earthquake", "火山", "Volcano",
                  "野火", "Wildfire", "环境", "Environment", "碳中和", "碳达峰"]),
    ("国际会议与展会", ["达沃斯", "Davos", "WEF", "论坛", "Forum", "峰会", "Summit", "展会",
                    "Expo", "MWC", "CES", "博鳌", "Boao", "进博会", "CIIE", "大会", "Conference"]),
    ("商业与产业", ["IPO", "财报", "Earnings", "收购", "Acquisition", "并购", "Merger",
                  "融资", "Funding", "债券", "Bond", "股票", "Stock", "市值", "Market Cap",
                  "MSCI", "投资", "Investment", "公司", "Corporation", "Tech", "科技股"]),
]

# Political keywords to filter out strictly
EXCLUDE_KEYWORDS = [
    "选举", "election", "总统", "president", "总理", "prime minister", "议长",
    "主席", "chairman", "党", "party", "政变", "coup", "战争", "war",
    "冲突", "conflict", "制裁", "sanction", "军事", "military", "导弹", "missile",
    "袭击", "attack", "爆炸", "explosion", "伤亡", "casualt",
    "港独", "台独", "藏独", "疆独",  # territorial integrity
]


def is_political(text: str) -> bool:
    t = text.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in t:
            return True
    return False


def fetch_all_feeds():
    items = []
    for url, src in FEEDS:
        print(f"  fetching {src} ...")
        got = fetch_rss(url, limit=40, source_name=src)
        print(f"    -> {len(got)} items")
        items.extend(got)
    return items


def filter_recent(items, days=2):
    cutoff = now_beijing() - timedelta(days=days)
    out = []
    for it in items:
        if is_political(f"{it['title']} {it['summary']}"):
            continue
        if not it["pub_date"]:
            out.append(it)
            continue
        try:
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
        cat = classify(text, CLASSIFY_RULES, "商业与产业")
        buckets[cat].append({
            "date_label": it["pub_label"] or "近期",
            "title": title,
            "summary": it["summary"],
            "source": it["source"],
            "url": it["link"] or "#",
        })
    for s in SECTION_ORDER:
        buckets[s] = buckets[s][:12]
    out = []
    for s in SECTION_ORDER:
        sid, color, en = SECTION_META[s]
        out.append({"id": sid, "zh": s, "en": en, "color": color, "items": buckets[s]})
    return out


def main():
    print("[AFFAIRS] fetching RSS feeds...")
    items = fetch_all_feeds()
    if not items:
        print("[AFFAIRS] no items fetched, abort")
        return 1
    items = filter_recent(items, days=2)
    print(f"[AFFAIRS] recent non-political items: {len(items)}")
    sections = build_sections(items)
    total = sum(len(s["items"]) for s in sections)
    today = today_str()
    date_range = f"{today.replace('-', '.')}（滚动近2日）"

    html_str = render_dashboard(
        title="国际要闻日报 · 今日速览",
        tag="WORLD THIS WEEK · DAILY DIGEST",
        subtitle="聚焦国内外非政治类事件：体育赛况、科技与太空、自然与气候、国际会议与展会、商业与产业。",
        gradient="linear-gradient(135deg,#7c2d12 0%,#c2410c 45%,#ea580c 100%)",
        date_range=date_range,
        period_label="更新日期",
        sections=sections,
        footer_source="中新网 / 人民网 / ESPN / NASA / ESA / New Scientist / Nature / BBC / Carbon Brief 等 RSS 源",
        footer_note="📌 本报告聚焦体育、科技、自然、会议、商业等非政治类国内外事件；时间均为北京时间。",
    )
    save_dashboard("affairs", html_str, today)

    write_meta("affairs", {
        "name": "affairs",
        "title": "国际要闻日报",
        "en": "World This Week Daily",
        "date": today,
        "date_range": date_range,
        "total": total,
        "sections": [{"zh": s["zh"], "en": s["en"], "count": len(s["items"])} for s in sections],
        "gradient": "linear-gradient(135deg,#7c2d12 0%,#c2410c 45%,#ea580c 100%)",
        "tag": "WORLD THIS WEEK · DIGEST",
    })
    print(f"[AFFAIRS] done. total={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
