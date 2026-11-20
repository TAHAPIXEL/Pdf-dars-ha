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
      d.lessons[subject + ":" + id] = Date.now();
      this._addXP(d, 10);
      this._touchStreak(d);
      this._write(d);
    },
    /** ثبت نتیجه آزمون */
    saveQuiz(subject, id, pct, xp) {
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
    const frag = document.createDocumentFragment();

    cfg.steps.forEach((s, i) => {
      const done = s.type === "quiz"
        ? !!Store.getQuiz(cfg.subject, s.id)
        : Store.isLessonDone(cfg.subject, s.id);

      const badge = el("div", { class: "badge" });
      if (done) {
        badge.classList.add("tick");
        badge.textContent = "✓";
      } else {
        badge.textContent = fa(i + 1);
      }

      const metaBits = [];
      (s.meta || []).forEach((m) => {
        metaBits.push(el("span", { html: m }));
      });

      const node = el(
        "a",
        { class: "node" + (done ? " done" : ""), href: s.href || "#" },
        badge,
        el("div", { class: "body" },
          s.kicker ? el("div", { class: "kicker", text: s.kicker }) : null,
          el("div", { class: "title", text: s.title }),
          metaBits.length ? el("div", { class: "meta" }, metaBits) : null
        ),
        el("div", { class: "go", html: "‹" })
      );
      frag.append(node);
    });

    host.append(frag);
    host.classList.add("stagger");
  }

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

      const actions = el("div", { class: "quiz-actions" },
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

    function finish() {
      trackFill.style.width = "100%";
      const pct = Math.round((correct / order.length) * 100);
      const pass = cfg.pass || 70;
      const earnedXP = Math.round(correct * 4) + (pct >= pass ? 18 : 0);

      Store.saveQuiz(cfg.subject, cfg.id, pct, earnedXP);

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
     راه‌اندازی
     ---------------------------------------------------------- */
  function boot() {
    paintStats();
    wireNav();
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
    Store, celebrate, buildPath, runQuiz,
    paintStats, boot
  };
})(window);
