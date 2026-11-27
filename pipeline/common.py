"""Shared paths and helpers for the pipeline scripts."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VIDEOS = DATA / "videos"
QUESTIONS = DATA / "questions"
WORK = ROOT / "work"
AUDIO = WORK / "audio"
TRANSCRIPTS = WORK / "transcripts"
JOBS = WORK / "jobs"


def load_yaml(name: str):
    return yaml.safe_load((ROOT / name).read_text())


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def videos() -> list[dict]:
    return [read_json(p) for p in sorted(VIDEOS.glob("*.json"))]


def has_questions(video_id: str) -> bool:
    return any(QUESTIONS.glob(f"{video_id}-*.json"))


def stage(video_id: str) -> str:
    """Pipeline stage derived from which files exist (no stored status)."""
    if has_questions(video_id):
        return "done"
    if (JOBS / f"{video_id}.md").exists():
        return "prepared"
    if (TRANSCRIPTS / f"{video_id}.json").exists():
        return "transcribed"
    return "pending"


def mmss(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
