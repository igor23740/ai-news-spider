# ai-news-spider

Генерирует синтетические RSS-фиды для AI-источников без собственных RSS.
Каждый день в 07:00 MSK GitHub Actions запускает crawl4ai, парсит index-страницы, тянет статьи, собирает RSS 2.0 и коммитит в `feeds/`. Расписание подобрано так, чтобы закончить до 08:00 MSK, когда смежный n8n workflow опрашивает все фиды.

## Источники

Настраиваются в `sources.yaml`. Сейчас покрыты:

- Anthropic News
- xAI News
- ElevenLabs Blog
- Cursor Blog
- Perplexity Hub
- Suno Blog
- Runway Research
- Stability AI News
- Black Forest Labs

## Публичные URL фидов

```
https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/anthropic.xml
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
INSERT INTO rss_feeds (url, name, category, type, weight, active) VALUES
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/anthropic.xml',      'Anthropic News',      'ai-models',   'rss', 3,   true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/xai.xml',            'xAI News',            'ai-models',   'rss', 2.5, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/elevenlabs.xml',     'ElevenLabs',          'ai-audio',    'rss', 2,   true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/cursor.xml',         'Cursor',              'ai-tools',    'rss', 2,   true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/perplexity.xml',     'Perplexity',          'ai-search',   'rss', 2,   true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/suno.xml',           'Suno',                'ai-audio',    'rss', 1.5, true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/runway.xml',         'Runway',              'ai-video',    'rss', 2,   true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/stability.xml',      'Stability AI',        'ai-image',    'rss', 2,   true),
('https://raw.githubusercontent.com/igor23740/ai-news-spider/main/feeds/blackforestlabs.xml','Black Forest Labs',   'ai-image',    'rss', 2,   true);
```

## Локальный запуск

```bash
pip install -r requirements.txt
python -m playwright install chromium
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python build_feeds.py
```

## CI

`.github/workflows/refresh.yml` — cron `0 4 * * *` UTC (07:00 MSK). Пушит обновления только если фиды реально изменились.
