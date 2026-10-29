# Brand Asset Kit — «Сначала процесс. Потом технология»

- Фирменные элементы, токены и гайд — см. README.md.
- **Монтаж Reels** — по утверждённому формату «До / После»: навык `.claude/skills/reels-montage`, правила `_tools/reels/RULES.md`, код `_tools/reels/`.
- **Расшифровка видео** с таймкодами слов (офлайн, без huggingface): `_tools/transcribe/`.
- Логотип — только из `00_BRAND_GUIDE/logo-mark.original.svg`. Интро в `11_MOTION/intro*` собрано с ошибкой в знаке — не использовать, пока не пересобрано.

- **HeyGen:** без прямого разрешения Ивана не создавать в HeyGen никакие ролики (аватарные видео, Video Agent, шаблоны, озвучку, клоны голоса). Смотреть списки можно; перед каждой генерацией показать сценарий, аватар, голос и длительность и ждать явного «да».

## Карта проекта «Рилсы / автоматизация бизнеса»

Одна тема в трёх репозиториях. Сценарий пишется в reels-content-system → монтируется в brand-asset-kit → публикуется через reels-crosspost.

- [Ivanweb1/reels-content-system](https://github.com/Ivanweb1/reels-content-system) (приватный) — **Что говорить.** Позиционирование, ЦА, тон, запреты, сценарии рилсов (`scripts/`), хуки, контент-план, аналитика.
- [Ivanweb1/brand-asset-kit](https://github.com/Ivanweb1/brand-asset-kit) (публичный, GitHub Pages) ← **этот репо** — **Как выглядит.** Фирменный стиль «Сначала процесс. Потом технология» и монтаж рилсов: навык `.claude/skills/reels-montage`, правила `_tools/reels/RULES.md`, обложки `cover.py`, готовые ролики в `_tools/reels/example-*`.
- [Ivanweb1/reels-crosspost](https://github.com/Ivanweb1/reels-crosspost) (приватный) — **Куда выкладывать.** Кросспостинг вертикальных видео: n8n, Telegram-бот-пульт, Postiz. Задание — `docs/TASK_REELS.md`.

Сценарий ролика в reels-content-system и его монтаж в brand-asset-kit связаны по смыслу: R001 «потерянная заявка» = ролик «ИИ-агент» (`_tools/reels/example-ai-agent-1080/`).
Задача относится к другому репо — работай там (сначала `git pull`), а не копируй файлы сюда. В публичный brand-asset-kit не переносить стратегию и черновики сценариев.

