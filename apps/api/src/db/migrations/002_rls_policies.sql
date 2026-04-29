-- Row Level Security for all attendact tables
-- Every read/write must match tenant_id to the user's tenant via JWT claim

alter table attendact.tenants enable row level security;
alter table attendact.users enable row level security;
alter table attendact.appointments enable row level security;
alter table attendact.scores enable row level security;
alter table attendact.outcomes enable row level security;
alter table attendact.interventions enable row level security;
alter table attendact.audit_log enable row level security;
alter table attendact.fairness_audits enable row level security;

-- Helper function to get current user's tenant_id from JWT
create or replace function attendact.get_user_tenant_id()
returns uuid
language sql
stable
as $$
  select tenant_id from attendact.users where id = auth.uid()
$$;

-- Tenants: users can only see their own tenant
create policy "Users can view own tenant"
  on attendact.tenants for select
  using (id = attendact.get_user_tenant_id());

-- Users: can view users in same tenant
create policy "Users can view same tenant users"
  on attendact.users for select
  using (tenant_id = attendact.get_user_tenant_id());

-- Appointments: tenant isolation
create policy "Tenant isolation on appointments"
  on attendact.appointments for all
  using (tenant_id = attendact.get_user_tenant_id());

-- Scores: tenant isolation
create policy "Tenant isolation on scores"
  on attendact.scores for all
  using (tenant_id = attendact.get_user_tenant_id());

-- Outcomes: tenant isolation
create policy "Tenant isolation on outcomes"
  on attendact.outcomes for all
  using (tenant_id = attendact.get_user_tenant_id());

-- Interventions: tenant isolation
create policy "Tenant isolation on interventions"
  on attendact.interventions for all
  using (tenant_id = attendact.get_user_tenant_id());

-- Audit log: read-only for tenant, append via service role
create policy "Tenant can read own audit log"
  on attendact.audit_log for select
  using (tenant_id = attendact.get_user_tenant_id());

-- Fairness audits: read-only for tenant
create policy "Tenant can read own fairness audits"
  on attendact.fairness_audits for select
  using (tenant_id = attendact.get_user_tenant_id());
