#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سازندهٔ صفحات درس‌یار نهم.
برای هر درس سه صفحه می‌سازد:
  lessons/<key>/index.html        → مسیر یادگیری
  lessons/<key>/lesson.html?id=   → خواندن درس‌نامه
  lessons/<key>/quiz.html?id=     → آزمون

اجرا:  python3 tools/build.py
"""
import os, json, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "assets", "data")

SUBJECTS = [
    "quran", "payam", "farsi", "negar", "math",
    "science", "social", "arabic", "english", "english-workbook",
]

# ---------------- قالب پایه ----------------
BASE_HEAD = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0e1117">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="../../assets/css/app.css">
</head>
<body style="--accent:{accent};--accent-deep:{accentDeep};--accent-soft:{accentSoft};--accent-glow:{accentGlow}">
"""

def soft(hexc, a):
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"

TOPBAR = """<header class="topbar">
  <div class="wrap">
    <a class="back-link" href="{homeHref}" data-back="{homeHref}">
      <span class="arrow">›</span>
      <span>{backLabel}</span>
    </a>
    <div class="spacer"></div>
    <div class="stat-chip accent">
      <span class="ico">⚡</span>
      <span data-xp>۰</span>
      <span class="lbl">XP</span>
    </div>
    <div class="ub-wrap" data-userbar></div>
  </div>
</header>
"""

FOOT = """<footer class="site-foot">
  <div class="wrap">
    <span>{footText}</span>
    <a href="{homeHref}">{footLink}</a>
  </div>
</footer>
"""

# ---------------- صفحه مسیر ----------------
PATH_TPL = BASE_HEAD + TOPBAR + """
<main>
  <section class="hero wrap">
    <div class="hero-grid">
      <div>
        <span class="eyebrow">{icon} پایه نهم</span>
        <h1>{name}</h1>
        <p class="lede">{lede}</p>
        <div class="hero-stats">
          <div class="s"><b>{nLessons}</b><span>درس</span></div>
          <div class="s"><b>{nQuiz}</b><span>آزمون</span></div>
          <div class="s"><b>{nQ}</b><span>پرسش</span></div>
          <div class="s"><b>{nPages}</b><span>صفحهٔ کتاب</span></div>
        </div>
      </div>
      <div class="hero-emblem">{icon}</div>
    </div>

    <div class="progress-band">
      <div class="pb-head">
        <span class="t">پیشرفت تو در این درس</span>
        <span class="v" id="pbv">۰٪</span>
      </div>
      <div class="bar"><i id="pbf"></i></div>
    </div>
  </section>

  <section class="wrap section">
    <div class="sec-head">
      <h2>مسیر یادگیری</h2>
      <div class="rule"></div>
      <span class="hint">اول بخوان، بعد آزمون بده</span>
    </div>
    <div class="path" id="path"></div>
  </section>

  <section class="wrap section">
    <div class="sec-head">
      <h2>دسترسی سریع</h2>
      <div class="rule"></div>
    </div>
    <div class="cards">
      <a class="card" href="all.html">
        <div class="ic">📖</div>
        <h3>همهٔ درس‌نامه‌ها</h3>
        <p class="desc">یک صفحه برای خواندن همهٔ درس‌های این کتاب، پشت سر هم.</p>
        <div class="foot"><span>مطالعهٔ پیوسته</span><span class="pill">بخوان</span></div>
      </a>
      <a class="card" href="quiz.html?all=1">
        <div class="ic">🎯</div>
        <h3>آزمون جامع</h3>
        <p class="desc">پرسش‌های همهٔ فصل‌ها در یک آزمون تصادفی.</p>
        <div class="foot"><span>همهٔ فصل‌ها</span><span class="pill">آزمون</span></div>
      </a>
      <a class="card" href="{homeHref}">
        <div class="ic">🏠</div>
        <h3>بازگشت به صفحهٔ اصلی</h3>
        <p class="desc">انتخاب درس دیگر از میان ده کتاب پایه نهم.</p>
        <div class="foot"><span>صفحهٔ اصلی</span><span class="pill">همه</span></div>
      </a>
      <a class="card" href="{pdfHref}">
        <div class="ic">📕</div>
        <h3>کتاب درسی PDF</h3>
        <p class="desc">نسخهٔ کامل کتاب درسی برای مرور و چاپ.</p>
        <div class="foot"><span>فایل PDF</span><span class="pill">دانلود</span></div>
      </a>
    </div>
  </section>
</main>
""" + FOOT + """
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/app.js"></script>
<script src="../../assets/js/cloud.js"></script>
<script src="../../assets/data/{key}.js"></script>
<script>
(function () {{
  if (!Dars.requireLogin()) return;
  const {{ fa, buildPath, Store }} = Dars;
  const C = window.CONTENT["{key}"];

  const lessonIds = C.lessons.map(l => l.id);
  const quizIds = Object.keys(C.quizzes || {{}});

  // ساخت گام‌ها: هر درس → خواندن + آزمون
  const steps = [];
  C.lessons.forEach((l) => {{
    steps.push({{
      id: l.id, type: "lesson",
      kicker: "درس " + fa(l.n),
      title: l.title,
      meta: ["صفحهٔ " + l.page, (C.quizzes[l.id] || []).length ? fa((C.quizzes[l.id] || []).length) + " پرسش" : ""],
      href: "lesson.html?id=" + l.id
    }});
    if (C.quizzes[l.id] && C.quizzes[l.id].length) {{
      steps.push({{
        id: l.id, type: "quiz",
        kicker: "آزمون",
        title: "آزمون " + l.title,
        meta: [fa(C.quizzes[l.id].length) + " پرسش", "بدون محدودیت"],
        href: "quiz.html?id=" + l.id
      }});
    }}
  }});

  buildPath(document.getElementById("path"), {{ subject: "{key}", steps: steps }});

  // نوار پیشرفت
  const pct = Store.subjectProgress("{key}", lessonIds, quizIds);
  document.getElementById("pbv").textContent = fa(pct) + "٪";
  requestAnimationFrame(() => {{
    document.getElementById("pbf").style.width = pct + "%";
  }});
}})();
</script>
</body>
</html>
"""

