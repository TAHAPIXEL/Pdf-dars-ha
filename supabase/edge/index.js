// ============================================================================
//  darsyar-auth — تابع لبهٔ «درس‌یار» روی پروژهٔ Supabase همدل
//  بدون هیچ ایمپورت خارجی: فقط fetch به PostgREST و Web Crypto.
//  (نسخهٔ JavaScript خالص — همان کدی که روی Supabase اجرا می‌شود)
//  مسیرها (آخرین بخش URL):  /login  /me  /save  /leaderboard  /teacher
// ============================================================================

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Cache-Control": "no-store",
};

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const REST = SUPABASE_URL + "/rest/v1";

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" },
  });

/* ------------------------------ PostgREST ------------------------------ */

function h(prefer) {
  const base = {
    apikey: SERVICE_KEY,
    Authorization: "Bearer " + SERVICE_KEY,
    "Content-Type": "application/json",
  };
  if (prefer) base.Prefer = prefer;
  return base;
}

/** خواندن ردیف‌ها؛ با single=true یک شیء یا null برمی‌گرداند. */
async function selectRows(table, query, single = false) {
  try {
    const res = await fetch(REST + "/" + table + "?" + query, {
      headers: {
        ...h(),
        Accept: single ? "application/vnd.pgrst.object+json" : "application/json",
      },
    });
    if (!res.ok) {
      const text = await res.text();
      if (single && res.status === 406) return { data: null, error: null };
      return { data: null, error: res.status + " " + text.slice(0, 300) };
    }
    const text = await res.text();
    if (!text) return { data: single ? null : [], error: null };
    return { data: JSON.parse(text), error: null };
  } catch (e) {
    return { data: null, error: e.message };
  }
}

async function upsertRows(table, rows, onConflict) {
  try {
    const prefer = "resolution=merge-duplicates,return=minimal";
    const qs = onConflict ? "?on_conflict=" + encodeURIComponent(onConflict) : "";
    const res = await fetch(REST + "/" + table + qs, {
      method: "POST",
      headers: h(prefer),
      body: JSON.stringify(rows),
    });
    if (!res.ok) return { error: res.status + " " + (await res.text()).slice(0, 300) };
    return { error: null };
  } catch (e) {
    return { error: e.message };
  }
}

async function updateRows(table, query, patch) {
  try {
    const res = await fetch(REST + "/" + table + "?" + query, {
      method: "PATCH",
      headers: h("return=minimal"),
      body: JSON.stringify(patch),
    });
    if (!res.ok) return { error: res.status + " " + (await res.text()).slice(0, 300) };
    return { error: null };
  } catch (e) {
    return { error: e.message };
  }
}

/* ------------------------------ کمکی‌ها ------------------------------ */

const norm = (v) =>
  String(v ?? "")
    .replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)))
    .replace(/[٠-٩]/g, (d) => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)))
    .replace(/[\s-]/g, "")
    .trim();

async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

async function createSession(userId) {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const raw = [...bytes].map((b) => ALPHABET.charAt(b % 64)).join("");
  const hash = await sha256(raw);
  const expires = new Date(Date.now() + 30 * 864e5).toISOString();
  const r = await upsertRows("hamdel_sessions", {
    token_hash: hash,
    user_id: userId,
    is_dev: false,
    expires_at: expires,
  });
  if (r.error) throw new Error(r.error);
  return raw;
}

/** کاربر جاری از روی توکن Bearer؛ null اگر نشست معتبر نباشد. */
async function viewer(req) {
  const m = /^Bearer\s+([A-Za-z0-9_-]{20,128})$/.exec(req.headers.get("authorization") ?? "");
  if (!m) return null;
  const hash = await sha256(m[1]);
  const s = await selectRows(
    "hamdel_sessions",
    "token_hash=eq." + hash + "&select=user_id,expires_at",
    true,
  );
  if (!s.data || new Date(s.data.expires_at).getTime() < Date.now()) return null;

  const r = await selectRows(
    "hamdel_records",
    "collection=eq.users&id=eq." +
      encodeURIComponent(s.data.user_id) +
      "&deleted=eq.false&select=id,data",
    true,
  );
  const u = (r.data && r.data.data) || {};
  if (!u.phone && s.data.user_id !== "dev-root") return null;
  return {
    id: s.data.user_id,
    role: String(u.role ?? "student"),
    name: (String(u.firstName ?? "") + " " + String(u.lastName ?? "")).trim() || "دانش‌آموز",
    grade: String(u.grade ?? ""),
    section: String(u.section ?? ""),
  };
}

/* -------------------------------- مسیرها -------------------------------- */

