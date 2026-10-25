# Монтаж Reels в фирменном стиле

Код, которым собран утверждённый ролик формата «До / После». Правила формата — в [RULES.md](RULES.md), эталон — `example/final.mp4`.

## Установка
```bash
pip install opencv-python-headless cairosvg pillow numpy soundfile sherpa-onnx
# нужен ffmpeg с фильтром zscale (для HDR с iPhone)
```

## Новый ролик
```bash
cd _tools/reels
# 1. Кусок исходника, звук, расшифровка и черновик монтаж-листа
python3 prepare.py ~/video/IMG_1234.MOV --start 4 --end 40 --work work
# 2. Править work/edit.json: оставить только чистую речь, расставить заглавные и пунктуацию в словах
REEL_WORK=work python3 edit.py                  # список слов с индексами и временем в ролике
# 3. Скопировать before_after.py, поменять тексты и привязки к словам E.wt(i)
REEL_WORK=work python3 peek.py before_after 1.5,8,14 light --zones   # быстрые кадры + зоны Reels
REEL_WORK=work python3 before_after.py light                         # -> work/out/reel_before_after_light.mp4
```

## Файлы
- `reel.py` — движок: камера с субпиксельным зумом, спрайты (плашки, текст, иконки, оригинальный логотип), наложение.
- `story.py` — общие сцены и элементы: плашка с именем, ленты, слоган, плитки процессов, кэш кадров, мягкие склейки, сборка видео и звука.
- `edit.py` — монтаж-лист из `edit.json`: перевод времени оригинала во время ролика.
- `before_after.py` — шаблон формата «До / После».
- `prepare.py` — подготовка исходника и черновика монтаж-листа.
- `peek.py`, `zonecheck.py` — проверка кадров и зон интерфейса.
- `example/edit.json`, `example/final.mp4` — данные и результат первого ролика.
