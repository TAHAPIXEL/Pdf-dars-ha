// ============================================================================
//  کارت «پیشرفت درس‌یار» برای پنل همدل
//  --------------------------------------------------------------------------
//  این کامپوننت را در پنل همدل (مثلاً کنار کارت‌های Attendance / Exams) بگذارید:
//
//      import LearningProgress from "@/components/LearningProgress";
//      <LearningProgress token={token} viewer={viewer} />
//
//  token همان توکن نشستِ همدل است (Bearer) و viewer کاربر جاری.
//  داده از تابع لبهٔ darsyar-auth خوانده می‌شود؛ هیچ کلید محرمانه‌ای در
//  مرورگر قرار نمی‌گیرد.
//
//  نسخهٔ ۲ — هم‌راستا با ساختار جدید درس‌یار:
//      کتاب → فصل → درس → مبحث → کوییز مبحث → آزمون درس/فصل
//  کارت، پیشرفت را در سطح «مبحث» نشان می‌دهد و برای هر آزمون
//  **نمره از ۲۰ + درصد + تعداد درست از کل** را می‌آورد.
// ============================================================================

import { useEffect, useMemo, useState } from "react";

const ENDPOINT =
  "https://musmyiwumgeffafxsmdd.supabase.co/functions/v1/darsyar-auth";

const SITE = "https://darsyar-five.vercel.app";

type Summary = {
  user_id: string;
  first_name?: string;
  last_name?: string;
  grade?: string;
  section?: string;
  lessons_read: number;
  quizzes_taken: number;
  avg_pct?: number | null;          // دانش‌آموز: از darsyar_my_summary
  avg_best_pct?: number | null;     // دبیر: از darsyar_student_summary
  avg_attempt_pct?: number | null;
  attempts?: number;
  xp: number;
  last_active: string | null;
};

type Attempt = {
  subject: string;
  lesson_id: string;
  section_id?: string | null;
  kind?: string | null;
  pct: number;
  correct?: number | null;
  total?: number | null;
  created_at?: string;
};

type ProgressRow = {
  subject: string;
  lesson_id: string;
  section_id?: string | null;
  read?: boolean;
  best_pct?: number | null;
  tries?: number;
};

type Props = {
  token: string;
  viewer?: { id: string; role: string; name?: string };
};

const fa = (v: unknown) =>
  String(v ?? "۰").replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[+d]);

/** ۷۸ → «۳.۹ از ۲۰» */
const nomre20 = (pct: number | null | undefined): string => {
  if (pct == null) return "—";
  const n = Math.round((Number(pct) / 100) * 20 * 10) / 10;
  return `${fa(Number.isInteger(n) ? n : n.toFixed(1))} از ۲۰`;
};

const SUBJECTS: Record<string, string> = {
  quran: "قرآن",
  payam: "پیام‌های آسمان",
  farsi: "فارسی",
  negar: "نگارش",
  math: "ریاضی",
  science: "علوم تجربی",
  social: "مطالعات اجتماعی",
  arabic: "عربی",
  english: "انگلیسی",
  "english-workbook": "کتاب کار انگلیسی",
};

