#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تولید درس‌نامه‌های درس‌یار نهم **مستقیماً از متن PDFهای کتاب درسی**.

هیچ متنی از بیرون کتاب نوشته نمی‌شود؛ هر بندِ درس‌نامه از خط‌های همان
صفحه‌های کتاب گرفته می‌شود و شمارهٔ صفحهٔ کتاب هم درج می‌گردد.

ورودی:
    /tmp/txt3/<book>.json   — خروجی ابزار extract_pdf_text.py
    tools/curriculum.json   — نقشهٔ درس/فصل (از فهرست خودِ کتاب)

خروجی:
    assets/data/<key>.js

اجرا:
    python3 tools/make_content.py [key ...]
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURR = json.load(open(os.path.join(ROOT, "tools", "curriculum.json"), encoding="utf-8"))

TXT_DIR = "/tmp/txt3"
BOOKS = {
    "quran": "01-قرآن-نهم",
    "payam": "02-پیام‌های-آسمانی-نهم",
    "farsi": "03-فارسی-نهم",
    "negar": "04-نگارش-نهم",
    "math": "05-ریاضی-نهم",
    "science": "06-علوم-تجربی-نهم",
    "social": "07-مطالعات-اجتماعی-نهم",
    "arabic": "08-عربی-نهم",
    "english": "09-زبان-انگلیسی-نهم",
    "english-workbook": "10-کتاب-کار-زبان-انگلیسی-نهم",
}

META = {
    "quran": dict(name="قرآن", full="آموزش قرآن پایه نهم", icon="📖", accent="#14b8a6",
                  accentDeep="#0d9488"),
    "payam": dict(name="پیام‌های آسمانی", full="پیام‌های آسمانی پایه نهم", icon="🕌",
                  accent="#8b5cf6", accentDeep="#7c3aed"),
    "farsi": dict(name="فارسی", full="فارسی پایه نهم", icon="📚", accent="#f59e0b",
                  accentDeep="#d97706"),
    "negar": dict(name="نگارش", full="نگارش پایه نهم", icon="✍️", accent="#ec4899",
                  accentDeep="#db2777"),
    "math": dict(name="ریاضی", full="ریاضی پایه نهم", icon="📐", accent="#3b82f6",
                 accentDeep="#2563eb"),
    "science": dict(name="علوم تجربی", full="علوم تجربی پایه نهم", icon="🔬",
                    accent="#22c55e", accentDeep="#16a34a"),
    "social": dict(name="مطالعات اجتماعی", full="مطالعات اجتماعی پایه نهم", icon="🌍",
                   accent="#0ea5e9", accentDeep="#0284c7"),
    "arabic": dict(name="عربی", full="عربی پایه نهم", icon="🕋", accent="#f97316",
                   accentDeep="#ea580c"),
    "english": dict(name="زبان انگلیسی", full="زبان انگلیسی پایه نهم", icon="🔤",
                    accent="#a855f7", accentDeep="#9333ea"),
    "english-workbook": dict(name="کتاب کار انگلیسی", full="کتاب کار زبان انگلیسی پایه نهم",
                             icon="📝", accent="#06b6d4", accentDeep="#0891b2"),
}

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def fa(n) -> str:
    """عدد لاتین → رقم فارسی."""
    return "".join(FA_DIGITS[int(c)] if c.isdigit() else c for c in str(n))


def clean(text: str) -> str:
    """پاک‌سازی سبکِ چاپی: فاصله‌های اضافی، نویسه‌های کنترلی."""
    text = "".join(c for c in text if unicodedata.category(c)[0] != "C")
    text = text.replace("\u200a", " ").replace("\u200b", "")
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


# نشانه‌هایی که در کتاب، آغاز یک عنوان یا کادر آموزشی‌اند
STOP_HEAD = re.compile(
    r"^(شکل|جدول|جدول\s*[٠-٩۰-۹\d]|فعالیت|آزمایش کنید|خود را بیازمایید|فکر کنید|"
    r"گفت ?وگو کنید|آیا می ?دانید|جمع ?آوری اطلاعات|بحث کنید|نکته|کار گروهی|"
    r"کاربرد|پرسش ?های|تمرین ?های|یادآوری|نمودار|تصویر|فصل \d+|درس \d+)"
)
SENT_END = (".", "!", "؟", "?", "؛")


