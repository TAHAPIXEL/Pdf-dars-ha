#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ساخت فایل ساختار فصل‌ها:  assets/data/_structure.js
--------------------------------------------------------------------
هر کتاب پایه نهم به فصل‌های واقعی خودش تقسیم می‌شود و هر فصل
درس‌هایش را با شماره مشخص می‌کند.

منبع فصل‌بندی:
  • ریاضی، علوم، مطالعات، فارسی، قرآن، پیام‌های آسمان، عربی، نگارش،
    انگلیسی و کتاب کار: فهرست رسمی همان کتاب درسی پایه نهم.
  • ترتیب درس‌های داخل هر کتاب همان ترتیب صفحه‌های PDF است، پس
    شماره‌گذاری فصل‌ها پیوسته و بدون جابه‌جایی است.
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "data", "_structure.js")

# name: عنوان فصل | lessons: شمارهٔ درس‌ها (۱‑based) | icon
STRUCTURE = {
    "quran": {
        "chapters": [
            {"name": "درس‌های ۱ تا ۶", "icon": "📖", "lessons": [1, 2, 3, 4, 5, 6]},
            {"name": "درس‌های ۷ تا ۱۱", "icon": "🌙", "lessons": [7, 8, 9, 10, 11]},
        ]
    },
    "payam": {
        "chapters": [
            {"name": "بخش یکم — شناخت و ایمان", "icon": "🕌", "lessons": [1, 2, 3, 4, 5]},
            {"name": "بخش دوم — عبادت و اخلاق", "icon": "🤲", "lessons": [6, 7, 8]},
            {"name": "بخش سوم — جامعه و تاریخ", "icon": "🏛️", "lessons": [9, 10, 11, 12]},
        ]
    },
    "farsi": {
        "chapters": [
            {"name": "فصل ۱ — ادبیات تعلیمی", "icon": "📜", "lessons": [1, 2, 3, 4, 5, 6]},
            {"name": "فصل ۲ — ادبیات حماسی", "icon": "⚔️", "lessons": [7, 8, 9, 10, 11, 12]},
            {"name": "فصل ۳ — ادبیات غنایی و نمایشی", "icon": "🎭", "lessons": [13, 14, 15, 16, 17]},
        ]
    },
    "negar": {
        "chapters": [
            {"name": "فصل ۱ — ساختار و واژه", "icon": "✍️", "lessons": [1, 2, 3]},
            {"name": "فصل ۲ — فضا و قالب نوشته", "icon": "🎨", "lessons": [4, 5, 6]},
            {"name": "فصل ۳ — ویرایش و بازنویسی", "icon": "🔍", "lessons": [7, 8]},
        ]
    },
    "math": {
        "chapters": [
            {"name": "فصل ۱ — مجموعه‌ها", "icon": "🎲", "lessons": [1, 2, 3, 4]},
            {"name": "فصل ۲ — عددهای حقیقی", "icon": "🔢", "lessons": [5, 6, 7]},
            {"name": "فصل ۳ — استدلال و اثبات در هندسه", "icon": "📐", "lessons": [8, 9, 10, 11]},
            {"name": "فصل ۴ — توان و ریشه", "icon": "√", "lessons": [12, 13, 14, 15, 16]},
            {"name": "فصل ۵ — عبارت‌های جبری", "icon": "✖️", "lessons": [17, 18]},
            {"name": "فصل ۶ — خط و معادله‌های خطی", "icon": "📈", "lessons": [19, 20, 21, 22]},
            {"name": "فصل ۷ — عبارت‌های گویا", "icon": "➗", "lessons": [23, 24, 25]},
            {"name": "فصل ۸ — حجم و مساحت", "icon": "🧊", "lessons": [26, 27, 28]},
        ]
    },
    "science": {
        "chapters": [
            {"name": "فصل ۱ — مواد و نقش آن‌ها در زندگی", "icon": "🧪", "lessons": [1, 2]},
            {"name": "فصل ۲ — رفتار اتم‌ها با یکدیگر", "icon": "⚛️", "lessons": [3]},
            {"name": "فصل ۳ — به دنبال محیطی بهتر", "icon": "🌱", "lessons": [4]},
            {"name": "فصل ۴ — حرکت چیست؟", "icon": "🏃", "lessons": [5]},
            {"name": "فصل ۵ — نیرو", "icon": "🧲", "lessons": [6]},
            {"name": "فصل ۶ — زمین‌ساخت ورقه‌ای", "icon": "🌍", "lessons": [7]},
            {"name": "فصل ۷ — ماشین‌ها و کار", "icon": "⚙️", "lessons": [8, 9, 10]},
            {"name": "فصل ۸ — فشار و آثار آن", "icon": "💨", "lessons": [11, 12]},
            {"name": "فصل ۹ — ماشین‌های گرم", "icon": "🔥", "lessons": [13, 14, 15]},
        ]
    },
    "social": {
        "chapters": [
            {"name": "بخش جغرافیا — زمین و زیست‌بوم", "icon": "🌍", "lessons": [1, 2, 3, 4, 5, 6]},
            {"name": "بخش جغرافیا — جمعیت و شهر", "icon": "🏙️", "lessons": [7, 8, 9, 10, 11]},
            {"name": "بخش تاریخ — ایران و جهان", "icon": "🏺", "lessons": [12, 13, 14, 15]},
            {"name": "بخش مدنی — جامعه و قانون", "icon": "⚖️", "lessons": [16, 17, 18]},
        ]
    },
    "arabic": {
        "chapters": [
            {"name": "درس‌های ۱ تا ۵", "icon": "🕋", "lessons": [1, 2, 3, 4, 5]},
            {"name": "درس‌های ۶ تا ۱۰", "icon": "📗", "lessons": [6, 7, 8, 9, 10]},
        ]
    },
    "english": {
        "chapters": [
            {"name": "Lesson 1", "icon": "🔤", "lessons": [1]},
            {"name": "Lesson 2", "icon": "🔤", "lessons": [2]},
            {"name": "Lesson 3", "icon": "🔤", "lessons": [3]},
            {"name": "Lesson 4", "icon": "🔤", "lessons": [4]},
            {"name": "Lesson 5", "icon": "🔤", "lessons": [5]},
            {"name": "Lesson 6", "icon": "🔤", "lessons": [6]},
        ]
    },
    "english-workbook": {
        "chapters": [
            {"name": "Lesson 1", "icon": "📝", "lessons": [1]},
            {"name": "Lesson 2", "icon": "📝", "lessons": [2]},
            {"name": "Lesson 3", "icon": "📝", "lessons": [3]},
            {"name": "Lesson 4", "icon": "📝", "lessons": [4]},
            {"name": "Lesson 5", "icon": "📝", "lessons": [5]},
            {"name": "Lesson 6", "icon": "📝", "lessons": [6]},
        ]
    },
}


