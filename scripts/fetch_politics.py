# -*- coding: utf-8 -*-
"""Fetch international politics news from RSS feeds, classify, render.

Focus areas: diplomacy, multilateral institutions, elections and political
dynamics, conflict and security, policy and governance.

Data sources (domestic + international, all public RSS):
Domestic (国内): 中新网国际, 人民网国际
International (国外): BBC World, The Guardian World, Al Jazeera, France 24,
NPR World, UN News, Crisis Group, Politico Europe, Foreign Affairs
"""
from __future__ import annotations
import sys
from datetime import datetime, timedelta, timezone
from common import (fetch_rss, today_str, now_beijing, classify,
                    render_dashboard, save_dashboard, write_meta)

FEEDS = [
    # 国内 Domestic (official RSS, stable)
    ("https://www.chinanews.com.cn/rss/world.xml",                  "中新网·国际"),
    ("http://www.people.com.cn/rss/world.xml",                      "人民网·国际"),
    # 国外 International (public RSS)
    ("http://feeds.bbci.co.uk/news/world/rss.xml",                  "BBC World"),
    ("https://www.theguardian.com/world/rss",                       "The Guardian World"),
    ("https://www.aljazeera.com/xml/rss/all.xml",                   "Al Jazeera"),
    ("https://www.france24.com/en/rss",                             "France 24"),
    ("https://feeds.npr.org/1004/rss.xml",                          "NPR World"),
    ("https://news.un.org/feed/subscribe/en/news/all/rss.xml",      "UN News"),
    ("https://www.crisisgroup.org/rss",                             "Crisis Group"),
    ("https://www.politico.eu/feed/",                               "Politico Europe"),
    ("https://www.foreignaffairs.com/rss.xml",                      "Foreign Affairs"),
]

SECTION_ORDER = ["外交与双边关系", "国际组织与多边机制", "选举与政局", "冲突与安全", "政策与治理"]
SECTION_META = {
    "外交与双边关系":     ("diplomacy", "#b91c1c", "Diplomacy"),
    "国际组织与多边机制": ("multilateral", "#7c2d12", "Multilateral"),
    "选举与政局":         ("elections", "#4338ca", "Elections"),
    "冲突与安全":         ("security", "#be123c", "Security"),
    "政策与治理":         ("policy", "#0f766e", "Governance"),
}

POLITICAL_KEYWORDS = [
    "政治", "外交", "外长", "国务卿", "大使", "使馆", "会晤", "会谈", "访问", "条约",
    "协议", "联合国", "安理会", "欧盟", "北约", "世贸", "七国集团", "二十国集团", "金砖",
    "选举", "投票", "民调", "总统", "总理", "首相", "政府", "内阁", "议会", "国会",
    "政党", "候选人", "公投", "政变", "抗议", "制裁", "战争", "冲突", "停火", "和谈",
    "军事", "国防", "边境", "难民", "移民", "关税", "法案", "政策", "宪法", "法院",
    "politic", "diplomacy", "diplomatic", "foreign minister", "secretary of state",
    "ambassador", "embassy", "envoy", "treaty", "agreement", "bilateral", "relations",
    "united nations", "security council", "european union", "nato", "wto", "g7", "g20",
    "brics", "asean", "election", "vote", "poll", "referendum", "president",
    "prime minister", "government", "cabinet", "parliament", "congress", "lawmaker",
    "party", "candidate", "campaign", "coup", "protest", "sanction", "war", "conflict",
    "ceasefire", "peace talks", "military", "defence", "defense", "border", "refugee",
    "migration", "tariff", "bill", "policy", "constitution", "court",
]

CLASSIFY_RULES = [
    ("国际组织与多边机制", [
        "联合国", "安理会", "欧盟", "北约", "世贸", "七国集团", "二十国集团", "金砖",
        "东盟", "国际刑事法院", "国际法院", "多边", "峰会", "united nations",
        "security council", "european union", "nato", "wto", "g7", "g20", "brics",
        "asean", "icc", "icj", "multilateral", "summit",
    ]),
    ("冲突与安全", [
        "战争", "冲突", "停火", "和谈", "军事", "国防", "边境", "制裁", "袭击",
        "导弹", "武器", "war", "conflict", "ceasefire", "peace talks", "military",
        "defence", "defense", "border", "sanction", "attack", "missile", "weapon",
    ]),
    ("外交与双边关系", [
        "外交", "外长", "国务卿", "大使", "使馆", "会晤", "会谈", "访问", "条约",
        "协议", "双边", "关系", "diplomacy", "diplomatic", "foreign minister",
        "secretary of state", "ambassador", "embassy", "envoy", "talks", "visit",
        "treaty", "agreement", "bilateral", "relations",
    ]),
    ("选举与政局", [
        "选举", "投票", "民调", "总统", "总理", "首相", "政府", "内阁", "议会",
        "国会", "政党", "候选人", "公投", "政变", "抗议", "election", "vote",
        "poll", "referendum", "president", "prime minister", "government", "cabinet",
        "parliament", "congress", "lawmaker", "party", "candidate", "campaign",
        "coup", "protest",
    ]),
    ("政策与治理", [
        "难民", "移民", "关税", "法案", "政策", "宪法", "法院", "预算", "监管",
        "治理", "refugee", "migration", "tariff", "bill", "policy", "constitution",
        "court", "budget", "regulation", "governance",
    ]),
]


