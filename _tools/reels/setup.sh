#!/usr/bin/env bash
# Готовит окружение для монтажа Reels: Python-пакеты, проверка ffmpeg, модель распознавания речи.
# Запуск из корня репозитория:  bash _tools/reels/setup.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== Python-пакеты"
python3 -m pip install -q opencv-python-headless cairosvg pillow numpy soundfile sherpa-onnx 2>&1 | grep -v "WARNING: Running pip as" || true

echo "== ffmpeg"
command -v ffmpeg >/dev/null || { echo "Нет ffmpeg — установите (apt-get install ffmpeg)"; exit 1; }
FILTERS="$(ffmpeg -hide_banner -filters 2>/dev/null || true)"
grep -q " zscale " <<<"$FILTERS" \
  && echo "zscale есть (HDR с iPhone тонмапится)" \
  || echo "ВНИМАНИЕ: в ffmpeg нет zscale — HDR-видео с iPhone выйдет бледным; нужен ffmpeg с libzimg"

echo "== Модель распознавания речи (≈300 МБ, один раз, из GitHub-релизов sherpa-onnx)"
python3 - <<PY
import sys; sys.path.insert(0, "$HERE/../transcribe")
import transcribe; print(transcribe.ensure_model())
PY

echo "== Шрифты и логотип"
ls "$HERE/../../00_BRAND_GUIDE/fonts/Manrope-ExtraBold.ttf" "$HERE/../../00_BRAND_GUIDE/logo-mark.original.svg" >/dev/null && echo "ok"
echo "Готово."
