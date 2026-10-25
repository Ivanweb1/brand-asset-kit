#!/usr/bin/env python3
"""Транскрибация русской речи с таймкодами слов — офлайн, без huggingface.

Модель (sherpa-onnx, zipformer-ru) скачивается из GitHub-релизов k2-fsa/sherpa-onnx,
поэтому работает в облачных сессиях, где huggingface.co закрыт.

    python3 transcribe.py video.mov            # -> video.words.json, video.srt, video.txt
    python3 transcribe.py video.mov --min-pause 0.25

Зависимости ставятся сами: pip install sherpa-onnx soundfile.
"""
import argparse, json, os, re, subprocess, sys, tarfile, urllib.request

MODEL = "sherpa-onnx-zipformer-ru-2024-09-18"
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL}.tar.bz2"
CACHE = os.path.expanduser("~/.cache/brand-asr")


def ensure_deps():
    try:
        import sherpa_onnx, soundfile  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sherpa-onnx", "soundfile"], check=True)


def ensure_model():
    d = os.path.join(CACHE, MODEL)
    if not os.path.exists(os.path.join(d, "tokens.txt")):
        os.makedirs(CACHE, exist_ok=True)
        arc = os.path.join(CACHE, MODEL + ".tar.bz2")
        print("Скачиваю модель…", file=sys.stderr)
        urllib.request.urlretrieve(URL, arc)
        with tarfile.open(arc) as t: t.extractall(CACHE, filter="data")
        os.remove(arc)
    return d


def speech_chunks(wav, min_pause):
    log = subprocess.run(["ffmpeg", "-i", wav, "-af", f"silencedetect=n=-38dB:d={min_pause}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(st, en))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media"); ap.add_argument("--min-pause", type=float, default=0.18)
    a = ap.parse_args()
    ensure_deps()
    import sherpa_onnx, soundfile as sf
    d = ensure_model()
    base = os.path.splitext(a.media)[0]; wav = base + ".16k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.media, "-map", "0:a:0", "-ac", "1", "-ar", "16000", wav], check=True)
    audio, sr = sf.read(wav, dtype="float32"); total = len(audio) / sr
    sil = speech_chunks(wav, a.min_pause)
    chunks, prev = [], 0.0
    for s, e in sil:
        if s - prev > 0.12: chunks.append((prev, s))
        prev = e
    if total - prev > 0.12: chunks.append((prev, total))
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.onnx", joiner=f"{d}/joiner.onnx",
        tokens=f"{d}/tokens.txt", num_threads=os.cpu_count() or 4)
    words, phrases = [], []
    for s, e in chunks:
        s0 = max(0, s - 0.15); seg = audio[int(s0 * sr):int(min(total, e + 0.15) * sr)]
        st = rec.create_stream(); st.accept_waveform(sr, seg); rec.decode_stream(st)
        r = st.result; ws = []
        for tok, ts in zip(r.tokens, r.timestamps):
            if tok.startswith(" ") or not ws: ws.append([tok.strip(), round(max(s, ts + s0), 2)])
            else: ws[-1][0] += tok
        if ws:
            phrases.append({"start": round(s, 2), "end": round(e, 2), "text": r.text.strip()})
            words += [{"word": w, "start": t} for w, t in ws]
    json.dump({"phrases": phrases, "words": words, "pauses": sil}, open(base + ".words.json", "w"), ensure_ascii=False, indent=1)
    fmt = lambda x: "%02d:%02d:%02d,%03d" % (x // 3600, x % 3600 // 60, x % 60, round(x % 1 * 1000) % 1000)
    with open(base + ".srt", "w") as f:
        for i, p in enumerate(phrases, 1): f.write(f"{i}\n{fmt(p['start'])} --> {fmt(p['end'])}\n{p['text']}\n\n")
    with open(base + ".txt", "w") as f:
        for p in phrases: f.write(f"[{p['start']:7.2f}] {p['text']}\n")
    os.remove(wav)
    print(open(base + ".txt").read())


if __name__ == "__main__":
    main()
