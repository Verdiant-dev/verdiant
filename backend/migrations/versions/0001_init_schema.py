from alembic import op

# revisions
revision = '0001_init_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Extension (für gen_random_uuid)
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # TENANT
    op.execute("""
    CREATE TABLE IF NOT EXISTS tenant (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name TEXT NOT NULL,
      plan TEXT NOT NULL DEFAULT 'basic',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)

    # USER
    op.execute("""
    CREATE TABLE IF NOT EXISTS app_user (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
      email TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'owner',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(tenant_id, email)
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_app_user_tenant ON app_user(tenant_id)")

    # REPORTING PERIOD (RLS)
    op.execute("""
    CREATE TABLE IF NOT EXISTS reporting_period (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
      year INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'open',
      locked_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE(tenant_id, year)
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_reporting_period_tenant ON reporting_period(tenant_id)")
    op.execute("ALTER TABLE reporting_period ENABLE ROW LEVEL SECURITY")
    op.execute("""
    CREATE POLICY tenant_isolation_reporting_period ON reporting_period
      USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    """)

    # EVIDENCE (RLS)
    op.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
      uri TEXT NOT NULL,
      hash TEXT,
      uploaded_by UUID REFERENCES app_user(id),
      uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_evidence_tenant ON evidence(tenant_id)")
    op.execute("ALTER TABLE evidence ENABLE ROW LEVEL SECURITY")
    op.execute("""
    CREATE POLICY tenant_isolation_evidence ON evidence
      USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    """)

    # DATAPOINT (RLS)
    op.execute("""
    CREATE TABLE IF NOT EXISTS datapoint (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
      period_id UUID NOT NULL REFERENCES reporting_period(id) ON DELETE CASCADE,
      esrs_code TEXT NOT NULL,
      value NUMERIC,
      unit TEXT,
      source TEXT,
      collected_at TIMESTAMPTZ,
      evidence_id UUID REFERENCES evidence(id),
      version INTEGER NOT NULL DEFAULT 1,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_datapoint_tenant ON datapoint(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_datapoint_period ON datapoint(period_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_datapoint_code ON datapoint(esrs_code)")
    op.execute("ALTER TABLE datapoint ENABLE ROW LEVEL SECURITY")
    op.execute("""
    CREATE POLICY tenant_isolation_datapoint ON datapoint
      USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    """)

    # AUDIT EVENT (RLS)
    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_event (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
      actor_user_id UUID REFERENCES app_user(id),
      action TEXT NOT NULL,
      entity TEXT NOT NULL,
      entity_id UUID,
      diff_json JSONB,
      at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_tenant ON audit_event(tenant_id)")
    op.execute("ALTER TABLE audit_event ENABLE ROW LEVEL SECURITY")
    op.execute("""
    CREATE POLICY tenant_isolation_audit_event ON audit_event
      USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS audit_event")
    op.execute("DROP TABLE IF EXISTS datapoint")
    op.execute("DROP TABLE IF EXISTS evidence")
    op.execute("DROP TABLE IF EXISTS reporting_period")
    op.execute("DROP TABLE IF EXISTS app_user")
    op.execute("DROP TABLE IF EXISTS tenant")
