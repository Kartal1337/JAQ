-- AI SDR Assistant — initial schema
-- Run against a Supabase Postgres project. Auth users live in auth.users.
-- Every app table is scoped per-user via Row Level Security (RLS).

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- profiles: 1:1 with auth.users, holds plan + usage counters
-- ---------------------------------------------------------------------------
create table if not exists profiles (
  id                  uuid primary key references auth.users(id) on delete cascade,
  email               text not null,
  company_name        text,
  plan                text not null default 'trial',   -- trial|starter|growth|pro
  leads_quota_used    int  not null default 0,         -- resets monthly via cron
  emails_sent_used    int  not null default 0,
  stripe_customer_id  text,
  created_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- sending_accounts: how a user sends mail (Gmail OAuth / SMTP / Resend)
-- ---------------------------------------------------------------------------
create table if not exists sending_accounts (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references profiles(id) on delete cascade,
  provider            text not null,                   -- gmail|smtp|resend
  from_email          text not null,
  oauth_refresh_token text,                            -- store encrypted at rest
  smtp_config         jsonb,                           -- store encrypted at rest
  daily_cap           int  not null default 20,
  is_verified         boolean not null default false,
  created_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- campaigns: one targeting definition ("dentists in Austin TX")
-- ---------------------------------------------------------------------------
create table if not exists campaigns (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references profiles(id) on delete cascade,
  name                text not null,
  target_query        text not null,                   -- natural language target
  location            text,
  offer               text,                            -- what the user sells (feeds the AI)
  status              text not null default 'draft',   -- draft|finding|ready|active|paused|done
  sending_account_id  uuid references sending_accounts(id) on delete set null,
  follow_up_days      int  not null default 3,
  send_window         jsonb not null default '{"start":9,"end":17,"tz":"America/Chicago"}',
  created_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- leads: scraped prospects
-- ---------------------------------------------------------------------------
create table if not exists leads (
  id                  uuid primary key default gen_random_uuid(),
  campaign_id         uuid not null references campaigns(id) on delete cascade,
  user_id             uuid not null references profiles(id) on delete cascade,
  business_name       text not null,
  contact_name        text,
  email               text,
  phone               text,
  website             text,
  instagram_handle    text,
  source              text not null default 'google_maps', -- google_maps|instagram|manual
  raw_data            jsonb,
  status              text not null default 'new',     -- new|approved|sending|sent|replied|booked|bounced|unsubscribed
  created_at          timestamptz not null default now(),
  unique (campaign_id, email)
);

-- ---------------------------------------------------------------------------
-- messages: every outbound + inbound touch
-- ---------------------------------------------------------------------------
create table if not exists messages (
  id                  uuid primary key default gen_random_uuid(),
  lead_id             uuid not null references leads(id) on delete cascade,
  user_id             uuid not null references profiles(id) on delete cascade,
  channel             text not null default 'email',   -- email|instagram_assist
  direction           text not null,                   -- outbound|inbound
  step                int  not null default 1,         -- 1=first touch, 2=follow-up
  subject             text,
  body                text not null,
  ai_generated        boolean not null default true,
  status              text not null default 'queued',  -- queued|sent|delivered|opened|failed
  ai_reply_tag        text,                            -- interested|maybe|no|unsubscribe (inbound)
  external_id         text,                            -- provider message/thread id
  scheduled_at        timestamptz,
  sent_at             timestamptz,
  created_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- appointments: booked calls (from Cal.com webhook)
-- ---------------------------------------------------------------------------
create table if not exists appointments (
  id                  uuid primary key default gen_random_uuid(),
  lead_id             uuid references leads(id) on delete set null,
  user_id             uuid not null references profiles(id) on delete cascade,
  scheduled_for       timestamptz,
  cal_booking_id      text,
  status              text not null default 'booked',  -- booked|completed|no_show|canceled
  created_at          timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- suppression_list: never email these again (unsubscribes/bounces)
-- ---------------------------------------------------------------------------
create table if not exists suppression_list (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references profiles(id) on delete cascade,
  email               text not null,
  reason              text not null default 'unsubscribe',
  created_at          timestamptz not null default now(),
  unique (user_id, email)
);

-- ---------------------------------------------------------------------------
-- Helpful indexes for the hot paths
-- ---------------------------------------------------------------------------
create index if not exists idx_leads_campaign      on leads(campaign_id);
create index if not exists idx_leads_status        on leads(user_id, status);
create index if not exists idx_messages_lead       on messages(lead_id);
create index if not exists idx_messages_due        on messages(status, scheduled_at)
  where direction = 'outbound';
create index if not exists idx_messages_inbox      on messages(user_id, direction, created_at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security: each user only sees their own rows
-- ---------------------------------------------------------------------------
alter table profiles          enable row level security;
alter table sending_accounts  enable row level security;
alter table campaigns         enable row level security;
alter table leads             enable row level security;
alter table messages          enable row level security;
alter table appointments      enable row level security;
alter table suppression_list  enable row level security;

create policy "own profile"   on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

create policy "own sending"   on sending_accounts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own campaigns" on campaigns
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own leads"     on leads
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own messages"  on messages
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own appts"     on appointments
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own suppress"  on suppression_list
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Auto-create a profile row when a new auth user signs up
-- ---------------------------------------------------------------------------
create or replace function handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();
