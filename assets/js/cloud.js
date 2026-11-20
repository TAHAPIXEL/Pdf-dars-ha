/* ============================================================
   درس‌یار نهم — لایهٔ ورود و همگام‌سازی با «همدل»
   ------------------------------------------------------------
   • ورود با همان شماره تلفن و رمز عبور حساب همدل
   • نشست Bearer روی تابع لبهٔ Supabase (darsyar-auth)
   • پیشرفت، نمرهٔ آزمون‌ها و روزهای فعالیت روی دیتابیس همدل
   • اگر دیتابیس در دسترس نبود، سایت آفلاین کار می‌کند و بعد
     همگام می‌شود (صف محلی)
   ============================================================ */
(function (global) {
  "use strict";

  const CFG = global.DARS_CLOUD || {};
  const API = (CFG.api || "").replace(/\/$/, "");
  // مسیرهای نسبی (مثل /api/auth) همیشه فعال‌اند؛ آدرس خالی = حالت آفلاین
  const ON = !!API;

  const KEY_TOKEN = "darsyar9:token";
  const KEY_USER = "darsyar9:user";
  const KEY_QUEUE = "darsyar9:queue";

  const ls = {
    get(k, d) {
      try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; }
      catch (e) { return d; }
    },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    del(k) { try { localStorage.removeItem(k); } catch (e) {} },
  };

  const Cloud = {
    ready: ON,
    _user: ls.get(KEY_USER, null),
    _token: ls.get(KEY_TOKEN, null),

    user() { return this._user; },
    loggedIn() { return !!this._token && !!this._user; },
    isStaff() {
      const r = (this._user || {}).role || "";
      return ["teacher", "principal", "edu_deputy", "cultural_deputy", "tech_deputy", "counselor", "developer"].includes(r);
    },

    async _call(path, body, opts) {
      const o = opts || {};
      if (!ON) throw new Error("آدرس سرور تنظیم نشده است.");
      const headers = { "Content-Type": "application/json" };
      if (this._token) headers.Authorization = "Bearer " + this._token;
      if (CFG.anonKey) { headers.apikey = CFG.anonKey; }
      let res;
      try {
        res = await fetch(API + "/" + path, {
          method: "POST",
          headers,
          body: JSON.stringify(body || {}),
          cache: "no-store",
        });
      } catch (netErr) {
        const e = new Error("ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی کنید.");
        e.status = 0;
        e.network = true;
        throw e;
      }
      let data = null;
      try { data = await res.json(); } catch (e) { /* بدنهٔ خالی */ }
      if (!res.ok) {
        let msg = data && data.error;
        if (!msg) {
          if (res.status === 404) msg = "سرور ورود در دسترس نیست. کمی بعد تلاش کنید.";
          else if (res.status === 502 || res.status === 504) msg = "سرور پاسخ نداد. کمی بعد تلاش کنید.";
          else msg = "خطا در ارتباط با سرور (کد " + res.status + ")";
        }
        const err = new Error(msg);
        err.status = res.status;
        throw err;
      }
      return data || {};
    },

    /* ---------------- ورود ---------------- */
    async login(phone, password) {
      const clean = String(phone || "").replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)))
        .replace(/[\s-]/g, "");
      const data = await this._call("login", { phone: clean, password: String(password || "").trim() });
      this._token = data.token;
      this._user = data.user;
      ls.set(KEY_TOKEN, this._token);
      ls.set(KEY_USER, this._user);
      return this._user;
    },

    async logout() {
      this._token = null;
      this._user = null;
      ls.del(KEY_TOKEN);
      ls.del(KEY_USER);
      ls.del(KEY_QUEUE);
    },

    async restore() {
      if (!this._token) return null;
      try {
        const data = await this._call("me");
        this._user = data.user || this._user;
        ls.set(KEY_USER, this._user);
        return data;
      } catch (e) {
        if (e.status === 401) { await this.logout(); return null; }
        return null;                    // آفلاین: همان نشست محلی بماند
      }
    },

    /* ---------------- صف تغییرات ---------------- */
    queue(op) {
      const q = ls.get(KEY_QUEUE, []);
      // آخرین تغییرِ هر درس، تغییرهای پیشین همان درس را بازنویسی می‌کند
      const key = op.subject + ":" + op.lessonId;
      const i = q.findIndex((x) => x.subject + ":" + x.lessonId === key);
      if (i >= 0) {
        const prev = q[i];
        q[i] = {
          ...prev,
          read: !!prev.read || !!op.read,
          pct: op.pct === undefined ? prev.pct : Math.max(prev.pct || 0, op.pct),
          correct: op.correct !== undefined ? op.correct : prev.correct,
          total: op.total !== undefined ? op.total : prev.total,
          xp: (prev.xp || 0) + (op.xp || 0),
          mode: op.mode || prev.mode,
        };
      } else {
        q.push(op);
      }
      ls.set(KEY_QUEUE, q.slice(-80));
    },

    pending() { return ls.get(KEY_QUEUE, []).length; },

    _flushing: false,

    async flush() {
      if (!this.loggedIn() || this._flushing) return;
      const q = ls.get(KEY_QUEUE, []);
      if (!q.length) return;
      this._flushing = true;
      try {
        await this._call("save", { ops: q });
        // فقط همان عملیاتی را بردار که فرستادیم؛ تغییرهای تازه در صف می‌مانند
        const rest = ls.get(KEY_QUEUE, []).slice(q.length);
        ls.set(KEY_QUEUE, rest);
        global.dispatchEvent(new CustomEvent("dars:synced"));
        this._mark(true);
      } catch (e) {
        this._mark(false);
        if (e.status === 401) await this.logout();
      } finally {
        this._flushing = false;
      }
    },

    /** نمایش وضعیت همگام‌سازی در نوار بالا */
    _mark(ok) {
      try {
        const dot = document.querySelector("[data-sync]");
        if (!dot) return;
        dot.setAttribute("data-state", ok ? "ok" : "off");
        dot.title = ok ? "همگام با حساب همدل" : "در انتظار اتصال…";
      } catch (e) { /* بی‌اهمیت */ }
    },

    /* ---------------- ذخیرهٔ فوری یک تغییر ---------------- */
    push(op) {
      this.queue(op);
      return this.flush();
    },
  };

  // همگام‌سازی خودکار: پس از هر ورود، بازگشت به شبکه و هر ۴۵ ثانیه
  if (typeof window !== "undefined") {
    window.addEventListener("online", () => Cloud.flush());
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") Cloud.flush();
    });
    setInterval(() => Cloud.flush(), 45000);
  }

  global.DarsCloud = Cloud;
})(window);
