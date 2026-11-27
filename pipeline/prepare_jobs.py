"""Build work/jobs/<id>.md for every transcribed video without questions.

A job is what the editing step (see EDITING.md) reads: metadata, a
segmentation mode, chapters, and the timestamped transcript.
"""
import re
import sys

from common import JOBS, TRANSCRIPTS, mmss, read_json, stage, videos

SINGLE_MAX_SECONDS = 600
SKIP_CHAPTER = re.compile(r"(?i)^(intro(duction)?|outro|conclusion|closing|du'?a|announcements?)\b")


def mode(v: dict) -> str:
    real = [c for c in v["chapters"] if not SKIP_CHAPTER.match(c["title"])]
    if len(real) >= 2:
        return "chapters"
    if (v["duration"] or 0) <= SINGLE_MAX_SECONDS:
        return "single"
    return "free"


def build(v: dict) -> str:
    t = read_json(TRANSCRIPTS / f"{v['id']}.json")
    m = mode(v)
    out = [
        f"# Job {v['id']}",
        "",
        f"- title: {v['title']}",
        f"- channel: {v['channel']}",
        f"- playlist: {(v.get('playlist') or {}).get('title', '-')}",
        f"- uploaded: {v['uploadDate']}",
        f"- duration: {mmss(v['duration'])} ({v['duration']}s)",
        f"- mode: **{m}**",
        f"- output: data/questions/{v['id']}-NN.json",
        "",
    ]
    if v["chapters"]:
        out += ["## Chapters", ""]
        out += [f"- [{mmss(c['start'])} | {int(c['start'])}s] {c['title']}" for c in v["chapters"]]
        out.append("")
    out += ["## Transcript", ""]
    out += [f"[{mmss(s['start'])} | {int(s['start'])}s] {s['text']}" for s in t["segments"]]
    return "\n".join(out) + "\n"


def main() -> None:
    JOBS.mkdir(parents=True, exist_ok=True)
    ids = set(sys.argv[1:])
    for v in videos():
        if ids and v["id"] not in ids:
            continue
        if stage(v["id"]) not in ("transcribed", "prepared"):
            continue
        (JOBS / f"{v['id']}.md").write_text(build(v))
        print(f"{v['id']}: mode={mode(v)}")


if __name__ == "__main__":
    main()