# ---------------- صفحه همهٔ درس‌نامه‌ها ----------------
ALL_TPL = BASE_HEAD + TOPBAR + """
<main>
  <section class="wrap section" style="padding-top:26px">
    <div class="sec-head">
      <h1 style="font-size:1.4rem">همهٔ درس‌نامه‌های {name}</h1>
      <div class="rule"></div>
      <span class="hint">مطالعهٔ پیوستهٔ همهٔ درس‌ها</span>
    </div>
    <div id="allwrap"></div>
  </section>
</main>
""" + FOOT + """
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/app.js"></script>
<script src="../../assets/js/cloud.js"></script>
<script src="../../assets/data/{key}.js"></script>
<script>
(function () {{
  if (!Dars.requireLogin()) return;
  const {{ fa }} = Dars;
  const C = window.CONTENT["{key}"];
  const host = document.getElementById("allwrap");
  const mode = Dars.Store.mode();

  C.lessons.forEach((L) => {{
    const card = document.createElement("article");
    card.className = "sheet rise";
    card.style.marginBottom = "22px";
    const pts = (L.points || []).map((p) =>
      '<div class="point"><span class="n">•</span><span class="t">' + p + "</span></div>").join("");
    card.innerHTML =
      '<h2>' + L.title + '</h2>' +
      '<div style="font-family:var(--f-ui);font-size:.82rem;color:var(--text-dim);margin-bottom:16px">' +
        'درس ' + fa(L.n) + ' · صفحهٔ ' + L.page +
      '</div>' +
      (pts ? '<div class="points"><h3>نکته‌های کلیدی</h3>' + pts + "</div>" : "") +
      '<div class="fullbody">' + L.body + "</div>";
    host.append(card);
  }});

  if (mode === "quick") {{
    host.querySelectorAll(".fullbody").forEach((e) => (e.hidden = true));
  }}
}})();
</script>
</body>
</html>
"""