async function login(req) {
  const body = await req.json().catch(() => ({}));
  const phone = norm(body.phone);
  const password = String(body.password ?? "").trim();
  if (!phone || !password) return json({ error: "شماره تلفن و رمز عبور را وارد کنید." }, 400);

  const r = await selectRows(
    "hamdel_records",
    "collection=eq.users&deleted=eq.false&data->>phone=eq." +
      encodeURIComponent(phone) +
      "&select=id,data&limit=1",
    true,
  );
  if (r.error) return json({ error: "خطا در ارتباط با پایگاه‌داده." }, 500);
  if (!r.data) return json({ error: "کاربری با این شماره در همدل یافت نشد." }, 401);

  const u = r.data.data ?? {};
  if (String(u.password ?? "").trim() !== password) {
    return json({ error: "رمز عبور با حساب همدل هم‌خوان نیست." }, 401);
  }

  await updateRows(
    "hamdel_records",
    "collection=eq.users&id=eq." + encodeURIComponent(r.data.id),
    { data: { ...u, lastLoginAt: Date.now() } },
  );

  const token = await createSession(r.data.id);
  return json({
    token,
    user: {
      id: r.data.id,
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

async function me(req) {
  const v = await viewer(req);
  if (!v) return json({ error: "نشست منقضی شده است؛ دوباره وارد شوید." }, 401);

  const uid = encodeURIComponent(v.id);
  const [progress, attempts, days, summary, subjects] = await Promise.all([
    selectRows("darsyar_progress", "user_id=eq." + uid + "&select=*"),
    selectRows("darsyar_attempts", "user_id=eq." + uid + "&select=*&order=created_at.desc&limit=80"),
    selectRows("darsyar_days", "user_id=eq." + uid + "&select=*&order=day.desc&limit=400"),
    selectRows("darsyar_my_summary", "user_id=eq." + uid + "&select=*", true),
    selectRows("darsyar_student_subjects", "user_id=eq." + uid + "&select=*"),
  ]);

  return json({
    user: v,
    progress: progress.data ?? [],
    attempts: attempts.data ?? [],
    days: days.data ?? [],
    summary: summary.data ?? null,
    subjects: subjects.data ?? [],
  });
}

async function save(req) {
  const v = await viewer(req);
  if (!v) return json({ error: "نشست منقضی شده است؛ دوباره وارد شوید." }, 401);

  const body = await req.json().catch(() => ({}));
  const ops = Array.isArray(body.ops) ? body.ops.slice(0, 60) : [];
  if (!ops.length) return json({ ok: true, saved: 0 });

  const now = new Date().toISOString();
  // چند عملیات برای یک درس در یک بچ، با هم ادغام می‌شوند (نه بازنویسی)
  const rows = new Map();
  const attempts = [];

  for (const op of ops) {
    if (!op || typeof op.subject !== "string" || typeof op.lessonId !== "string") continue;
    if (op.subject === "__mode") continue;
    const subject = op.subject.slice(0, 40);
    const lessonId = op.lessonId.slice(0, 40);
    const key = subject + ":" + lessonId;
    const read = op.read === true;
    const pct = Number.isFinite(op.pct)
      ? Math.max(0, Math.min(100, Math.round(op.pct)))
      : undefined;
    const gainedXp = Number.isFinite(op.xp) ? Math.max(0, Math.round(op.xp)) : 0;

    let row = rows.get(key);
    if (!row) {
      const p = await selectRows(
        "darsyar_progress",
        "user_id=eq." +
          encodeURIComponent(v.id) +
          "&subject=eq." +
          encodeURIComponent(subject) +
          "&lesson_id=eq." +
          encodeURIComponent(lessonId) +
          "&select=*",
        true,
      );
      const prev = p.data;
      row = {
        user_id: v.id,
        subject,
        lesson_id: lessonId,
        read: !!prev?.read,
        read_at: prev?.read_at ?? null,
        best_pct: prev?.best_pct ?? null,
        last_pct: prev?.last_pct ?? null,
        tries: prev?.tries ?? 0,
        xp: prev?.xp ?? 0,
        mode: prev?.mode ?? "normal",
        updated_at: now,
      };
      rows.set(key, row);
    }

    if (read && !row.read) {
      row.read = true;
      row.read_at = row.read_at ?? now;
    }
    if (pct !== undefined) {
      row.best_pct = Math.max(pct, row.best_pct ?? 0);
      row.last_pct = pct;
      row.tries = (row.tries ?? 0) + 1;
    }
    row.xp = (row.xp ?? 0) + gainedXp;
    if (op.mode === "quick") {
      if (!row.read) row.mode = "quick";
    } else if (op.mode) {
      row.mode = "normal";
    }

    if (pct !== undefined) {
      attempts.push({
        id: v.id + ":" + subject + ":" + lessonId + ":" + Date.now() + ":" + attempts.length,
        user_id: v.id,
        subject,
        lesson_id: lessonId,
        pct,
        correct: Number.isFinite(op.correct) ? Math.round(op.correct) : null,
        total: Number.isFinite(op.total) ? Math.round(op.total) : null,
        mode: op.mode === "quick" ? "quick" : "normal",
        created_at: now,
      });
    }
  }

  const list = [...rows.values()];
  if (list.length) {
    const r = await upsertRows("darsyar_progress", list, "user_id,subject,lesson_id");
    if (r.error) return json({ error: r.error }, 500);
  }
  if (attempts.length) {
    const r = await upsertRows("darsyar_attempts", attempts);
    if (r.error) return json({ error: r.error }, 500);
  }

  // XP امروز جمع می‌شود، نه بازنویسی
  const today = new Date().toISOString().slice(0, 10);
  const gained = list.reduce((s, r) => s + Number(r.xp ?? 0), 0);
  const tr = await selectRows(
    "darsyar_days",
    "user_id=eq." + encodeURIComponent(v.id) + "&day=eq." + today + "&select=xp",
    true,
  );
  await upsertRows(
    "darsyar_days",
    { user_id: v.id, day: today, xp: Number(tr.data?.xp ?? 0) + gained },
    "user_id,day",
  );

  return json({ ok: true, saved: list.length });
}

const STAFF = new Set([
  "teacher",
  "principal",
  "edu_deputy",
  "cultural_deputy",
  "tech_deputy",
  "counselor",
  "developer",
]);


// ---------------------------------------------------------------------------
//  /leaderboard — تابلوی قهرمانان (فقط نام کوتاه، بدون هیچ داده شخصی)
//  ورودی: { subject? }   خروجی: { players: [{ name, xp, streak, lessons }] }
// ---------------------------------------------------------------------------
async function leaderboard(req) {
  let v = null;
  try { v = await viewer(req); } catch (e) { v = null; }
  if (!v) return json({ error: "نشست منقضی شده است؛ دوباره وارد شوید." }, 401);

  // جمع امتیاز هر دانش‌آموز از خلاصهٔ آماده در دیتابیس
  const rows = await selectRows(
    "darsyar_student_summary",
    "select=user_id,first_name,last_name,xp,lessons_read,quizzes_taken&xp=gt.0&order=xp.desc&limit=50",
  );
  if (rows.error) return json({ error: rows.error }, 500);

  const me = String(v.id ?? "");
  const players = (rows.data ?? []).map((r, i) => ({
    rank: i + 1,
    name: shortName([r.first_name, r.last_name].filter(Boolean).join(" ")),
    xp: Number(r.xp) || 0,
    lessons: Number(r.lessons_read) || 0,
    quizzes: Number(r.quizzes_taken) || 0,
    me: String(r.user_id) === me,
  }));

  return json({ players });
}

/** نام را برای نمایش عمومی کوتاه می‌کند: «علی محمدی» → «علی م.» */
function shortName(n) {
  const s = String(n || "").trim();
  if (!s) return "دانش‌آموز";
  const parts = s.split(/\s+/);
  if (parts.length === 1) return parts[0];
  return parts[0] + " " + parts[parts.length - 1].slice(0, 1) + ".";
}

async function teacher(req) {
  const v = await viewer(req);
  if (!v) return json({ error: "نشست منقضی شده است." }, 401);
  if (!STAFF.has(v.role)) return json({ error: "این بخش برای کادر مدرسه است." }, 403);

  const rows = await selectRows(
    "darsyar_student_summary",
    "select=*&order=last_active.desc.nullslast",
  );
  if (rows.error) return json({ error: rows.error }, 500);

  const attempts = await selectRows(
    "darsyar_attempts",
    "select=user_id,subject,lesson_id,pct,created_at&order=created_at.desc&limit=3000",
  );

  return json({ rows: rows.data ?? [], attempts: attempts.data ?? [] });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const segs = new URL(req.url).pathname.split("/").filter(Boolean);
  const path = segs[segs.length - 1] || "";
  try {
    if (path === "login") return await login(req);
    if (path === "me") return await me(req);
    if (path === "save") return await save(req);
    if (path === "leaderboard") return await leaderboard(req);
    if (path === "teacher") return await teacher(req);
    return json({ error: "مسیر ناشناخته", path }, 404);
  } catch (err) {
    return json({ error: err.message ?? "خطای ناشناخته" }, 500);
  }
});
