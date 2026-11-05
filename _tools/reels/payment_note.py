"""Плашка оплаты с другой суммой: берёт картинку Ивана work/r025/payment.png (Тинькофф, СБП, + 25 000 ₽),
стирает сумму и пишет новую тем же зелёным, выровненной по правому краю и по высоте цифр.

    python payment_note.py 35000 work/r030/payment.png
"""
import sys, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

K = pathlib.Path(__file__).resolve().parents[2]
SRC = K / "work" / "r025" / "payment.png"
GREEN = (19, 143, 42)
X1, Y0, Y1 = 1902, 112, 167          # правый край суммы и высота цифр в исходнике (2000×356)


def make(amount, out):
    im = Image.open(SRC).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle([1450, 80, 1960, 200], fill=(255, 255, 255, 255))      # стереть «+ 25 000 ₽»
    text = "+ " + f"{amount:,}".replace(",", " ") + " ₽"
    size = 40
    while True:                                                        # подобрать кегль по высоте цифр
        f = ImageFont.truetype("arial.ttf", size); b = f.getbbox("0")
        if b[3] - b[1] >= Y1 - Y0 - 2: break        # обводка 1 px добавит высоту
        size += 1
    b0 = f.getbbox("0"); w = f.getlength(text)
    d.text((X1 - w - 1, Y0 - b0[1]), text, font=f, fill=GREEN + (255,), stroke_width=1, stroke_fill=GREEN + (255,))
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True); im.save(out); return out


if __name__ == "__main__":
    print(make(int(sys.argv[1]), K / sys.argv[2]))