def main():
    lines = [
        "/* ============================================================",
        "   ساختار فصل‌ها — تولیدشده توسط tools/gen_structure.py",
        "   هر کتاب → فصل‌ها → شمارهٔ درس‌ها",
        "   ============================================================ */",
        "window.DARS_STRUCTURE = window.DARS_STRUCTURE || {};",
        "",
    ]
    total_ch = 0
    for key, cfg in STRUCTURE.items():
        lines.append('window.DARS_STRUCTURE["%s"] = [' % key)
        for ch in cfg["chapters"]:
            lines.append(
                "  { name: %s, icon: %s, lessons: %s },"
                % (json.dumps(ch["name"], ensure_ascii=False),
                   json.dumps(ch["icon"], ensure_ascii=False),
                   json.dumps(ch["lessons"]))
            )
            total_ch += 1
        lines.append("];")
        lines.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # validate: no lesson repeated, no lesson missing
    print("chapters:", total_ch)
    import subprocess
    for key, cfg in STRUCTURE.items():
        js = ('global.window={};require("./assets/data/%s.js");'
              'console.log(window.CONTENT["%s"].lessons.length);' % (key, key))
        n = int(subprocess.run(["node", "-e", js], capture_output=True, text=True,
                               cwd=ROOT).stdout.strip())
        covered = [x for ch in cfg["chapters"] for x in ch["lessons"]]
        dup = len(covered) != len(set(covered))
        miss = sorted(set(range(1, n + 1)) - set(covered))
        extra = sorted(set(covered) - set(range(1, n + 1)))
        flag = "OK " if not (dup or miss or extra) else "ERR"
        print("%s %-18s lessons=%-3d chapters=%-2d covered=%-3d%s%s%s"
              % (flag, key, n, len(cfg["chapters"]), len(covered),
                 " DUP" if dup else "", " MISSING=%s" % miss if miss else "",
                 " EXTRA=%s" % extra if extra else ""))


if __name__ == "__main__":
    main()
