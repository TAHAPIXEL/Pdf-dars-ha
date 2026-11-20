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
<meta name="theme-color" content="#05080f">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="../../assets/css/tw.css">
<link rel="stylesheet" href="../../assets/css/quest.css">
</head>
<body class="bg-ink text-snow antialiased bg-fabric" style="--accent:{accent};--accent-deep:{accentDeep};--accent-soft:{accentSoft};--accent-glow:{accentGlow}">
"""

def soft(hexc, a):
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"

TOPBAR = """<header class="fixed top-0 inset-x-0 z-50 glass-strong">
  <div class="mx-auto max-w-7xl px-4 h-16 flex items-center gap-2 sm:gap-3">
    <a href="{homeHref}" class="flex items-center gap-2 font-black text-sm sm:text-base shrink-0">
      <span class="w-9 h-9 rounded-xl grid place-items-center bg-gradient-to-br from-violet to-skyy text-ink">{icon}</span>
      <span>{backLabel}</span>
    </a>
    <div class="flex-1"></div>
    <div class="ub-wrap flex items-center gap-1.5 sm:gap-2 text-xs font-bold" data-userbar></div>
  </div>
</header>
<main class="pt-16">
"""

FOOT = """</main>
<footer class="border-t border-line/50 py-8 px-4 text-center text-fog text-xs mt-16">
  <p>{footText}</p>
  <a href="{homeHref}" class="text-violet font-bold mt-2 inline-block">{footLink}</a>
</footer>
"""

# ---------------- صفحه مسیر ----------------
PATH_TPL = BASE_HEAD + TOPBAR + """
  <div class="mx-auto max-w-5xl px-4 sm:px-6 py-8 sm:py-10">

    <!-- سرصفحهٔ کتاب -->
    <div class="glass rounded-3xl p-5 sm:p-8 mb-8 relative overflow-hidden rv rv-in">
      <div class="absolute rounded-full pointer-events-none"
           style="top:-80px;right:-80px;width:288px;height:288px;filter:blur(100px);background:{accentSoft}"></div>
      <div class="relative flex flex-wrap items-center gap-5">
        <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl grid place-items-center text-3xl sm:text-4xl shrink-0 -rotate-3"
             style="background:{accentSoft};border:1px solid {accentGlow}">{icon}</div>
        <div class="min-w-0 flex-1">
          <div class="text-[11px] font-black mb-1" style="color:{accent}">پایه نهم</div>
          <h1 class="text-2xl sm:text-3xl font-black mb-2">{name}</h1>
          <p class="text-fog text-xs sm:text-sm leading-7 max-w-xl">{lede}</p>
        </div>
      </div>

      <div class="relative mt-6 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
        <div class="rounded-2xl bg-white/5 border border-white/10 px-3 py-3 text-center">
          <div class="text-lg sm:text-xl font-black" style="color:{accent}">{nLessons}</div>
          <div class="text-[10px] sm:text-xs text-fog mt-0.5">درس</div>
        </div>
        <div class="rounded-2xl bg-white/5 border border-white/10 px-3 py-3 text-center">
          <div class="text-lg sm:text-xl font-black" style="color:{accent}">{nQuiz}</div>
          <div class="text-[10px] sm:text-xs text-fog mt-0.5">آزمون</div>
        </div>
        <div class="rounded-2xl bg-white/5 border border-white/10 px-3 py-3 text-center">
          <div class="text-lg sm:text-xl font-black" style="color:{accent}">{nQ}</div>
          <div class="text-[10px] sm:text-xs text-fog mt-0.5">پرسش</div>
        </div>
        <div class="rounded-2xl bg-white/5 border border-white/10 px-3 py-3 text-center">
          <div class="text-lg sm:text-xl font-black" style="color:{accent}">{nPages}</div>
          <div class="text-[10px] sm:text-xs text-fog mt-0.5">صفحهٔ کتاب</div>
        </div>
      </div>

      <div class="relative mt-5">
        <div class="flex items-center justify-between text-xs font-bold mb-2">
          <span class="text-fog">پیشرفت تو</span>
          <span class="font-black" id="pbv" style="color:{accent}">۰٪</span>
        </div>
        <div class="h-2.5 rounded-full bg-white/10 overflow-hidden">
          <i class="block h-full rounded-full transition-all duration-700" id="pbf"
             style="width:0;background:linear-gradient(90deg,{accent},#22d3ee)"></i>
        </div>
      </div>
    </div>

    <!-- مسیر یادگیری -->
    <div class="mb-6 text-center">
      <h2 class="text-xl sm:text-2xl font-black mb-2">مسیر یادگیری</h2>
      <p class="text-fog text-xs sm:text-sm">اول بخوان، بعد آزمون بده — آزمون اختیاری است</p>
    </div>

    <div id="path"></div>

    <!-- دسترسی سریع -->
    <div class="mt-14 grid sm:grid-cols-3 gap-3 sm:gap-4">
      <a href="all.html" class="tilt glass rounded-3xl p-5 group hover:border-white/25 transition-colors">
        <div class="text-3xl mb-3">📖</div>
        <h3 class="font-black mb-1.5">همهٔ درس‌نامه‌ها</h3>
        <p class="text-fog text-xs leading-6">یک صفحه برای خواندن همهٔ درس‌های این کتاب، پشت سر هم.</p>
        <div class="mt-3 text-xs font-bold" style="color:{accent}">بخوان ←</div>
      </a>
      <a href="quiz.html?all=1" class="tilt glass rounded-3xl p-5 group hover:border-white/25 transition-colors">
        <div class="text-3xl mb-3">🎯</div>
        <h3 class="font-black mb-1.5">آزمون جامع</h3>
        <p class="text-fog text-xs leading-6">پرسش‌های همهٔ فصل‌ها در یک آزمون تصادفی.</p>
        <div class="mt-3 text-xs font-bold" style="color:{accent}">شروع ←</div>
      </a>
      <a href="{homeHref}" class="tilt glass rounded-3xl p-5 group hover:border-white/25 transition-colors">
        <div class="text-3xl mb-3">🏠</div>
        <h3 class="font-black mb-1.5">درس دیگر</h3>
        <p class="text-fog text-xs leading-6">بازگشت به صفحهٔ اصلی و انتخاب یکی از ده کتاب.</p>
        <div class="mt-3 text-xs font-bold" style="color:{accent}">صفحهٔ اصلی ←</div>
      </a>
    </div>
  </div>
