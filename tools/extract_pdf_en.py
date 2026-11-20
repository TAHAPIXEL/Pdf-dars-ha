#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""استخراج متن دو کتاب انگلیسی (Prospect 3 و Workbook) از PDF.

این کتاب‌ها انگلیسیِ چپ‌به‌راست‌اند و — برخلاف کتاب‌های فارسی — متن‌شان
با get_text("blocks") کامل و خوانا برمی‌گردد. مشکل فقط ترتیب است:
چیدمان چندستونه بلوک‌ها را به هم می‌ریزد (گفتگو، تمرین، برچسب).

راه‌حل: بلوک‌ها را سطری می‌چینیم (نوارهای ارتفاعی) و درون هر نوار از
چپ به راست؛ سرصفحه/پاصفحه کنار گذاشته می‌شود.

کاربرد:
    python3 tools/extract_pdf_en.py "پایه-نهم/09-زبان-انگلیسی-نهم.pdf" /tmp/txt3/english.json
"""
from __future__ import annotations

import json
import re
import sys

import pymupdf

# نویسه‌های مجاز متن انگلیسی
KEEP = re.compile(
    r"[^A-Za-z0-9\s.,;:!?'\u2019\"\u201c\u201d()\-\u2013\u2014/&%+=*#@$"
    r"\u22ef\u2026\u00ab\u00bb\u066a\u060c\u061f]"
)


def clean_block(text: str) -> str:
    t = text.replace("\t", " ")
    t = re.sub(r"[ \u00a0]{2,}", " ", t)
    t = KEEP.sub("", t)
    t = re.sub(r"\s*\n\s*", " ", t)
    return t.strip()


def page_text(page, height: float) -> str:
    blocks = [b for b in page.get_text("blocks") if b[6] == 0]      # فقط متن
    out = []
    for b in blocks:
        y0, y1, x0 = b[1], b[3], b[0]
        if y1 < height * 0.055 or y0 > height * 0.945:              # سرصفحه/پاصفحه
            continue
        t = clean_block(b[4])
        if not t:
            continue
        out.append((y0, x0, t))
    # گروه‌بندی سطری: بلوک‌های هم‌ارتفاع پشت‌سرهم، درون نوار از چپ به راست
    out.sort(key=lambda r: (r[0], r[1]))
    rows, band = [], []
    for item in out:
        if band and item[0] - band[0][0] > 14:
            rows.append(band)
            band = []
        band.append(item)
    if band:
        rows.append(band)
    lines = []
    for row in rows:
        row.sort(key=lambda r: r[1])
        lines.extend(t for _y, _x, t in row)
    return "\n".join(lines)


def extract(pdf_path: str):
    doc = pymupdf.open(pdf_path)
    return [page_text(pg, pg.rect.height) for pg in doc]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    pages = extract(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        json.dump(pages, fh, ensure_ascii=False)
    print(f"{len(pages)} صفحه → {sys.argv[2]}")


if __name__ == "__main__":
    main()
