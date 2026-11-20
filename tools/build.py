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

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(v):
    """عدد را به رقم فارسی تبدیل می‌کند."""
    return str(v).translate(FA_DIGITS)


def _load_structure():
    """ساختار فصل‌ها را از assets/data/_structure.js می‌خواند."""
    import subprocess
    js = (
        'global.window={};require("./assets/data/_structure.js");'
        'console.log(JSON.stringify(window.DARS_STRUCTURE));'
    )
    try:
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=ROOT)
        return json.loads(out.stdout or "{}")
    except Exception:
        return {}


STRUCTURE = _load_structure()


def _fmt(tpl, values):
    """جایگزینی امن {key} — فقط کلیدهای شناخته‌شده؛ بقیهٔ آکولادها (JS) دست‌نخورده."""
    out = tpl
    for k in sorted(values, key=len, reverse=True):
        out = out.replace("{" + k + "}", str(values[k]))
    return out


_orig_fmt = str.format


def _load_content():
    """محتوای همهٔ کتاب‌ها را برای شمارش مبحث‌ها می‌خواند."""
    import subprocess
    js = (
        "global.window={};"
        + "".join('require("./assets/data/%s.js");' % k for k in SUBJECTS)
        + "console.log(JSON.stringify(window.CONTENT));"
    )
    try:
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=ROOT)
        return json.loads(out.stdout or "{}")
    except Exception:
        return {}


