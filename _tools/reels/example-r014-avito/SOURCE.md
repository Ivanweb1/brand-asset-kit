# Ролик «ИИ-агент отвечает на Авито ночью» (сценарий R014)

- Текущая версия (v7, 30.10.2026): аватар перегенерирован на новой модели HeyGen (Avatar 6) одной записью — вступление и финал из одного видео, id `0633c7c018ec455eb732e20191bc2b48`, 9,6 с. Тайминги записи — `clip.json`.
- Первая версия (v6, 29.10.2026): две отдельные записи HeyGen (Avatar III) `work/r014/intro.mp4`, `outro.mp4`, тайминги вписаны в `r014_avito.py`. Пересобирается без `R014_CLIPS`.
- Скриншот чата Авито не публикуется (чужая переписка): `work/r014/avito-chat.png`.

## Пересобрать v7
```bash
mkdir -p work/r014v2
# видео аватара из HeyGen → work/r014v2/intro.mp4 и копия work/r014v2/outro.mp4
cp _tools/reels/example-r014-avito/clip.json work/r014v2/
R014_CLIPS=work/r014v2 python3 _tools/reels/r014_avito.py      # -> example-r014-avito/final.mp4, cover.jpg
```
Windows: папку `C:\Program Files\Tesseract-OCR` добавить в PATH (cairo).

- Готовый ролик: `final.mp4` — 21,8 с, 1080×1920, 30 к/с. Первый кадр — обложка (кадр 6,15 с записи: рот закрыт, лёгкая улыбка).
- Склейка: вступление 0–6,2 с записи, финал с 6,30 с (пауза между «бронь» и «Напишите» — 0,34 с).
