CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name     TEXT,
  role          TEXT NOT NULL CHECK (role IN ('admin', 'investigator', 'analyst', 'viewer')),
  badge_number  TEXT,
  department    TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  last_login    TIMESTAMPTZ,
  is_active     BOOLEAN DEFAULT TRUE
);

CREATE TABLE cases (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  case_number     TEXT UNIQUE NOT NULL,
  status          TEXT DEFAULT 'open' CHECK (status IN ('open','investigating','escalated','closed','archived')),
  priority        TEXT DEFAULT 'medium' CHECK (priority IN ('low','medium','high','critical')),
  assigned_to     UUID REFERENCES users(id),
  created_by      UUID REFERENCES users(id),
  description     TEXT,
  total_amount    NUMERIC(20, 2),
  victim_count    INT DEFAULT 0,
  suspect_count   INT DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  closed_at       TIMESTAMPTZ
);

CREATE TABLE accounts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_number  TEXT UNIQUE NOT NULL,
  bank_name       TEXT,
  account_type    TEXT,
  registered_name TEXT,
  phone_number    TEXT,
  pan_number      TEXT,
  ifsc_code       TEXT,
  state           TEXT,
  city            TEXT,
  account_label   TEXT CHECK (account_label IN ('suspect','victim','relay','mule','clean','unknown')),
  is_frozen       BOOLEAN DEFAULT FALSE,
  freeze_date     TIMESTAMPTZ,
  freeze_reason   TEXT,
  neo4j_node_id   TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  neo4j_rel_id        TEXT,
  transaction_ref     TEXT UNIQUE NOT NULL,
  from_account        TEXT NOT NULL,
  to_account          TEXT NOT NULL,
  amount              NUMERIC(20, 2) NOT NULL,
  currency            TEXT DEFAULT 'INR',
  timestamp           TIMESTAMPTZ NOT NULL,
  transaction_type    TEXT,
  upi_id              TEXT,
  bank_ref            TEXT,
  narration           TEXT,
  source_file         TEXT,
  case_id             UUID REFERENCES cases(id),
  risk_flag           TEXT CHECK (risk_flag IN ('high','medium','low','unknown')),
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ml_scores (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id              UUID REFERENCES accounts(id),
  run_id                  UUID NOT NULL,
  isolation_forest_score  FLOAT,
  random_forest_score     FLOAT,
  kmeans_cluster          INT,
  kmeans_distance         FLOAT,
  gnn_score               FLOAT,
  ensemble_score          FLOAT NOT NULL,
  verdict                 TEXT CHECK (verdict IN ('FRAUD','SUSPICIOUS','CLEAN')),
  confidence              FLOAT,
  shap_values             JSONB,
  feature_vector          JSONB,
  model_version           TEXT,
  scored_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE case_evidence (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         UUID REFERENCES cases(id),
  evidence_type   TEXT CHECK (evidence_type IN ('transaction','account','graph_screenshot','ml_report','note')),
  reference_id    TEXT,
  title           TEXT NOT NULL,
  description     TEXT,
  file_url        TEXT,
  added_by        UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         UUID REFERENCES cases(id),
  report_type     TEXT CHECK (report_type IN ('investigation','centrality','ml_analysis','digital_arrest','full_case')),
  generated_by    UUID REFERENCES users(id),
  file_url        TEXT,
  metadata        JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE digital_arrest_events (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  victim_account_id   UUID REFERENCES accounts(id),
  case_id             UUID REFERENCES cases(id),
  detection_score     FLOAT,
  pressure_start_ts   TIMESTAMPTZ,
  pressure_end_ts     TIMESTAMPTZ,
  communication_count INT,
  amount_transferred  NUMERIC(20,2),
  verdict             TEXT CHECK (verdict IN ('CONFIRMED','PROBABLE','POSSIBLE','CLEARED')),
  evidence            JSONB,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id),
  action      TEXT NOT NULL,
  entity_type TEXT,
  entity_id   TEXT,
  ip_address  TEXT,
  user_agent  TEXT,
  metadata    JSONB,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ingestion_jobs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name       TEXT NOT NULL,
  file_size       BIGINT,
  status          TEXT DEFAULT 'pending' CHECK (status IN ('pending','parsing','normalizing','writing','complete','failed')),
  total_rows      INT,
  processed_rows  INT DEFAULT 0,
  errors          JSONB,
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  created_by      UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_from_account ON transactions(from_account);
CREATE INDEX idx_transactions_to_account ON transactions(to_account);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_case_id ON transactions(case_id);
CREATE INDEX idx_ml_scores_account_id ON ml_scores(account_id);
CREATE INDEX idx_ml_scores_ensemble ON ml_scores(ensemble_score DESC);
CREATE INDEX idx_accounts_label ON accounts(account_label);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

INSERT INTO users (email, password_hash, full_name, role, badge_number, department)
VALUES ('admin@fraudlens.local', '$2b$12$placeholder_change_before_use', 'System Admin', 'admin', 'ADM001', 'Cybercrime Cell');