DATA_CONTENT = _load_content()

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
  <div class="mx-auto max-w-7xl px-3 sm:px-4 h-16 flex items-center gap-2">

    <a href="{homeHref}" class="flex items-center gap-2 font-black text-sm sm:text-base shrink-0 min-w-0">
      <span class="w-9 h-9 rounded-xl grid place-items-center bg-gradient-to-br from-violet to-skyy text-ink shrink-0">{icon}</span>
      <span class="truncate max-w-[7.5rem] sm:max-w-none">{backLabel}</span>
    </a>

    <!-- ناوبری دسکتاپ -->
    <nav class="hidden md:flex items-center gap-4 lg:gap-5 text-sm font-bold text-fog ms-3">
      <a href="{homeHref}" class="navlink">خانه</a>
      <a href="index.html" class="navlink">فصل‌ها</a>
      <a href="all.html" class="navlink">همهٔ درس‌نامه‌ها</a>
      <a href="{rootHref}progress.html" class="navlink">کارنامه</a>
      <a href="{rootHref}leaderboard.html" class="navlink">قهرمانان</a>
    </nav>

    <div class="flex-1 min-w-0"></div>

    <div class="ub-wrap flex items-center gap-1 sm:gap-2 text-xs font-bold shrink-0" data-userbar></div>

    <!-- دکمهٔ منو: فقط موبایل -->
    <button type="button" id="navToggle" aria-label="منو" aria-expanded="false" aria-controls="navDrawer"
            class="md:hidden w-10 h-10 shrink-0 rounded-xl grid place-items-center border border-white/15 text-snow active:scale-95 transition">
      <svg id="navIconOpen" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
        <path d="M4 7h16M4 12h16M4 17h16"/>
      </svg>
      <svg id="navIconClose" class="w-5 h-5 hidden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
        <path d="M6 6l12 12M18 6L6 18"/>
      </svg>
    </button>
  </div>

  <!-- کشوی موبایل -->
  <div id="navDrawer" class="md:hidden hidden border-t border-white/10 bg-abyss/95 backdrop-blur-xl">
    <nav class="px-3 py-3 grid gap-1 text-sm font-bold">
      <a href="{homeHref}" class="nav-row">🏠 <span>صفحهٔ اصلی</span></a>
      <a href="index.html" class="nav-row">🗂 <span>فصل‌های {backLabel}</span></a>
      <a href="all.html" class="nav-row">📖 <span>همهٔ درس‌نامه‌ها</span></a>
      <a href="quiz.html?all=1" class="nav-row">🎯 <span>آزمون جامع</span></a>
      <div class="my-1.5 h-px bg-white/10"></div>
      <a href="{rootHref}progress.html" class="nav-row">📊 <span>کارنامهٔ من</span></a>
      <a href="{rootHref}leaderboard.html" class="nav-row">🏆 <span>تابلوی قهرمانان</span></a>
      <a href="{rootHref}resources.html" class="nav-row">📕 <span>کتاب‌های درسی</span></a>
    </nav>
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
  <div class="mx-auto max-w-4xl px-4 sm:px-6 py-7 sm:py-10">

    <!-- سرصفحهٔ کتاب -->
    <div class="glass rounded-3xl p-5 sm:p-7 mb-6 relative overflow-hidden">
      <div class="absolute rounded-full pointer-events-none"
           style="top:-80px;right:-80px;width:260px;height:260px;filter:blur(100px);background:{accentSoft}"></div>
      <div class="relative flex items-start gap-4">
        <div class="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl grid place-items-center text-2xl sm:text-3xl shrink-0 -rotate-3"
             style="background:{accentSoft};border:1px solid {accentGlow}">{icon}</div>
        <div class="min-w-0 flex-1">
          <div class="text-[11px] font-black mb-0.5" style="color:{accent}">پایه نهم</div>
          <h1 class="text-xl sm:text-2xl font-black leading-snug mb-1.5">{name}</h1>
          <p class="text-fog text-xs sm:text-sm leading-6">{lede}</p>
        </div>
      </div>

      <div class="relative mt-5 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
        <div class="rounded-2xl bg-white/5 border border-white/10 px-2 py-2.5 text-center">
          <div class="text-base sm:text-lg font-black" style="color:{accent}">{nChapters}</div>
          <div class="text-[10px] text-fog mt-0.5">فصل</div>
        </div>
        <div class="rounded-2xl bg-white/5 border border-white/10 px-2 py-2.5 text-center">
          <div class="text-base sm:text-lg font-black" style="color:{accent}">{nLessons}</div>
          <div class="text-[10px] text-fog mt-0.5">درس</div>
        </div>
        <div class="rounded-2xl bg-white/5 border border-white/10 px-2 py-2.5 text-center">
          <div class="text-base sm:text-lg font-black" style="color:{accent}">{nSections}</div>
          <div class="text-[10px] text-fog mt-0.5">مبحث</div>
        </div>
        <div class="rounded-2xl bg-white/5 border border-white/10 px-2 py-2.5 text-center">
          <div class="text-base sm:text-lg font-black" style="color:{accent}">{nQ}</div>
          <div class="text-[10px] text-fog mt-0.5">پرسش</div>
        </div>
      </div>

      <div class="relative mt-4">
        <div class="flex items-center justify-between text-[11px] font-bold mb-1.5">
          <span class="text-fog">پیشرفت کل کتاب</span>
          <span class="font-black" id="pbv" style="color:{accent}">۰٪</span>
        </div>
        <div class="h-2 rounded-full bg-white/10 overflow-hidden">
          <i class="block h-full rounded-full transition-all duration-700" id="pbf"
             style="width:0;background:linear-gradient(90deg,{accent},#22d3ee)"></i>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg sm:text-xl font-black">فصل‌ها</h2>
      <a href="all.html" class="text-[11px] font-bold px-3 py-1.5 rounded-lg border border-white/15 text-fog hover:text-snow transition-colors">📖 همهٔ درس‌نامه‌ها</a>
    </div>

    <div id="chapters" class="space-y-3"></div>
  </div>
