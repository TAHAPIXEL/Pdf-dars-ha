#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تولید دادهٔ درس‌یار نهم از روی متن PDFهای کتاب درسی.

هر درس‌نامه فقط از خط‌های همان صفحه‌های کتاب ساخته می‌شود؛ هیچ متنی از
بیرون کتاب اضافه نمی‌شود. شمارهٔ صفحهٔ کتاب هم در هر درس‌نامه درج می‌گردد.

اجرا:
    python3 tools/gen_site_data.py            # همهٔ درس‌ها
    python3 tools/gen_site_data.py math farsi # فقط چند درس
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_content as M   # noqa: E402

ROOT = M.ROOT
CURR = M.CURR
OUT = os.path.join(ROOT, "assets", "data")

MAX_CHARS = 2600          # سقف نویسهٔ متن هر درس‌نامه

# صفحه‌های آغاز فصل در علوم تجربی (بازبینی‌شده روی صفحه‌های جداکنندهٔ PDF)
SCIENCE_CH_START = {1: 1, 2: 13, 3: 25, 4: 39, 5: 51, 6: 63, 7: 73, 8: 83,
                    9: 95, 10: 107, 11: 121, 12: 131, 13: 141, 14: 151, 15: 163}

# اندیس صفحهٔ آغاز هر درس در کتاب‌های انگلیسی (از خود PDF)
EN_START = {"english": {1: 9, 2: 23, 3: 48, 4: 63, 5: 85, 6: 97},
            "english-workbook": {1: 1, 2: 17, 3: 30, 4: 44, 5: 58, 6: 72}}


# ---------------------------------------------------------------------------
# ورودی‌ها
# ---------------------------------------------------------------------------
def pages_of(key: str) -> list[str]:
    path = os.path.join(M.TXT_DIR, M.BOOKS[key] + ".json")
    return json.load(open(path, encoding="utf-8"))


def flatten(cur: dict) -> list[dict]:
    """فصل‌ها → فهرست تخت درس‌ها (ترتیب کتاب، با برچسب فصل)."""
    if "lessons" in cur:
        return [dict(it) for it in cur["lessons"]]
    out = []
    for ch in cur["chapters"]:
        subs = ch.get("lessons")
        if subs:
            for sub in subs:
                out.append({"title": sub["title"], "page": sub.get("page", ch["page"]),
                            "chapter": ch["title"], "chapter_n": ch["n"]})
        else:
            out.append({"title": ch["title"], "page": ch["page"],
                        "chapter": ch["title"], "chapter_n": ch["n"]})
    return out


# ---------------------------------------------------------------------------
# یافتن صفحه‌ها
# ---------------------------------------------------------------------------
def _is_toc(raw: str) -> bool:
    """صفحهٔ فهرست؟ (شماره‌های پشت‌سرهم یا نقطه‌چین فراوان)"""
    if raw.count(".") > 40 or raw.count("....") > 2:
        return True
    nums = re.findall(r"(?<![\d\u06F0-\u06F9\u0660-\u0669])\d{1,3}(?![\d\u06F0-\u06F9])", raw)
    if len(nums) >= 8 and len(raw) < 1200:
        return True
    # صفحهٔ عنوان درس: خیلی کوتاه و بی‌بندِ متنی
    lines = [ln for ln in raw.split("\n") if ln.strip()]
    return len(lines) <= 3 and len(raw) < 220


STOPW = {"و", "ها", "های", "در", "به", "از", "با", "را", "که", "این", "آن",
          "the", "and", "of", "to", "a", "an", "in"}


def _words(t: str) -> list[str]:
    """واژه‌های معنادار عنوان (بی‌واژه‌های دستوری و کوتاه)."""
    ws = [w for w in M.denorm(t).split(" ") if w]
    core = [w for w in ws if len(w) > 2 and w not in STOPW]
    return core or ws


def index_of_printed(pages, printed: int, offset: int) -> int | None:
    """اندیسی که شمارهٔ چاپی صفحه‌اش با printed برابر است."""
    for d in range(0, 4):
        for i in (printed + offset - 1 + d, printed + offset - 1 - d,
                  printed - 1 + d, printed - 1 - d):
            if not (0 <= i < len(pages)):
                continue
            lines = [ln.strip() for ln in pages[i].split("\n") if ln.strip()]
            # شمارهٔ صفحه در حاشیهٔ پایین است، نه خطِ عنوان در بالای صفحه
            for cand in (lines[-1] if lines else "",):
                if cand.translate(M.PERSIAN_DIGITS_EN) == str(printed):
                    return i
    return None


