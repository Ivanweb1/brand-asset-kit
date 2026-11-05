"""Ролик «Скидку не дал — а клиент оплатил» (сценарий R032 v2), ~7 с, без голоса и без автора.

Чат с Ольгой: ваша цена «Сайт под ключ — 60 000 ₽» уже на экране → «А скидку сделаете?» (с первой секунды) →
плашка «ИИ-агент ↓» над обычным сообщением: тариф «Старт» 45 000 ₽ или «Под ключ» 60 000 ₽ на выбор →
«печатает…» → «Давайте «Старт». Куда платить?» → ссылка (размыта) → уведомление + 45 000 ₽ → конец.

Тонкая обёртка над r030_silent: тот же крупный телефон, разделители, подпись «ИИ-агент ↓», payment_note.

    python r032_discount.py              # -> example-r032-discount/final.mp4, cover.jpg
    python r032_discount.py peek 0.5 3   # кадры work/r032/peek_<t>.png
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r030_silent as B
import r019_harvi as T
from r014_avito import GRAPH, OFF, BLUE, K

B.WORK = K / "work" / "r032"
B.OUT = pathlib.Path(__file__).resolve().parent / "example-r032-discount"
B.AMOUNT = 45000                                      # 35 000 — R030, 40 000 — R031, 60 000 — R033

# клиентка — Ольга (фото из R025, там другая тема); новых фото клиентов нет
T.NAME = "Ольга"; T.harvi_avatar = lambda d=128: B.face(K / "work" / "r019" / "av_olga.jpg", d)
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()     # шапка тоже закэширована в R030
B.SUBS = ["в сети", "печатает…"]
for s in B.SUBS: T.empty_chat(s); T.top_layer(s)

B.T_NOTE = 5.2
B.TOT = B.T_NOTE + 1.5
B.MSGS = [
    (-1.0, "sep", "Сегодня", None, "", None),
    (-1.0, "in", "Здравствуйте! Сколько стоит сайт для нашей студии?", None, "14:02", None),
    (-1.0, "out", "Сайт под ключ — 60 000 ₽", None, "14:05", None),
    (0.10, "in", "А скидку сделаете?", None, "14:07", None),              # движение с первого кадра
    (1.50, "lbl", "ИИ-агент ↓", None, "", None),                          # подпись для зрителя — вне сообщения
    (1.60, "out", "Скидок не делаем, но есть тариф «Старт» — 45 000 ₽: главная и 3 страницы, без интеграций.\n"
                  "Под ключ — 60 000 ₽. Какой вам ближе?", None, "14:07", None),
    (4.10, "in", "Давайте «Старт». Куда платить?", None, "14:09", None),
    (4.65, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "14:09", None),
]
B.CAPS = [(0.0, 1.45, [("Скидку не дал —", OFF, GRAPH), ("а клиент оплатил", BLUE, OFF)]),
          (1.55, B.T_NOTE - 0.15, [("ИИ-агент ответил", BLUE, OFF), ("по моим правилам", OFF, GRAPH)]),
          (B.T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]
B.COVER = [("Скидку не дал —", OFF, GRAPH), ("а клиент оплатил", BLUE, OFF)]
B.sub_at = lambda t: "печатает…" if 3.4 <= t < 4.1 else "в сети"

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