def is_political(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in POLITICAL_KEYWORDS)


def fetch_all_feeds():
    items = []
    for url, src in FEEDS:
        print(f"  fetching {src} ...")
        got = fetch_rss(url, limit=40, source_name=src)
        print(f"    -> {len(got)} items")
        items.extend(got)
    return items


def item_timestamp(item: dict) -> float:
    if not item.get("pub_date"):
        return 0
    try:
        dt = datetime.fromisoformat(item["pub_date"].replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0


def filter_recent_politics(items, days=2):
    cutoff = now_beijing() - timedelta(days=days)
    out = []
    for it in items:
        text = f"{it['title']} {it['summary']}"
        if not is_political(text):
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
    return sorted(out, key=item_timestamp, reverse=True)


def build_sections(items):
    buckets = {s: [] for s in SECTION_ORDER}
    seen_titles = set()
    for it in items:
        title = it["title"]
        normalized = " ".join(title.lower().split())
        if not title or normalized in seen_titles:
            continue
        seen_titles.add(normalized)
        text = f"{title} {it['summary']}"
        cat = classify(text, CLASSIFY_RULES, "政策与治理")
        buckets[cat].append({
            "date_label": it["pub_label"] or "近期",
            "title": title,
            "summary": it["summary"],
            "source": it["source"],
            "url": it["link"] or "#",
        })

    # Cap each section to 30; keep international feeds prominent for this board.
    DOMESTIC = {"中新网·国际", "人民网·国际"}
    for s in SECTION_ORDER:
        domestic = [it for it in buckets[s] if it["source"] in DOMESTIC]
        intl = [it for it in buckets[s] if it["source"] not in DOMESTIC]
        buckets[s] = (intl[:20] + domestic[:10])[:30]

    out = []
    for s in SECTION_ORDER:
        sid, color, en = SECTION_META[s]
        out.append({"id": sid, "zh": s, "en": en, "color": color, "items": buckets[s]})
    return out


def main():
    print("[POLITICS] fetching RSS feeds...")
    items = fetch_all_feeds()
    if not items:
        print("[POLITICS] no items fetched, abort")
        return 1
    items = filter_recent_politics(items, days=2)
    print(f"[POLITICS] recent political items: {len(items)}")
    sections = build_sections(items)
    total = sum(len(s["items"]) for s in sections)
    today = today_str()
    date_range = f"{today.replace('-', '.')}（滚动近2日）"

    html_str = render_dashboard(
        title="国际政治日报 · 今日速览",
        tag="GLOBAL POLITICS · DAILY DIGEST",
        subtitle="聚焦国际政治动态：外交关系、多边机制、选举政局、冲突安全与政策治理。",
        gradient="linear-gradient(135deg,#111827 0%,#7f1d1d 48%,#b45309 100%)",
        date_range=date_range,
        period_label="更新日期",
        sections=sections,
        footer_source="中新网 / 人民网 / BBC / The Guardian / Al Jazeera / France 24 / NPR / UN News / Crisis Group / Politico Europe / Foreign Affairs 等 RSS 源",
        footer_note="注：本报告仅汇总公开来源的国际政治新闻，不代表任何政治立场；时间均为北京时间。",
    )
    save_dashboard("politics", html_str, today)

    write_meta("politics", {
        "name": "politics",
        "title": "国际政治日报",
        "en": "Global Politics Daily",
        "date": today,
        "date_range": date_range,
        "total": total,
        "sections": [{"zh": s["zh"], "en": s["en"], "count": len(s["items"])} for s in sections],
        "gradient": "linear-gradient(135deg,#111827 0%,#7f1d1d 48%,#b45309 100%)",
        "tag": "GLOBAL POLITICS · DIGEST",
    })
    print(f"[POLITICS] done. total={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
