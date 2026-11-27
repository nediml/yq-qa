// Build-time data layer: reads ../data and ../taxonomy.yaml once per build.
import fs from 'node:fs';
import path from 'node:path';
import YAML from 'yaml';
import { marked } from 'marked';

const ROOT = path.resolve(process.cwd(), '..');
export const PAGE_SIZE = 24;
export const SCHOLAR = 'Shaykh Dr. Yasir Qadhi';

export interface Sub { slug: string; name: string }
export interface Category { slug: string; name: string; description: string; subs: Sub[] }
export interface Chapter { start: number; end: number; title: string }
export interface Playlist { id: string; title: string }
export interface Video {
  id: string; title: string; channel: string; channelHandle: string;
  playlist: Playlist | null; uploadDate: string | null; duration: number; chapters: Chapter[];
}
export interface Question {
  id: string; videoId: string; index: number; slug: string; question: string; asked?: string;
  answer: string; start: number; end: number; category: string; subcategory: string; tags: string[];
  // derived
  video: Video; html: string; excerpt: string; words: number;
}

const readJsonDir = <T>(dir: string): T[] =>
  fs.existsSync(dir)
    ? fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()
        .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')) as T)
    : [];

export const slugify = (s: string) =>
  s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

const plain = (md: string) =>
  md.replace(/^>\s?/gm, '').replace(/[*_`#]/g, '').replace(/\s+/g, ' ').trim();

const excerpt = (md: string, n = 190) => {
  const t = plain(md);
  return t.length <= n ? t : t.slice(0, t.lastIndexOf(' ', n)) + '…';
};

export const mmss = (sec: number) => {
  const s = Math.floor(sec), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  const p = (x: number) => String(x).padStart(2, '0');
  return h ? `${h}:${p(m)}:${p(r)}` : `${p(m)}:${p(r)}`;
};

export const formatDate = (d: string | null) =>
  d ? new Date(d + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }) : '';

export const ytUrl = (id: string, start = 0) =>
  `https://www.youtube.com/watch?v=${id}${start ? `&t=${Math.floor(start)}s` : ''}`;

// ---------- load ----------
export const categories: Category[] = YAML.parse(fs.readFileSync(path.join(ROOT, 'taxonomy.yaml'), 'utf8'));
export const videos = new Map(readJsonDir<Video>(path.join(ROOT, 'data/videos')).map((v) => [v.id, v]));

export const questions: Question[] = readJsonDir<Omit<Question, 'video' | 'html' | 'excerpt' | 'words'>>(
  path.join(ROOT, 'data/questions'),
)
  .filter((q) => videos.has(q.videoId))
  .map((q) => ({
    ...q,
    video: videos.get(q.videoId)!,
    html: marked.parse(q.answer, { async: false }) as string,
    excerpt: excerpt(q.answer),
    words: q.answer.split(/\s+/).length,
  }))
  // newest video first, then in video order
  .sort((a, b) =>
    (b.video.uploadDate ?? '').localeCompare(a.video.uploadDate ?? '') ||
    a.videoId.localeCompare(b.videoId) || a.index - b.index);

// ---------- lookups ----------
export const category = (slug: string) => categories.find((c) => c.slug === slug)!;
export const sub = (cat: string, slug: string) => category(cat).subs.find((s) => s.slug === slug)!;

export const inCategory = (cat: string, subSlug?: string) =>
  questions.filter((q) => q.category === cat && (!subSlug || q.subcategory === subSlug));

export const inVideo = (videoId: string) =>
  questions.filter((q) => q.videoId === videoId).sort((a, b) => a.index - b.index);

export const tags = (() => {
  const m = new Map<string, { slug: string; name: string; items: Question[] }>();
  for (const q of questions)
    for (const t of q.tags) {
      const slug = slugify(t);
      if (!m.has(slug)) m.set(slug, { slug, name: t, items: [] });
      m.get(slug)!.items.push(q);
    }
  return m;
})();

export const series = (() => {
  const m = new Map<string, { playlist: Playlist; videos: Video[]; count: number }>();
  for (const v of videos.values()) {
    if (!v.playlist) continue;
    if (!m.has(v.playlist.id)) m.set(v.playlist.id, { playlist: v.playlist, videos: [], count: 0 });
    const s = m.get(v.playlist.id)!;
    s.videos.push(v);
    s.count += inVideo(v.id).length;
  }
  for (const s of m.values()) s.videos.sort((a, b) => (b.uploadDate ?? '').localeCompare(a.uploadDate ?? ''));
  return [...m.values()].filter((s) => s.count > 0);
})();

export function related(q: Question, n = 8): Question[] {
  const tagSet = new Set(q.tags.map(slugify));
  return questions
    .filter((o) => o.id !== q.id)
    .map((o) => ({
      o,
      score:
        (o.subcategory === q.subcategory && o.category === q.category ? 3 : 0) +
        (o.category === q.category ? 1 : 0) +
        2 * o.tags.filter((t) => tagSet.has(slugify(t))).length,
    }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, n)
    .map((x) => x.o);
}

export function pages<T>(items: T[], size = PAGE_SIZE): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out.length ? out : [[]];
}

export const pageUrl = (base: string, n: number) => (n <= 1 ? base : `${base}page/${n}/`);