async function call(path: string, token: string, body?: unknown) {
  const res = await fetch(`${ENDPOINT}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body ?? {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error ?? "خطا در دریافت پیشرفت درس‌یار");
  return data;
}

/** کارت خلاصهٔ خودِ دانش‌آموز (در پروفایل یا خانهٔ همدل) */
export default function LearningProgress({ token, viewer }: Props) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [subjects, setSubjects] = useState<Record<string, unknown>[]>([]);
  const [progress, setProgress] = useState<ProgressRow[]>([]);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const staff = useMemo(
    () => ["teacher", "principal", "edu_deputy", "cultural_deputy", "tech_deputy", "counselor", "developer"]
      .includes(viewer?.role ?? ""),
    [viewer?.role],
  );

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        if (staff) {
          const data = await call("teacher", token);
          if (!alive) return;
          setSubjects(data.rows ?? []);
          setAttempts(data.attempts ?? []);
        } else {
          const data = await call("me", token);
          if (!alive) return;
          setSummary(data.summary ?? null);
          setSubjects(data.subjects ?? []);
          setProgress(data.progress ?? []);
          setAttempts(data.attempts ?? []);
        }
      } catch (e) {
        if (alive) setErr((e as Error).message);
      }
    })();
    return () => { alive = false; };
  }, [token, staff]);

  /* ------------- آمار مبحث (برای هر دو نما) ------------- */
  const secStat = useMemo(() => {
    const read = progress.filter((p) => p.section_id && p.section_id !== "-");
    const bySub = new Map<string, { read: number; scored: number[] }>();
    for (const p of read) {
      const b = bySub.get(p.subject) ?? { read: 0, scored: [] };
      b.read += 1;
      if (p.best_pct != null) b.scored.push(Number(p.best_pct));
      bySub.set(p.subject, b);
    }
    const secAttempts = attempts.filter((a) => a.section_id && a.section_id !== "-");
    const lessonAttempts = attempts.filter((a) => !a.section_id || a.section_id === "-");
    const avg = (xs: number[]) =>
      xs.length ? Math.round((xs.reduce((s, x) => s + x, 0) / xs.length) * 10) / 10 : null;
    return {
      totalRead: read.length,
      secQuizzes: secAttempts.length,
      lessonExams: lessonAttempts.length,
      avgSec: avg(secAttempts.map((a) => Number(a.pct))),
      avgLesson: avg(lessonAttempts.map((a) => Number(a.pct))),
      bySub,
    };
  }, [progress, attempts]);

  if (err) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {err}
      </div>
    );
  }

  /* ---------------- نمای دبیر ---------------- */
  if (staff) {
    const rows = subjects as Summary[];
    const bySubject = new Map<string, Attempt[]>();
    for (const a of attempts) {
      const k = a.subject;
      const arr = bySubject.get(k) ?? [];
      arr.push(a);
      bySubject.set(k, arr);
    }

    return (
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h3 className="font-bold text-slate-800">پیشرفت درس‌یار دانش‌آموزان</h3>
            <a className="text-xs text-indigo-600 hover:underline" href={`${SITE}/teacher.html`}
               target="_blank" rel="noopener">
              نمای کامل ↗
            </a>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-right text-sm">
              <thead className="text-xs text-slate-500">
                <tr>
                  <th className="p-2">دانش‌آموز</th>
                  <th className="p-2">کلاس</th>
                  <th className="p-2">درس خوانده</th>
                  <th className="p-2">آزمون</th>
                  <th className="p-2">میانگین</th>
                  <th className="p-2">نمره</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.user_id} className="border-t border-slate-100">
                    <td className="p-2">{`${r.first_name ?? ""} ${r.last_name ?? ""}`.trim() || "دانش‌آموز"}</td>
                    <td className="p-2 text-slate-500">
                      {fa(r.grade ?? "—")}{r.section ? ` / ${fa(r.section)}` : ""}
                    </td>
                    <td className="p-2">{fa(r.lessons_read ?? 0)}</td>
                    <td className="p-2">{fa(r.quizzes_taken ?? 0)}</td>
                    <td className="p-2">{r.avg_best_pct == null ? "—" : `${fa(r.avg_best_pct)}٪`}</td>
                    <td className="p-2 font-bold text-slate-700">{nomre20(r.avg_best_pct)}</td>
                  </tr>
                ))}
                {!rows.length && (
                  <tr>
                    <td colSpan={6} className="p-3 text-center text-slate-400">
                      هنوز فعالیتی ثبت نشده است.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* تفکیک آزمون‌ها: مبحث در برابر درس */}
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { label: "کوییز مبحث", value: secStat.secQuizzes, avg: secStat.avgSec },
            { label: "آزمون درس", value: secStat.lessonExams, avg: secStat.avgLesson },
            { label: "مبحث خوانده‌شده", value: secStat.totalRead, avg: null as number | null },
          ].map((t) => (
            <div key={t.label} className="rounded-xl bg-slate-50 p-3">
              <div className="text-lg font-black text-slate-800">{fa(t.value)}</div>
              <div className="text-[11px] text-slate-500">{t.label}</div>
              {t.avg != null && (
                <div className="mt-1 text-[11px] font-bold text-indigo-600">
                  میانگین {nomre20(t.avg)}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* عملکرد به تفکیک کتاب */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h4 className="mb-3 text-sm font-bold text-slate-800">عملکرد به تفکیک کتاب</h4>
          <div className="space-y-2">
            {[...bySubject.entries()].map(([sub, list]) => {
              const avg =
                Math.round((list.reduce((s, a) => s + Number(a.pct), 0) / list.length) * 10) / 10;
              const secs = list.filter((a) => a.section_id && a.section_id !== "-");
              return (
                <div key={sub} className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="w-28 shrink-0 text-slate-600">{SUBJECTS[sub] ?? sub}</span>
                  <div className="h-2 min-w-16 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.min(100, avg)}%` }} />
                  </div>
                  <span className="w-12 text-left text-slate-500">{fa(avg)}٪</span>
                  <span className="rounded-md bg-slate-50 px-2 py-0.5 text-[10px] text-slate-500">
                    {fa(list.length)} آزمون · {fa(secs.length)} مبحث
                  </span>
                </div>
              );
            })}
            {!bySubject.size && <p className="text-xs text-slate-400">هنوز آزمونی ثبت نشده است.</p>}
          </div>
        </div>
      </div>
    );
  }

  /* ---------------- نمای دانش‌آموز ---------------- */
  const recent = attempts.slice(0, 8);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-bold text-slate-800">پیشرفت من در درس‌یار</h3>
        <a className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700"
           href={`${SITE}/index.html`} target="_blank" rel="noopener">
          ادامهٔ یادگیری ↗
        </a>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-lg font-black text-slate-800">{fa(secStat.totalRead)}</div>
          <div className="text-[11px] text-slate-500">مبحث خوانده</div>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-lg font-black text-slate-800">{fa(secStat.secQuizzes)}</div>
          <div className="text-[11px] text-slate-500">کوییز مبحث</div>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-lg font-black text-slate-800">{fa(secStat.lessonExams)}</div>
          <div className="text-[11px] text-slate-500">آزمون درس/فصل</div>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-sm font-black text-slate-800">{nomre20(secStat.avgLesson ?? secStat.avgSec)}</div>
          <div className="text-[11px] text-slate-500">میانگین نمره</div>
        </div>
      </div>

      <div className="space-y-2">
        {subjects.map((s) => {
          const row = s as Record<string, unknown>;
          const pct = Number(row.read_pct ?? 0);
          return (
            <div key={String(row.subject)} className="flex items-center gap-2">
              <span className="w-24 shrink-0 text-xs text-slate-600">
                {SUBJECTS[String(row.subject)] ?? String(row.subject)}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
              </div>
              <span className="w-9 text-left text-[11px] text-slate-500">{fa(pct)}٪</span>
            </div>
          );
        })}
        {!subjects.length && (
          <p className="text-xs text-slate-400">هنوز درسی در درس‌یار نخوانده‌اید.</p>
        )}
      </div>

      {recent.length > 0 && (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <h4 className="mb-2 text-xs font-bold text-slate-700">آخرین آزمون‌ها</h4>
          <div className="space-y-1.5">
            {recent.map((a, i) => (
              <div key={`${a.lesson_id}-${a.created_at}-${i}`}
                   className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-2.5 py-1.5 text-[11px]">
                <span className="truncate text-slate-600">
                  {SUBJECTS[a.subject] ?? a.subject}
                  {a.section_id && a.section_id !== "-" ? " · مبحث" : " · درس"}
                  {a.lesson_id ? ` ${fa(a.lesson_id.replace(/^l0?/, ""))}` : ""}
                </span>
                <span className="shrink-0 font-bold text-slate-800">
                  {a.correct != null && a.total != null
                    ? `${fa(a.correct)} از ${fa(a.total)} درست · `
                    : ""}
                  {nomre20(a.pct)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
