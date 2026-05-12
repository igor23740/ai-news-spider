# SOURCES_AUDIT — реальная проверка RSS-эндпоинтов

Дата: 2026-05-12. Проверено через WebFetch (живые запросы, не из памяти).
Свежесть фидов и заголовков отражает реальное состояние на момент проверки.

---

## 1. NATIVE RSS — берём напрямую, паука не нужно

### 1.1 Топ AI-лаборатории (модели)

| # | Источник | URL | items | свежее | примечание |
|---|---|---|---|---|---|
| 1 | OpenAI | `https://openai.com/blog/rss.xml` | 200+ | 12.05.2026 | основной источник. `/news/rss.xml` — 404 |
| 2 | Anthropic | `https://www.anthropic.com/rss.xml` | 200 | 11.05.2026 | уже подключён в qvabo id=57 |
| 3 | Google DeepMind | `https://deepmind.google/blog/rss.xml` | 150 | 06.05.2026 | темп умеренный |
| 4 | Hugging Face Blog | `https://huggingface.co/blog/feed.xml` | 500+ | 11.05.2026 | огромный пул, включая community-posts |
| 5 | Apple ML Research | `https://machinelearning.apple.com/rss.xml` | 10 | 11.05.2026 | глубокий research |

### 1.2 Newsroom бигтеха (продуктовые анонсы)

| # | Источник | URL | items | свежее | примечание |
|---|---|---|---|---|---|
| 6 | Google Keyword (AI) | `https://blog.google/technology/ai/rss/` | 20 | 11.05.2026 | продуктовые AI-анонсы |
| 7 | Google Gemini | `https://blog.google/products/gemini/rss/` | 20 | 11.05.2026 | релизы Gemini отдельно |
| 8 | Google Research | `https://research.google/blog/rss/` | 100 | 01.05.2026 | research-уровень, темп медленный |
| 9 | Microsoft AI (news.ms) | `https://news.microsoft.com/source/topics/ai/feed/` | 10 | 07.05.2026 | продуктовый AI-фид MS |
| 10 | Microsoft Research | `https://www.microsoft.com/en-us/research/blog/feed/` | 4 | 12.05.2026 | research, мало но качественно |
| 11 | Nvidia Blog | `https://blogs.nvidia.com/feed/` | 10 | 12.05.2026 | продуктовые анонсы и партнёрства |
| 12 | Nvidia Developer | `https://developer.nvidia.com/blog/feed/` | 15 | 12.05.2026 | глубоко технический |
| 13 | AWS ML Blog | `https://aws.amazon.com/blogs/machine-learning/feed/` | ~10 | 12.05.2026 | ML/Bedrock |
| 14 | Together AI | `https://www.together.ai/blog/rss.xml` | 100 | 12.05.2026 | inference/training, активный |
| 15 | Cloudflare AI tag | `https://blog.cloudflare.com/tag/ai/rss/` | 4 | май 2026 | Workers AI и edge-инференс |

### 1.3 Специализированная журналистика (вторичка с фильтром)

| # | Источник | URL | items | свежее | примечание |
|---|---|---|---|---|---|
| 16 | TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` | 20 | 12.05.2026 | основной журналистский поток |
| 17 | VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | 6 | 12.05.2026 | enterprise-уклон |
| 18 | MIT Tech Review AI | `https://www.technologyreview.com/topic/artificial-intelligence/feed/` | 10 | 11.05.2026 | длинные аналитические статьи |
| 19 | IEEE Spectrum AI | `https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss` | 12 | 12.05.2026 | инженерный угол |
| 20 | AI News | `https://artificialintelligence-news.com/feed/` | 15 | 12.05.2026 | enterprise AI / governance |
| 21 | Simon Willison | `https://simonwillison.net/atom/everything/` | 25 | 11.05.2026 | один автор, но эталонный AI-эксперт |

### 1.4 Заблокировано WebFetch, но фиды известны (проверим curl'ом в Actions)

| Источник | URL | примечание |
|---|---|---|
| The Verge AI | `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` | WebFetch блокирует, но фид публичный |
| Ars Technica AI | `https://arstechnica.com/ai/feed/` | WebFetch блокирует |
| Wired | `https://www.wired.com/feed/category/business/artificial-intelligence/rss` | WebFetch блокирует |
| DeepLearning.ai Batch | `https://www.deeplearning.ai/the-batch/feed/` | ECONNREFUSED — проверить позже |

---

## 2. SPIDER — нативного RSS нет, парсим HTML

