# ai-news-spider

Генерирует синтетические RSS-фиды для AI-источников **без собственных RSS**. Источники с уже работающим native RSS (Anthropic, OpenAI, Google DeepMind, Hugging Face и т.п.) **в этом репо больше не парсятся** — qvabo n8n тянет их напрямую. Полный реестр проверенных native RSS — в `SOURCES_AUDIT.md`.

## Расписание

GitHub Actions запускает crawl4ai **4 раза в сутки, каждые 6 часов**:

| UTC | MSK | Готовит фид к cron MAIN n8n |
|---|---|---|
| 20:30 | 23:30 | 00:00 MSK |
| 02:30 | 05:30 | 06:00 MSK |
| 08:30 | 11:30 | 12:00 MSK |
| 14:30 | 17:30 | 18:00 MSK |

Каждый паук-прогон завершается за 30 минут до cron MAIN n8n — свежие фиды успевают обновиться до запуска основного pipeline.

Push идёт только если `git diff --staged` непустой. Лимит GitHub Actions 2000 мин/мес, прогон ~5-10 мин (4×30=120 прогонов/мес, ~1200 мин — запас 40%).

## Источники

Настраиваются в `sources.yaml`. Сейчас покрыты:

- xAI News (`x.ai/news`)
- ElevenLabs Blog (`elevenlabs.io/blog`)
- Cursor Blog (`cursor.com/blog`)
- Perplexity Hub (`perplexity.ai/hub/blog`)
- Suno Blog (`suno.com/blog`) — SPA, `wait_until: networkidle`
- Runway Research (`runwayml.com/research`)
- Stability AI News (`stability.ai/news`) — `stealth: true` (Patchright)
- Black Forest Labs (`blackforestlabs.ai/blog`) — `stealth: true`

**Anthropic** убран из паука 2026-05-12 — у них есть `https://www.anthropic.com/rss.xml`, n8n использует его напрямую.

## Логика парсера

`build_feeds.py` для каждой статьи пытается извлечь pubDate в порядке:

1. `<meta article:published_time>` / `<meta og:updated_time>` / `<meta date>` и пр.
2. JSON-LD (`datePublished`, `publishedAt`, `first_published_at` и пр.).
3. Дата из URL (паттерн `/YYYY/MM/DD/`).
4. Человеческая дата в HTML (`May 11, 2026`).
5. **Fallback**: момент паучения. Это значит, что статьи без extractable pubDate всё равно попадают в фид со свежей датой. Защита от повторного попадания — на стороне qvabo (`rss_seen_articles` + `rss_post_mirrors` UNION-дедуп).

## Антипротухание

Парсер отсекает:

- title короче 20 символов (плейсхолдеры / навигация);
- title с маркетинговыми стоп-словами (`coming soon`, `we will announce`, `stay tuned`, `sponsored`, `whitepaper`, `webinar`, `register now`, `press release`);
- description короче 50 символов — заменяется на title как fallback.

## Публичные URL фидов

```
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/xai.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/elevenlabs.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/cursor.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/perplexity.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/suno.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/runway.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/stability.xml
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/blackforestlabs.xml
```

## Подключение в n8n / Postgres

```sql
INSERT INTO rss_feeds (url, name, category, type, weight, lookback_hours, active) VALUES
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/xai.xml',            'xAI News',          'ai-models', 'rss', 3.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/elevenlabs.xml',     'ElevenLabs',        'ai-audio',  'rss', 2.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/cursor.xml',         'Cursor',            'ai-tools',  'rss', 3.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/perplexity.xml',     'Perplexity',        'ai-search', 'rss', 3.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/suno.xml',           'Suno',              'ai-audio',  'rss', 2.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/runway.xml',         'Runway',            'ai-video',  'rss', 2.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/stability.xml',      'Stability AI',      'ai-image',  'rss', 2.0, 168, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/blackforestlabs.xml','Black Forest Labs', 'ai-image',  'rss', 2.0, 168, true);
```

Anthropic NEM: подключить напрямую `https://www.anthropic.com/rss.xml` (а не файл паука).

## Локальный запуск

```bash
pip install -r requirements.txt
python -m playwright install chromium
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python build_feeds.py
```
