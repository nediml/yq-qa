# Editing guide — turning a job into question files

Input: `work/jobs/<videoId>.md`, which holds the video metadata, a segmentation
mode, chapters (if any), and a Whisper transcript as `[mm:ss | <seconds>s] text` lines.
Output: one JSON file per question in `data/questions/<videoId>-<NN>.json`
(`NN` = 01, 02, … in video order). Write nothing else.

## 1. Find the questions

| Mode | Rule |
|---|---|
| `single` | The whole clip is one question. `start` = when he starts on the question (usually 0). |
| `chapters` | Each chapter is a candidate question. Skip intro, outro, du'a, announcements. If one chapter holds two separate questions, split it; if a chapter title is wrong, trust the transcript. Some videos use chapters as sub-topic markers inside one long answer ("The term itself", "Where did it come from"): merge consecutive chapters that answer the same question into one. |
| `free` | Read the transcript and find each question being read out or asked, and where his answer ends. |

- `start`: the second the **question is read out** (or, if not read out, when he
  starts answering). Pick it from the transcript line timestamps. A viewer clicking
  the embed must land on the question, not mid-sentence of the previous one.
- `end`: the second his answer finishes.
- Skip pure chatter, logistics and anything that isn't a religious/practical question.
- A short follow-up on the same topic stays inside its parent question.

## 2. Write each question

```json
{
  "id": "O6Te1jA8Ztw-03",
  "videoId": "O6Te1jA8Ztw",
  "index": 3,
  "slug": "is-organ-donation-permissible",
  "question": "Is organ donation permissible in Islam?",
  "asked": "My father passed away and the hospital asked whether we would donate his organs…",
  "answer": "Paragraph one.\n\nParagraph two.",
  "start": 1265,
  "end": 1540,
  "category": "health",
  "subcategory": "medical-ethics",
  "tags": ["organ donation", "medical ethics", "the deceased"]
}
```

- `question`: a clear, neutral English question, ≤ 110 chars, ending in `?`.
  Title case not required. No "Q:" prefixes, no clickbait.
- `asked`: optional. The question as read out, lightly cleaned, when it has
  detail the title drops (context, the asker's situation). Omit if the title says it all.
- `slug`: lowercase kebab-case from the question, ≤ 70 chars, no stop-word soup
  (`is-organ-donation-permissible`, not `is-it-permissible-in-islam-to-do-organ-donation`).
- `category` / `subcategory`: exactly one pair from `taxonomy.yaml`. Pick by the
  question's main point, not a side remark.
- `tags`: 2–6 lowercase topic words a reader would search for (`backbiting`,
  `hanafi madhhab`, `cryptocurrency`). Reuse common terms; no tag that just repeats the category.

## 3. Edit the answer — faithful, light, readable

The answer is **his words**, edited for reading. Not a summary, not a paraphrase.

Do:
- Remove fillers (um, uh, you know, okay so), false starts, stutters and repetitions.
- Fix transcription errors you are confident about, especially Arabic terms and
  names (Whisper writes "Hanafi mad hub" → "Hanafi madhhab", "sallallahu" etc.).
- Standard spellings: Qur'an, hadith, Sunnah, madhhab, fiqh, salah, wudu, du'a,
  Allah ﷻ only if he says it, the Prophet ﷺ when he says the salawat.
- Keep first person, his tone, his examples, his jokes, his hedges ("and Allah knows best").
- Keep Qur'an and hadith as he quoted/paraphrased them. Don't swap in a
  different translation.
- Arabic-script recitation in the transcript: drop it when he follows with his
  own English rendering (keep that). If he gives no English, keep the Arabic as a
  `>` blockquote. Short phrases he uses in speech (inshallah, alhamdulillah,
  subhanAllah) stay, transliterated.
- The first transcript lines can contain words leaked from the Whisper prompt
  (e.g. "Shafi'i and Hanbali madhhab." at 0s with no context). Ignore them.
- Split into short paragraphs (2–5 sentences) at natural turns in the argument.
  Use a markdown list only when he clearly enumerates ("firstly… secondly…").
- `**bold**` sparingly for his bottom-line ruling or key sentence, at most one or two per answer.

Don't:
- Add facts, evidence, references or rulings he didn't state.
- Soften, strengthen or "correct" his position.
- Drop substantive content to shorten. A 10-minute answer stays long.
- Add headings, intros ("In this answer…") or closing summaries.
- Include the question reader's preamble, salams, or crowd noise.

If a passage is inaudible or garbled, keep what's clear; never guess the meaning.
