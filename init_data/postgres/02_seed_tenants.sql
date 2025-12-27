-- 02_seed_tenants.sql
INSERT INTO tenants (name, config) VALUES ('default', '{"plan": "enterprise"}') ON CONFLICT DO NOTHING;
