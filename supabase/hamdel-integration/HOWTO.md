# اتصال «درس‌یار» به پنل همدل

هدف: نمایش پیشرفت درس‌خواندن و نمرهٔ آزمون‌های دانش‌آموز داخل پنل همدل،
به‌طوری که دبیر وضعیت تحصیلی هر دانش‌آموز را ببیند. ورود با **همان شماره و رمز همدل**.

ساختار درس‌یار: **کتاب → فصل → درس → مبحث → کوییز مبحث → آزمون درس/فصل**.
کارت همدل همین سه سطح را نشان می‌دهد و برای هر آزمون **نمره از ۲۰، درصد و
تعداد درست از کل** را می‌آورد.

---

## پیش‌نیاز (انجام‌شده)

| مورد | وضعیت |
|---|---|
| تابع لبهٔ `darsyar-auth` روی پروژهٔ Supabase همدل | ✅ نسخهٔ ۸ فعال |
| جدول‌های `darsyar_progress` / `darsyar_attempts` / `darsyar_days` | ✅ ساخته شد |
| ستون `section_id` + `kind` روی `darsyar_progress` و `darsyar_attempts` | ✅ افزوده شد |
| کلید اصلی `darsyar_progress` → `(user_id, subject, lesson_id, section_id)` | ✅ تغییر کرد |
| ویوهای `darsyar_student_summary` / `darsyar_my_summary` / `darsyar_student_subjects` / `darsyar_section_summary` | ✅ ساخته شد |
| اعتبارسنجی روی `hamdel_records(collection='users')` | ✅ ۵۰۵ کاربر موجود |

> در جدول، آزمونِ سطح درس با `section_id = '-'` ذخیره می‌شود (NULL در کلید اصلی مجاز نیست).

---

## قدم ۱ — کپی کامپوننت

```bash
cp supabase/hamdel-integration/LearningProgress.tsx \
   /path/to/hamdel/src/components/LearningProgress.tsx
```

## قدم ۲ — افزودن به پنل

در `src/components/Shell.tsx`:

```tsx
import LearningProgress from "./LearningProgress";
```

و در فهرست ناوبری:

```tsx
import { GraduationCap } from "lucide-react";

const nav = [
  // … موارد موجود …
  { v: "learning", label: "درس‌یار", icon: <GraduationCap className="size-5" />, show: true },
];
```

نوع `View` را هم به‌روز کنید:

```ts
export type View = "chats" | … | "profile" | "learning";
```

و در بخش رندر:

```tsx
{view === "learning" && <LearningProgress token={token} viewer={user} />}
```

> `token` همان توکن نشست همدل است. اگر در `Shell` در دسترس نیست،
> از `localStorage.getItem("hamdel:token")` یا معادل همان پروژه استفاده کنید.

## قدم ۳ — میان‌بر در پروفایل

در `src/components/Profile.tsx` بعد از کارت کلاس:

```tsx
<a href="https://darsyar-five.vercel.app/index.html" target="_blank" rel="noopener"
   className="…">
   🎓 ورود به درس‌یار نهم
</a>
```

---

## نقش‌ها

| نقش | چه می‌بیند |
|---|---|
| `student` | کارت «پیشرفت من» — مبحث خوانده، کوییز مبحث، آزمون درس/فصل، میانگین از ۲۰، نوار هر کتاب، آخرین آزمون‌ها |
| `teacher` / `principal` / معاونان | جدول همهٔ دانش‌آموزان با ستون نمرهٔ از ۲۰ + تفکیک کوییز مبحث و آزمون درس + عملکرد هر کتاب + لینک به `/teacher.html` |

### قالب داده‌ای که کارت می‌خواند

```
POST /me          → { user, progress[], attempts[], days[], summary, subjects[] }
POST /teacher     → { rows[] (darsyar_student_summary), attempts[] }
```

`attempts[]`:

```json
{
  "subject": "math",
  "lesson_id": "l03",
  "section_id": "l03-s2",   // '-' یعنی آزمون سطح درس
  "kind": "section",        // section | lesson
  "pct": 78,
  "correct": 7,
  "total": 9,
  "created_at": "2026-11-20T…"
}
```

نمایش نمره: `nomre20(pct) = pct / 100 * 20` با یک رقم اعشار و ارقام فارسی.

---

## نکته‌های امنیتی

- کارت فقط با **توکن Bearer** کار می‌کند؛ کلید `service_role` هرگز به مرورگر نمی‌رود.
- دبیر فقط با نقش کادری پاسخ می‌گیرد (`STAFF` در تابع لبه)، بقیه ۴۰۳ می‌گیرند.
- CORS باز است ولی هر درخواست باید نشست معتبر داشته باشد.

---

## آدرس‌ها

- سایت درس‌یار: **`https://darsyar-five.vercel.app/`**
- صفحهٔ ورود: `/login.html`
- کارنامهٔ دانش‌آموز: `/progress.html`
- پنل دبیر: `/teacher.html`
- تابع لبه: `https://musmyiwumgeffafxsmdd.supabase.co/functions/v1/darsyar-auth`
