"""
ai-news-spider: HTML-источники AI-лабораторий → синтетические RSS 2.0.

Для каждого источника:
  1. загружает index-страницу (crawl4ai)
  2. достаёт ссылки на статьи по link_pattern
  3. параллельно загружает каждую статью
  4. извлекает заголовок, дату публикации, краткое описание
  5. собирает RSS 2.0 в feeds/<slug>.xml
"""
from __future__ import annotations

import asyncio
import html
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import yaml
from feedgen.feed import FeedGenerator

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

HERE = Path(__file__).parent
FEEDS_DIR = HERE / "feeds"
FEEDS_DIR.mkdir(exist_ok=True)

META_DATE_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+property=["\']og:updated_time["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']publish_date["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']pubdate["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<time[^>]+datetime=["\']([^"\']+)["\']', re.I),
]

JSON_DATE_PATTERNS = [
    re.compile(r'"datePublished"\s*:\s*"([^"]+)"'),
    re.compile(r'"publishedOn"\s*:\s*"([^"]+)"'),
    re.compile(r'"publishedAt"\s*:\s*"([^"]+)"'),
    re.compile(r'"published_at"\s*:\s*"([^"]+)"'),
    re.compile(r'"first_published_at"\s*:\s*"([^"]+)"'),
    re.compile(r'"dateCreated"\s*:\s*"([^"]+)"'),
    re.compile(r'"_createdAt"\s*:\s*"([^"]+)"'),
]

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
HUMAN_DATE_RE = re.compile(r'\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(20\d{2})\b')

META_DESC_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\']([^"\']+)["\']', re.I),
]

META_TITLE_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<title[^>]*>([^<]+)</title>', re.I),
]

URL_DATE_PATTERN = re.compile(r'/(\d{4})/(\d{2})(?:/(\d{2}))?/')


@dataclass
class Article:
    url: str
    title: str
    published: datetime
    description: str


def parse_iso(s: str) -> Optional[datetime]:
    s = s.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def first_match(patterns, html_text: str) -> Optional[str]:
    for p in patterns:
        m = p.search(html_text)
        if m:
            return html.unescape(m.group(1)).strip()
    return None


def extract_date_from_json(html_text: str) -> Optional[datetime]:
    for p in JSON_DATE_PATTERNS:
        m = p.search(html_text)
        if not m:
            continue
        dt = parse_iso(m.group(1))
        if dt:
            return dt
    return None


def extract_human_date(html_text: str) -> Optional[datetime]:
    m = HUMAN_DATE_RE.search(html_text)
    if not m:
        return None
    month = MONTHS.get(m.group(1).lower())
    if not month:
        return None
    try:
        return datetime(int(m.group(3)), month, int(m.group(2)), tzinfo=timezone.utc)
    except Exception:
        return None


def extract_date_from_url(url: str) -> Optional[datetime]:
    m = URL_DATE_PATTERN.search(url)
    if not m:
        return None
    y, mo, d = m.group(1), m.group(2), m.group(3) or "01"
    try:
        return datetime(int(y), int(mo), int(d), tzinfo=timezone.utc)
    except Exception:
        return None


def clean_text(s: str, max_chars: int = 500) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_chars:
        s = s[: max_chars].rsplit(" ", 1)[0] + "…"
    return s


def build_browser_config(stealth: bool) -> BrowserConfig:
    if stealth:
        return BrowserConfig(headless=True, verbose=False, browser_mode="dedicated")
    return BrowserConfig(headless=True, verbose=False)


def build_run_config(src: dict, for_index: bool) -> CrawlerRunConfig:
    cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=60000,
        excluded_tags=["nav", "footer", "aside", "form"],
        remove_overlay_elements=True,
    )
    if for_index:
        wait_until = src.get("wait_until")
        if wait_until:
            cfg.wait_until = wait_until
        wait_selector = src.get("wait_selector")
        if wait_selector:
            cfg.wait_for = f"css:{wait_selector}"
    return cfg


async def collect_article_links(crawler: AsyncWebCrawler, src: dict) -> list[str]:
    cfg = build_run_config(src, for_index=True)
    res = await crawler.arun(url=src["index_url"], config=cfg)
    if not res.success:
        print(f"  ! index failed: {res.error_message}", file=sys.stderr)
        return []
    pattern = re.compile(src["link_pattern"])
    internal = res.links.get("internal") if isinstance(res.links, dict) else []
    seen: set[str] = set()
    out: list[str] = []
    for l in internal or []:
        href = l.get("href") if isinstance(l, dict) else l
        if not href:
            continue
        if not pattern.search(href):
            continue
        clean = href.split("?")[0].split("#")[0].rstrip("/")
        if clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return out


