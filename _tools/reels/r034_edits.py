"""Ролик «3-й круг правок — + 10 000 ₽» (сценарий R034 v2), ~7 с, без голоса, без автора и без ИИ-агента.

Чат с Игорем: «Макет_v3.pdf» и «Отлично, почти готово!» уже на экране → «Ещё правки: …» (с первой секунды) →
ваш ответ по договору: 2 круга использованы, третий — 10 000 ₽, выставить счёт? → «печатает…» →
«Да, выставляйте» → ссылка (размыта) → уведомление + 10 000 ₽ → конец.
После подписания договора отвечает сам дизайнер, не агент (Иван, 05.11).

Тонкая обёртка над r030_silent: крупный телефон, «печатает…», payment_note.

    python r034_edits.py              # -> example-r034-edits/final.mp4, cover.jpg
    python r034_edits.py peek 0.5 3   # кадры work/r034/peek_<t>.png
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r030_silent as B
import r019_harvi as T
from r014_avito import GRAPH, OFF, BLUE, K

B.WORK = K / "work" / "r034"
B.OUT = pathlib.Path(__file__).resolve().parent / "example-r034-edits"
B.AMOUNT = 10000                                      # 35 000 — R030, 40 000 — R031, 45 000 — R032, 60 000 — R033

T.NAME = "Игорь"; T.harvi_avatar = lambda d=128: B.face(K / "work" / "r019" / "av_igor.jpg", d)
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()     # шапка закэширована в R030
B.SUBS = ["в сети", "печатает…"]
for s in B.SUBS: T.empty_chat(s); T.top_layer(s)

B.T_NOTE = 5.2
B.TOT = B.T_NOTE + 1.5
B.MSGS = [
    (-1.0, "sep", "Сегодня", None, "", None),
    (-1.0, "out", None, ("file", "Макет_v3.pdf", "4,2 МБ · PDF"), "11:20", None),
    (-1.0, "in", "Отлично, почти готово!", None, "11:48", None),
    (0.10, "in", "Ещё правки: шрифт крупнее, кнопку зелёную, блок с отзывами поменять местами с ценами",
     None, "11:52", None),                                               # движение с первого кадра
    (1.60, "out", "По договору в стоимость входят 2 круга правок — они уже использованы. "
                  "Третий круг — 10 000 ₽, сделаем за 2 дня. Выставить счёт?", None, "11:58", None),   # неразрывные пробелы: сумма не рвётся
    (4.10, "in", "Да, выставляйте", None, "12:03", None),
    (4.65, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "12:04", None),
]
B.CAPS = [(0.0, 1.45, [("3-й круг правок —", OFF, GRAPH), ("+ 10 000 ₽", BLUE, OFF)]),
          (1.55, B.T_NOTE - 0.15, [("Отвечаю по договору", OFF, GRAPH)]),
          (B.T_NOTE, 99, [("Клиент оплатил правки", BLUE, OFF)])]
B.COVER = [("3-й круг правок —", OFF, GRAPH), ("+ 10 000 ₽", BLUE, OFF)]
B.sub_at = lambda t: "печатает…" if 3.4 <= t < 4.1 else "в сети"

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
