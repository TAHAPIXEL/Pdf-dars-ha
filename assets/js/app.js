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
    host.classList.add("path-spine");

    // جابه‌جایی افقی گره‌ها؛ همان ریتم مارپیچی طرح مرجع
    const OFFSETS = [0, 54, 0, -54];
    const steps = cfg.steps || [];
    let nextIdx = -1;

    steps.forEach((s, i) => {
      const done = s.type === "quiz"
        ? !!Store.getQuiz(cfg.subject, s.id)
        : Store.isLessonDone(cfg.subject, s.id);
      if (!done && nextIdx === -1) nextIdx = i;
    });
    if (nextIdx === -1 && steps.length) nextIdx = steps.length - 1;

    const frag = document.createDocumentFragment();

    steps.forEach((s, i) => {
      const done = s.type === "quiz"
        ? !!Store.getQuiz(cfg.subject, s.id)
        : Store.isLessonDone(cfg.subject, s.id);
      const isNext = i === nextIdx && !done;

      const btn = el("span", {
        class: "node-btn" + (done ? " done" : isNext ? " next" : " locked"),
        "aria-hidden": "true",
      });
      btn.textContent = done ? "✓" : isNext ? "▶" : fa(i + 1);

      const metaBits = [];
      (s.meta || []).forEach((m) => metaBits.push(el("span", { html: m })));

      const inner = el("div", {},
        el("div", { class: "node-label", text: s.title }),
        s.kicker ? el("div", { class: "node-cap", text: s.kicker }) : null,
        metaBits.length ? el("div", { class: "node-cap" }, metaBits) : null
      );

      const node = el(
        "a",
        {
          class: "node-wrap",
          href: s.href || "#",
          style: "transform: translateX(" + OFFSETS[i % 4] + "px)",
          "data-step": i,
        },
        btn,
        inner
      );
      frag.append(node);
    });

    host.append(frag);
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
      host.innerHTML = '<div class="empty"><div class="e-ic">📭</div><p>سؤالی برای این آزمون ثبت نشده است.</p></div>';
      return;
    }

    const order = shuffle(Q);
    let i = 0, correct = 0, answered = false;
    const startXP = Store.xp();

    host.innerHTML = "";

    const trackFill = el("i");
    const countEl = el("div", { class: "quiz-count" });
    const top = el("div", { class: "quiz-top" },
      countEl,
      el("div", { class: "quiz-track" }, trackFill)
    );

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

      const optWrap = el("div", { class: "opts" });
      const letters = ["الف", "ب", "ج", "د", "هـ", "و"];

      const fb = el("div");

      const nextBtn = el("button", {
        class: "btn btn-primary",
        type: "button",
        text: i === order.length - 1 ? "دیدن نتیجه" : "سؤال بعدی",
        onclick: () => {
          if (i < order.length - 1) { i++; render(); }
          else finish();
        }
      });
      nextBtn.style.display = "none";

      const skipBtn = el("button", {
        class: "btn btn-quiet", type: "button", text: "رد کردن آزمون",
        title: "آزمون اجباری نیست؛ می‌توانی بعداً بدهی",
        onclick: () => skip()
      });

      const actions = el("div", { class: "quiz-actions" },
        skipBtn,
        el("div", { class: "spacer" }),
        nextBtn
      );

      q.opts.forEach((o, oi) => {
        const mark = el("div", { class: "mark", text: letters[oi] || fa(oi + 1) });
        const btn = el("button", { class: "opt", type: "button" },
          mark,
          el("div", { class: "txt", text: o })
        );

        btn.addEventListener("click", () => {
          if (answered) return;
          answered = true;

          const good = oi === q.a;
          if (good) correct++;

          // قفل و رنگ‌آمیزی همه گزینه‌ها
          optWrap.querySelectorAll(".opt").forEach((b, bi) => {
            b.classList.add("locked");
            if (bi === q.a) b.classList.add("correct");
            else if (bi === oi) b.classList.add("wrong");
            else b.classList.add("faded");
          });

          fb.innerHTML = "";
          const box = el("div", { class: "feedback " + (good ? "good" : "bad") },
            el("div", { class: "fh" },
              el("span", { text: good ? "✓" : "✕" }),
              el("span", { text: good ? "درست بود!" : "پاسخ درست: " + (q.opts[q.a]) })
            ),
            q.why ? el("div", { class: "expl", text: q.why }) : null
          );
          fb.append(box);

          nextBtn.style.display = "";
          nextBtn.focus({ preventScroll: true });
        });

        optWrap.append(btn);
      });

      const card = el("div", { class: "qcard rise" },
        q.tag ? el("span", { class: "qtag", text: q.tag }) : null,
        el("div", { class: "qtext", text: q.q }),
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
      const box = el("div", { class: "result rise" },
        el("div", { class: "rbadge", text: "⏭" }),
        el("h2", { text: "آزمون را رد کردی" }),
        el("p", { class: "sub", text: "هیچ اشکالی ندارد. درس را خوانده‌ای و هر وقت خواستی می‌توانی آزمون بدهی — نمره‌ای ثبت نشد." }),
        el("div", { class: "result-actions" },
          el("a", { class: "btn btn-primary", href: nextHref, text: "درس بعدی ‹" }),
          el("a", { class: "btn btn-ghost", href: backHref, text: "بازگشت به مسیر" })
        )
      );
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

      const result = el("div", { class: "result rise" },
        el("div", { class: "rbadge", text: pct >= 90 ? "🏆" : pct >= pass ? "🎯" : "📚" }),
        el("h2", { text: pct >= 90 ? "بی‌نقص!" : pct >= pass ? "عالی بود!" : "ادامه بده!" }),
        el("p", { class: "sub", text: pct >= 90
          ? "همهٔ سؤال‌ها را درست پاسخ دادی. تسلطت کامل است."
          : pct >= pass
          ? "آزمون را با موفقیت گذراندی. یک قدم دیگر جلو رفتی."
          : "این بار کافی نبود، اما هیچ اشکالی ندارد. درس را یک بار دیگر بخوان و برگرد." }),
        el("div", { class: "score-ring" },
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
          el("div", { class: "val" },
            el("b", { text: fa(pct) + "٪" }),
            el("small", { text: "پاسخ درست" })
          )
        ),
        el("div", { class: "result-grid" },
          el("div", { class: "rg ok" }, el("b", { text: fa(correct) }), el("span", { text: "درست" })),
          el("div", { class: "rg bad" }, el("b", { text: fa(order.length - correct) }), el("span", { text: "نادرست" })),
          el("div", { class: "rg" }, el("b", { text: "+" + fa(earnedXP) }), el("span", { text: "XP" }))
        ),
        el("div", { class: "result-actions" },
          el("button", {
            class: "btn btn-primary", type: "button", text: "تلاش دوباره",
            onclick: () => { i = 0; correct = 0; render(); }
          }),
          el("a", { class: "btn btn-ghost", href: cfg.backHref || "index.html", text: "بازگشت به مسیر" })
        )
      );
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
      host.append(el("a", { class: "ub-login", href: loginHref(), text: "ورود" }));
      return;
    }
    const initial = (u.firstName || u.lastName || "د").trim().slice(0, 1);
    const quick = Store.mode() === "quick";

    // چیپ XP و لِوِل، مثل طرح مرجع
    const st = Store.stats();
    const xp = st.xp || 0;
    const lvl = Math.floor(xp / 250) + 1;

    host.append(
      el("a", {
        class: "ub-user",
        href: rootHref() + "progress.html",
        title: "کارنامه و پیشرفت من",
      },
        el("span", { class: "ub-av", text: initial }),
        el("span", { class: "ub-nm", text: (u.firstName || "دانش‌آموز") })
      ),
      el("a", {
        class: "lvl-chip",
        href: rootHref() + "progress.html",
        title: "امتیاز و سطح تو",
      },
        el("span", { text: "⚡" }),
        el("span", { text: fa(xp) }),
        el("span", { text: "· سطح " + fa(lvl) })
      ),
      st.streak > 0 ? el("span", { class: "lvl-chip", title: "روزهای پشت‌سرهم", style: "background:rgba(251,146,60,.12);border-color:rgba(251,146,60,.3);color:#fdba74" },
        el("span", { text: "🔥" }), el("span", { text: fa(st.streak) })) : null,
      el("button", {
        class: "ub-mode" + (quick ? " on" : ""),
        type: "button",
        title: "یادگیری سریع: فقط نکته‌های کلیدی",
        onclick: () => {
          const m = Store.setMode(Store.mode() === "quick" ? "normal" : "quick");
          document.documentElement.setAttribute("data-mode", m);
          paintUserBar();
          global.dispatchEvent(new CustomEvent("dars:mode", { detail: m }));
        }
      }, el("span", { class: "ub-dot" }), el("span", { text: quick ? "سریع" : "کامل" })),
      el("span", { class: "sync-dot", "data-sync": "", "data-state": "ok", title: "همگام با حساب همدل" }),
      el("button", {
        class: "ub-out", type: "button", text: "خروج",
        onclick: async () => { await C.logout(); location.href = rootHref() + "login.html"; }
      })
    );
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
