# Ролик «Спасение для всех, кто делает презентации» (сценарий R017)

- Версия v1, 30.10.2026. Готовый ролик `final.mp4` — 14,55 с, 1080×1920, 30 к/с. Первый кадр — обложка (кадр 0,12 с записи).
- Аватар: одна запись HeyGen (Avatar 6), id `800b35fe5ed7407ba4998e5faeb51f33`, 6 с. Хук 0–2,95 с, призыв с 3,2 с.
- Экран Claude собран по скриншоту приложения Claude (Windows): кропы иконок, плейсхолдера, нижней строки и маскота ×2; текст задачи, рефы, кнопка отправки и курсор нарисованы кодом. Боковая панель скриншота не используется.
- Результат — 5 слайдов из презентации «ВСЕКУПОНЫ» (vsekupony-deck-v5.pdf): 1, 3, 5, 8, 13 из 13.
- Исходники не публикуются: `work/r017/` (intro.mp4 = outro.mp4, claude-app.png, ref1–3, slide*.png).

## Пересобрать
```bash
python3 _tools/reels/r017_presentation.py              # -> example-r017-presentation/final.mp4, cover.jpg
python3 _tools/reels/r017_presentation.py peek 1 5 9   # кадры в work/r017/
```
Windows: папку `C:\Program Files\Tesseract-OCR` добавить в PATH (cairo).
