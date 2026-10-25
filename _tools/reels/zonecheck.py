"""Зоны интерфейса Instagram Reels в кадре 1080×1920 (сняты со скриншота iPhone, 10.2026)."""
import numpy as np

TOP = 340                 # шапка «Reels / Друзья»
BOTTOM = 1640             # ник, «Подписаться», подпись, прогресс
RAIL_X, RAIL_Y = 830, 920  # колонка лайк/коммент/репост/отправить: справа от x=830 и ниже y=920
SAFE_TEXT_BOTTOM = 1600   # нижняя граница для субтитров


def overlay(fr):
    z = np.zeros(fr.shape[:2], np.float32)
    z[:TOP] = 1; z[BOTTOM:] = 1; z[RAIL_Y:BOTTOM, RAIL_X:] = 1
    out = fr.astype(np.float32); red = np.array([255, 40, 40], np.float32)
    out = out * (1 - 0.35 * z[..., None]) + red * 0.35 * z[..., None]
    return out.astype(np.uint8)
