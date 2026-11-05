"""Ролик «Клиенту дорого — а он оплатил» (сценарий R039), ~8 с, без голоса и без автора.

Чат с клиентом: «Сколько стоит?» → «60 000 ₽» → «Нет, дорого.» (с первого кадра) →
плашка «Claude ↓» над обычным сообщением: КП с двумя тарифами «Под ключ» 60 000 ₽ / «Старт» 35 000 ₽ →
клиент выбирает «Старт» → ссылка (размыта) → уведомление + 35 000 ₽ → конец.

По запросу Ивана 05.11: «когда говорят дорого я генерирую кп в клод с тарифами и кидаю в чат клиенту и он выбирает другой тариф дешевле».

Тонкая обёртка над r030_silent: крупный телефон, разделители, payment_note.

    python r039_expensive_claude.py              # -> example-r039-expensive-claude/final.mp4, cover.jpg
    python r039_expensive_claude.py peek 0.5 3   # кадры work/r039/peek_<t>.png
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r030_silent as B
import r019_harvi as T
from r014_avito import GRAPH, OFF, BLUE, K

B.WORK = K / "work" / "r039"
B.OUT = pathlib.Path(__file__).resolve().parent / "example-r039-expensive-claude"
B.AMOUNT = 35000                                      # своя сумма (25k R026, 30k R037, 45k R032)

# клиентка — Марина (как в R026)
T.NAME = "Марина"; T.harvi_avatar = lambda d=128: B.face(K / "work" / "r019" / "av_marina.jpg", d)
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()
B.SUBS = ["в сети", "печатает…"]
for s in B.SUBS: T.empty_chat(s); T.top_layer(s)

B.T_NOTE = 5.4
B.TOT = B.T_NOTE + 1.5
B.MSGS = [
    (-1.0, "sep", "Сегодня", None, "", None),
    (-1.0, "in", "Да, интересно. Сколько стоит?", None, "18:30", None),
    (-1.0, "out", "60 000 ₽", None, "18:31", None),
    (0.10, "in", "Нет, дорого.", None, "18:33", None),                 # конфликт с первого кадра
    (1.40, "lbl", "Claude ↓", None, "", None),                         # подпись для зрителя
    (1.50, "out", "Собрал КП с двумя тарифами:\n«Под ключ» — 60 000 ₽\n«Старт» — 35 000 ₽ (главная + 3 страницы)\n\nКакой ближе?",
     ("file", "КП — сайт.pdf", "1,2 МБ · PDF"), "18:34", None),
    (3.80, "in", "О, «Старт» подходит. Куда платить?", None, "18:36", None),
    (4.40, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "18:36", None),
]
B.CAPS = [(0.0, 1.35, [("Клиенту дорого —", OFF, GRAPH), ("а он оплатил", BLUE, OFF)]),
          (1.45, B.T_NOTE - 0.15, [("Сгенерировал КП в Claude", BLUE, OFF)]),
          (B.T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]
B.COVER = [("Клиенту дорого —", OFF, GRAPH), ("а он оплатил", BLUE, OFF)]
B.sub_at = lambda t: "печатает…" if 3.2 <= t < 3.8 else "в сети"

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
