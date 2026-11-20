/* ============================================================
   درس‌یار نهم — موتور مشترک
   ذخیره‌سازی، پیشرفت، آزمون، افکت‌ها
   بدون هیچ وابستگی خارجی. کامل آفلاین.
   ============================================================ */
(function (global) {
  "use strict";

  /* ----------------------------------------------------------
     ابزارهای پایه
     ---------------------------------------------------------- */
  const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

  /** تبدیل عدد لاتین به فارسی */
  function fa(n) {
    return String(n).replace(/\d/g, (d) => FA_DIGITS[+d]);
  }

  /** عدد به حروف فارسی (تا ۹۹) */
  const ONES = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"];
  const TEENS = ["ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده"];
  const TENS = ["", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"];
  function faWords(n) {
    n = Math.trunc(n);
    if (n === 0) return "صفر";
    if (n < 10) return ONES[n];
    if (n < 20) return TEENS[n - 10];
    if (n < 100) {
      const t = Math.floor(n / 10), o = n % 10;
      return TENS[t] + (o ? " و " + ONES[o] : "");
    }
    if (n < 1000) {
      const h = Math.floor(n / 100), r = n % 100;
      const hw = ONES[h] + "صد";
      return hw + (r ? " و " + faWords(r) : "");
    }
    const th = Math.floor(n / 1000), r = n % 1000;
    return faWords(th) + " هزار" + (r ? " و " + faWords(r) : "");
  }

  /** انتخاب تصادفی */
  const rnd = (arr) => arr[Math.floor(Math.random() * arr.length)];

  /** بُر زدن آرایه (Fisher–Yates) */
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  /** ساخت المان با ویژگی‌ها */
  function el(tag, attrs, ...kids) {
    const n = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        const v = attrs[k];
        if (v === null || v === undefined || v === false) continue;
        if (k === "class") n.className = v;
        else if (k === "html") n.innerHTML = v;
        else if (k === "text") n.textContent = v;
        else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
        else n.setAttribute(k, v);
      }
    }
    kids.flat().forEach((c) => {
      if (c === null || c === undefined || c === false) return;
      n.append(c.nodeType ? c : document.createTextNode(String(c)));
    });
    return n;
  }

  /* ----------------------------------------------------------
     ذخیره‌سازی — با محافظت در برابر حالت خصوصی
     ---------------------------------------------------------- */
  const KEY = "darsyar9:v1";

  const Store = {
    _mem: null,
    _read() {
      if (this._mem) return this._mem;
      try {
        const raw = localStorage.getItem(KEY);
        this._mem = raw ? JSON.parse(raw) : { lessons: {}, quizzes: {}, xp: 0, streak: 0, lastDay: null };
      } catch (e) {
        this._mem = { lessons: {}, quizzes: {}, xp: 0, streak: 0, lastDay: null };
      }
      if (!this._mem.lessons) this._mem.lessons = {};
      if (!this._mem.quizzes) this._mem.quizzes = {};
      return this._mem;
    },
    _write(d) {
      this._mem = d;
      try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) { /* حالت خصوصی */ }
    },
    /** علامت‌گذاری درس به‌عنوان خوانده‌شده */
    markLesson(subject, id) {
      const d = this._read();
      const k = subject + ":" + id;
      const first = !d.lessons[k];
      d.lessons[k] = d.lessons[k] || Date.now();
      d.quick = d.quick || {};
      if (first) this._addXP(d, 10);
      this._touchStreak(d);
      this._write(d);
      // فقط بار اول XP می‌رود؛ تکرار کلیک، امتیاز دوباره نمی‌دهد
      this._cloud({ subject, lessonId: id, read: true, xp: first ? 10 : 0, mode: d.mode });
    },
    /** ثبت نتیجه آزمون */
    saveQuiz(subject, id, pct, xp, extra) {
      const d = this._read();
      const k = subject + ":" + id;
      const prev = d.quizzes[k];
      d.quizzes[k] = {
        best: Math.max(prev ? prev.best : 0, pct),
        last: pct,
        at: Date.now(),
        tries: (prev ? prev.tries : 0) + 1
      };
      if (xp) this._addXP(d, xp);
      this._touchStreak(d);
      this._write(d);
      this._cloud(Object.assign({ subject, lessonId: id, pct, xp: xp || 0 }, extra || {}));
    },

    /** ارسال تغییر به ابر (اگر وارد شده باشد) */
    _cloud(op) {
      try {
        if (global.DarsCloud && global.DarsCloud.loggedIn()) global.DarsCloud.push(op);
      } catch (e) { /* آفلاین */ }
    },

    /* ---------------- حالت یادگیری سریع ---------------- */
    mode() { return this._read().mode || "normal"; },
    setMode(m) {
      const d = this._read();
      d.mode = m === "quick" ? "quick" : "normal";
      this._write(d);
      return d.mode;
    },

    /** خلاصهٔ درس را خوانده‌شده حساب می‌کند (حالت سریع) */
    markQuickRead(subject, id) {
      const d = this._read();
      d.quick = d.quick || {};
      const k = subject + ":" + id;
      const first = !d.quick[k] && !d.lessons[k];
      d.quick[k] = d.quick[k] || Date.now();
      if (!d.lessons[k]) {
        d.lessons[k] = Date.now();
        if (first) this._addXP(d, 6);
      }
      this._touchStreak(d);
      this._write(d);
      this._cloud({ subject, lessonId: id, read: true, xp: first ? 6 : 0, mode: "quick" });
    },
    isQuickRead(subject, id) { return !!(this._read().quick || {})[subject + ":" + id]; },

    /** همگام‌سازی وضعیت محلی با داده‌های دیتابیس پس از ورود */
    hydrate(progress, days) {
      const d = this._read();
      (progress || []).forEach((r) => {
        const k = r.subject + ":" + r.lesson_id;
        if (r.read) d.lessons[k] = new Date(r.read_at || Date.now()).getTime();
        if (r.best_pct !== null && r.best_pct !== undefined) {
          const prev = d.quizzes[k];
          d.quizzes[k] = {
            best: Math.max(prev ? prev.best : 0, r.best_pct),
            last: r.last_pct === null || r.last_pct === undefined ? r.best_pct : r.last_pct,
            at: new Date(r.updated_at || Date.now()).getTime(),
            tries: r.tries || 1
          };
        }
        if (r.mode === "quick") { d.quick = d.quick || {}; d.quick[k] = d.quick[k] || Date.now(); }
      });
      if (Array.isArray(days) && days.length) {
        const set = new Set(days.map((x) => String(x.day).slice(0, 10)));
        d.days = [...set];
        let st = 0;
        const day = new Date();
        for (;;) {
          const key = day.toISOString().slice(0, 10);
          if (!set.has(key)) break;
          st++;
          day.setDate(day.getDate() - 1);
        }
        d.streak = Math.max(d.streak || 0, st);
        d.lastDay = new Date().toISOString().slice(0, 10);
      }
      d.xp = Math.max(d.xp || 0, (progress || []).reduce((s, r) => s + (r.xp || 0), 0));
      this._write(d);
    },
    _addXP(d, n) { d.xp = (d.xp || 0) + n; },
    _touchStreak(d) {
      const today = new Date().toISOString().slice(0, 10);
      if (d.lastDay === today) return;
      const y = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
      d.streak = d.lastDay === y ? (d.streak || 0) + 1 : 1;
      d.lastDay = today;
    },
    isLessonDone(subject, id) { return !!this._read().lessons[subject + ":" + id]; },
    getQuiz(subject, id) { return this._read().quizzes[subject + ":" + id] || null; },
    xp() { return this._read().xp || 0; },
    streak() { return this._read().streak || 0; },
    /** شمارنده‌های کارنامه */
    stats() {
      const d = this._read();
      return {
        xp: d.xp || 0,
        streak: d.streak || 0,
        lessons: d.lessons || {},
        quizzes: d.quizzes || {},
        quick: d.quick || {},
      };
    },
    /** درصد کل پیشرفت یک درس */
    subjectProgress(subject, lessonIds, quizIds) {
      const d = this._read();
      let done = 0, total = 0;
      (lessonIds || []).forEach((id) => { total++; if (d.lessons[subject + ":" + id]) done++; });
      (quizIds || []).forEach((id) => { total++; if (d.quizzes[subject + ":" + id]) done++; });
      return total ? Math.round((done / total) * 100) : 0;
    },
    reset() { this._mem = null; try { localStorage.removeItem(KEY); } catch (e) {} }
  };

  /* ----------------------------------------------------------
     جشن ذرات — پایان آزمون موفق
     ---------------------------------------------------------- */
  function celebrate(count) {
    try {
      if (typeof window.matchMedia === "function" &&
          window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    } catch (e) { /* محیط بدون matchMedia */ }
    if (typeof document.body.animate !== "function" && !Element.prototype.animate) return;
    const colors = ["#6c8cff", "#34d399", "#fbbf24", "#f472b6", "#38bdf8", "#a78bfa"];
    const host = document.createElement("div");
    host.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:9999;overflow:hidden";
    document.body.append(host);
    const n = count || 46;
    for (let i = 0; i < n; i++) {
      const p = document.createElement("i");
      const size = 6 + Math.random() * 8;
      p.style.cssText = [
        "position:absolute",
        "left:" + (Math.random() * 100) + "%",
        "top:-20px",
        "width:" + size + "px",
        "height:" + size + "px",
        "border-radius:" + (Math.random() > .5 ? "50%" : "2px"),
        "background:" + rnd(colors),
        "opacity:" + (.7 + Math.random() * .3),
        "transform:rotate(" + (Math.random() * 360) + "deg)"
      ].join(";");
      host.append(p);
      const dur = 1400 + Math.random() * 1400;
      const drift = (Math.random() - .5) * 220;
      p.animate(
        [
          { transform: "translate3d(0,0,0) rotate(0deg)", opacity: 1 },
          { transform: "translate3d(" + drift + "px," + (window.innerHeight + 80) + "px,0) rotate(" + (Math.random() * 720 - 360) + "deg)", opacity: 0 }
        ],
        { duration: dur, easing: "cubic-bezier(.2,.6,.5,1)", delay: Math.random() * 260 }
      );
    }
    setTimeout(() => host.remove(), 3200);
    try { sfx.correct(); } catch (e) { /* بی‌صدا */ }
  }

  /* ----------------------------------------------------------
     نوار بالای صفحه — آمار زنده
     ---------------------------------------------------------- */
  function paintStats() {
    const xpEls = document.querySelectorAll("[data-xp]");
    if (xpEls.length) {
      const xp = Store.xp();
      xpEls.forEach((e) => (e.textContent = fa(xp)));
    }
    const stEls = document.querySelectorAll("[data-streak]");
    if (stEls.length) {
      const s = Store.streak();
      stEls.forEach((e) => (e.textContent = fa(s)));
    }
  }

  /* ----------------------------------------------------------
     مسیر یادگیری
     ---------------------------------------------------------- */
  /**
   * @param {HTMLElement} host
   * @param {Object} cfg  { subject, steps:[{id,type,title,kicker,meta,href}], quizBase }
   */
  function buildPath(host, cfg) {
    if (!host) return;
    host.innerHTML = "";
    host.className = "relative py-6";

    // ریتم مارپیچی نمونه: 0, +52, 0, -52
    const OFFSETS = [0, 52, 0, -52];
    const steps = cfg.steps || [];

    // گرهٔ بعدی = اولین گام انجام‌نشده
    let nextIdx = -1;
    steps.forEach((s, i) => {
      const done = s.type === "quiz"
        ? !!Store.getQuiz(cfg.subject, s.id)
        : Store.isLessonDone(cfg.subject, s.id);
      if (!done && nextIdx === -1) nextIdx = i;
    });
    if (nextIdx === -1 && steps.length) nextIdx = steps.length - 1;

    // خط‌چین عمودی (spine)
    const spine = document.createElement("div");
    spine.className = "absolute inset-y-0 left-1/2 -translate-x-1/2 w-px";
    spine.innerHTML =
      '<svg class="w-8 h-full -translate-x-1/2" aria-hidden="true">' +
        '<line x1="50%" y1="0" x2="50%" y2="100%" stroke="rgba(148,163,184,.3)" ' +
        'stroke-width="3" class="path-dash" stroke-dasharray="6 10"></line>' +
      "</svg>";
    host.append(spine);

    const list = document.createElement("div");
    list.className = "relative flex flex-col items-center gap-12 sm:gap-14 py-4";

    steps.forEach((s, i) => {
      const done = s.type === "quiz"
        ? !!Store.getQuiz(cfg.subject, s.id)
        : Store.isLessonDone(cfg.subject, s.id);
      const isNext = i === nextIdx && !done;
      const offset = OFFSETS[i % 4];

      const a = document.createElement("a");
      a.href = s.href || "#";
      a.style.transform = "translateX(" + offset + "px)";
      a.className = "flex flex-col items-center gap-3 group";

      // دایره
      const btn = document.createElement("div");
      btn.className = "w-[68px] h-[68px] sm:w-[72px] sm:h-[72px] rounded-full grid place-items-center " +
        "border-4 transition-all duration-200 " +
        (done
          ? "bg-mint border-mint/40 shadow-[0_0_30px_-4px_rgba(52,211,153,.6)]"
          : isNext
            ? "animate-pulse-ring border-white/30"
            : "bg-panel2 border-white/10");
      if (isNext) btn.style.background = "var(--accent, #a78bfa)";
      btn.innerHTML = done
        ? '<span class="text-ink text-2xl font-black">✓</span>'
        : isNext
          ? '<span class="text-ink text-xl" style="fill:#05080f">▶</span>'
          : '<span class="text-fog text-lg font-black">' + fa(i + 1) + "</span>";

      // برچسب
      const label = document.createElement("div");
      label.className = "text-center max-w-[190px] sm:max-w-[230px]";
      const kicker = s.kicker
        ? '<div class="text-[10px] font-black uppercase tracking-wide text-fog/70 mb-1">' + s.kicker + "</div>"
        : "";
      const meta = (s.meta || []).filter(Boolean).length
        ? '<div class="mt-1.5 flex items-center justify-center gap-2 flex-wrap text-[11px] text-fog/80">' +
            (s.meta || []).filter(Boolean).map(m => "<span>" + m + "</span>").join("") + "</div>"
        : "";
      label.innerHTML =
        kicker +
        '<div class="font-black text-sm leading-6 ' + (done ? "text-mint" : isNext ? "text-snow" : "text-fog") + '">' +
          s.title + "</div>" + meta;

      a.append(btn, label);
      list.append(a);
    });

    host.append(list);
  }


  /* ----------------------------------------------------------
     افکت‌های سبک: کانفتی و صدا (بدون فایل بیرونی)
     ---------------------------------------------------------- */

  /** کانفتی سبک روی canvas — روی گوشی ضعیف هم روان است */
  function confetti(n) {
    try {
      if (!document.body) return;
      const cv = document.createElement("canvas");
      cv.width = innerWidth; cv.height = innerHeight;
      cv.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:9999";
      document.body.appendChild(cv);
      const ctx = cv.getContext("2d");
      if (!ctx) { cv.remove(); return; }
      const colors = ["#34d399", "#22d3ee", "#a78bfa", "#facc15", "#fb7185"];
      const total = Math.min(70, Math.round((innerWidth * innerHeight) / 24000));
      const parts = Array.from({ length: n || total }, () => ({
        x: innerWidth / 2 + (Math.random() - .5) * 180,
        y: innerHeight * .42,
        vx: (Math.random() - .5) * 9,
        vy: -Math.random() * 11 - 3,
        r: Math.random() * 5 + 3,
        c: colors[(Math.random() * colors.length) | 0],
        a: 1,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - .5) * .3,
      }));
      let frames = 0;
      (function loop() {
        ctx.clearRect(0, 0, cv.width, cv.height);
        parts.forEach((p) => {
          p.x += p.vx; p.y += p.vy; p.vy += .32; p.rot += p.vr; p.a -= .008;
          if (p.a <= 0) return;
          ctx.save();
          ctx.translate(p.x, p.y); ctx.rotate(p.rot);
          ctx.globalAlpha = Math.max(0, p.a);
          ctx.fillStyle = p.c;
          ctx.fillRect(-p.r / 2, -p.r / 2, p.r, p.r * 1.7);
          ctx.restore();
        });
        frames++;
        if (frames < 130) requestAnimationFrame(loop);
        else cv.remove();
      })();
    } catch (e) { /* بی‌اهمیت */ }
  }

  /** صدا با WebAudio؛ بدون فایل. اگر مرورگر نگذارد، بی‌صدا رد می‌شود. */
  const sfx = {
    _ctx: null,
    _on() { try { return localStorage.getItem("darsyar9:sound") !== "0"; } catch (e) { return true; } },
    set(on) { try { localStorage.setItem("darsyar9:sound", on ? "1" : "0"); } catch (e) {} },
    on() { return this._on(); },
    _ac() {
      if (!this._ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        this._ctx = new AC();
      }
      return this._ctx;
    },
    _beep(freq, dur, type, gain) {
      if (!this._on()) return;
      try {
        const ac = this._ac();
        if (!ac) return;
        if (ac.state === "suspended") ac.resume();
        const o = ac.createOscillator();
        const g = ac.createGain();
        o.type = type || "sine";
        o.frequency.value = freq;
        g.gain.setValueAtTime(0, ac.currentTime);
        g.gain.linearRampToValueAtTime(gain || .06, ac.currentTime + .01);
        g.gain.exponentialRampToValueAtTime(.0001, ac.currentTime + dur);
        o.connect(g); g.connect(ac.destination);
        o.start(); o.stop(ac.currentTime + dur + .02);
      } catch (e) { /* بی‌صدا */ }
    },
    correct() { this._beep(660, .12, "sine", .07); setTimeout(() => this._beep(990, .16, "sine", .06), 90); },
    wrong()   { this._beep(220, .18, "triangle", .05); },
    pop()     { this._beep(520, .07, "square", .035); },
  };

  /* ----------------------------------------------------------
     موتور آزمون
     ---------------------------------------------------------- */
  /**
   * @param {Object} cfg
   *   subject  : کلید درس
   *   id       : شناسه آزمون
   *   host     : المان میزبان
   *   questions: [{ q, opts:[..], a:index, why, tag }]
   *   pass     : درصد قبولی (پیش‌فرض ۷۰)
   *   onDone   : callback
   */
  function runQuiz(cfg) {
    const host = cfg.host;
    if (!host) return;
    const Q = cfg.questions || [];
    if (!Q.length) {
      host.innerHTML = '<div class="glass rounded-3xl p-10 text-center"><div class="text-5xl mb-3">📭</div><p class="text-fog">سؤالی برای این آزمون ثبت نشده است.</p></div>';
      return;
    }

    const order = shuffle(Q);
    let i = 0, correct = 0, answered = false;
    const startXP = Store.xp();

    host.innerHTML = "";

    const trackFill = el("i");
    trackFill.className = "block h-full rounded-full transition-all duration-300";
    trackFill.style.background = "linear-gradient(90deg,#a78bfa,#22d3ee)";
    trackFill.style.width = "0%";

    const countEl = el("div", { class: "text-xs font-black text-fog mb-2" });
    const track = el("div", { class: "h-2 rounded-full bg-white/10 overflow-hidden" }, trackFill);
    const top = el("div", { class: "mb-6" }, countEl, track);

    const stage = el("div", { id: "qz-stage" });
    host.append(top, stage);

    function paintTop() {
      countEl.innerHTML = "سؤال <b>" + fa(i + 1) + "</b> از " + fa(order.length);
      trackFill.style.width = ((i / order.length) * 100) + "%";
    }

    function render() {
      answered = false;
      paintTop();
      const q = order[i];
      stage.innerHTML = "";

      const optWrap = el("div", { class: "space-y-2.5" });
      const letters = ["الف", "ب", "ج", "د", "هـ", "و"];

      const fb = el("div", { class: "mt-4" });

      const nextBtn = el("button", {
        class: "btn3d rounded-xl px-5 py-3 text-sm font-black text-ink cursor-pointer",
        type: "button",
        text: i === order.length - 1 ? "دیدن نتیجه" : "سؤال بعدی ←",
        onclick: () => {
          if (i < order.length - 1) { i++; render(); }
          else finish();
        }
      });
      nextBtn.style.background = "linear-gradient(90deg,#a78bfa,#22d3ee)";
      nextBtn.style.display = "none";

      const skipBtn = el("button", {
        class: "rounded-xl px-4 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors",
        type: "button", text: "رد کردن آزمون",
        title: "آزمون اجباری نیست؛ می‌توانی بعداً بدهی",
        onclick: () => skip()
      });

      const actions = el("div", { class: "mt-6 flex items-center gap-2 flex-wrap" },
        skipBtn,
        el("div", { class: "flex-1" }),
        nextBtn
      );

      q.opts.forEach((o, oi) => {
        const mark = el("div", {
          class: "w-8 h-8 rounded-lg grid place-items-center shrink-0 text-xs font-black bg-white/10 text-fog transition-colors",
          text: letters[oi] || fa(oi + 1)
        });
        const btn = el("button", {
          class: "w-full flex items-center gap-3 rounded-2xl border-2 border-white/10 bg-white/[0.03] px-4 py-3.5 text-start font-bold text-sm leading-6 transition-all hover:bg-white/[0.08] hover:-translate-y-0.5",
          type: "button"
        }, mark, el("div", { class: "flex-1 text-start", text: o }));

        btn.addEventListener("click", () => {
          if (answered) return;
          answered = true;

          const good = oi === q.a;
          if (good) correct++;

          // قفل و رنگ‌آمیزی همه گزینه‌ها
          optWrap.querySelectorAll("button").forEach((b, bi) => {
            b.classList.add("pointer-events-none");
            const mk = b.querySelector("div");
            if (bi === q.a) {
              b.className = "w-full flex items-center gap-3 rounded-2xl border-2 border-mint bg-mint/15 text-mint px-4 py-3.5 text-start font-bold text-sm leading-6 animate-pop";
              if (mk) { mk.className = "w-8 h-8 rounded-lg grid place-items-center shrink-0 text-xs font-black bg-mint text-ink"; }
            } else if (bi === oi) {
              b.className = "w-full flex items-center gap-3 rounded-2xl border-2 border-rosee bg-rosee/15 text-rosee px-4 py-3.5 text-start font-bold text-sm leading-6 animate-shake";
              if (mk) { mk.className = "w-8 h-8 rounded-lg grid place-items-center shrink-0 text-xs font-black bg-rosee text-ink"; }
            } else {
              b.className = "w-full flex items-center gap-3 rounded-2xl border-2 border-white/5 bg-white/[0.02] text-fog/50 px-4 py-3.5 text-start font-bold text-sm leading-6 opacity-50";
            }
          });

          fb.innerHTML = "";
          const box = el("div", {
            class: "rounded-2xl border px-4 py-3.5 animate-pop " +
              (good ? "border-mint/40 bg-mint/10 text-mint" : "border-rosee/40 bg-rosee/10 text-rosee")
          },
            el("div", { class: "flex items-center gap-2 font-black text-sm" },
              el("span", { text: good ? "✓" : "✕" }),
              el("span", { text: good ? "درست بود!" : "پاسخ درست: " + (q.opts[q.a]) })
            ),
            q.why ? el("div", { class: "mt-2 text-xs leading-6 text-fog", text: q.why }) : null
          );
          fb.append(box);
          if (good) { try { confetti(); } catch (e) {} }

          nextBtn.style.display = "";
          nextBtn.focus({ preventScroll: true });
        });

        optWrap.append(btn);
      });

      const card = el("div", { class: "glass rounded-3xl p-5 sm:p-7 animate-pop" },
        q.tag ? el("span", { class: "inline-block rounded-full bg-white/10 px-3 py-1 text-[10px] font-black text-fog mb-3", text: q.tag }) : null,
        el("div", { class: "font-black text-base sm:text-lg leading-8 mb-5", text: q.q }),
        optWrap,
        fb,
        actions
      );

      stage.append(card);
    }

    /** آزمون اختیاری است: رد کردن بدون ثبت نمرهٔ نادرست */
    function skip() {
      Store._skipQuiz = true;
      stage.innerHTML = "";
      trackFill.style.width = "100%";
      const backHref = cfg.backHref || "index.html";
      const nextHref = cfg.nextHref || backHref;
      const box = el("div", { class: "glass rounded-3xl p-8 sm:p-12 text-center animate-pop" },
        el("div", { class: "text-6xl mb-4", text: "⏭" }),
        el("h2", { class: "text-2xl font-black mb-3", text: "آزمون را رد کردی" }),
        el("p", { class: "text-fog text-sm leading-8 mb-7 max-w-md mx-auto", text: "هیچ اشکالی ندارد. درس را خوانده‌ای و هر وقت خواستی می‌توانی آزمون بدهی — نمره‌ای ثبت نشد." }),
        el("div", { class: "flex flex-wrap items-center justify-center gap-3" },
          el("a", { class: "btn3d rounded-xl px-6 py-3 text-sm font-black text-ink", href: nextHref, text: "درس بعدی ←" }),
          el("a", { class: "rounded-xl px-6 py-3 text-sm font-bold border border-white/15 text-fog hover:text-snow transition-colors", href: backHref, text: "بازگشت به مسیر" })
        )
      );
      box.querySelector("a.btn3d").style.background = "linear-gradient(90deg,#34d399,#22d3ee)";
      stage.append(box);
      paintStats();
      if (typeof cfg.onSkip === "function") cfg.onSkip();
    }

    function finish() {
      trackFill.style.width = "100%";
      const pct = Math.round((correct / order.length) * 100);
      const pass = cfg.pass || 70;
      const earnedXP = Math.round(correct * 4) + (pct >= pass ? 18 : 0);

      Store.saveQuiz(cfg.subject, cfg.id, pct, earnedXP,
        { correct, total: order.length, mode: cfg.mode });

      try { if (pct >= pass) celebrate(52); } catch (e) { /* افکت نباید مانع نتیجه شود */ }

      stage.innerHTML = "";
      const ring = 150, r = 64, c = 2 * Math.PI * r;
      const off = c - (pct / 100) * c;

      const result = el("div", { class: "glass rounded-3xl p-6 sm:p-10 text-center animate-pop" },
        el("div", { class: "text-6xl mb-3", text: pct >= 90 ? "🏆" : pct >= pass ? "🎯" : "📚" }),
        el("h2", { class: "text-2xl sm:text-3xl font-black mb-3", text: pct >= 90 ? "بی‌نقص!" : pct >= pass ? "عالی بود!" : "ادامه بده!" }),
        el("p", { class: "text-fog text-sm leading-8 mb-6 max-w-md mx-auto", text: pct >= 90
          ? "همهٔ سؤال‌ها را درست پاسخ دادی. تسلطت کامل است."
          : pct >= pass
          ? "آزمون را با موفقیت گذراندی. یک قدم دیگر جلو رفتی."
          : "این بار کافی نبود، اما هیچ اشکالی ندارد. درس را یک بار دیگر بخوان و برگرد." }),
        el("div", { class: "relative w-[150px] h-[150px] mx-auto my-4" },
          (() => {
            const ns = "http://www.w3.org/2000/svg";
            const svg = document.createElementNS(ns, "svg");
            svg.setAttribute("viewBox", "0 0 150 150");
            const tr = document.createElementNS(ns, "circle");
            tr.setAttribute("cx", 75); tr.setAttribute("cy", 75); tr.setAttribute("r", r);
            tr.setAttribute("fill", "none"); tr.setAttribute("stroke-width", 11);
            tr.setAttribute("class", "track");
            const fl = document.createElementNS(ns, "circle");
            fl.setAttribute("cx", 75); fl.setAttribute("cy", 75); fl.setAttribute("r", r);
            fl.setAttribute("fill", "none"); fl.setAttribute("stroke-width", 11);
            fl.setAttribute("class", "fill");
            fl.setAttribute("stroke-dasharray", c);
            fl.setAttribute("stroke-dashoffset", c);
            svg.append(tr, fl);
            requestAnimationFrame(() => setTimeout(() => fl.setAttribute("stroke-dashoffset", off), 90));
            return svg;
          })(),
          el("div", { class: "absolute inset-0 grid place-items-center" },
            el("div", {},
              el("b", { class: "block text-3xl font-black", text: fa(pct) + "٪" }),
              el("small", { class: "text-[10px] text-fog", text: "پاسخ درست" })
            )
          )
        ),
        el("div", { class: "grid grid-cols-3 gap-2 sm:gap-3 mb-7 max-w-sm mx-auto" },
          el("div", { class: "rounded-2xl bg-mint/10 border border-mint/30 px-2 py-3" },
            el("b", { class: "block text-lg font-black text-mint", text: fa(correct) }),
            el("span", { class: "text-[10px] text-mint/80", text: "درست" })),
          el("div", { class: "rounded-2xl bg-rosee/10 border border-rosee/30 px-2 py-3" },
            el("b", { class: "block text-lg font-black text-rosee", text: fa(order.length - correct) }),
            el("span", { class: "text-[10px] text-rosee/80", text: "نادرست" })),
          el("div", { class: "rounded-2xl bg-xp/10 border border-xp/30 px-2 py-3" },
            el("b", { class: "block text-lg font-black text-xp", text: "+" + fa(earnedXP) }),
            el("span", { class: "text-[10px] text-xp/80", text: "XP" }))
        ),
        el("div", { class: "flex flex-wrap items-center justify-center gap-3" },
          el("button", {
            class: "btn3d rounded-xl px-6 py-3 text-sm font-black text-ink cursor-pointer", type: "button", text: "تلاش دوباره",
            onclick: () => { i = 0; correct = 0; render(); }
          }),
          el("a", { class: "rounded-xl px-6 py-3 text-sm font-bold border border-white/15 text-fog hover:text-snow transition-colors", href: cfg.backHref || "index.html", text: "بازگشت به مسیر" })
        )
      );
      result.querySelector("button.btn3d").style.background = "linear-gradient(90deg,#a78bfa,#22d3ee)";
      stage.append(result);

      paintStats();
      if (typeof cfg.onDone === "function") cfg.onDone(pct);
    }

    render();
  }

  /* ----------------------------------------------------------
     پیوند پیمایش سراسری
     ---------------------------------------------------------- */
  function wireNav() {
    document.querySelectorAll("[data-back]").forEach((b) => {
      b.addEventListener("click", (e) => {
        e.preventDefault();
        if (history.length > 1) history.back();
        else location.href = b.getAttribute("data-back") || "../index.html";
      });
    });
  }

  /* ----------------------------------------------------------
     ورود اجباری و نوار کاربر
     ---------------------------------------------------------- */

  /** اگر کاربر وارد نشده باشد به صفحهٔ ورود می‌رود. */
  function requireLogin(opts) {
    const o = opts || {};
    const C = global.DarsCloud;
    const onLogin = /(^|\/)login\.html(\?|$)/.test(location.pathname + location.search);
    if (!C) return true;                             // بدون لایهٔ ابر: آفلاین
    if (!C.ready && !C.loggedIn()) return true;      // آدرس تنظیم نشده: آفلاین
    if (C.loggedIn()) return true;
    if (onLogin) return false;
    // مسیر بازگشت را نسبت به ریشهٔ سایت بساز (صفحه‌های درس یک پوشه عمق دارند)
    const m = location.pathname.match(/\/lessons\/([^/]+)\/([^/]*)$/);
    const rel = m ? ("lessons/" + m[1] + "/" + (m[2] || "index.html")) : location.pathname.split("/").pop() || "index.html";
    const back = encodeURIComponent(rel + location.search);
    location.replace(loginHref() + "?next=" + back);
    return false;
  }

  /** نوار بالای صفحه: نام دانش‌آموز، XP، استریک، حالت یادگیری، خروج */
  function paintUserBar() {
    const C = global.DarsCloud;
    if (!C || !C.ready) return;
    const host = document.querySelector("[data-userbar]");
    if (!host) return;
    host.innerHTML = "";
    const u = C.user();
    if (!u) {
      const a = el("a", { href: loginHref(), text: "ورود" });
      a.className = "px-4 py-2 rounded-xl font-black text-ink bg-gradient-to-l from-violet to-skyy";
      host.append(a);
      return;
    }

    const initial = (u.firstName || u.lastName || "د").trim().slice(0, 1);
    const quick = Store.mode() === "quick";
    const st = Store.stats();
    const xp = st.xp || 0;
    const lvl = Math.floor(xp / 250) + 1;

    // آواتار + نام
    const prof = el("a", { href: rootHref() + "progress.html", title: "کارنامهٔ من" });
    prof.className = "flex items-center gap-2 rounded-xl px-2 py-1 hover:bg-white/5 transition-colors";
    const av = el("span", { text: initial });
    av.className = "w-8 h-8 rounded-lg grid place-items-center bg-white/10 text-sm font-black text-snow";
    const nm = el("span", { text: (u.firstName || "دانش‌آموز") });
    nm.className = "hidden md:inline text-snow";
    prof.append(av, nm);

    // چیپ XP
    const chip = el("a", { href: rootHref() + "progress.html", title: "امتیاز و سطح" });
    chip.className = "hidden sm:inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xp bg-xp/10 border border-xp/30";
    chip.innerHTML = "⚡ " + fa(xp) + " · سطح " + fa(lvl);

    // استریک
    if (st.streak > 0) {
      const fl = el("span");
      fl.className = "hidden sm:inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-orangey bg-orangey/10 border border-orangey/30";
      fl.innerHTML = "🔥 " + fa(st.streak);
      host.append(prof, chip, fl);
    } else {
      host.append(prof, chip);
    }

    // حالت
    const md = el("button", { type: "button", title: "یادگیری سریع: فقط نکته‌های کلیدی" });
    md.className = "rounded-xl px-3 py-1.5 border transition-colors " +
      (quick ? "border-mint/50 text-mint bg-mint/10" : "border-white/15 text-fog hover:text-snow");
    md.textContent = quick ? "⚡ سریع" : "📖 کامل";
    md.addEventListener("click", () => {
      const m = Store.setMode(Store.mode() === "quick" ? "normal" : "quick");
      document.documentElement.setAttribute("data-mode", m);
      paintUserBar();
      global.dispatchEvent(new CustomEvent("dars:mode", { detail: m }));
    });

    // وضعیت همگام‌سازی
    const dot = el("span", { title: "همگام با حساب همدل" });
    dot.className = "sync-dot w-2 h-2 rounded-full bg-mint";
    dot.setAttribute("data-sync", "");
    dot.setAttribute("data-state", "ok");

    // خروج
    const out = el("button", { type: "button", text: "خروج" });
    out.className = "hidden md:inline rounded-xl px-3 py-1.5 border border-white/10 text-fog hover:text-rosee hover:border-rosee/40 transition-colors";
    out.addEventListener("click", async () => {
      await C.logout();
      location.href = rootHref() + "login.html";
    });

    host.append(md, dot, out);
  }

  /** مسیر ریشهٔ سایت از عمق صفحهٔ جاری */
  function rootHref() {
    const depth = location.pathname.includes("/lessons/") ? "../../" : "";
    return depth;
  }
  function loginHref() {
    const depth = location.pathname.includes("/lessons/") ? "../../" : "";
    return depth + "login.html";
  }

  function boot() {
    paintStats();
    wireNav();
    const C = global.DarsCloud;
    if (C && C.ready) {
      const m = Store.mode();
      document.documentElement.setAttribute("data-mode", m);
      paintUserBar();
      global.addEventListener("dars:mode", () => paintStats());
      // بازیابی نشست و کشیدن پیشرفت از دیتابیس
      if (C.loggedIn()) {
        C.restore().then((data) => {
          if (data && data.progress) {
            Store.hydrate(data.progress, data.days);
            paintStats();
            paintUserBar();
            global.dispatchEvent(new CustomEvent("dars:ready"));
          } else {
            C.flush();
          }
        });
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  /* ----------------------------------------------------------
     صادرات
     ---------------------------------------------------------- */
  global.Dars = {
    fa, faWords, shuffle, rnd, el,
    Store, celebrate, buildPath, runQuiz, confetti, sfx,
    paintStats, boot, requireLogin, paintUserBar, rootHref
  };
})(window);
