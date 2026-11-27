"""Check data/questions against videos and taxonomy. Exit 1 on errors.

Also prints pipeline status per stage and warnings worth a human look.
"""
import re
import sys
from collections import Counter

from common import QUESTIONS, ROOT, load_yaml, read_json, stage, videos

REQUIRED = {"id", "videoId", "index", "slug", "question", "answer", "start", "end",
            "category", "subcategory", "tags"}
OPTIONAL = {"asked"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def main() -> int:
    tax = {c["slug"]: {s["slug"] for s in c["subs"]} for c in load_yaml("taxonomy.yaml")}
    vids = {v["id"]: v for v in videos()}
    errors: list[str] = []
    warns: list[str] = []
    slugs: Counter = Counter()

    files = sorted(QUESTIONS.glob("*.json"))
    for f in files:
        rel = f.relative_to(ROOT)
        try:
            q = read_json(f)
        except ValueError as e:
            errors.append(f"{rel}: bad JSON ({e})")
            continue
        err = lambda msg: errors.append(f"{rel}: {msg}")  # noqa: E731

        keys = set(q)
        if missing := REQUIRED - keys:
            err(f"missing {sorted(missing)}")
            continue
        if extra := keys - REQUIRED - OPTIONAL:
            err(f"unknown keys {sorted(extra)}")
        if f.stem != q["id"] or q["id"] != f"{q['videoId']}-{q['index']:02d}":
            err(f"id/filename/index mismatch ({q['id']})")
        v = vids.get(q["videoId"])
        if not v:
            err(f"unknown video {q['videoId']}")
            continue
        if not (0 <= q["start"] < q["end"] <= (v["duration"] or 0) + 1):
            err(f"bad range {q['start']}–{q['end']} (duration {v['duration']})")
        if q["category"] not in tax:
            err(f"unknown category {q['category']}")
        elif q["subcategory"] not in tax[q["category"]]:
            err(f"unknown subcategory {q['category']}/{q['subcategory']}")
        if not SLUG_RE.match(q["slug"]) or len(q["slug"]) > 80:
            err(f"bad slug {q['slug']!r}")
        slugs[q["slug"]] += 1
        if not q["question"].strip().endswith("?"):
            warns.append(f"{rel}: question doesn't end with '?'")
        if not (2 <= len(q["tags"]) <= 6) or any(t != t.lower() for t in q["tags"]):
            err(f"tags must be 2–6 lowercase strings: {q['tags']}")
        words = len(q["answer"].split())
        if words == 0:
            err("empty answer")
        elif words < 40:
            warns.append(f"{rel}: very short answer ({words} words)")
        span = q["end"] - q["start"]
        if span > 60 and words / (span / 60) < 60:
            warns.append(f"{rel}: {words} words for {span}s — possibly over-trimmed")

    for slug, n in slugs.items():
        if n > 1:
            errors.append(f"duplicate slug {slug!r} ({n}×)")

    st = Counter(stage(v) for v in vids)
    print(f"videos: {len(vids)}  " + "  ".join(f"{k}={n}" for k, n in sorted(st.items())))
    print(f"questions: {len(files)}")
    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