async def fetch_article(crawler: AsyncWebCrawler, src: dict, url: str, sem: asyncio.Semaphore) -> Optional[Article]:
    async with sem:
        cfg = build_run_config(src, for_index=False)
        try:
            res = await crawler.arun(url=url, config=cfg)
        except Exception as e:
            print(f"  ! {url}: {e}", file=sys.stderr)
            return None
        if not res.success:
            print(f"  ! {url}: {res.error_message}", file=sys.stderr)
            return None

        raw_html = res.html or ""
        title = first_match(META_TITLE_PATTERNS, raw_html) or ""
        title = re.sub(r"\s*[|·–-]\s*[^|·–-]+$", "", title).strip()

        dt_raw = first_match(META_DATE_PATTERNS, raw_html)
        dt = parse_iso(dt_raw) if dt_raw else None
        if dt is None:
            dt = extract_date_from_json(raw_html)
        if dt is None:
            dt = extract_date_from_url(url)
        if dt is None:
            dt = extract_human_date(raw_html)
        if dt is None:
            # Fallback: используем момент паучения. Без этого статьи без meta-date
            # отбрасываются полностью, что и было корнем «spider даёт 0».
            # Дубли защищены через rss_seen_articles + rss_post_mirrors UNION в qvabo.
            dt = datetime.now(timezone.utc)

        desc = first_match(META_DESC_PATTERNS, raw_html) or ""
        desc = clean_text(desc, 500)

        # Антипротухание: title и description гигиена.
        title_clean = clean_text(title, 300)
        if not title_clean or len(title_clean) < 20:
            return None
        stop_words_re = re.compile(
            r"\b(coming\s+soon|we\s+will\s+announce|stay\s+tuned|sponsored|whitepaper|"
            r"join\s+the\s+webinar|register\s+now|sign\s+up\s+today|press\s+release)\b",
            re.I,
        )
        if stop_words_re.search(title_clean):
            return None
        # Если description пустой/слишком короткий — берём первую часть title как fallback.
        if len(desc) < 50:
            desc = title_clean

        return Article(url=url, title=title_clean, published=dt, description=desc)


async def build_feed_for_source(crawler: AsyncWebCrawler, src: dict, lookback_days: int, max_items: int, concurrency: int) -> int:
    print(f"[{src['slug']}] index → {src['index_url']}")
    links = await collect_article_links(crawler, src)
    print(f"  · links found: {len(links)}")
    if not links:
        return 0

    sem = asyncio.Semaphore(concurrency)
    tasks = [fetch_article(crawler, src, u, sem) for u in links]
    results = await asyncio.gather(*tasks)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)
    articles = [a for a in results if a and a.published >= cutoff]
    articles.sort(key=lambda a: a.published, reverse=True)
    articles = articles[:max_items]
    print(f"  · articles in window: {len(articles)}")

    if not articles:
        return 0

    fg = FeedGenerator()
    fg.id(src["site"])
    fg.title(src["name"])
    fg.link(href=src["index_url"], rel="alternate")
    fg.link(href=f"https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/{src['slug']}.xml", rel="self")
    fg.description(f"{src['name']} — synthesized feed by ai-news-spider")
    fg.language("en")

    for a in articles:
        fe = fg.add_entry()
        fe.id(a.url)
        fe.title(a.title)
        fe.link(href=a.url)
        fe.guid(a.url, permalink=True)
        fe.pubDate(a.published)
        if a.description:
            fe.description(a.description)

    out = FEEDS_DIR / f"{src['slug']}.xml"
    fg.rss_file(str(out), pretty=True)
    print(f"  · wrote {out.name}")
    return len(articles)


async def main():
    with open(HERE / "sources.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    lookback_days = int(cfg.get("lookback_days", 14))
    max_items = int(cfg.get("max_items_per_feed", 30))
    concurrency = int(cfg.get("article_concurrency", 6))

    normal: list[dict] = []
    stealth: list[dict] = []
    for s in cfg["sources"]:
        (stealth if s.get("stealth") else normal).append(s)

    total = 0

    async def run_batch(sources: list[dict], is_stealth: bool):
        nonlocal total
        if not sources:
            return
        bc = build_browser_config(stealth=is_stealth)
        async with AsyncWebCrawler(config=bc) as crawler:
            for src in sources:
                try:
                    total += await build_feed_for_source(crawler, src, lookback_days, max_items, concurrency)
                except Exception as e:
                    print(f"[{src['slug']}] CRASH: {e}", file=sys.stderr)

    await run_batch(normal, is_stealth=False)
    await run_batch(stealth, is_stealth=True)

    print(f"\nTOTAL: {total} articles across {len(cfg['sources'])} sources")


if __name__ == "__main__":
    asyncio.run(main())