</main>
"""

ALL_TPL = BASE_HEAD + TOPBAR + """
<main>
  <div class="mx-auto max-w-3xl px-4 py-8">
    <div class="mb-7">
      <a href="index.html" class="text-xs font-bold text-fog hover:text-snow transition-colors">← مسیر درس</a>
      <h1 class="text-2xl font-black mt-3 mb-2">همهٔ درس‌نامه‌های {name}</h1>
      <p class="text-fog text-sm">مطالعهٔ پیوستهٔ همهٔ درس‌ها، پشت سر هم.</p>
    </div>
    <div id="allwrap" class="space-y-5"></div>
  </div>
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
    card.className = "glass rounded-3xl p-5 sm:p-7";
    const pts = (L.points || []).map((p, pi) =>
      '<div class="glass rounded-2xl px-3 py-2.5 mb-2 flex items-start gap-2.5">' +
        '<span class="w-6 h-6 rounded-md grid place-items-center shrink-0 text-[10px] font-black text-ink mt-0.5" ' +
          'style="background:linear-gradient(135deg,#a78bfa,#22d3ee)">' + fa(pi + 1) + '</span>' +
        '<span class="text-sm leading-7 flex-1">' + p + "</span></div>").join("");
    card.innerHTML =
      '<h2 class="text-lg sm:text-xl font-black mb-1.5">' + L.title + '</h2>' +
      '<div class="text-xs text-fog mb-4">درس ' + fa(L.n) + ' · صفحهٔ ' + L.page + '</div>' +
      (pts ? '<div class="mb-5"><h3 class="text-xs font-black text-fog mb-2.5">نکته‌های کلیدی</h3>' + pts + "</div>" : "") +
      '<div class="lesson-body fullbody">' + L.body + "</div>";
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
<div class="mx-auto max-w-3xl px-4 sm:px-6 py-6 sm:py-8">

    <!-- نوار وضعیت -->
    <div class="flex items-center gap-3 mb-4 flex-wrap">
      <a href="index.html" class="text-xs font-bold text-fog hover:text-snow transition-colors">← مسیر درس</a>
      <div class="flex-1"></div>
      <span class="glass rounded-full px-3 py-1.5 text-xs font-black" style="color:{accent}">درس <b id="ln">۱</b></span>
      <span class="text-[11px] text-fog" id="lp"></span>
    </div>

    <!-- تب‌ها -->
    <div class="glass rounded-2xl p-1 flex gap-1 mb-5" role="tablist">
      <button type="button" role="tab" id="tabQuick" aria-selected="true"
              class="flex-1 rounded-xl px-4 py-2.5 text-sm font-black transition-all bg-white/10 text-snow">⚡ یادگیری سریع</button>
      <button type="button" role="tab" id="tabFull" aria-selected="false"
              class="flex-1 rounded-xl px-4 py-2.5 text-sm font-black transition-all text-fog hover:text-snow">📖 متن کامل</button>
    </div>

    <!-- پنل سریع -->
    <div id="quickPane">
      <div class="glass rounded-2xl px-4 py-3 mb-4 flex items-center gap-2 flex-wrap">
        <span class="text-xs font-bold text-fog">فقط <b class="text-snow" id="pn">۶</b> نکتهٔ کلیدی — همه از خودِ کتاب</span>
        <div class="flex-1"></div>
        <a class="rounded-lg px-3 py-1.5 text-[11px] font-bold border border-white/15 text-fog hover:text-snow transition-colors"
           href="{pdfHref}" target="_blank" rel="noopener">PDF صفحه</a>
      </div>

      <div class="space-y-2.5" id="points"></div>

      <div class="mt-6 flex flex-wrap items-center gap-2">
        <button class="btn3d rounded-xl px-5 py-3 text-sm font-black text-ink cursor-pointer"
                style="background:linear-gradient(90deg,{accent},#22d3ee)" id="quickDone" type="button">
          نکته‌ها را یاد گرفتم ✓
        </button>
        <div class="flex-1"></div>
        <a class="rounded-xl px-4 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors"
           id="quickNext" href="quiz.html">برو به آزمون ←</a>
      </div>
    </div>

    <!-- پنل کامل -->
    <div id="fullPane" hidden>
      <article class="glass rounded-3xl p-5 sm:p-7 leading-9" id="sheet"></article>
    </div>

    <div class="mt-6 flex flex-wrap items-center gap-2" id="fullActions" hidden>
      <a class="rounded-xl px-4 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors" href="index.html">مسیر درس</a>
      <div class="flex-1"></div>
      <button class="btn3d rounded-xl px-5 py-3 text-sm font-black text-ink cursor-pointer"
              style="background:linear-gradient(90deg,{accent},#22d3ee)" id="doneBtn" type="button">خواندم ✓</button>
      <a class="btn3d rounded-xl px-5 py-3 text-sm font-black text-ink cursor-pointer hidden"
         style="background:linear-gradient(90deg,#34d399,#22d3ee)" id="nextBtn" href="quiz.html">برو به آزمون ←</a>
    </div>
  </div>
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
    '<h2 class="text-xl sm:text-2xl font-black mb-2">' + L.title + '</h2>' +
    '<div class="text-xs text-fog mb-6">{name} · پایه نهم · صفحهٔ ' + L.page + '</div>' +
    '<div class="lesson-body">' + L.body + '</div>';

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
  const ACTIVE = "flex-1 rounded-xl px-4 py-2.5 text-sm font-black transition-all bg-white/10 text-snow";
  const IDLE = "flex-1 rounded-xl px-4 py-2.5 text-sm font-black transition-all text-fog hover:text-snow";

  function show(mode) {{
    const q = mode !== "full";
    tabQuick.className = q ? ACTIVE : IDLE;
    tabFull.className = q ? IDLE : ACTIVE;
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
    doneBtn.style.background = "rgba(255,255,255,.08)";
    doneBtn.style.color = "#93a2c0";
    doneBtn.style.boxShadow = "none";
    nextBtn.style.display = "";
    quickDone.textContent = "یاد گرفتم ✓";
    quickDone.disabled = true;
    quickDone.style.background = "rgba(255,255,255,.08)";
    quickDone.style.color = "#93a2c0";
    quickDone.style.boxShadow = "none";
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
  <div class="mx-auto max-w-3xl px-4 sm:px-6 py-6 sm:py-8">
    <div class="flex items-center gap-3 mb-6 flex-wrap">
      <a href="index.html" class="text-xs font-bold text-fog hover:text-snow transition-colors">← مسیر درس</a>
      <div class="flex-1"></div>
      <span class="glass rounded-full px-3 py-1.5 text-[11px] font-bold text-fog">آزمون اختیاری</span>
    </div>
    <h2 id="qtitle" class="text-xl sm:text-2xl font-black mb-5">آزمون</h2>
    <div id="qz"></div>
  </div>
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
