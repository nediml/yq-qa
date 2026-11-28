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
    # Ignore yt-dlp's partial downloads (.part / .ytdl). They are not usable audio.
    existing = [p for p in AUDIO.glob(f"{video_id}.*") if p.suffix not in (".part", ".ytdl")]
    if existing:
        return existing[0]
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        # YouTube read timeouts happen. Retry and resume the .part file.
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(AUDIO / "%(id)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    done = [p for p in AUDIO.glob(f"{video_id}.*") if p.suffix not in (".part", ".ytdl")]
    if not done:
        raise yt_dlp.utils.DownloadError(f"{video_id}: no complete audio file after download")
    return done[0]


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
    failed = []
    for vid in ids:
        try:
            transcribe(vid)
        except yt_dlp.utils.DownloadError as e:
            print(f"{vid}: download failed ({e})", file=sys.stderr)
            failed.append(vid)
    if failed:
        print(f"FAILED: {' '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
