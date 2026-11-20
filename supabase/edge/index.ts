// ============================================================================
//  درس‌یار نهم — تابع لبهٔ احراز هویت و همگام‌سازی
//
//  دانش‌آموز با همان «شماره تلفن» و «رمز عبور» سایت همدل وارد می‌شود.
//  اعتبارنامه فقط سمت سرور با hamdel_records سنجیده می‌شود؛ رمز هیچ‌گاه
//  به مرورگر فرستاده نمی‌شود. نشست با همان الگوی همدل ساخته می‌شود
//  (hamdel_sessions + توکن Bearer با هش SHA-256) تا هر دو سامانه یک ورود
//  مشترک داشته باشند.
//
//  مسیرها (همه با POST، بدنه JSON):
//    /login   { phone, password }            -> { token, user }
//    /me      (Authorization: Bearer)        -> { user, progress }
//    /save    { ops:[...] }                  -> { ok, xp, streak }
//    /teacher (Authorization: Bearer)        -> { rows }  فقط برای کادر
// ============================================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Cache-Control": "no-store",
};

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const db = createClient(SUPABASE_URL, SERVICE_KEY, {
  auth: { persistSession: false, autoRefreshToken: false },
});

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" },
  });

const norm = (v: unknown) => String(v ?? "").replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d))).trim();

async function sha256(text: string) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** نشست تازه؛ همان ساختار hamdel_sessions که همدل استفاده می‌کند */
async function createSession(userId: string): Promise<string> {
  const raw = [...crypto.getRandomValues(new Uint8Array(32))]
    .map((b) => "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"[b & 63])
    .join("");
  const hash = await sha256(raw);
  const expires = new Date(Date.now() + 30 * 864e5).toISOString();
  const { error } = await db.from("hamdel_sessions").insert({
    token_hash: hash,
    user_id: userId,
    is_dev: false,
    expires_at: expires,
  });
  if (error) throw new Error(error.message);
  return raw;
}

type Viewer = { id: string; role: string; name: string; grade: string; section: string };

async function viewer(req: Request): Promise<Viewer | null> {
  const m = /^Bearer\s+([A-Za-z0-9_-]{20,128})$/.exec(req.headers.get("authorization") ?? "");
  if (!m) return null;
  const hash = await sha256(m[1]);
  const { data: sess } = await db
    .from("hamdel_sessions")
    .select("user_id, expires_at")
    .eq("token_hash", hash)
    .maybeSingle();
  if (!sess || new Date(sess.expires_at).getTime() < Date.now()) return null;
  const { data: row } = await db
    .from("hamdel_records")
    .select("data")
    .eq("collection", "users")
    .eq("id", sess.user_id)
    .eq("deleted", false)
    .maybeSingle();
  const u = (row?.data ?? {}) as Record<string, unknown>;
  if (!u.phone && sess.user_id !== "dev-root") return null;
  return {
    id: sess.user_id,
    role: String(u.role ?? "student"),
    name: `${String(u.firstName ?? "")} ${String(u.lastName ?? "")}`.trim() || "دانش‌آموز",
    grade: String(u.grade ?? ""),
    section: String(u.section ?? ""),
  };
}

/* -------------------------------------------------------------------------- */
/*  ورود                                                                      */
/* -------------------------------------------------------------------------- */
async function login(req: Request) {
  const body = await req.json().catch(() => ({}));
  const phone = norm(body.phone);
  const password = String(body.password ?? "").trim();
  if (!phone || !password) return json({ error: "شماره تلفن و رمز عبور را وارد کنید." }, 400);

  const { data: row, error } = await db
    .from("hamdel_records")
    .select("id, data")
    .eq("collection", "users")
    .eq("deleted", false)
    .eq("data->>phone", phone)
    .limit(1)
    .maybeSingle();
  if (error) return json({ error: "خطا در ارتباط با پایگاه‌داده." }, 500);
  if (!row) return json({ error: "کاربری با این شماره در همدل یافت نشد." }, 401);

  const u = (row.data ?? {}) as Record<string, unknown>;
  if (String(u.password ?? "").trim() !== password) {
    return json({ error: "رمز عبور با حساب همدل هم‌خوان نیست." }, 401);
  }

  await db
    .from("hamdel_records")
    .update({ data: { ...u, lastLoginAt: Date.now() } })
    .eq("collection", "users")
    .eq("id", row.id);

  const token = await createSession(row.id);
  return json({
    token,
    user: {
      id: row.id,
      phone,
      firstName: u.firstName ?? "",
      lastName: u.lastName ?? "",
      role: u.role ?? "student",
      grade: u.grade ?? "",
      section: u.section ?? "",
      avatar: u.avatar ?? "",
      staffRole: u.staffRole ?? "",
    },
  });
}

/* -------------------------------------------------------------------------- */
/*  وضعیت من (پیشرفت + نمرات)                                                 */
/* -------------------------------------------------------------------------- */
async function me(req: Request) {
  const v = await viewer(req);
  if (!v) return json({ error: "نشست منقضی شده است؛ دوباره وارد شوید." }, 401);

  const [{ data: progress }, { data: attempts }, { data: days }] = await Promise.all([
    db.from("darsyar_progress").select("*").eq("user_id", v.id),
    db
      .from("darsyar_attempts")
      .select("*")
      .eq("user_id", v.id)
      .order("created_at", { ascending: false })
      .limit(80),
    db.from("darsyar_days").select("*").eq("user_id", v.id).order("day", { ascending: false }).limit(400),
  ]);

  const { data: summary } = await db
    .from("darsyar_my_summary")
    .select("*")
    .eq("user_id", v.id)
    .maybeSingle();

  const { data: perSubject } = await db
    .from("darsyar_student_subjects")
    .select("*")
    .eq("user_id", v.id);

  return json({
    user: v,
    progress: progress ?? [],
    attempts: attempts ?? [],
    days: days ?? [],
    summary: summary ?? null,
    subjects: perSubject ?? [],
  });
}

