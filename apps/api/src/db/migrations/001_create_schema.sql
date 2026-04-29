-- AttendAct schema: core tables for no-show prediction signal product
-- Applied to existing nomoi-core Supabase project (umodapwphcxtiijizqll)

create schema if not exists attendact;

-- Tenants (hospitals)
create table attendact.tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  emirate text not null,
  ehr_vendor text,
  pilot_status text default 'pre_pilot',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Users (ops staff)
create table attendact.users (
  id uuid primary key references auth.users(id),
  tenant_id uuid references attendact.tenants(id) not null,
  role text not null,
  email text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Appointments (scored)
create table attendact.appointments (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references attendact.tenants(id) not null,
  external_id text,
  appointment_at timestamptz not null,
  booked_at timestamptz not null,
  specialty text not null,
  provider_id text,
  clinic_location text,
  patient_age_band text,
  patient_gender text,
  insurance_tier text,
  booking_channel text,
  language_pref text,
  prior_noshow_count_12mo int default 0,
  prior_attended_count_12mo int default 0,
  distance_km numeric,
  raw_features jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Scores (one row per scoring event)
create table attendact.scores (
  id uuid primary key default gen_random_uuid(),
  appointment_id uuid references attendact.appointments(id) not null,
  tenant_id uuid references attendact.tenants(id) not null,
  model_version text not null,
  probability numeric not null check (probability between 0 and 1),
  risk_band text not null,
  shap_top_factors jsonb not null,
  scored_at timestamptz default now()
);

-- Outcomes (ground truth)
create table attendact.outcomes (
  id uuid primary key default gen_random_uuid(),
  appointment_id uuid references attendact.appointments(id) not null,
  tenant_id uuid references attendact.tenants(id) not null,
  status text not null,
  observed_at timestamptz not null,
  source text not null,
  created_at timestamptz default now()
);

-- Interventions (Phase 2)
create table attendact.interventions (
  id uuid primary key default gen_random_uuid(),
  appointment_id uuid references attendact.appointments(id) not null,
  tenant_id uuid references attendact.tenants(id) not null,
  channel text not null,
  template_name text,
  language text not null,
  variant text,
  triggered_by_score_id uuid references attendact.scores(id),
  sent_at timestamptz,
  delivered_at timestamptz,
  read_at timestamptz,
  replied_at timestamptz,
  reply_text text,
  patient_opted_out boolean default false,
  created_at timestamptz default now()
);

-- Audit log (append-only, ADHICS)
create table attendact.audit_log (
  id bigserial primary key,
  tenant_id uuid,
  user_id uuid,
  action text not null,
  entity_type text,
  entity_id uuid,
  ip_address inet,
  user_agent text,
  metadata jsonb,
  occurred_at timestamptz default now()
);

-- Fairness audits
create table attendact.fairness_audits (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references attendact.tenants(id) not null,
  model_version text not null,
  audit_date date not null,
  subgroup_metrics jsonb not null,
  flagged_disparities jsonb,
  created_at timestamptz default now()
);

-- Indexes
create index idx_appointments_tenant on attendact.appointments(tenant_id);
create index idx_appointments_at on attendact.appointments(appointment_at);
create index idx_scores_appointment on attendact.scores(appointment_id);
create index idx_scores_tenant on attendact.scores(tenant_id);
create index idx_outcomes_appointment on attendact.outcomes(appointment_id);
create index idx_audit_tenant_action on attendact.audit_log(tenant_id, action);
create index idx_audit_occurred on attendact.audit_log(occurred_at);
create index idx_interventions_appointment on attendact.interventions(appointment_id);
