#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استخراج متن کتاب‌های درسی PDF با بازسازی درستِ دوجهته (BiDi).

PDFهای فارسی، متن را به «ترتیب بصری» (راست‌به‌چپ) ذخیره می‌کنند؛ استخراج
معمولی (pypdf / get_text) ترتیب کلمه‌ها را وارونه می‌کند. این ابزار:

  ۱) حروف هر خط را بر اساس مختصات افقی از راست به چپ می‌چیند،
  ۲) بازه‌های لاتین/رقمی درون‌خطی را برمی‌گرداند،
  ۳) کمانک‌ها و نمادهای آینه‌ای را در بافت راست‌به‌چپ اصلاح می‌کند،
  ۴) ترکیب‌های «لا» را که به‌صورت الفِ صفرعرض + لام ذخیره شده‌اند بازسازی می‌کند.

کاربرد:
    python3 tools/extract_pdf_text.py "پایه-نهم/05-ریاضی-نهم.pdf" out.json
"""
from __future__ import annotations

import json
import re
import sys

import pymupdf

# حروفی که در ترکیب «لا» پیش از لام قرار می‌گیرند
ALEFS = set("اآأإٱ")
# کمانک‌ها در این PDFها به‌درستی (به ترتیب منطقی) ذخیره شده‌اند؛
# آینه کردن آن‌ها متن را خراب می‌کرد. فقط نویسه‌های کنترلی پاک می‌شوند.


def is_asii_run_char(c: str) -> bool:
    """حروف/ارقام/نمادهای لاتین که باید درون خط برعکس شوند."""
    return c.isascii() and (c.isalnum() or c in ".,:;%+-*/=^_@#$&|~`'\"\\")


def _fix_lam_alef(glyphs: list[tuple[float, float, float, str]]):
    """glyphs: [(x0, x1, y, char)] به ترتیب بصری (راست→چپ).

    در PDF، ترکیب «لا» به شکل یک گلیف ذخیره می‌شود و دو نویسه تولید می‌کند:
    یک الفِ صفرعرض در لبهٔ راستِ گلیف لام، و خودِ لام که کل عرض را می‌پوشاند.
    ترتیب منطقی درست «ل + ا» است، پس الف را به بعد از لام منتقل می‌کنیم.
    گاهی یک الفِ عادی هم در همسایگی هست، از این‌رو تا دو گلیف جلوتر را می‌بینیم.
    """
    i = 0
    n = len(glyphs)
    while i < n - 1:
        x0, x1, _y, c = glyphs[i]
        if c in ALEFS and (x1 - x0) <= 1.0:                 # الفِ صفرعرض
            moved = False
            for j in (i + 1, i + 2):
                if j < n and glyphs[j][3] == "ل" and abs(glyphs[j][1] - x0) <= 1.5:
                    glyphs.insert(j, glyphs.pop(i))         # الف → بعد از لام
                    i = j + 1
                    moved = True
                    break
            if moved:
                continue
        i += 1
    return glyphs


RTL_RANGES = ((0x0600, 0x06FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))


def _is_rtl_char(c: str) -> bool:
    o = ord(c)
    return any(a <= o <= b for a, b in RTL_RANGES)


def _has_rtl(glyphs) -> bool:
    return any(_is_rtl_char(g[3]) for g in glyphs)


def _paren_mismatch(text: str) -> bool:
    """اگر ترتیب کمانک‌ها نادرست باشد، یعنی خط باید برعکس شود."""
    depth, bad = 0, 0
    for c in text:
        if c in "([\u00ab":
            depth += 1
        elif c in ")]\u00bb":
            depth -= 1
            if depth < 0:
                bad += 1
                depth = 0
    return bad > 0


def rebuild_line(glyphs: list[tuple[float, float, float, str]],
                 direction: str | None = None) -> str:
    """یک خط را از روی مختصات گلیف‌ها بازمی‌سازد.

    جهت ذخیره‌سازی در این کتاب‌ها یکسان نیست: متن فارسی به ترتیب «چپ→راست»
    و متن انگلیسی به ترتیب «راست→چپ» ذخیره شده است. جهت از روی جهت غالبِ
    حروف همان خط تشخیص داده می‌شود.
    """
    glyphs = sorted(glyphs, key=lambda g: g[0])          # چپ → راست
    raw = "".join(g[3] for g in glyphs)
    if direction is None:
        direction = "rtl" if _has_rtl(glyphs) else "ltr"
    if direction == "rtl":
        glyphs = glyphs[::-1]
        glyphs = _fix_lam_alef(glyphs)
    raw = "".join(g[3] for g in glyphs)
    return re.sub(r"[ \u200a]{2,}", "  ", raw).strip()


def page_text(page) -> str:
    raw = page.get_text("rawdict")
    rows = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            glyphs = []
            for span in line["spans"]:
                for ch in span["chars"]:
                    c = ch["c"]
                    if c in "\n\r\t":
                        continue
                    x0, _y0, x1, _y1 = ch["bbox"]
                    glyphs.append((x0, x1, ch["origin"][1], c))
            if not glyphs:
                continue
            txt = rebuild_line(glyphs)
            if txt:
                rows.append((line["bbox"][1], txt))
    rows.sort(key=lambda t: t[0])
    return "\n".join(t for _, t in rows)


def extract(pdf_path: str) -> list[str]:
    doc = pymupdf.open(pdf_path)
    try:
        return [page_text(pg) for pg in doc]
    finally:
        doc.close()


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pages = extract(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        json.dump(pages, fh, ensure_ascii=False)
    print(f"{sys.argv[2]}: {len(pages)} pages, "
          f"{sum(len(p) for p in pages)} chars")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# استخراج ساختاری: متن + اندازهٔ قلم + پرچم توپُر بودن
# ---------------------------------------------------------------------------
def page_lines(page) -> list[dict]:
    """خط‌های صفحه با فرادادهٔ ساختاری.

    خروجی: [{"text", "size", "bold", "y"}] — برای تشخیص سرتیتر از متن.
    """
    raw = page.get_text("rawdict")
    rows = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            glyphs, sizes, bold = [], [], False
            for span in line["spans"]:
                fname = (span.get("font") or "").lower()
                flags = span.get("flags", 0)
                is_bold = "bold" in fname or bool(flags & 16)
                for ch in span["chars"]:
                    c = ch["c"]
                    if c in "\n\r\t":
                        continue
                    x0, _y0, x1, _y1 = ch["bbox"]
                    glyphs.append((x0, x1, ch["origin"][1], c))
                    sizes.append(span["size"])
                    if is_bold and c.strip():
                        bold = True
            if not glyphs:
                continue
            txt = rebuild_line(glyphs)
            if not txt:
                continue
            rows.append({
                "text": txt,
                "size": round(max(sizes), 1),
                "bold": bold,
                "y": round(line["bbox"][1], 1),
            })
    rows.sort(key=lambda r: r["y"])
    return rows


def extract_struct(pdf_path: str) -> list[list[dict]]:
    doc = pymupdf.open(pdf_path)
    try:
        return [page_lines(pg) for pg in doc]
    finally:
        doc.close()

# ---------------------------------------------------------------------------
# مسیر جایگزین: بازسازی با کلمه‌ها (برای صفحه‌هایی که ترتیب بلوک‌ها خراب است)
# ---------------------------------------------------------------------------
def page_words_rtl(page) -> str:
    """صفحه را از روی جعبهٔ هر «کلمه» بازسازی می‌کند.

    بعضی صفحه‌ها (داستان‌ها و شعرهای فارسی) بلوک‌هایشان ترتیب منطقی ندارد؛
    ولی خودِ کلمه‌ها مختصات درست دارند. با گروه‌بندی کلمه‌ها در سطرهای
    افقی و چیدن راست‌به‌چپ، متنِ خوانا بازمی‌گردد.
    """
    words = [w for w in page.get_text("words") if w[4].strip()]
    if not words:
        return ""
    rows: dict[int, list] = {}
    for w in words:
        rows.setdefault(round(w[1] / 6) * 6, []).append(w)
    out = []
    for y in sorted(rows):
        line = sorted(rows[y], key=lambda w: -w[2])
        parts: list[str] = []
        for w in line:
            tok = w[4]
            if tok == "\u200c":
                continue
            # «می ‌ شد» ← «می‌شد» (نیم‌فاصله به تک‌واژهٔ پیشین می‌چسبد)
            if parts and (w[0] - line[0][2] < 0):   # فقط برای پیوند نیم‌فاصله
                pass
            if parts and tok in ("‌",) :
                parts[-1] += "\u200c"
                continue
            parts.append(tok)
        out.append(_join_zwnj(" ".join(parts)))
    return "\n".join(out)


def _join_zwnj(line: str) -> str:
    """«مي ‌ شود» ← «مي‌شود»؛ «نقّاش ي» درست می‌ماند."""
    line = re.sub(r"\s+\u200c\s*", "\u200c", line)
    line = re.sub(r"\u200c\s+", "\u200c", line)
    return re.sub(r"\s{2,}", " ", line).strip()
