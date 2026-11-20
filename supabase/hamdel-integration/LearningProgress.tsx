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
// ============================================================================

import { useEffect, useMemo, useState } from "react";

const ENDPOINT =
  "https://musmyiwumgeffafxsmdd.supabase.co/functions/v1/darsyar-auth";

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

type Props = {
  token: string;
  viewer?: { id: string; role: string; name?: string };
};

const fa = (v: unknown) =>
  String(v ?? "۰").replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[+d]);

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
  "english-workbook": "کتاب کار",
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
        } else {
          const data = await call("me", token);
          if (!alive) return;
          setSummary(data.summary ?? null);
          setSubjects(data.subjects ?? []);
        }
      } catch (e) {
        if (alive) setErr((e as Error).message);
      }
    })();
    return () => { alive = false; };
  }, [token, staff]);

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
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-bold text-slate-800">پیشرفت درس‌یار دانش‌آموزان</h3>
          <a className="text-xs text-indigo-600 hover:underline" href="https://darsyar.vercel.app/teacher.html" target="_blank" rel="noopener">
            نمای کامل ↗
          </a>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-right text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                <th className="p-2">دانش‌آموز</th>
                <th className="p-2">کلاس</th>
                <th className="p-2">درس خوانده</th>
                <th className="p-2">آزمون</th>
                <th className="p-2">میانگین</th>
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
                </tr>
              ))}
              {!rows.length && (
                <tr><td colSpan={5} className="p-3 text-center text-slate-400">هنوز فعالیتی ثبت نشده است.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  /* ---------------- نمای دانش‌آموز ---------------- */
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-bold text-slate-800">پیشرفت من در درس‌یار</h3>
        <a className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700"
           href="https://darsyar.vercel.app/index.html" target="_blank" rel="noopener">
          ادامهٔ یادگیری ↗
        </a>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-lg font-black text-slate-800">{fa(summary?.lessons_read ?? 0)}</div>
          <div className="text-[11px] text-slate-500">درس خوانده</div>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-lg font-black text-slate-800">{fa(summary?.quizzes_taken ?? 0)}</div>
          <div className="text-[11px] text-slate-500">آزمون داده</div>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-lg font-black text-slate-800">
            {summary?.avg_pct == null ? "—" : `${fa(summary.avg_pct)}٪`}
          </div>
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
    </div>
  );
}