/* -------------------------------------------------------------------------- */
/*  ذخیرهٔ پیشرفت — فهرست عملیات از مرورگر                                    */
/* -------------------------------------------------------------------------- */
type Op = {
  subject: string;
  lessonId: string;
  read?: boolean;
  pct?: number;
  correct?: number;
  total?: number;
  mode?: string;
  xp?: number;
};

async function save(req: Request) {
  const v = await viewer(req);
  if (!v) return json({ error: "نشست منقضی شده است؛ دوباره وارد شوید." }, 401);

  const body = await req.json().catch(() => ({}));
  const ops: Op[] = Array.isArray(body.ops) ? body.ops.slice(0, 60) : [];
  if (!ops.length) return json({ ok: true, saved: 0 });

  const now = new Date().toISOString();
  const rows = new Map<string, Record<string, unknown>>();
  const attempts: Record<string, unknown>[] = [];

  for (const op of ops) {
    if (!op || typeof op.subject !== "string" || typeof op.lessonId !== "string") continue;
    if (op.subject === "__mode") continue;
    const subject = op.subject.slice(0, 40);
    const lessonId = op.lessonId.slice(0, 40);
    const key = `${subject}:${lessonId}`;
    const read = op.read === true;
    const pct = Number.isFinite(op.pct) ? Math.max(0, Math.min(100, Math.round(op.pct!))) : undefined;

    const { data: prev } = await db
      .from("darsyar_progress")
      .select("*")
      .eq("user_id", v.id)
      .eq("subject", subject)
      .eq("lesson_id", lessonId)
      .maybeSingle();

    rows.set(key, {
      user_id: v.id,
      subject,
      lesson_id: lessonId,
      read: read || !!prev?.read,
      read_at: read ? (prev?.read_at ?? now) : (prev?.read_at ?? null),
      best_pct: pct === undefined ? (prev?.best_pct ?? null) : Math.max(pct, prev?.best_pct ?? 0),
      last_pct: pct === undefined ? (prev?.last_pct ?? null) : pct,
      tries: (prev?.tries ?? 0) + (pct === undefined ? 0 : 1),
      xp: (prev?.xp ?? 0) + (Number.isFinite(op.xp) ? Math.max(0, Math.round(op.xp!)) : 0),
      mode: op.mode === "quick" ? "quick" : (prev?.mode ?? "normal"),
      updated_at: now,
    });

    if (pct !== undefined) {
      attempts.push({
        id: `${v.id}:${subject}:${lessonId}:${Date.now()}:${attempts.length}`,
        user_id: v.id,
        subject,
        lesson_id: lessonId,
        pct,
        correct: Number.isFinite(op.correct) ? Math.round(op.correct!) : null,
        total: Number.isFinite(op.total) ? Math.round(op.total!) : null,
        mode: op.mode === "quick" ? "quick" : "normal",
        created_at: now,
      });
    }
  }

  const list = [...rows.values()];
  if (list.length) {
    const { error } = await db
      .from("darsyar_progress")
      .upsert(list, { onConflict: "user_id,subject,lesson_id" });
    if (error) return json({ error: error.message }, 500);
  }
  if (attempts.length) {
    const { error } = await db.from("darsyar_attempts").insert(attempts);
    if (error) return json({ error: error.message }, 500);
  }

  // استریک: روزهای فعال
  const today = new Date().toISOString().slice(0, 10);
  await db.from("darsyar_days").upsert(
    { user_id: v.id, day: today, xp: list.reduce((s, r) => s + Number(r.xp ?? 0), 0) },
    { onConflict: "user_id,day" },
  );

  return json({ ok: true, saved: list.length });
}

/* -------------------------------------------------------------------------- */
/*  پنل دبیر                                                                  */
/* -------------------------------------------------------------------------- */
async function teacher(req: Request) {
  const v = await viewer(req);
  if (!v) return json({ error: "نشست منقضی شده است." }, 401);
  const staff = ["teacher", "principal", "edu_deputy", "cultural_deputy", "tech_deputy", "counselor", "developer"];
  if (!staff.includes(v.role)) return json({ error: "این بخش برای کادر مدرسه است." }, 403);

  const { data, error } = await db
    .from("darsyar_student_summary")
    .select("*")
    .order("last_active", { ascending: false, nullsFirst: false });
  if (error) return json({ error: error.message }, 500);

  const { data: attempts } = await db
    .from("darsyar_attempts")
    .select("user_id,subject,lesson_id,pct,created_at")
    .order("created_at", { ascending: false })
    .limit(3000);

  return json({ rows: data ?? [], attempts: attempts ?? [] });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const segs = new URL(req.url).pathname.split("/").filter(Boolean);
  const path = segs[segs.length - 1] || "";
  try {
    if (path === "login") return await login(req);
    if (path === "me") return await me(req);
    if (path === "save") return await save(req);
    if (path === "teacher") return await teacher(req);
    return json({ error: "مسیر ناشناخته" }, 404);
  } catch (err) {
    return json({ error: (err as Error).message ?? "خطای ناشناخته" }, 500);
  }
});
