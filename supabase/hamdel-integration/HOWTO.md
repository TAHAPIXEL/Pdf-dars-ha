# اتصال «درس‌یار» به پنل همدل

هدف: نمایش پیشرفت درس‌خواندن و نمرهٔ آزمون‌های دانش‌آموز داخل پنل همدل،
به‌طوری که دبیر وضعیت تحصیلی هر دانش‌آموز را ببیند. ورود با **همان شماره و رمز همدل**.

## پیش‌نیاز (انجام‌شده)

| مورد | وضعیت |
|---|---|
| تابع لبهٔ `darsyar-auth` روی پروژهٔ Supabase همدل | ✅ نسخهٔ ۲ فعال |
| جدول‌های `darsyar_progress` / `darsyar_attempts` / `darsyar_days` | ✅ ساخته شد |
| ویوهای `darsyar_student_summary` / `darsyar_my_summary` / `darsyar_student_subjects` | ✅ ساخته شد |
| اعتبارسنجی روی `hamdel_records(collection='users')` | ✅ ۵۰۵ کاربر موجود |

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
<a href="https://darsyar.vercel.app/index.html" target="_blank" rel="noopener"
   className="…">
   🎓 ورود به درس‌یار نهم
</a>
```

## نقش‌ها

| نقش | چه می‌بیند |
|---|---|
| `student` | کارت «پیشرفت من» — درس خوانده، آزمون داده، میانگین، نوار هر کتاب |
| `teacher` / `principal` / معاونان | جدول همهٔ دانش‌آموزان + لینک به `/teacher.html` |

## نکته‌های امنیتی

- کارت فقط با **توکن Bearer** کار می‌کند؛ کلید `service_role` هرگز به مرورگر نمی‌رود.
- دبیر فقط با نقش کادری پاسخ می‌گیرد (`STAFF` در تابع لبه)، بقیه ۴۰۳ می‌گیرند.
- CORS باز است ولی هر درخواست باید نشست معتبر داشته باشد.

## آدرس‌ها

- سایت درس‌یار: `https://darsyar.vercel.app/`
- صفحهٔ ورود: `/login.html`
- کارنامهٔ دانش‌آموز: `/progress.html`
- پنل دبیر: `/teacher.html`
- تابع لبه: `https://musmyiwumgeffafxsmdd.supabase.co/functions/v1/darsyar-auth`
