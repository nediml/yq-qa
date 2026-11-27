"""List Q&A videos from sources.yaml and write data/videos/<id>.json.

  ingest.py --ids utLodVTY8YA O6Te1jA8Ztw   # only these videos
  ingest.py --all                           # every playlist + title matches

Re-runnable: existing video files are kept unless --refresh is given.
"""
import argparse
import re
import sys

import yt_dlp

from common import VIDEOS, load_yaml, write_json

QUIET = {"quiet": True, "no_warnings": True, "skip_download": True}


def flat(url: str) -> list[dict]:
    with yt_dlp.YoutubeDL({**QUIET, "extract_flat": "in_playlist"}) as ydl:
        info = ydl.extract_info(url, download=False)
    return [e for e in info.get("entries") or [] if e and e.get("id")]


def full(video_id: str) -> dict:
    with yt_dlp.YoutubeDL(QUIET) as ydl:
        return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)


def candidates(src: dict, want_all: bool) -> dict[str, dict]:
    """video id -> playlist it belongs to (first match wins)."""
    found: dict[str, dict] = {}
    for pl in src["playlists"]:
        for e in flat(f"https://www.youtube.com/playlist?list={pl['id']}"):
            found.setdefault(e["id"], {"id": pl["id"], "title": pl["title"]})
    if want_all:
        title_re = re.compile(src["title_match"])
        for handle in src["channels"]:
            for tab in ("videos", "streams"):
                try:
                    entries = flat(f"https://www.youtube.com/@{handle}/{tab}")
                except yt_dlp.utils.DownloadError:
                    continue  # channel has no such tab
                for e in entries:
                    if title_re.search(e.get("title") or ""):
                        found.setdefault(e["id"], None)
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ids", nargs="+")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    src = load_yaml("sources.yaml")
    speaker_re = re.compile(src["speaker_match"])
    # uploader_id case varies (EPICMASJID vs EPICMasjid); normalise to sources.yaml.
    handles = {h.lower(): h for h in src["channels"]}
    found = candidates(src, args.all)
    ids = args.ids if args.ids else list(found)

    added = skipped = 0
    for vid in ids:
        path = VIDEOS / f"{vid}.json"
        if path.exists() and not args.refresh:
            continue
        info = full(vid)
        raw = (info.get("uploader_id") or "").lstrip("@")
        handle = handles.get(raw.lower(), raw)
        if handle != "YasirQadhi" and not speaker_re.search(info.get("title") or ""):
            print(f"skip {vid}: speaker not in title ({info.get('title')})", file=sys.stderr)
            skipped += 1
            continue
        d = info.get("upload_date") or ""
        write_json(path, {
            "id": vid,
            "title": (info.get("title") or "").strip(),
            "channel": src["channels"].get(handle, info.get("channel")),
            "channelHandle": handle,
            "playlist": found.get(vid),
            "uploadDate": f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else None,
            "duration": info.get("duration"),
            "chapters": [
                {"start": c["start_time"], "end": c["end_time"], "title": c["title"].strip()}
                for c in info.get("chapters") or []
            ],
        })
        added += 1
        print(f"added {vid}: {info.get('title')}")
    print(f"done: {added} added, {skipped} skipped")


if __name__ == "__main__":
    main()