# ---------------- صفحه درس ----------------
LESSON_TPL = BASE_HEAD + TOPBAR + """
<main>
  <article class="wrap section" style="padding-top:26px">
    <div class="quiz" style="max-width:860px">
      <div class="quiz-top">
        <span class="quiz-count">درس <b id="ln">۱</b></span>
        <div class="spacer" style="flex:1"></div>
        <span class="hint" style="font-family:var(--f-ui);font-size:.8rem;color:var(--text-dim)" id="lp"></span>
      </div>

      <div class="learn-tabs" role="tablist" aria-label="حالت یادگیری">
        <button type="button" role="tab" id="tabQuick" aria-selected="true">⚡ یادگیری سریع</button>
        <button type="button" role="tab" id="tabFull" aria-selected="false">📖 متن کامل</button>
      </div>

      <div id="quickPane">
        <div class="quick-bar">
          <span class="qb-t">فقط <b id="pn">۶</b> نکتهٔ کلیدی — همه از خودِ کتاب</span>
          <div class="spacer" style="flex:1"></div>
          <a class="btn btn-quiet" href="{pdfHref}" target="_blank" rel="noopener">PDF صفحه</a>
        </div>
        <div class="points rise" id="points"></div>
        <div class="quiz-actions" style="margin-top:6px">
          <button class="btn btn-primary" id="quickDone" type="button">نکته‌ها را یاد گرفتم ✓</button>
          <div class="spacer"></div>
          <a class="btn btn-ghost" id="quickNext" href="quiz.html">برو به آزمون ‹</a>
        </div>
      </div>

      <div id="fullPane" hidden>
        <div class="sheet rise" id="sheet"></div>
      </div>

      <div class="quiz-actions" style="margin-top:18px" id="fullActions" hidden>
        <a class="btn btn-ghost" href="index.html">مسیر درس</a>
        <a class="btn btn-quiet" href="{pdfHref}" target="_blank" rel="noopener">PDF کتاب</a>
        <div class="spacer"></div>
        <button class="btn btn-primary" id="doneBtn" type="button">خواندم ✓</button>
        <a class="btn btn-primary" id="nextBtn" href="quiz.html" style="display:none">برو به آزمون ‹</a>
      </div>
    </div>
  </article>
</main>
""" + FOOT + """
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/app.js"></script>
<script src="../../assets/js/cloud.js"></script>
<script src="../../assets/data/{key}.js"></script>
<script>
(function () {{
  if (!Dars.requireLogin()) return;
  const {{ fa, Store, celebrate }} = Dars;
  const C = window.CONTENT["{key}"];
  const KEY = "{key}";

  const params = new URLSearchParams(location.search);
  const id = params.get("id") || C.lessons[0].id;
  const idx = C.lessons.findIndex(l => l.id === id);
  const L = C.lessons[idx >= 0 ? idx : 0];

  document.title = L.title + " — {name}";
  document.getElementById("ln").textContent = fa(L.n);
  document.getElementById("lp").textContent = "صفحهٔ " + L.page;

  /* ---------- نکته‌های کلیدی ---------- */
  const pts = L.points || [];
  document.getElementById("pn").textContent = fa(pts.length);
  const pointsBox = document.getElementById("points");
  const words = ["یکم", "دوم", "سوم", "چهارم", "پنجم", "ششم", "هفتم", "هشتم"];
  pointsBox.append(Dars.el("h3", {{ text: "نکته‌های کلیدیِ «" + L.title + "»" }}));
  if (!pts.length) {{
    pointsBox.append(Dars.el("div", {{ class: "point" }},
      Dars.el("span", {{ class: "t", text: "برای این درس نکتهٔ جداگانه‌ای ثبت نشده؛ متن کامل را ببین." }})));
  }}
  pts.forEach((p, i) => {{
    pointsBox.append(Dars.el("div", {{ class: "point" }},
      Dars.el("span", {{ class: "n", text: fa(i + 1) }}),
      Dars.el("span", {{ class: "t", text: p }})
    ));
  }});

  /* ---------- متن کامل ---------- */
  const sheet = document.getElementById("sheet");
  sheet.innerHTML =
    '<h2>' + L.title + '</h2>' +
    '<div style="font-family:var(--f-ui);font-size:.84rem;color:var(--text-dim);margin-bottom:22px">' +
      '{name} · پایه نهم · صفحهٔ ' + L.page +
    '</div>' + L.body;

  // ناوبری درس قبل/بعد
  const prev = C.lessons[idx - 1];
  const next = C.lessons[idx + 1];
  const nav = document.createElement("div");
  nav.style.cssText = "display:flex;gap:10px;margin-top:18px;flex-wrap:wrap";
  if (prev) {{
    const a = document.createElement("a");
    a.className = "btn btn-ghost";
    a.href = "lesson.html?id=" + prev.id;
    a.textContent = "› " + prev.title;
    nav.append(a);
  }}
  if (next) {{
    const a = document.createElement("a");
    a.className = "btn btn-ghost";
    a.style.marginInlineStart = "auto";
    a.href = "lesson.html?id=" + next.id;
    a.textContent = next.title + " ‹";
    nav.append(a);
  }}
  sheet.after(nav);

  /* ---------- تعویض تب سریع / کامل ---------- */
  const quickPane = document.getElementById("quickPane");
  const fullPane = document.getElementById("fullPane");
  const fullActions = document.getElementById("fullActions");
  const tabQuick = document.getElementById("tabQuick");
  const tabFull = document.getElementById("tabFull");

  function show(mode) {{
    const q = mode !== "full";
    tabQuick.setAttribute("aria-selected", q ? "true" : "false");
    tabFull.setAttribute("aria-selected", q ? "false" : "true");
    quickPane.hidden = !q;
    fullPane.hidden = q;
    fullActions.hidden = q;
    Store.setMode(q ? "quick" : "normal");
  }}
  tabQuick.addEventListener("click", () => show("quick"));
  tabFull.addEventListener("click", () => show("full"));
  if (Store.mode() === "quick") show("quick"); else show("full");

  /* ---------- ثبت یادگیری ---------- */
  const doneBtn = document.getElementById("doneBtn");
  const nextBtn = document.getElementById("nextBtn");
  const quickDone = document.getElementById("quickDone");
  const quickNext = document.getElementById("quickNext");

  const hasQuiz = !!(C.quizzes[L.id] && C.quizzes[L.id].length);
  if (hasQuiz) {{
    nextBtn.href = "quiz.html?id=" + L.id;
    quickNext.href = "quiz.html?id=" + L.id;
  }} else if (next) {{
    nextBtn.href = "lesson.html?id=" + next.id;
    nextBtn.textContent = "درس بعدی ‹";
    quickNext.href = "lesson.html?id=" + next.id;
    quickNext.textContent = "درس بعدی ‹";
  }} else {{
    nextBtn.href = "index.html";
    nextBtn.textContent = "پایان مسیر ‹";
    quickNext.href = "index.html";
    quickNext.textContent = "پایان مسیر ‹";
  }}

  function paintDone() {{
    const done = Store.isLessonDone(KEY, L.id);
    if (!done) return;
    doneBtn.textContent = "خوانده شده ✓";
    doneBtn.classList.remove("btn-primary");
    doneBtn.classList.add("btn-ghost");
    nextBtn.style.display = "";
    quickDone.textContent = "یاد گرفتم ✓";
    quickDone.disabled = true;
    quickDone.classList.remove("btn-primary");
    quickDone.classList.add("btn-ghost");
  }}
  paintDone();

  doneBtn.addEventListener("click", () => {{
    Store.markLesson(KEY, L.id);
    Dars.paintStats();
    paintDone();
    celebrate(18);
  }});

  quickDone.addEventListener("click", () => {{
    Store.markQuickRead(KEY, L.id);
    Dars.paintStats();
    paintDone();
    celebrate(14);
  }});
}})();
</script>
</body>
</html>
"""

