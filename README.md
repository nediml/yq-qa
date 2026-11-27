# yq-qa

An unofficial, searchable archive of questions answered by Shaykh Dr. Yasir Qadhi in his Q&A sessions. Each question gets its own page with an edited transcript of the answer and a YouTube embed that starts where the question begins. The site is modelled on pitanjaiodgovori.ba.

## Pipeline

```bash
python3 -m venv .venv && .venv/bin/pip install yt-dlp mlx-whisper pyyaml
.venv/bin/python pipeline/ingest.py --ids <videoId> …   # or --all (sources.yaml)
.venv/bin/python pipeline/transcribe.py                 # mlx-whisper, Apple Silicon
.venv/bin/python pipeline/prepare_jobs.py               # work/jobs/<id>.md
# editing step: Claude Code processes pending jobs following EDITING.md
.venv/bin/python pipeline/validate.py
```

| Path | What |
|---|---|
| `sources.yaml` | Playlists and channels to ingest |
| `taxonomy.yaml` | Fixed topic → sub-topic tree |
| `EDITING.md` | Rules for splitting and editing answers |
| `data/videos/` | One JSON file per video (metadata, chapters) |
| `data/questions/` | One JSON file per question: the site's content |
| `work/` | Audio, transcripts, jobs (gitignored, rebuildable) |

A video's stage comes from which files exist: no transcript, transcribed, job prepared, or done.

## Site

Astro static site plus Pagefind search, in `site/`.

```bash
cd site && npm install
npm run build      # astro build + pagefind index
npm run preview    # http://localhost:4321
```
