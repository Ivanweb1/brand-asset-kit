"""Режет общий рендер (интро 0–1.8 с, аутро 1.8–5.0 с) на файлы для монтажа в BRAND_ASSET_KIT/11_MOTION.
Сначала: npx hyperframes render -o renders/full.mp4 --quality delivery
         npx hyperframes render -o renders/full-alpha.mov --format mov --variables '{"background":false}'
Потом:   python export.py"""
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "11_MOTION"
PARTS = {"intro": (0.0, 1.8), "outro": (1.8, 3.2)}


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def main():
    OUT.mkdir(exist_ok=True)
    full, alpha = HERE / "renders/full.mp4", HERE / "renders/full-alpha.mov"
    for name, (ss, t) in PARTS.items():
        cut = ["-ss", f"{ss}", "-t", f"{t}"]
        # графитовый фон: со звуком и без
        ff("-i", str(full), *cut, "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", str(OUT / f"{name}-sound.mp4"))
        ff("-i", str(full), *cut, "-an", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           str(OUT / f"{name}.mp4"))
        # прозрачный фон: ProRes 4444 (Premiere, DaVinci, Final Cut) и WebM VP9 (CapCut, браузер)
        ff("-i", str(alpha), *cut, "-an", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
           str(OUT / f"{name}-alpha.mov"))
        ff("-i", str(alpha), *cut, "-an", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "22",
           "-auto-alt-ref", "0", str(OUT / f"{name}-alpha.webm"))
        # превью для каталога
        ff("-i", str(full), *cut, "-vf", "fps=15,scale=270:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=48[p];[b][p]paletteuse",
           str(OUT / f"{name}-preview.gif"))
    for snd in ("click", "pop"):
        shutil.copy(HERE / f"assets/sfx/{snd}.mp3", OUT / f"sfx-{snd}.mp3")
    for p in sorted(OUT.iterdir()):
        print(f"{p.name:28s} {p.stat().st_size / 1e6:6.2f} MB")


if __name__ == "__main__":
    main()
