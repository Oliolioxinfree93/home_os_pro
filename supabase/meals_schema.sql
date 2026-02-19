-- Meals feature schema

create table if not exists public.children (
  id bigserial primary key,
  user_id text not null,
  child_name text not null,
  birthdate date,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.meal_feedback (
  id bigserial primary key,
  user_id text not null,
  child_id bigint references public.children(id) on delete set null,
  meal_name text not null,
  ingredients jsonb not null default '[]'::jsonb,
  ate boolean not null default true,
  liked boolean not null default true,
  rating int,
  notes text,
  created_at timestamptz not null default now()
);

alter table public.children enable row level security;
alter table public.meal_feedback enable row level security;

-- children policies
create policy if not exists "children_select_own"
on public.children for select
to authenticated
using (user_id = auth.uid()::text);

create policy if not exists "children_insert_own"
on public.children for insert
to authenticated
with check (user_id = auth.uid()::text);

create policy if not exists "children_update_own"
on public.children for update
to authenticated
using (user_id = auth.uid()::text)
with check (user_id = auth.uid()::text);

create policy if not exists "children_delete_own"
on public.children for delete
to authenticated
using (user_id = auth.uid()::text);

-- meal_feedback policies
create policy if not exists "meal_feedback_select_own"
on public.meal_feedback for select
to authenticated
using (user_id = auth.uid()::text);

create policy if not exists "meal_feedback_insert_own"
on public.meal_feedback for insert
to authenticated
with check (user_id = auth.uid()::text);

create policy if not exists "meal_feedback_update_own"
on public.meal_feedback for update
to authenticated
using (user_id = auth.uid()::text)
with check (user_id = auth.uid()::text);

create policy if not exists "meal_feedback_delete_own"
on public.meal_feedback for delete
to authenticated
using (user_id = auth.uid()::text);
