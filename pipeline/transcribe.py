"""Download audio and transcribe with mlx-whisper.

  transcribe.py            # every video without a transcript
  transcribe.py ID [ID..]  # only these

Writes work/transcripts/<id>.json: {"model", "segments": [{start, end, text}]}.
"""
import sys
import time

import mlx_whisper
import yt_dlp

from common import AUDIO, TRANSCRIPTS, videos, write_json

MODEL = "mlx-community/whisper-large-v3-turbo"
# Biases spelling of recurring names and terms.
PROMPT = (
    "Shaykh Yasir Qadhi answers questions about Islam: the Qur'an, hadith, "
    "the Sunnah, fiqh, aqeedah, salah, wudu, ghusl, Ramadan, zakat, Hajj, "
    "the Hanafi, Maliki, Shafi'i and Hanbali madhhabs, halal and haram, "
    "Sahih al-Bukhari, Ibn Taymiyyah, the Prophet ﷺ, sallallahu alayhi wa sallam."
)


def download(video_id: str):
    AUDIO.mkdir(parents=True, exist_ok=True)
    existing = list(AUDIO.glob(f"{video_id}.*"))
    if existing:
        return existing[0]
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(AUDIO / "%(id)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return next(AUDIO.glob(f"{video_id}.*"))


def transcribe(video_id: str) -> None:
    out = TRANSCRIPTS / f"{video_id}.json"
    if out.exists():
        return
    audio = download(video_id)
    t0 = time.time()
    result = mlx_whisper.transcribe(
        str(audio),
        path_or_hf_repo=MODEL,
        language="en",
        initial_prompt=PROMPT,
        condition_on_previous_text=False,  # avoids runaway repetition loops
    )
    segments = [
        {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
        for s in result["segments"]
        if s["text"].strip()
    ]
    write_json(out, {"model": MODEL, "segments": segments})
    print(f"{video_id}: {len(segments)} segments in {time.time() - t0:.0f}s")


def main() -> None:
    ids = sys.argv[1:] or [v["id"] for v in videos()]
    for vid in ids:
        transcribe(vid)


if __name__ == "__main__":
    main()