# ---------------- صفحه آزمون ----------------
QUIZ_TPL = BASE_HEAD + TOPBAR + """
<main>
  <section class="wrap section" style="padding-top:26px">
    <div class="quiz">
      <div class="sec-head" style="margin-bottom:18px">
        <h2 id="qtitle" style="font-size:1.2rem">آزمون</h2>
        <div class="rule"></div>
      </div>
      <div id="qz"></div>
    </div>
  </section>
</main>
""" + FOOT + """
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/app.js"></script>
<script src="../../assets/js/cloud.js"></script>
<script src="../../assets/data/{key}.js"></script>
<script>
(function () {{
  if (!Dars.requireLogin()) return;
  const {{ runQuiz }} = Dars;
  const C = window.CONTENT["{key}"];
  const KEY = "{key}";
  const params = new URLSearchParams(location.search);

  let questions = [];
  let title = "آزمون";
  let qid = null;

  if (params.get("all") === "1") {{
    // آزمون جامع: از همهٔ فصل‌ها سهم می‌گیریم
    const all = [];
    Object.keys(C.quizzes).forEach((k) => all.push(...C.quizzes[k]));
    questions = Dars.shuffle(all).slice(0, 25);
    title = "آزمون جامع {name}";
    qid = "all";
  }} else {{
    const id = params.get("id") || C.lessons[0].id;
    qid = id;
    questions = C.quizzes[id] || [];
    const L = C.lessons.find(l => l.id === id);
    title = "آزمون " + (L ? L.title : "");
  }}

  document.title = title + " — {name}";
  document.getElementById("qtitle").textContent = title;

  // آزمون اجباری نیست: مقصد دکمهٔ «رد کردن»
  const lessonEntry = C.lessons.find(l => l.id === qid);
  let nextHref = "index.html";
  if (lessonEntry) {{
    const i = C.lessons.indexOf(lessonEntry);
    const nx = C.lessons[i + 1];
    nextHref = nx ? "lesson.html?id=" + nx.id : "index.html";
  }}

  runQuiz({{
    host: document.getElementById("qz"),
    subject: KEY,
    id: qid,
    questions: questions,
    pass: 70,
    backHref: "index.html",
    nextHref: nextHref,
    mode: Dars.Store.mode()
  }});
}})();
</script>
</body>
</html>
"""