def is_reversed_line(line: str) -> bool:
    """خطی که کلمه‌هایش برعکس چیده شده‌اند («یاپ قمرآنی» ← «پای قرآن»)."""
    if not re.search(r"[\u0600-\u06FF]", line):
        return False                     # متن انگلیسی معکوس نیست
    words = [w for w in line.split() if len(w) > 2]
    if len(words) < 2:
        return False
    hits = 0
    for w in words:
        for cand in (w[::-1], "".join(reversed(list(w)))):
            if cand in REV_WORDS or cand.rstrip("ٔ") in REV_WORDS:
                hits += 1
                break
    persian = sum(bool(re.search(r"[ا-ی]", w)) for w in words)
    if persian == 0:
        return True
    return hits >= max(2, len(words) // 2)


REV_WORDS = {"پای", "قرآن", "قرآنی", "درس", "اول", "دوم", "سوم", "چهارم", "پنجم",
             "ششم", "هفتم", "هشتم", "نهم", "دهم", "جلسه", "جلسۀ", "فصل", "کتاب",
             "خدا", "خداوند", "سوره", "آیه", "آیات", "ترجمه", "گروه", "خواندن"}


def collapse_repeats(text: str) -> str:
    """هر عبارتِ پشت‌سرهم تکرارشده را به یک بار کاهش می‌دهد.

    «درس سوم درس سوم» / «یاپ قمرآنی یاپ قمرآنی» ← یک بار.
    """
    t = re.sub(r"\s+", " ", text).strip()
    for _ in range(6):
        new = re.sub(r"^(\S+(?:\s+\S+){0,3}?)(?:\s+\1)+", r"\1", t)
        new = re.sub(r"(\S+(?:\s+\S+){0,3}?)(?:\s+\1)+$", r"\1", new)
        if new == t:
            break
        t = new
    return t


def is_junk(line: str) -> bool:
    """خطِ بی‌معنای برجای‌مانده از چیدمان PDF.

    نمونهٔ واقعی: «ححففظ ظ» — حرف‌های تکراریِ چسبیده که از جابه‌جایی
    گلیف‌ها ساخته می‌شود. متنِ سالمِ کتاب چنین الگویی ندارد.
    """
    t = line.strip()
    if len(t) < 4:
        return True
    # حرف تکراریِ چسبیده در یک واژهٔ بی‌واژه (ححففظ) — «یی» در «بیازمایید» مجاز است
    for w in t.split():
        if len(w) < 4:
            continue
        if re.search(r"(?<!ی)(\S)\1(?!ی)", w) and w not in ("بیازمایید",):
            return True
    # واژه‌های تک‌حرفیِ پرشمار
    words = t.split()
    if len(words) >= 3 and sum(1 for w in words if len(w) <= 1) > len(words) / 2:
        return True
    return False


def is_heading(line: str) -> bool:
    """خط سرتیتر است؟ (کوتاه، بی‌نقطهٔ پایانی، جمله‌ای نیست)"""
    t = line.strip()
    if not t or len(t) > 62:
        return False
    if t.endswith(SENT_END):
        return False
    if STOP_HEAD.match(t):
        return False
    if re.match(r"^[\d٠-٩۰-۹\s.]+$", t):
        return False
    return t.count(" ") >= 1


def looks_garbled(line: str) -> bool:
    """خط با قلم اختصاصی/رمزگذاری‌شده رندر شده است؟"""
    letters = [c for c in line if not c.isspace()]
    if not letters:
        return True
    weird = 0
    for c in letters:
        o = ord(c)
        if c.isascii() or 0x0600 <= o <= 0x06FF or c in "«»٪۰۱۲۳۴۵۶۷۸۹":
            continue
        if 0x2000 <= o <= 0x206F:        # فاصله‌های ویژه و نیم‌فاصله
            continue
        weird += 1
    return weird / max(1, len(letters)) > 0.06


MATH_JUNK = re.compile(
    r"^[\s\d\u0660-\u0669\u06f0-\u06f9+\-*/=<>()\[\]{}.^_|\u00d7\u00f7\u2212\u22c5"
    r"\u221a\u03c0\uf8eb\uf8ec\uf8ed\uf8ee\uf8ef\uf8f0\uf8f1\uf8f2\uf8f3\uf8f4\uf8f5"
    r"\uf8f6\uf8f7\uf8f8\uf8f9\uf8fa\uf8fb\uf8fc\uf8fd\uf8fe\uf8ff,;:.]{1,6}$"
)


def is_formula_fragment(line: str) -> bool:
    """تکهٔ نیمه‌کارهٔ فرمولِ ریاضی که در PDF از هم پاشیده است.

    در کتاب ریاضی، فرمول‌ها به تک‌حرف‌ها و نیم‌های کمانک شکسته می‌شوند
    («m»، «a»، «»). این تکه‌ها بدون تصویرِ اصلی معنا ندارند.
    """
    t = line.strip()
    if not t:
        return True
    if ord(t[0]) >= 0xF8E0 and ord(t[0]) <= 0xF8FF:     # کمانک‌های ریاضی
        return True
    if MATH_JUNK.match(t):
        return True
    # خطِ تک/دوحرفیِ لاتین یا ریاضی (a، m، =1و…)
    if len(t) <= 2 and not re.search(r"[\u0600-\u06FF]", t):
        return True
    # خطی که تقریباً همه‌اش رقم و نماد است (دنبالهٔ محاسبه‌های PDF)
    letters = sum(1 for ch in t if ch.isalpha() or "\u0600" <= ch <= "\u06FF")
    if len(t) >= 8 and letters / len(t) < 0.18 and re.search(r"[=\u00d7*/+\-]", t):
        return True
    return False


def is_prose(line: str) -> bool:
    t = line.strip()
    if len(t) < 28:
        return False
    if STOP_HEAD.match(t):
        return False
    if t.startswith("شکل") or re.match(r"^[٠-٩۰-۹\d]+\s*[ــ-]", t):
        return False
    return True


def para(lines: list[str]) -> str:
    """چند خط → یک بندِ به‌هم‌پیوسته (اصلاح شکست سطر)."""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out and not out.endswith((" ", "\u200c")):
            # اگر خط پیشین با نیم‌فاصله تمام شده، فاصله لازم نیست
            out += " "
        out += ln
    return re.sub(r"[ ]{2,}", " ", out).strip()


def split_paragraphs(text: str) -> list[str]:
    """خط‌های یک صفحه → بندهای معنادار بر اساس نقطه/حالت متن."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    blocks: list[str] = []
    buf: list[str] = []
    for ln in lines:
        buf.append(ln)
        joined = para(buf)
        # بند وقتی تمام می‌شود که با نقطه/پرسش تمام شده و به اندازهٔ کافی بلند است
        if joined.endswith((".", "!", "؟", ":", "»")) and len(joined) > 90:
            blocks.append(joined)
            buf = []
    if buf:
        tail = para(buf)
        if tail:
            blocks.append(tail)
    return blocks


SHADDA = "\u0651"
SUKUN = "\u0652"


def fix_arabic_marks(text: str) -> str:
    """اعرابِ عربی که در PDF پیش از حرفِ پایه ذخیره شده‌اند را سر جایشان می‌برد.

    PDF کتاب عربی، نشانه‌ها را پیش از حرف می‌دهد («َأنـا» به‌جای «أَنا») و
    کشیده (تطویل) را هم چاپ می‌کند. نتیجه بدون این اصلاح ناخوانا است.
    """
    if not re.search(r"[\u0600-\u06FF]", text):
        return text
    import unicodedata as _ud
    out: list[str] = []
    pending: list[str] = []
    for ch in text:
        if _ud.combining(ch):
            pending.append(ch)
        elif pending and ch.isalpha():
            out.append(ch)
            out.extend(pending)
            pending = []
        else:
            if pending:
                out.extend(pending)
                pending = []
            out.append(ch)
    if pending:
        out.extend(pending)
    res = "".join(out).replace("\u0640", "")
    # شَدّه باید بی‌درنگ پس از حرف باشد و حرکت‌ها پس از آن
    res = re.sub(r"([\u0621-\u064A])([\u064B-\u0650\u0652])(\u0651)",
                 r"\1\3\2", res)
    # حرکت‌ها دور از حرف نیستند ولی ترتیبشان باید یکدست شود
    res = re.sub(r"\s+([\u064B-\u0652])", r"\1", res)
    return res


PREFIX_JOIN = ("مي", "می", "نمي", "نمی")
SUFFIX_JOIN = ("هایی", "هاي", "های", "ها", "ترین", "ترين", "تر", "اند", "ايم", "اید", "ات", "اش", "ام")


def _join_affixes(text: str) -> str:
    """پسوندهای جداشدهٔ فارسی را با نیم‌فاصله به واژه می‌چسباند."""
    words = text.split(" ")
    out: list[str] = []
    for w in words:
        if out and w in SUFFIX_JOIN and len(out[-1]) >= 2:
            prev = out[-1]
            if all("\u0600" <= ch <= "\u06FF" for ch in prev[-1]):
                out[-1] = prev + "\u200c" + w
                continue
        out.append(w)
    text = " ".join(out)
    # پیشوندهای فعلی: «مي شود» ← «مي‌شود»
    for pre in PREFIX_JOIN:
        text = re.sub(r"(?<![\u0600-\u06FF])" + pre + r" ([\u0600-\u06FF]{2,})",
                      lambda m: m.group(0).replace(" ", "\u200c"), text)
    return text


def polish(text: str) -> str:
    """اصلاح آسیب‌های رایجِ استخراج.

    • خطِ خرابِ ترتیب در PDFهای قرآن («س اورلدس اول»).
    • رقم‌های دو‌جهته که وارونه شده‌اند: در PDF «01» ذخیره شده ولی کتاب «۱۰»
      دارد. قاعده: دنبالهٔ دو رقمی که رقم دومش صفر است و در بافت فارسی آمده
      (نه اعشار، نه سال میلادی) برعکس می‌شود.
    """
    if not re.search(r"[\u0600-\u06FF]", text):
        return text                      # متن انگلیسی دست‌کاری نمی‌شود

    text = re.sub(r"س\s*اورل[^\n]{0,16}", "", text)
    # سرتیترهایی که در PDF معکوس ذخیره شده‌اند: «ردس سوم» → «درس سوم»
    text = re.sub(r"ر\s*د\s*س", "درس", text)
    text = re.sub(r"ف\s*ص\s*ل", "فصل", text)
    for bad, good in (("رد صراط", "در صراط"), ("رد ", "در "),
                      ("ازر دختر غور", "از درخت غرور"), ("تمخسر", "تمسخر"),
                      ("س دورمدس", "درس"), ("دورمدس", "درس"),
                      ("همٔهٔ", "همهٔ")):
        text = text.replace(bad, good)

    text = fix_arabic_marks(text)

    # «مي شد» ← «می‌شد» و «كتاب هاي» ← «كتاب‌های» (پیوند پسوندها)
    text = _join_affixes(text)

    # رقم‌های دوجهته که وارونه شده‌اند: «01» در PDF ← «۱۰» در کتاب
    to_fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    text = re.sub(r"(?<![\d۰-۹.])([1-9])0(?![\d۰-۹])",
                  lambda m: m.group(1).translate(to_fa) + "۰", text)
    text = re.sub(r"(?<![\d۰-۹.])0([1-9])(?![\d۰-۹])",
                  lambda m: m.group(1).translate(to_fa) + "۰", text)
    return text


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")


def js(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# هستهٔ ساختِ متن درس‌نامه از خط‌های کتاب
# ---------------------------------------------------------------------------
def build_body(pages: list[str], first: int, last: int,
               headings: list[str] | None = None,
               max_sections: int = 6, max_chars: int = 3000) -> str:
    """از صفحه‌های [first..last] یک متن درس‌نامه می‌سازد.

    ساختار: سرتیترها (خطوط کوتاهِ بی‌نقطه) + بندهای متن کتاب.
    """
    blocks: list[tuple[str, str]] = []          # ("h"/"p", text)
    for pno in range(first, last + 1):
        if pno >= len(pages):
            break
        for raw_line in pages[pno].split("\n"):
            line = polish(clean(raw_line))
            if not line:
                continue
            if (looks_garbled(line) or is_junk(line) or is_reversed_line(line)
                    or is_formula_fragment(line)):
                continue
            if is_heading(line):
                if blocks and blocks[-1][0] == "h":
                    blocks[-1] = ("h", collapse_repeats(blocks[-1][1] + " " + line))
                else:
                    blocks.append(("h", line))
            elif is_prose(line):
                if blocks and blocks[-1][0] == "p":
                    prev = blocks[-1][1]
                    sep = "" if prev.endswith("\u200c") else " "
                    blocks[-1] = ("p", prev + sep + line)
                else:
                    blocks.append(("p", line))

    # ادغام بندهای کوتاهِ پشت‌سرهم، حذف تکرار
    merged: list[tuple[str, str]] = []
    for kind, txt in blocks:
        txt = re.sub(r"[ ]{2,}", " ", txt).strip()
        if len(txt) < 30 and kind == "p":
            if merged and merged[-1][0] == "p":
                merged[-1] = ("p", merged[-1][1] + " " + txt)
                continue
        txt = collapse_repeats(txt)
        if merged and merged[-1][0] == kind and merged[-1][1].strip() == txt.strip():
            continue
        merged.append((kind, txt))

    # انتخاب بخش‌ها تا سقف حجم
    out: list[str] = []
    total = 0
    section = 0
    for kind, txt in merged:
        if kind == "h":
            section += 1
            if section > max_sections:
                break
            out.append(f"<h3>{esc(txt)}</h3>")
            continue
        if total + len(txt) > max_chars:
            # بند را در نقطهٔ جمله می‌بُریم
            room = max_chars - total
            if room < 160:
                break
            cut = txt[:room]
            dot = max(cut.rfind("."), cut.rfind("؟"), cut.rfind("!"))
            if dot > 120:
                cut = cut[:dot + 1]
            out.append(f"<p>{esc(cut)}</p>")
            break
        out.append(f"<p>{esc(txt)}</p>")
        total += len(txt)

    return "\n".join(out)


# ---------------------------------------------------------------------------
# یافتن انحراف شمارهٔ صفحهٔ چاپی از شمارهٔ صفحهٔ PDF
# ---------------------------------------------------------------------------
_FA2EN = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def page_offset(pages: list[str]) -> int:
    """«شمارهٔ صفحهٔ PDF + offset = شمارهٔ صفحهٔ چاپی»"""
    from collections import Counter
    c = Counter()
    for i, pg in enumerate(pages):
        lines = [ln.strip() for ln in pg.split("\n") if ln.strip()]
        if not lines:
            continue
        for cand in (lines[-1], lines[0]):
            val = cand.translate(_FA2EN)
            if re.fullmatch(r"\d{1,3}", val):
                diff = (i + 1) - int(val)
                if -20 <= diff <= 20:
                    c[diff] += 1
    return c.most_common(1)[0][0] if c else 0


def pdf_index(printed_page: int, offset: int) -> int:
    """شمارهٔ صفحهٔ چاپی → اندیس صفحه در فهرست صفحه‌ها."""
    return max(0, printed_page - offset - 1)


# ---------------------------------------------------------------------------
# یافتن صفحهٔ آغاز هر درس با جست‌وجوی عنوان آن در متن کتاب
# ---------------------------------------------------------------------------
PERSIAN_DIGITS_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def denorm(text: str) -> str:
    """نرمال‌سازی برای تطبیق: حذف اعراب، یکسان‌سازی ی/ک، حذف فاصله‌های تکراری."""
    text = text.translate(PERSIAN_DIGITS_EN)
    text = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", text)      # اعراب و کشیده
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ").replace("\u200a", " ")
    text = re.sub(r"[\u0640\s]+", " ", text)
    return text.strip()


def _match_subseq(body: str, chars: list[str]) -> bool:
    """آیا همهٔ نویسه‌های chars به ترتیب در body پیدا می‌شوند؟"""
    pos = 0
    for c in chars:
        k = body.find(c, pos)
        if k < 0:
            return False
        pos = k + 1
    return True


def find_heading_page(pages: list[str], title: str, start: int = 0) -> int | None:
    """صفحه‌ای که عنوان درس در آن آمده (نه صفحهٔ فهرست).

    تطبیق نویسه‌به‌نویسه و بدون فاصله انجام می‌شود تا شکستن کلمه بین سطرها
    («وم نایش» به‌جای «نمایش») هم پیدا شود.
    """
    needle = denorm(title)
    if len(needle) < 4:
        return None
    chars = [c for c in needle if c != " "][:38]
    for i in range(start, len(pages)):
        raw_page = pages[i]
        body = denorm(raw_page).replace(" ", "")
        # صفحه‌های فهرست: پر از نقطه‌چین یا نقطه
        if raw_page.count(".") > 40 or body.count(".") > 12:
            continue
        if _match_subseq(body, chars):
            return i
    return None


def build_body_en(pages: list[str], first: int, last: int,
                  max_chars: int = 3200,
                  head_title: str | None = None) -> str:
    """درس‌نامهٔ کتاب‌های انگلیسی (Prospect / Workbook).

    این کتاب‌ها گفتگو، تمرین و برچسب‌های کوتاه دارند و قاعده‌های متنِ فارسی
    (خطِ بلند = بند) روی آن‌ها جواب نمی‌دهد. اینجا هر خطِ خوانا می‌ماند و
    فقط چیدمانِ تکراری و سرصفحه/پاصفحه پاک می‌شود.
    """
    lines: list[str] = []
    for pno in range(first, last + 1):
        if pno >= len(pages):
            break
        for raw in pages[pno].split("\n"):
            ln = clean(raw)
            if not ln or looks_garbled(ln):
                continue
            if re.fullmatch(r"[\d٠-٩۰-۹\s]+", ln):           # شمارهٔ صفحه
                continue
            if re.fullmatch(r"[A-Za-z'’.\-\s]{1,3}", ln):     # «A» و تکه‌های تک‌حرفی
                continue
            if len(ln) < 3 and not ln.isalnum():
                continue
            ln = collapse_repeats(ln)                         # «Lesson 2: Travel Lesson 2: Travel»
            if lines and lines[-1] == ln:                     # تکرار ستون دوم
                continue
            # صفحهٔ عنوانِ خود درس: نام درس دوبار در صفحهٔ سایت می‌آید
            if head_title:
                low = ln.lower()
                tt = head_title.lower()
                if (low == tt or low == "lesson" or low == tt.replace(" and ", " & ")
                        or re.fullmatch(r"lesson\s*\d+\s*[:\-]?\s*" + re.escape(tt), low)):
                    continue
            lines.append(ln)

    # سرصفحه‌های تکراری («Lesson 2: Travel») فقط بار اول می‌آیند
    seen_head: dict[str, int] = {}
    kept: list[str] = []
    for ln in lines:
        low = ln.lower()
        if len(ln) < 40 and low in seen_head:
            seen_head[low] += 1
            if seen_head[low] > 1:
                continue
        else:
            seen_head[low] = 0
        kept.append(ln)

    out: list[str] = []
    total = 0
    for ln in kept:
        if total + len(ln) > max_chars and out:
            break
        out.append(ln)
        total += len(ln) + 1

    # هر خط جدا می‌ماند: گفتگو و تمرین کتاب ساختار سطری دارند
    html = []
    for ln in out:
        words = len(ln.split())
        if (words <= 5 and len(ln) <= 42
                and not ln.endswith((".", "?", "!", ":", "…"))
                and not re.match(r"^[A-Z][a-z]+:", ln)):
            html.append(f"<h3>{esc(ln)}</h3>")
        else:
            html.append(f"<p>{esc(ln)}</p>")
    return "\n".join(html)