| # | Источник | index URL | статус сегодня |
|---|---|---|---|
| s1 | xAI | https://x.ai/news | работает |
| s2 | Perplexity | https://www.perplexity.ai/hub/blog | работает |
| s3 | Cursor | https://cursor.com/changelog (приоритет) или /blog | RSS нет, паучим |
| s4 | Suno | https://suno.com/blog | в feeds/ нет — починить |
| s5 | Runway | https://runwayml.com/research | в feeds/ нет — починить |
| s6 | Stability | https://stability.ai/news | в feeds/ нет — починить (CF) |
| s7 | Black Forest Labs | https://blackforestlabs.ai/blog | работает |
| s8 | ElevenLabs | https://elevenlabs.io/blog | работает (но /blog/rss и /blog/feed.xml — 401/404) |
| s9 | Mistral | https://mistral.ai/news | новый: RSS нет |
| s10 | Cohere | https://cohere.com/blog | новый: RSS нет |
| s11 | Meta AI | https://ai.meta.com/blog | новый: RSS нет, link_pattern `/blog/[a-z0-9-]+` |
| s12 | Groq | https://groq.com/news/ (newsroom) | новый: HTML, паучим |
| s13 | Replicate | https://replicate.com/blog | новый: RSS нет |
| s14 | Databricks | https://www.databricks.com/blog | новый: RSS нет |
| s15 | Snowflake | https://www.snowflake.com/en/blog/ | новый: RSS нет |

Anthropic убрать из паука (есть native).

---

## 3. GITHUB RELEASES — отдельный трек

GitHub отдаёт нативный Atom: `https://github.com/{owner}/{repo}/releases.atom` для **любого** репо без капчи и rate-limit (с публичными репо).

Кандидатный whitelist (по памяти, требует подтверждения звёзд через `gh api`):

**Inference / serving**:
- ollama/ollama
- vllm-project/vllm
- ggerganov/llama.cpp
- huggingface/transformers
- huggingface/text-generation-inference

**Агенты / оркестрация**:
- langchain-ai/langchain
- langchain-ai/langgraph
- microsoft/autogen
- crewAIInc/crewAI
- run-llama/llama_index
- joaomdmoura/crewai
- All-Hands-AI/OpenHands (был SWE-Agent)

**Dev-AI**:
- continuedev/continue
- paul-gauthier/aider
- block/goose
- cline/cline
- sst/opencode

**UI / chat**:
- lobehub/lobe-chat
- open-webui/open-webui
- mckaywrigley/chatbot-ui
- comfyanonymous/ComfyUI

**RAG / data**:
- microsoft/graphrag
- infiniflow/ragflow
- weaviate/weaviate
- qdrant/qdrant

**ML-фундамент**:
- pytorch/pytorch
- tensorflow/tensorflow
- ray-project/ray
- pydantic/pydantic-ai

**Computer-use / multimodal**:
- browser-use/browser-use
- anthropic-ai/computer-use-demo (если есть релизы)
- modelscope/agentscope

Звёзды и темп релизов подтверждаем через `gh api repos/{owner}/{repo}` перед включением.

---

## 4. Cron-стратегия

Текущая: 2×/сутки, ~10 мин/прогон.

Цель: 8×/сутки (каждые 3 часа), на пике релизов попадаем в окно 30-180 мин от публикации первоисточника.

**Оптимизация под лимит 2000 мин/мес Actions**:
- Native-RSS (21 источник) — НЕ паучить, просто `curl` + копирование в feeds/. Прогон ~30 сек.
- Spider (~15 источников) — прогон ~5-7 мин с Patchright для stealth-сайтов.
- Trending-scan GitHub — раз в неделю отдельным job.

Расчёт: 8 × 30 × (0.5 + 6) = ~1560 мин/мес. В лимит укладываемся.

---

## 5. Антипротухание (правила фильтрации)

Применяются ко всем источникам после сбора:
- `max_age_hours: 72` — отсеиваем то, что старше 3 дней (для дайджеста бесполезно).
- Минимум 80 символов в description (отсекает плейсхолдеры и навигационные элементы).
- Стоп-слова в title: `coming soon`, `we will`, `next month`, `announce.*event`, `we're hiring`, `sponsored` — отсев маркетинга.
- AI-signal regex (как в n8n `🧹 Дедупликация и ранг`): должно совпадать хотя бы одно из `ai|llm|model|gpt|claude|gemini|llama|agent|inference|fine.?tun|embedding|rag|multimodal|diffusion|reasoning`. Применяем только к non-AI-категорийным фидам (newsroom бигтеха, GitHub Releases).