# ---------------- اجرا ----------------
def main():
    # خواندن اطلاعات درس‌ها از فایل داده (رگیولار اکسپرشن ساده)
    meta = {}
    for key in SUBJECTS:
        p = os.path.join(DATA, key + ".js")
        if not os.path.exists(p):
            print(f"!! missing data: {key}")
            continue
        src = open(p, encoding="utf-8").read()
        def grab(field):
            m = re.search(r'\b' + field + r'\s*:\s*"([^"]*)"', src)
            return m.group(1) if m else ""
        meta[key] = {
            "name": grab("name").replace('\\"', '"'),
            "full": grab("full"),
            "icon": grab("icon"),
            "accent": grab("accent"),
            "accentDeep": grab("accentDeep"),
            "lede": grab("lede"),
        }

    PDFS = {
        "quran": "01-قرآن-نهم.pdf",
        "payam": "02-پیام‌های-آسمانی-نهم.pdf",
        "farsi": "03-فارسی-نهم.pdf",
        "negar": "04-نگارش-نهم.pdf",
        "math": "05-ریاضی-نهم.pdf",
        "science": "06-علوم-تجربی-نهم.pdf",
        "social": "07-مطالعات-اجتماعی-نهم.pdf",
        "arabic": "08-عربی-نهم.pdf",
        "english": "09-زبان-انگلیسی-نهم.pdf",
        "english-workbook": "10-کتاب-کار-زبان-انگلیسی-نهم.pdf",
    }

    total_lessons = 0
    total_quiz = 0
    total_q = 0

    for key in SUBJECTS:
        m = meta.get(key)
        if not m:
            continue
        d = os.path.join(ROOT, "lessons", key)
        os.makedirs(d, exist_ok=True)

        src = open(os.path.join(DATA, key + ".js"), encoding="utf-8").read()
        n_lessons = src.count('{ id: "')
        # شمارش پرسش‌ها: هر { q: " در quizzes
        n_q = src.count('{ q: "')
        n_quiz = n_lessons  # هم‌تعداد با درس‌ها

        total_lessons += n_lessons
        total_quiz += n_quiz
        total_q += n_q

        accent = m["accent"] or "#6c8cff"
        accentDeep = m["accentDeep"] or accent

        common = dict(
            key=key,
            name=m["name"],
            icon=m["icon"] or "📘",
            lede=m["lede"],
            accent=accent,
            accentDeep=accentDeep,
            accentSoft=soft(accent, 0.14),
            accentGlow=soft(accent, 0.35),
            homeHref="../../index.html",
            nLessons=str(n_lessons),
            nQuiz=str(n_quiz),
            nQ=str(n_q),
            nPages="۰",
            pdfHref="../../پایه-نهم/" + PDFS[key],
        )

        # --- صفحه مسیر ---
        path_html = PATH_TPL.format(
            title=f"{m['name']} — درسیار نهم",
            desc=f"{m['full']} — درس‌نامه، آزمون و پیشرفت",
            backLabel="صفحهٔ اصلی",
            footText=f"{m['name']} · {m['full']}",
            footLink="صفحهٔ اصلی",
            **common,
        )
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(path_html)

        # --- صفحه درس ---
        lesson_html = LESSON_TPL.format(
            title=f"درس — {m['name']}",
            desc=m["full"],
            backLabel="مسیر درس",
            footText=f"{m['name']} · {m['full']}",
            footLink="صفحهٔ اصلی",
            **common,
        )
        open(os.path.join(d, "lesson.html"), "w", encoding="utf-8").write(lesson_html)

        # --- صفحه همهٔ درس‌نامه‌ها ---
        unit = "فصل" if key in ("math", "science", "social", "payam", "farsi") else "درس"
        all_html = ALL_TPL.format(
            title=f"همهٔ درس‌نامه‌ها — {m['name']}",
            desc=f"مطالعهٔ پیوستهٔ همهٔ درس‌های {m['full']}",
            backLabel="مسیر درس",
            footText=f"{m['name']} · {m['full']}",
            footLink="صفحهٔ اصلی",
            unit=unit,
            **common,
        )
        open(os.path.join(d, "all.html"), "w", encoding="utf-8").write(all_html)

        # --- صفحه آزمون ---
        quiz_html = QUIZ_TPL.format(
            title=f"آزمون — {m['name']}",
            desc=f"آزمون {m['full']}",
            backLabel="مسیر درس",
            footText=f"{m['name']} · {m['full']}",
            footLink="صفحهٔ اصلی",
            **common,
        )
        open(os.path.join(d, "quiz.html"), "w", encoding="utf-8").write(quiz_html)

        print(f"  ✓ {key:18s} lessons={n_lessons:2d}  questions={n_q:3d}")

    print(f"\nمجموع: {total_lessons} درس‌نامه، {total_quiz} آزمون، {total_q} پرسش")


if __name__ == "__main__":
    main()