def page_label(pages, i: int, offset: int) -> int:
    """شمارهٔ چاپی صفحه؛ اگر روی صفحه نبود، از انحراف استفاده می‌شود."""
    lines = [ln.strip() for ln in pages[i].split("\n") if ln.strip()]
    if lines:
        val = lines[-1].translate(M.PERSIAN_DIGITS_EN)
        if re.fullmatch(r"\d{1,3}", val):
            return int(val)
        val = lines[0].translate(M.PERSIAN_DIGITS_EN)
        if re.fullmatch(r"\d{1,3}", val) and len(lines) > 2:
            return int(val)
    return i + 1 - offset


def _title_ok(pages, i: int, ws: list[str]) -> bool:
    """آیا عنوانِ ws در صفحهٔ i آمده است؟"""
    raw = pages[i]
    if _is_toc(raw):
        return False
    body = M.denorm(raw)
    need = max(1, len(ws) // 2)
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    for k, ln in enumerate(lines):
        if not ln.startswith(ws[0]):
            continue
        ctx = ln + " " + (lines[k + 1] if k + 1 < len(lines) else "")
        if sum(1 for w in ws if w in ctx) >= need:
            return True
    compact = body.replace("\n", " ")
    pos = compact.find(ws[0])
    while pos >= 0:
        if sum(1 for w in ws if w in compact[pos:pos + 60]) >= need:
            return True
        pos = compact.find(ws[0], pos + 1)
    # عنوانِ چسبیده به شمارهٔ درس: «درس 4آب فراوان، هوای پاک»
    m = re.search(r"(?:درس|فصل|Lesson)\s*[\d۰-۹٠-٩]{1,2}", compact)
    if m:
        tail = compact[m.end(): m.end() + 80]
        if sum(1 for w in ws if w in tail) >= need:
            return True
    return False


def find_lesson_page(pages, title: str, printed_page: int, offset: int,
                     start: int = 0) -> int | None:
    """صفحهٔ آغاز درس: اول با شمارهٔ چاپی، بعد با تطبیق عنوان."""
    ws = _words(title)
    anchor = index_of_printed(pages, printed_page, offset)
    if anchor is not None and _is_toc(pages[anchor]):
        anchor = None
    if anchor is not None and anchor >= start:
        if not ws or _title_ok(pages, anchor, ws):
            return anchor
        for d in range(1, 3):
            for i in (anchor + d, anchor - d):
                if start <= i < len(pages) and (not ws or _title_ok(pages, i, ws)):
                    return i
        return anchor
    if not ws:
        return None
    for i in range(start, len(pages)):
        if _title_ok(pages, i, ws):
            return i
    return None


# ---------------------------------------------------------------------------
# پرسش‌سازی (فارسی)
# ---------------------------------------------------------------------------
STOP = set("""است که را این در از با برای می های شود کرد بود هم آن ها بر به یا
تا نیز خود کنید دهید بین شد آنها او وی ما شما ایشان یک دو سه چه کدام چرا
چگونه زیرا ولی اما اگر چون پس همهٔ هر باید نباید می‌توان می‌شود داشته دارد
دارند باشد باشند می‌باشد مثل مثال مانند طور طوری دربارهٔ روی زیر کند کنند
کنیم است. کند. کنند. کند، شود، کرد، داد، شد، آن‌ها برخی دیگر وقتی حال
هیچ بسیار همه ترین طور، مورد، انواع، شامل، وجود، عنوان، طریق، جهت، صورت
خواهد می‌کند می‌دهد می‌گیرد می‌دهند می‌شوند
""".split())


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.(?=[\u0600-\u06FF])", ". ", text)
    parts = re.split(r"(?<=[.!؟])\s+", text)
    out = []
    for p in parts:
        p = p.strip()
        if out and len(out[-1]) > 90 and len(p) > 12 and p[0] not in \
                "اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی":
            out[-1] += " " + p
            continue
        out.append(p)
    return [p for p in out if len(p) > 38]


def _key_phrase(sent: str, freq: dict) -> str | None:
    """عبارت کلیدیِ محتوایی: ۲–۳ کلمهٔ پرمعنا که در درس هم تکرار شده است.

    اگر جمله کوتاه باشد (پرسش‌های کتاب) هنوز عبارتِ چندکلمه‌ای ارزش آزمون
    دارد؛ فقط تکرار شرط ترجیح است، نه شرط لازم.
    """
    words = re.findall(r"[\u0600-\u06FF\u200c]{3,}", sent)
    best = None
    for n in (3, 2):
        for i in range(len(words) - n + 1):
            grp = words[i:i + n]
            if any(w in STOP for w in grp):
                continue
            ph = " ".join(grp).strip("،,؛: ")
            if not (8 <= len(ph) <= 34):
                continue
            score = sum(freq.get(w, 0) for w in grp)
            score += len(ph) / 12.0                  # عبارتِ روشن‌تر بهتر
            if sent.strip().startswith(ph):
                score -= 4
            if score <= 0:
                continue
            if best is None or score > best[0]:
                best = (score, ph)
    return best[1] if best else None


def _phrases(text: str) -> list[str]:
    words = re.findall(r"[\u0600-\u06FF\u200c]{3,}", text)
    out, seen = [], set()
    for i in range(len(words) - 1):
        for n in (3, 2):
            grp = words[i:i + n]
            if len(grp) < n or any(w in STOP for w in grp):
                continue
            ph = " ".join(grp).strip("،,؛: ")
            if 9 <= len(ph) <= 36 and ph not in seen:
                seen.add(ph)
                out.append(ph)
    return out


def quizzes_from_prompts(title: str, body_html: str, limit: int = 4) -> list[dict]:
    """پرسش از «تمرین‌های شماره‌دارِ خود کتاب» وقتی متنِ روان کم است.

    صورت تمرین‌ها در صفحه‌های کتاب با شماره می‌آید (١ــ ، 2ــ ، 3ــ). این
    تابع همان صورت‌ها را جدا می‌کند و گزینه‌های نادرست را از عنوان‌های
    واژگانیِ همان درس می‌سازد. منبعِ همه‌چیز، خود کتاب است.
    """
    plain = re.sub(r'<div class="box note">.*?</div>', "\n", body_html, flags=re.S)
    plain = re.sub(r'<div class="box tip">.*?</div>', "\n", plain, flags=re.S)
    plain = re.sub(r"<[^>]+>", "\n", plain)
    prompts = []
    for ln in plain.split("\n"):
        t = ln.strip()
        if len(t) < 46:
            continue
        if not re.match(r"^[\u0660-\u06F9\d]{1,2}\s*[ــ\-–]", t):
            continue
        t = re.sub(r"^[\u0660-\u06F9\d]{1,2}\s*[ــ\-–]\s*", "", t)
        if 30 <= len(t) <= 200:
            prompts.append(t)
    if not prompts:
        return []
    vocab = [w for w in dict.fromkeys(re.findall(r"[\u0600-\u06FF\u200c]{4,}", plain))
             if w not in STOP]
    out = []
    for i, pr in enumerate(prompts[:limit]):
        if len(vocab) < 3:
            break
        opts = [f"از تمرین‌های کتاب، {title}", "در کتاب این درس نیامده است",
                "فقط در پایهٔ هشتم آمده", "این تمرین حذف شده است"]
        rot = i % 4
        opts = opts[rot:] + opts[:rot]
        out.append({
            "q": "این صورتِ تمرین در کدام درسِ کتاب آمده است؟<br>"
                 f'<span style="opacity:.85">«{pr[:170]}»</span>',
            "opts": opts,
            "a": opts.index(f"از تمرین‌های کتاب، {title}"),
            "tag": title,
            "why": f"این صورتِ تمرین، از تمرین‌های درس «{title}» در کتاب درسی است.",
        })
    return out


def quizzes_from_text(title: str, plain: str, limit: int = 4) -> list[dict]:
    """پرسش جای‌خالی از جمله‌های خود کتاب، با گزینه‌هایی از همان درس."""
    sents = _sentences(plain)
    if len(sents) < 1:
        return []
    pool = _phrases(plain)
    if len(pool) < 4:
        return []
    freq: dict[str, int] = {}
    for w in re.findall(r"[\u0600-\u06FF\u200c]{3,}", plain):
        freq[w] = freq.get(w, 0) + 1

    out, used = [], set()
    for s in sents:
        ph = _key_phrase(s, freq)
        if not ph or ph in used:
            continue
        q = s.replace(ph, "ــــــــ", 1)
        if "ــــــــ" not in q:
            continue
        used.add(ph)
        cands = [c for c in pool
                 if c not in ph and ph not in c
                 and not (set(c.split()) & set(ph.split()))
                 and 0.6 <= len(c) / max(1, len(ph)) <= 1.7]
        if len(cands) < 3:
            continue
        if len(cands) < 3:
            continue
        wrong = [cands[len(cands) // 5],
                 cands[len(cands) // 2],
                 cands[-max(1, len(cands) // 5)]]
        opts = [ph, *wrong]
        # چرخش منظم تا پاسخ درست یکنواخت بین چهار گزینه پخش شود
        rot = len(out) % 4
        opts = opts[rot:] + opts[:rot]
        out.append({
            "q": "جای خالی را با عبارت درست کتاب پر کنید:<br>"
                 f'<span style="opacity:.85">{q}</span>',
            "opts": opts,
            "a": opts.index(ph),
            "tag": title,
            "why": f"کتاب می‌گوید: «{s}»",
        })
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# پرسش‌سازی (انگلیسی)
# ---------------------------------------------------------------------------
EN_STOP = set("""a an the is are am was were be been to of in on at for with
and or but not no yes this that these those there here it its it's i you he
she we they me him her us them my your his their our do does did done have
has had can could will would should may might must what who when where why
how which whose please thank thanks now then so very really also too just
about from by as if all any some each every more most much many few
""".split())


def en_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.?!])\s+", text)
    return [p.strip() for p in parts
            if 30 <= len(p.strip()) <= 190 and p.strip().count(" ") >= 5]


def quizzes_en(title: str, plain: str, limit: int = 4) -> list[dict]:
    """جای خالی از جمله‌های انگلیسیِ خود کتاب."""
    sents = en_sentences(plain)
    pool = [w for w in set(re.findall(r"[A-Za-z][A-Za-z'’-]{3,}", plain))
            if w.lower() not in EN_STOP]
    pool.sort(key=lambda w: (-len(w), w))
    out, used = [], set()
    for s in sents:
        cand = [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]{3,}", s)
                if w.lower() not in EN_STOP and 4 <= len(w) <= 12]
        if not cand:
            continue
        target = cand[len(cand) // 2]
        if target in used:
            continue
        used.add(target)
        q = s.replace(target, "______", 1)
        if "______" not in q:
            continue
        others = {x.lower() for x in re.findall(r"[A-Za-z]{3,}", s)}
        wrong = [w for w in pool
                 if w.lower() != target.lower()
                 and w.lower() not in others
                 and abs(len(w) - len(target)) <= 3][:9]
        if len(wrong) < 9:
            continue
        opts = [target, wrong[0], wrong[3], wrong[7]]
        rot = len(out) % 4
        opts = opts[rot:] + opts[:rot]
        out.append({
            "q": "Complete the sentence from the book:<br>"
                 f'<span style="opacity:.85">{q}</span>',
            "opts": opts,
            "a": opts.index(target),
            "tag": title,
            "why": f"The book says: “{s}”",
        })
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# ساخت درس‌نامه
# ---------------------------------------------------------------------------
def body_with_pages(pages, a: int, b: int, offset: int,
                    head_title: str | None = None,
                    max_chars: int = MAX_CHARS) -> str:
    html = M.build_body(pages, a, b, max_chars=max_chars)
    if not html:
        return ""
    first, last = page_label(pages, a, offset), page_label(pages, b, offset)
    if last < first:
        last = first
    span = (f"صفحهٔ {M.fa(first)}" if first == last
            else f"صفحه‌های {M.fa(first)} تا {M.fa(last)}")
    src = ('<div class="box note"><div class="bt">📖 از خود کتاب درسی</div>'
           f'<p>همهٔ مطالب این درس‌نامه، بندبه‌بند از <b>{span}</b> کتاب گرفته شده است.</p></div>')
    head = f"<h3>{M.esc(head_title)}</h3>\n" if head_title else ""
    return head + src + "\n" + html


def plain_of(html: str) -> str:
    """متنِ خوانایِ کتاب از HTML درس‌نامه (بدون کارتِ منبع و سرتیترِ خودمان)."""
    body = re.sub(r'<div class="box note">.*?</div>', " ", html, flags=re.S)
    body = re.sub(r'<div class="box tip">.*?</div>', " ", body, flags=re.S)
    body = re.sub(r"<h3>[^<]*</h3>", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"همهٔ مطالب این درس‌نامه[^.]*\.", " ", body)
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def lede_of(key: str, lessons: list[dict]) -> str:
    titles = "، ".join(l["title"] for l in lessons[:3])
    return (f"مستقیماً از کتاب درسی {M.META[key]['full']} — {M.fa(len(lessons))} درس، "
            f"از «{titles}» تا «{lessons[-1]['title']}».")


def topic_quizzes(title: str, body_html: str, other_titles: list[str],
                  limit: int = 2) -> list[dict]:
    """پرسش «موضوعِ این درس» از سرتیترهای خودِ همان درسِ کتاب.

    صورت پرسش از نام درس، و گزینهٔ درست از سرتیترِ داخل همان درس گرفته
    می‌شود؛ گزینه‌های نادرست، سرتیترهای درس‌های دیگرِ همان کتاب‌اند. همه
    از خودِ PDF می‌آیند.
    """
    heads = [t for t in re.findall(r"<h3>(.*?)</h3>", body_html)
             if t and len(t) > 6 and t != title]
    heads = [h for h in heads if not re.match(r"^(فصل|درس)\s", h)]
    if not heads:
        return []
    pool = [t for t in other_titles if t and t != title]
    out = []
    for i, h in enumerate(heads[:limit]):
        if len(pool) < 3:
            break
        opts = [h, pool[i % len(pool)], pool[(i + 3) % len(pool)], pool[(i + 5) % len(pool)]]
        rot = i % 4
        opts = opts[rot:] + opts[:rot]
        out.append({
            "q": f"کدام موضوع در درس «{title}» آمده است؟",
            "opts": opts,
            "a": opts.index(h),
            "tag": title,
            "why": f"سرتیتر «{h}» در همین درس از کتاب آمده است.",
        })
    return out


def build_subject(key: str) -> dict:
    pages = pages_of(key)
    info = M.META[key]
    items = flatten(CURR[key])
    off = M.page_offset(pages)

    lessons, quizzes = [], {}
    cursor = 0
    for idx, it in enumerate(items):
        sid = f"l{idx + 1:02d}"

        start = None
        if key == "science" and it.get("chapter_n") in SCIENCE_CH_START:
            start = SCIENCE_CH_START[it["chapter_n"]] - 1
        elif key in EN_START:
            start = EN_START[key].get(idx + 1)
        if start is None:
            guessed = max(0, it.get("page", 1) + off - 1)
            ws = _words(it["title"])
            # اگر همان صفحهٔ فهرست، عنوان را دارد، همان را بردار
            if guessed < len(pages) and (not ws or _title_ok(pages, guessed, ws)) \
                    and guessed >= cursor - 1:
                start = guessed
            elif guessed + 1 < len(pages) and (not ws or _title_ok(pages, guessed + 1, ws)) \
                    and guessed + 1 >= cursor - 1:
                start = guessed + 1
            else:
                start = find_lesson_page(pages, it["title"], it.get("page", 1), off,
                                         start=cursor)
        if start is None:
            start = max(0, it.get("page", 1) + off - 1)
        # صفحه‌ها باید صعودی باشند؛ اگر تکراری/عقب بود یک صفحه جلو برو
        if lessons and start <= cursor - 1:
            start = cursor
        cursor = max(cursor, start + 1)

        nxt = None
        if idx + 1 < len(items):
            nitem = items[idx + 1]
            if key == "science" and nitem.get("chapter_n") in SCIENCE_CH_START:
                nxt = SCIENCE_CH_START[nitem["chapter_n"]] - 1
            elif key in EN_START:
                nxt = EN_START[key].get(idx + 2)
            else:
                nxt = find_lesson_page(pages, nitem["title"],
                                       nitem.get("page", 1), off, start=start + 1)
        end = (nxt - 1) if (nxt and nxt > start) else min(start + 5, len(pages) - 1)
        if end < start:
            end = start

        body = body_with_pages(pages, start, end, off, head_title=it["title"])
        if len(body) < 420:
            body = body_with_pages(pages, start, min(end + 2, len(pages) - 1), off,
                                   head_title=it["title"])

        lessons.append({"id": sid, "n": idx + 1, "title": it["title"],
                        "page": M.fa(page_label(pages, start, off)), "body": body})

        if key in ("english", "english-workbook"):
            qs = quizzes_en(it["title"], plain_of(body), limit=4)
        else:
            qs = quizzes_from_text(it["title"], plain_of(body), limit=4)
        if len(qs) < 2:                       # کمکی: از تمرین‌های شماره‌دار کتاب
            extra = quizzes_from_prompts(it["title"], body, limit=4 - len(qs))
            have = {q["q"] for q in qs}
            qs = qs + [q for q in extra if q["q"] not in have]
        if len(qs) < 2:                       # کمکی: موضوع‌های خودِ درس
            all_titles = [x["title"] for x in items]
            extra = topic_quizzes(it["title"], body, all_titles, limit=2 - len(qs))
            have = {q["q"] for q in qs}
            qs = qs + [q for q in extra if q["q"] not in have]
        if qs:
            quizzes[sid] = qs

    return {
        "key": key, "name": info["name"], "full": info["full"], "icon": info["icon"],
        "accent": info["accent"], "accentDeep": info["accentDeep"],
        "lede": lede_of(key, lessons),
        "lessons": lessons, "quizzes": quizzes,
    }


# ---------------------------------------------------------------------------
# نوشتن فایل دادهٔ جاوااسکریپت
# ---------------------------------------------------------------------------
def js_str(s: str) -> str:
    return ('"' + s.replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", "\\n") + '"')


def js_tpl(s: str) -> str:
    s = s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    return "`" + s + "`"


def write_js(d: dict) -> str:
    nq = sum(len(v) for v in d["quizzes"].values())
    L = ["/* ============================================================",
         f"   {d['name']} — محتوای درس‌نامه و آزمون",
         f"   منبع: {d['full']} (PDF کتاب درسی پایه نهم)",
         f"   {M.fa(len(d['lessons']))} درس · {M.fa(nq)} پرسش",
         "   ============================================================ */",
         "window.CONTENT = window.CONTENT || {};",
         "",
         f"window.CONTENT[{js_str(d['key'])}] = {{",
         f"  key: {js_str(d['key'])},",
         f"  name: {js_str(d['name'])},",
         f"  full: {js_str(d['full'])},",
         f"  icon: {js_str(d['icon'])},",
         f"  accent: {js_str(d['accent'])},",
         f"  accentDeep: {js_str(d['accentDeep'])},",
         f"  lede: {js_str(d['lede'])},",
         "",
         "  lessons: ["]
    for l in d["lessons"]:
        L.append(f'    {{ id: {js_str(l["id"])}, n: {l["n"]}, '
                 f'title: {js_str(l["title"])}, page: {js_str(l["page"])},')
        L.append(f'      body: {js_tpl(l["body"])} }},')
    L.append("  ],")
    L.append("")
    L.append("  quizzes: {")
    for sid, qs in d["quizzes"].items():
        L.append(f"    {js_str(sid)}: [")
        for q in qs:
            opts = ", ".join(js_str(o) for o in q["opts"])
            L.append(f'      {{ q: {js_str(q["q"])}, opts: [{opts}], a: {q["a"]}, '
                     f'tag: {js_str(q["tag"])}, why: {js_str(q["why"])} }},')
        L.append("    ],")
    L.append("  },")
    L.append("};")
    L.append("")
    return "\n".join(L)


def emit(key: str) -> dict:
    d = build_subject(key)
    with open(os.path.join(OUT, key + ".js"), "w", encoding="utf-8") as fh:
        fh.write(write_js(d))
    return d


def main(argv: list[str]) -> None:
    keys = argv or list(M.BOOKS)
    os.makedirs(OUT, exist_ok=True)
    tl = tq = 0
    for k in keys:
        d = emit(k)
        nq = sum(len(v) for v in d["quizzes"].values())
        tl += len(d["lessons"])
        tq += nq
        print(f"  ✓ {k:18s} lessons={len(d['lessons']):2d} questions={nq:3d}")
    print(f"\nمجموع: {tl} درس‌نامه، {tq} پرسش — همه از متن PDFها")


if __name__ == "__main__":
    main(sys.argv[1:])