</main>
""" + FOOT + """
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/app.js"></script>
<script src="../../assets/js/cloud.js"></script>
<script src="../../assets/data/_structure.js"></script>
<script src="../../assets/data/{key}.js"></script>
<script>
(function () {
  if (!Dars.requireLogin()) return;
  const { fa, Store, sections, chaptersOf } = Dars;
  const C = window.CONTENT["{key}"];
  const ACC = "{accent}";
  const CHS = chaptersOf("{key}");
  const host = document.getElementById("chapters");

  if (!CHS.length) {
    host.innerHTML = '<div class="glass rounded-2xl p-8 text-center text-fog text-sm">فصلی ثبت نشده است.</div>';
    return;
  }

  // --- کارت فصل ---
  function chapterCard(ch, ci) {
    const doneLessons = ch.lessons.filter(l => Store.isLessonDone("{key}", l.id)).length;
    const pct = ch.nLessons ? Math.round(doneLessons / ch.nLessons * 100) : 0;

    const wrap = document.createElement("section");
    wrap.className = "glass rounded-3xl overflow-hidden";

    const head = document.createElement("button");
    head.type = "button";
    head.className = "w-full text-start px-4 sm:px-5 py-4 flex items-center gap-3 active:bg-white/5 transition-colors";
    head.setAttribute("aria-expanded", ci === 0 ? "true" : "false");
    head.innerHTML =
      '<span class="w-11 h-11 rounded-2xl grid place-items-center text-xl shrink-0 -rotate-3" ' +
        'style="background:' + ACC + '1f;border:1px solid ' + ACC + '4d">' + ch.icon + '</span>' +
      '<span class="min-w-0 flex-1">' +
        '<span class="block font-black text-sm sm:text-base leading-6">' + ch.name + '</span>' +
        '<span class="block text-[11px] text-fog mt-0.5">' +
          fa(ch.nLessons) + ' درس · ' + fa(ch.nSections) + ' مبحث' +
        '</span>' +
        '<span class="mt-2 block h-1.5 rounded-full bg-white/10 overflow-hidden">' +
          '<i class="block h-full rounded-full transition-all duration-500" ' +
            'style="width:' + pct + '%;background:' + ACC + '"></i>' +
        '</span>' +
      '</span>' +
      '<span class="shrink-0 text-fog text-xs font-black tabular-nums">' + fa(pct) + '٪</span>' +
      '<span class="chev shrink-0 text-fog transition-transform duration-200" style="transform:rotate(' +
        (ci === 0 ? "90deg" : "0deg") + ')">‹</span>';

    const body = document.createElement("div");
    body.className = "px-3 sm:px-4 pb-4 space-y-2" + (ci === 0 ? "" : " hidden");

    // --- کارت درس ---
    ch.lessons.forEach((L, li) => {
      const secs = sections(L);
      const sdone = secs.filter(s => Store.isSectionDone("{key}", L.id, s.id)).length;
      const qz = Store.getQuiz("{key}", L.id);
      const lpct = secs.length ? Math.round(sdone / secs.length * 100) : 0;

      const lesson = document.createElement("div");
      lesson.className = "rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden";

      const lhead = document.createElement("button");
      lhead.type = "button";
      lhead.className = "w-full text-start px-3.5 py-3 flex items-center gap-3 active:bg-white/5 transition-colors";
      lhead.setAttribute("aria-expanded", "false");
      lhead.innerHTML =
        '<span class="w-8 h-8 rounded-xl grid place-items-center text-[11px] font-black shrink-0" ' +
          'style="background:' + ACC + '1f;color:' + ACC + '">' + fa(li + 1) + '</span>' +
        '<span class="min-w-0 flex-1">' +
          '<span class="block text-[13px] font-black leading-6">' + L.title + '</span>' +
          '<span class="block text-[10px] text-fog mt-0.5">' +
            fa(secs.length) + ' مبحث · ' + fa(sdone) + ' خوانده' +
            (qz ? ' · آزمون ' + fa(qz.best) + '٪' : '') +
          '</span>' +
        '</span>' +
        '<span class="shrink-0 text-[10px] font-black tabular-nums ' +
          (lpct === 100 ? 'text-mint' : 'text-fog') + '">' + fa(lpct) + '٪</span>' +
        '<span class="chev shrink-0 text-fog text-[10px] transition-transform duration-200">‹</span>';

      const lbody = document.createElement("div");
      lbody.className = "px-3 pb-3 hidden";

      // --- مسیر مبحث‌ها ---
      const pathWrap = document.createElement("div");
      pathWrap.className = "relative ps-5";

      // خط عمودی مسیر
      const spine = document.createElement("i");
      spine.className = "absolute top-2 bottom-2 start-[9px] w-0.5 rounded-full";
      spine.style.background = "linear-gradient(180deg," + ACC + "66,transparent)";
      pathWrap.append(spine);

      secs.forEach((sec, si) => {
        const done = Store.isSectionDone("{key}", L.id, sec.id);
        const sq = Store.getSectionQuiz("{key}", L.id, sec.id);
        const isNext = !done && si === secs.findIndex(x => !Store.isSectionDone("{key}", L.id, x.id));

        const node = document.createElement("a");
        node.href = "section.html?l=" + encodeURIComponent(L.id) + "&s=" + encodeURIComponent(sec.id);
        node.className = "relative flex items-center gap-2.5 rounded-xl px-2 py-2 mb-1.5 " +
          "hover:bg-white/5 active:bg-white/10 transition-colors";
        node.innerHTML =
          '<span class="absolute start-[-14px] w-3.5 h-3.5 rounded-full shrink-0 grid place-items-center ' +
            (done ? "bg-mint" : isNext ? "animate-pulse-ring" : "bg-panel2 border border-white/20") + '" ' +
            'style="' + (done ? "" : isNext ? "background:" + ACC : "") + '">' +
            (done ? '<span class="text-[8px] text-ink font-black">✓</span>' : '') +
          '</span>' +
          '<span class="min-w-0 flex-1">' +
            '<span class="block text-[12px] leading-6 ' +
              (done ? "text-mint font-bold" : isNext ? "text-snow font-black" : "text-fog") + '">' +
              sec.title +
            '</span>' +
            (sq ? '<span class="block text-[10px] text-fog/80 mt-0.5">کوییز: ' +
              fa(sq.best) + '٪ · ' + fa(sq.correct) + ' از ' + fa(sq.total) + ' درست</span>' : '') +
          '</span>' +
          '<span class="shrink-0 text-fog/60 text-[10px]">‹</span>';
        pathWrap.append(node);
      });

      // --- آزمون پایان درس ---
      const hasQ = ((C.quizzes || {})[L.id] || []).length > 0;
      let exam = null;
      if (hasQ) {
        exam = document.createElement("a");
        exam.href = "quiz.html?id=" + encodeURIComponent(L.id);
        exam.className = "mt-3 flex items-center gap-3 rounded-xl px-3 py-2.5 border transition-colors " +
          (qz ? "border-mint/40 bg-mint/10" : "border-white/15 bg-white/5 hover:bg-white/10");
        exam.innerHTML =
          '<span class="text-lg shrink-0">' + (qz ? "🏆" : "🎯") + '</span>' +
          '<span class="min-w-0 flex-1">' +
            '<span class="block text-[12px] font-black">' +
              (qz ? "آزمون پایان درس — بهترین نمره" : "آزمون پایان درس") + '</span>' +
            '<span class="block text-[10px] text-fog mt-0.5">' +
              (qz ? fa(qz.best) + '٪ · ' + fa(qz.tries) + ' بار شرکت' :
                    fa(((C.quizzes || {})[L.id] || []).length) + ' پرسش') +
            '</span>' +
          '</span>' +
          '<span class="shrink-0 text-xs ' + (qz ? "text-mint" : "text-fog") + '">‹</span>';
      }

      lbody.append(pathWrap);
      if (exam) lbody.append(exam);

      lhead.addEventListener("click", () => {
        const open = lbody.classList.toggle("hidden");
        lhead.setAttribute("aria-expanded", String(!open));
        const ch2 = lhead.querySelector(".chev");
        if (ch2) ch2.style.transform = open ? "rotate(0deg)" : "rotate(-90deg)";
      });

      lesson.append(lhead, lbody);
      body.append(lesson);
    });

    // آزمون کل فصل
    const totalQ = ch.lessons.reduce((s, l) => s + (((C.quizzes || {})[l.id]) || []).length, 0);
    if (totalQ) {
      const a = document.createElement("a");
      a.href = "quiz.html?ch=" + ci;
      a.className = "mt-1 flex items-center gap-3 rounded-2xl px-3.5 py-3 border-2 border-dashed border-white/20 hover:border-white/35 transition-colors";
      a.innerHTML =
        '<span class="text-xl shrink-0">🏁</span>' +
        '<span class="min-w-0 flex-1">' +
          '<span class="block text-[12px] font-black">آزمون فصل — ' + ch.name + '</span>' +
          '<span class="block text-[10px] text-fog mt-0.5">' + fa(totalQ) + ' پرسش از همهٔ درس‌های این فصل</span>' +
        '</span>' +
        '<span class="shrink-0 text-fog text-xs">‹</span>';
      body.append(a);
    }

    head.addEventListener("click", () => {
      const hidden = body.classList.toggle("hidden");
      head.setAttribute("aria-expanded", String(!hidden));
      const ch2 = head.querySelector(".chev");
      if (ch2) ch2.style.transform = hidden ? "rotate(0deg)" : "rotate(-90deg)";
    });

    wrap.append(head, body);
    return wrap;
  }

  CHS.forEach((ch, i) => host.append(chapterCard(ch, i)));

  // نوار پیشرفت کل کتاب = درس خوانده / کل درس
  const allLessons = CHS.reduce((a, c) => a.concat(c.lessons), []);
  const done = allLessons.filter(l => Store.isLessonDone("{key}", l.id)).length;
  const pct = allLessons.length ? Math.round(done / allLessons.length * 100) : 0;
  document.getElementById("pbv").textContent = fa(pct) + "٪";
  requestAnimationFrame(() => { document.getElementById("pbf").style.width = pct + "%"; });
})();
</script>
</body>
</html>
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
      '<div class="flex items-start justify-between gap-3 mb-1.5 flex-wrap">' +
        '<h2 class="text-lg sm:text-xl font-black">' + L.title + '</h2>' +
        '<a class="shrink-0 rounded-lg px-3 py-1.5 text-[11px] font-black border border-white/20 ' +
          'hover:bg-white/10 transition-colors" href="section.html?l=' + encodeURIComponent(L.id) +
          '&s=' + encodeURIComponent(Dars.sections(L)[0].id) + '">مبحث‌ها ‹</a>' +
      '</div>' +
      '<div class="text-xs text-fog mb-4">درس ' + fa(L.n) + ' · صفحهٔ ' + L.page + ' · ' +
        fa(Dars.sections(L).length) + ' مبحث</div>' +
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

    <!-- مدل قدیمی: صفحهٔ درس بازنشسته شد و به نخستین مبحث همان درس می‌رود -->
    <script>
    (function () {{
      var id = new URLSearchParams(location.search).get("id");
      if (!id) {{ location.replace("index.html"); return; }}
      location.replace("section.html?l=" + encodeURIComponent(id));
    }})();
    </script>

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
# ---------------- صفحه مبحث ----------------
SECTION_TPL = BASE_HEAD + TOPBAR + """
<main>
  <div class="mx-auto max-w-3xl px-4 sm:px-6 py-5 sm:py-8">

    <div class="flex items-center gap-2 mb-4 flex-wrap text-[11px]">
      <a href="index.html" class="font-bold text-fog hover:text-snow transition-colors">← مسیر کتاب</a>
      <span class="text-fog/40">/</span>
      <span class="font-bold" id="chName" style="color:{accent}">—</span>
    </div>

    <div class="flex items-center justify-between gap-2 mb-3">
      <span class="glass rounded-full px-3 py-1.5 text-[11px] font-black" style="color:{accent}" id="secIdx">مبحث</span>
      <a class="rounded-lg px-3 py-1.5 text-[11px] font-bold border border-white/15 text-fog hover:text-snow transition-colors"
         href="{pdfHref}" target="_blank" rel="noopener">PDF کتاب</a>
    </div>

    <h1 class="text-xl sm:text-2xl font-black leading-snug mb-1.5" id="secTitle">…</h1>
    <p class="text-[11px] text-fog mb-5" id="secMeta"></p>

    <article class="glass rounded-3xl p-5 sm:p-7 lesson-body" id="secBody"></article>

    <div class="mt-5 flex flex-wrap items-center gap-2">
      <button class="btn3d rounded-xl px-5 py-3 text-sm font-black text-ink cursor-pointer"
              style="background:linear-gradient(90deg,{accent},#22d3ee)" id="markRead" type="button">
        این مبحث را خواندم ✓
      </button>
      <div class="flex-1"></div>
      <a class="rounded-xl px-4 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors"
         href="#" id="prevSec">← قبلی</a>
      <a class="rounded-xl px-4 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors"
         href="#" id="nextSec">بعدی →</a>
    </div>

    <!-- کوییز مبحث -->
    <section class="mt-8">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-base sm:text-lg font-black">کوییز این مبحث</h2>
        <span class="text-[10px] text-fog" id="sqInfo"></span>
      </div>
      <div id="sqHost"></div>
    </section>

    <!-- پایان درس -->
    <div class="mt-8 glass rounded-3xl p-5 sm:p-6" id="lessonEnd">
      <div class="text-sm font-black mb-1.5" id="leTitle">پایان درس</div>
      <p class="text-[11px] text-fog leading-6 mb-4" id="leText"></p>
      <div class="flex flex-wrap gap-2" id="leActions"></div>
    </div>
  </div>
</main>
""" + FOOT + """
<script src="../../assets/js/config.js"></script>
<script src="../../assets/js/app.js"></script>
<script src="../../assets/js/cloud.js"></script>
<script src="../../assets/data/_structure.js"></script>
<script src="../../assets/data/{key}.js"></script>
<script>
(function () {
  if (!Dars.requireLogin()) return;
  const { fa, Store, sections } = Dars;
  const C = window.CONTENT["{key}"];
  const ACC = "{accent}";
  const SUBJ = "{key}";
  const $ = (id) => document.getElementById(id);

  const qs = new URLSearchParams(location.search);
  const lid = qs.get("l") || (C.lessons[0] || {}).id;
  const sid = qs.get("s") || "";

  const idx = C.lessons.findIndex((x) => x.id === lid);
  const L = C.lessons[idx];
  if (!L) { $("secBody").textContent = "درس یافت نشد."; return; }

  const secs = sections(L);
  let si = secs.findIndex((x) => x.id === sid);
  if (si < 0) si = 0;
  const S = secs[si];

  // فصل این درس
  const chs = (window.DARS_STRUCTURE || {})[SUBJ] || [];
  const ch = chs.find((c) => c.lessons.includes(idx + 1));
  $("chName").textContent = ch ? ch.name : "درس";

  $("secIdx").textContent = "مبحث " + fa(si + 1) + " از " + fa(secs.length);
  $("secTitle").textContent = S.fullTitle || S.title;
  $("secMeta").textContent = "درس " + fa(L.n) + " · صفحهٔ " + L.page + " · " + fa(secs.length) + " مبحث";

  // بدنه + نکته‌های همین مبحث
  let body = S.html || "";
  if (S.points && S.points.length) {
    body += '<div class="mt-5 rounded-2xl p-4" style="background:' + ACC + '14;border:1px solid ' + ACC + '3d">' +
      '<div class="text-xs font-black mb-2" style="color:' + ACC + '">⭐ نکته‌های کلیدی</div>' +
      S.points.map((p, i) => '<div class="flex gap-2 text-[13px] leading-7 mb-1.5">' +
        '<span class="shrink-0 font-black" style="color:' + ACC + '">' + fa(i + 1) + '.</span>' +
        '<span>' + p + '</span></div>').join("") +
      '</div>';
  }
  $("secBody").innerHTML = body;

  // ناوبری قبلی/بعدی در سطح مبحث
  function go(delta) {
    let n = si + delta;
    if (n < 0) {
      if (idx > 0) {
        const pl = C.lessons[idx - 1];
        const ps = sections(pl);
        location.href = "section.html?l=" + encodeURIComponent(pl.id) + "&s=" + encodeURIComponent(ps[ps.length - 1].id);
      }
      return;
    }
    if (n >= secs.length) {
      if (idx + 1 < C.lessons.length) {
        const nl = C.lessons[idx + 1];
        const ns = sections(nl);
        location.href = "section.html?l=" + encodeURIComponent(nl.id) + "&s=" + encodeURIComponent(ns[0].id);
      }
      return;
    }
    location.href = "section.html?l=" + encodeURIComponent(L.id) + "&s=" + encodeURIComponent(secs[n].id);
  }
  $("prevSec").addEventListener("click", (e) => { e.preventDefault(); go(-1); });
  $("nextSec").addEventListener("click", (e) => { e.preventDefault(); go(1); });

  // دکمهٔ «خواندم»
  const mr = $("markRead");
  function paintRead() {
    if (Store.isSectionDone(SUBJ, L.id, S.id)) {
      mr.textContent = "خوانده شد ✓";
      mr.disabled = true;
      mr.style.background = "rgba(255,255,255,.08)";
      mr.style.color = "#93a2c0";
      mr.style.boxShadow = "none";
    }
  }
  mr.addEventListener("click", () => {
    const first = Store.markSection(SUBJ, L.id, S.id);
    Dars.paintStats();
    paintRead();
    if (first) Dars.celebrate(14);
  });
  paintRead();

  /* ---------------- کوییز مبحث ---------------- */
  const allQ = ((C.quizzes || {})[L.id] || []);
  const sqHost = $("sqHost");
  const prev = Store.getSectionQuiz(SUBJ, L.id, S.id);
  $("sqInfo").textContent = prev ? "بهترین: " + fa(prev.best) + "٪" : "";

  if (!allQ.length) {
    sqHost.innerHTML = '<div class="glass rounded-2xl p-6 text-center text-xs text-fog">' +
      'برای این درس پرسشی ثبت نشده است.</div>';
  } else {
    // ۳ پرسش برای هر مبحث — نوبتی از مجموعهٔ درس، تا هر مبحث سهم خودش را بگیرد
    const per = Math.min(3, allQ.length);
    const start = (si * per) % allQ.length;
    const pick = [];
    for (let i = 0; i < per; i++) pick.push(allQ[(start + i) % allQ.length]);

    Dars.runQuiz({
      host: sqHost,
      questions: pick,
      backHref: "index.html",
      nextHref: "index.html",
      compact: true,
      save: false,
      onDone: (pct, correct, total) => {
        Store.saveSectionQuiz(SUBJ, L.id, S.id, pct, correct, total);
        Dars.paintStats();
        paintRead();
        $("sqInfo").textContent = "بهترین: " + fa(pct) + "٪";
        paintEnd();
      }
    });
  }

  /* ---------------- پایان درس ---------------- */
  function paintEnd() {
    const doneAll = secs.every((x) => Store.isSectionDone(SUBJ, L.id, x.id));
    const qz = Store.getQuiz(SUBJ, L.id);
    const isLast = si === secs.length - 1;

    $("leTitle").textContent = isLast ? "پایان درس — " + L.title : "ادامهٔ درس";
    $("leText").textContent = isLast
      ? (doneAll
          ? "همهٔ مبحث‌های این درس را خواندی. حالا آزمون پایان درس را بده و نمره‌ات را ببین."
          : "هنوز چند مبحث خوانده نشده است؛ می‌توانی آزمون را همین حالا بدهی یا بعداً برگردی.")
      : "مبحث بعدی این درس در انتظار توست.";

    const acts = $("leActions");
    acts.innerHTML = "";
    const hasQ = allQ.length > 0;

    if (hasQ) {
      const a = document.createElement("a");
      a.href = "quiz.html?id=" + encodeURIComponent(L.id);
      a.className = "btn3d rounded-xl px-5 py-2.5 text-xs font-black text-ink";
      a.style.background = qz
        ? "linear-gradient(90deg,#34d399,#22d3ee)"
        : "linear-gradient(90deg," + ACC + ",#22d3ee)";
      a.textContent = qz ? "🏆 آزمون درس — بهترین " + fa(qz.best) + "٪" : "🎯 آزمون پایان درس";
      acts.append(a);
    }
    if (!isLast) {
      const b = document.createElement("a");
      b.href = "section.html?l=" + encodeURIComponent(L.id) + "&s=" + encodeURIComponent(secs[si + 1].id);
      b.className = "rounded-xl px-5 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors";
      b.textContent = "مبحث بعدی →";
      acts.append(b);
    } else {
      const b = document.createElement("a");
      b.href = "index.html";
      b.className = "rounded-xl px-5 py-2.5 text-xs font-bold border border-white/15 text-fog hover:text-snow transition-colors";
      b.textContent = "بازگشت به فهرست فصل‌ها";
      acts.append(b);
    }
  }
  paintEnd();
})();
</script>
</body>
</html>
"""


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

  if (params.get("ch") !== null) {{
    // آزمون فصل: پرسش‌های همهٔ درس‌های این فصل
    const chs = (window.DARS_STRUCTURE || {{}})[KEY] || [];
    const ci = parseInt(params.get("ch"), 10) || 0;
    const ch = chs[ci];
    if (ch) {{
      const qs2 = [];
      ch.lessons.forEach((n) => {{
        const lid2 = "l" + (n < 10 ? "0" : "") + n;
        qs2.push(...((C.quizzes || {{}})[lid2] || []));
      }});
      questions = Dars.shuffle(qs2);
      title = "آزمون فصل — " + ch.name;
      qid = "ch:" + ci;
    }}
  }} else if (params.get("all") === "1") {{
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
            rootHref="../../",
            nLessons=str(n_lessons),
            nQuiz=str(n_quiz),
            nQ=str(n_q),
            nPages="۰",
            pdfHref="../../پایه-نهم/" + PDFS[key],
        )

        # --- صفحه مسیر ---
        n_chapters = len(STRUCTURE.get(key, []))
        n_sections = sum(
            (len(re.findall(r"<h3[^>]*>", L["body"])) or 1) for L in DATA_CONTENT[key]["lessons"]
        )
        path_html = _fmt(PATH_TPL, dict(
            nChapters=fa(n_chapters),
            nSections=fa(n_sections),
            title=f"{m['name']} — درسیار نهم",
            desc=f"{m['full']} — درس‌نامه، آزمون و پیشرفت",
            backLabel="صفحهٔ اصلی",
            footText=f"{m['name']} · {m['full']}",
            footLink="صفحهٔ اصلی",
            **common,
        ))
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

        # --- صفحه مبحث ---
        section_html = _fmt(SECTION_TPL, dict(
            title=f"مبحث — {m['name']}",
            desc=f"مبحث‌های {m['full']}",
            backLabel="مسیر درس",
            footText=f"{m['name']} · {m['full']}",
            footLink="صفحهٔ اصلی",
            **common,
        ))
        open(os.path.join(d, "section.html"), "w", encoding="utf-8").write(section_html)

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
