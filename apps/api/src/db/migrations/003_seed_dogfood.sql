-- Seed: dogfood tenant and initial user
-- Note: user ID must match the auth.users ID after magic link signup

insert into attendact.tenants (id, name, emirate, ehr_vendor, pilot_status)
values (
  'a0000000-0000-0000-0000-000000000001',
  'NOMOI Dogfood',
  'AD',
  'other',
  'shadow'
)
on conflict (id) do nothing;

-- Placeholder user row. Replace user ID with actual auth.users.id after first login.
-- insert into attendact.users (id, tenant_id, role, email)
-- values (
--   '<auth_user_id_after_signup>',
--   'a0000000-0000-0000-0000-000000000001',
--   'admin',
--   'assel@nomoi.ai'
-- );
