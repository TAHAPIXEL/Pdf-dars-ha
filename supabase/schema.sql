-- ============================================================================
--  درس‌یار نهم — جدول‌های پیشرفت، در همان دیتابیس «همدل»
--  کاربران و نشست‌ها از خودِ همدل خوانده می‌شوند (hamdel_records / hamdel_sessions)
--  تا دانش‌آموز با همان شماره و رمز همدل وارد درس‌یار شود و یک نشست داشته باشد.
-- ============================================================================

create table if not exists public.darsyar_progress (
  user_id    text        not null,
  subject    text        not null,
  lesson_id  text        not null,
  read       boolean     not null default false,
  read_at    timestamptz,
  best_pct   integer,
  last_pct   integer,
  tries      integer     not null default 0,
  xp         integer     not null default 0,
  mode       text        not null default 'normal',
  updated_at timestamptz not null default now(),
  primary key (user_id, subject, lesson_id)
);

create index if not exists darsyar_progress_subject_idx
  on public.darsyar_progress (subject, lesson_id);

create table if not exists public.darsyar_attempts (
  id         text        primary key,
  user_id    text        not null,
  subject    text        not null,
  lesson_id  text        not null,
  pct        integer     not null,
  correct    integer,
  total      integer,
  mode       text,
  created_at timestamptz not null default now()
);

create index if not exists darsyar_attempts_user_idx
  on public.darsyar_attempts (user_id, created_at desc);

create table if not exists public.darsyar_days (
  user_id text not null,
  day     date not null,
  xp      integer not null default 0,
  primary key (user_id, day)
);

-- ---------------------------------------------------------------------------
--  نمای آماده برای پنل دبیر در سایت همدل
--  هر ردیف = یک دانش‌آموز پایه نهم با خلاصهٔ پیشرفت و معدل آزمون‌ها
-- ---------------------------------------------------------------------------
create or replace view public.darsyar_student_summary as
with students as (
  select r.id                                 as user_id,
         r.data->>'firstName'                 as first_name,
         r.data->>'lastName'                  as last_name,
         r.data->>'phone'                     as phone,
         r.data->>'grade'                     as grade,
         r.data->>'section'                   as section
    from public.hamdel_records r
   where r.collection = 'users'
     and r.deleted = false
     and coalesce(r.data->>'role', 'student') = 'student'
),
p as (
  select user_id,
         count(*) filter (where read)                    as lessons_read,
         count(*) filter (where best_pct is not null)    as quizzes_taken,
         round(avg(best_pct))                            as avg_best_pct,
         max(updated_at)                                 as last_active,
         sum(xp)                                         as xp
    from public.darsyar_progress
   group by user_id
),
a as (
  select user_id,
         round(avg(pct))      as avg_attempt_pct,
         count(*)             as attempts
    from public.darsyar_attempts
   group by user_id
)
select s.user_id,
       s.first_name,
       s.last_name,
       s.phone,
       s.grade,
       s.section,
       coalesce(p.lessons_read, 0)    as lessons_read,
       coalesce(p.quizzes_taken, 0)   as quizzes_taken,
       p.avg_best_pct,
       a.avg_attempt_pct,
       coalesce(a.attempts, 0)        as attempts,
       coalesce(p.xp, 0)              as xp,
       p.last_active
  from students s
  left join p on p.user_id = s.user_id
  left join a on a.user_id = s.user_id;

grant select on public.darsyar_student_summary to anon, authenticated;

-- ============================================================================
--  امنیت: دادهٔ درس‌یار فقط از راه تابع لبه خوانده می‌شود
--  (کلید anon هیچ دسترسی مستقیمی به جدول‌ها یا ویوها ندارد)
-- ============================================================================
revoke all on public.darsyar_progress          from anon, authenticated;
revoke all on public.darsyar_attempts          from anon, authenticated;
revoke all on public.darsyar_days              from anon, authenticated;
revoke all on public.darsyar_student_summary   from anon, authenticated;
revoke all on public.darsyar_student_subjects  from anon, authenticated;
revoke all on public.darsyar_my_summary        from anon, authenticated;

alter table public.darsyar_progress enable row level security;
alter table public.darsyar_attempts enable row level security;
alter table public.darsyar_days     enable row level security;
