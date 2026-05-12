-- Stripe per-hospital subscriptions for Noshight.

create table if not exists hospitals (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  contact_email text,
  stripe_customer_id text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists hospitals_stripe_customer_idx on hospitals (stripe_customer_id);

create table if not exists stripe_subscriptions (
  id text primary key,
  hospital_id uuid not null references hospitals(id) on delete cascade,
  stripe_customer_id text not null,
  stripe_price_id text not null,
  lookup_key text not null,
  status text not null,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists stripe_subscriptions_hospital_idx on stripe_subscriptions (hospital_id);
create index if not exists stripe_subscriptions_status_idx on stripe_subscriptions (status);

create or replace function touch_stripe_subscriptions_updated_at()
returns trigger as $$
begin
  new.updated_at := now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists stripe_subscriptions_updated_at on stripe_subscriptions;
create trigger stripe_subscriptions_updated_at
  before update on stripe_subscriptions
  for each row execute function touch_stripe_subscriptions_updated_at();

drop trigger if exists hospitals_updated_at on hospitals;
create trigger hospitals_updated_at
  before update on hospitals
  for each row execute function touch_stripe_subscriptions_updated_at();
