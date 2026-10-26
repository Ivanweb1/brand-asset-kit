# Ролик «ИИ-агент отвечает на заявки» (аватар HeyGen)

- Исходник: `_.mp4` — 31,6 с, 720×1280, 25 к/с, SDR, аватар HeyGen (водяной знак внизу справа).
- Где лежит: релиз «тестииаватара» — https://github.com/Ivanweb1/brand-asset-kit/releases/tag/тестииаватара
- Скачать:
  ```bash
  curl -L -o raw.mp4 "https://github.com/Ivanweb1/brand-asset-kit/releases/download/%D1%82%D0%B5%D1%81%D1%82%D0%B8%D0%B8%D0%B0%D0%B2%D0%B0%D1%82%D0%B0%D1%80%D0%B0/_.mp4"
  ```
- Пересобрать:
  ```bash
  cd _tools/reels
  python3 prepare.py raw.mp4 --start 0 --work work
  cp example-ai-agent/edit.json work/edit.json
  REEL_WORK=work python3 ai_agent.py light     # -> work/out/reel_ai_agent_light.mp4
  ```
- Монтаж: вырезаны только паузы между фразами (у аватара нет слов-паразитов), 31,5 с → 26 с. «я агент» в расшифровке → «ИИ-агент».
- Сцены: хук (две плашки) → панель «Самое обидное — не в рекламе» → «ДО · ВРУЧНУЮ» + пустая заготовка «Клиент у конкурентов» → крупный план «Платите за привлечение / Теряете из-за долгого ответа» → панель «Автоматизировать» с тумблером → «ПОСЛЕ · ИИ-АГЕНТ» → призыв «Напишите в директ „Заявка“».
- Аватар HeyGen стоит в кадре почти как исходник с iPhone, поэтому `FACE_SRC` в `reel.py` менять не пришлось.
