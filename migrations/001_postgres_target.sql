-- DESIGN-ONLY target schema. NOT connected to the snapshot application.
-- Apply only to an empty evaluation PostgreSQL database; assess migrations,
-- permissions, RLS, encryption, retention, indexes and repository tests first.
BEGIN;
CREATE SCHEMA cassandre;
CREATE TABLE cassandre.institution (
 institution_id text PRIMARY KEY, name text NOT NULL
);
CREATE TABLE cassandre.borrower (
 institution_id text NOT NULL REFERENCES cassandre.institution,
 borrower_id text NOT NULL, external_ref text NOT NULL, legal_name text NOT NULL,
 PRIMARY KEY(institution_id, borrower_id), UNIQUE(institution_id, external_ref)
);
CREATE TABLE cassandre.facility (
 institution_id text NOT NULL, facility_id text NOT NULL, borrower_id text NOT NULL,
 external_ref text NOT NULL, currency char(3) NOT NULL CHECK(currency='INR'),
 sanctioned_limit numeric(24,2) NOT NULL CHECK(sanctioned_limit>=0), state text NOT NULL,
 PRIMARY KEY(institution_id, facility_id), UNIQUE(institution_id, external_ref),
 FOREIGN KEY(institution_id, borrower_id) REFERENCES cassandre.borrower
);
CREATE TABLE cassandre.document (
 institution_id text NOT NULL, facility_id text NOT NULL, document_id text NOT NULL,
 object_key text NOT NULL, sha256 char(64) NOT NULL, received_at timestamptz NOT NULL,
 evidence_period date, source_system text NOT NULL, reviewer_state text NOT NULL,
 PRIMARY KEY(institution_id, document_id),
 UNIQUE(institution_id, facility_id, document_id),
 FOREIGN KEY(institution_id, facility_id) REFERENCES cassandre.facility
);
CREATE TABLE cassandre.rule_version (
 institution_id text NOT NULL, facility_id text NOT NULL, rule_id text NOT NULL,
 version integer NOT NULL CHECK(version>0), effective_from date NOT NULL,
 definition jsonb NOT NULL, source_document_id text NOT NULL, maker text NOT NULL,
 checker text, approved_at timestamptz,
 CHECK((checker IS NULL) = (approved_at IS NULL)), CHECK(checker IS NULL OR checker<>maker),
 PRIMARY KEY(institution_id, facility_id, rule_id, version),
 FOREIGN KEY(institution_id, facility_id) REFERENCES cassandre.facility,
 FOREIGN KEY(institution_id, facility_id, source_document_id)
 REFERENCES cassandre.document(institution_id, facility_id, document_id)
);
CREATE TABLE cassandre.import_revision (
 institution_id text NOT NULL, facility_id text NOT NULL, revision_id text NOT NULL,
 period date NOT NULL, content_sha256 char(64) NOT NULL,
 received_at timestamptz NOT NULL, source_document_id text NOT NULL, values_json jsonb NOT NULL,
 PRIMARY KEY(institution_id, facility_id, revision_id),
 UNIQUE(institution_id, facility_id, period, content_sha256),
 FOREIGN KEY(institution_id, facility_id) REFERENCES cassandre.facility,
 FOREIGN KEY(institution_id, facility_id, source_document_id)
 REFERENCES cassandre.document(institution_id, facility_id, document_id)
);
CREATE TABLE cassandre.calculation_run (
 institution_id text NOT NULL, facility_id text NOT NULL, run_id text NOT NULL,
 period date NOT NULL, rule_id text NOT NULL, rule_version integer NOT NULL,
 revision_id text NOT NULL, algorithm_version text NOT NULL,
 input_snapshot jsonb NOT NULL, result_snapshot jsonb NOT NULL,
 computed_at timestamptz NOT NULL, actor text NOT NULL,
 PRIMARY KEY(institution_id, run_id),
 UNIQUE(institution_id, facility_id, run_id),
 FOREIGN KEY(institution_id, facility_id, rule_id, rule_version) REFERENCES cassandre.rule_version,
 FOREIGN KEY(institution_id, facility_id, revision_id) REFERENCES cassandre.import_revision
);
CREATE TABLE cassandre.decision (
 institution_id text NOT NULL, facility_id text NOT NULL, decision_id text NOT NULL,
 run_id text NOT NULL, maker text NOT NULL, checker text NOT NULL CHECK(maker<>checker),
 decision text NOT NULL, rationale text NOT NULL, decided_at timestamptz NOT NULL,
 PRIMARY KEY(institution_id, decision_id),
 FOREIGN KEY(institution_id, facility_id) REFERENCES cassandre.facility,
 FOREIGN KEY(institution_id, facility_id, run_id) REFERENCES cassandre.calculation_run(institution_id,facility_id,run_id)
);
CREATE TABLE cassandre.audit_event (
 institution_id text NOT NULL REFERENCES cassandre.institution,
 event_id text NOT NULL, occurred_at timestamptz NOT NULL, actor text NOT NULL,
 action text NOT NULL, detail jsonb NOT NULL,
 PRIMARY KEY(institution_id, event_id)
);
CREATE TABLE cassandre.outbox (
 institution_id text NOT NULL, event_id text NOT NULL, destination text NOT NULL,
 delivered_at timestamptz, attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
 PRIMARY KEY(institution_id, event_id, destination),
 FOREIGN KEY(institution_id, event_id) REFERENCES cassandre.audit_event
);
CREATE FUNCTION cassandre.deny_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
 BEGIN RAISE EXCEPTION 'Historical record is append-only'; END; $$;
CREATE TRIGGER protect_calculation BEFORE UPDATE OR DELETE ON cassandre.calculation_run
 FOR EACH ROW EXECUTE FUNCTION cassandre.deny_history_mutation();
CREATE TRIGGER protect_import BEFORE UPDATE OR DELETE ON cassandre.import_revision
 FOR EACH ROW EXECUTE FUNCTION cassandre.deny_history_mutation();
CREATE TRIGGER protect_decision BEFORE UPDATE OR DELETE ON cassandre.decision
 FOR EACH ROW EXECUTE FUNCTION cassandre.deny_history_mutation();
CREATE TRIGGER protect_audit BEFORE UPDATE OR DELETE ON cassandre.audit_event
 FOR EACH ROW EXECUTE FUNCTION cassandre.deny_history_mutation();
CREATE INDEX facility_borrower_idx ON cassandre.facility(institution_id,borrower_id);
CREATE INDEX evidence_period_idx ON cassandre.import_revision(institution_id,facility_id,period);
CREATE INDEX run_period_idx ON cassandre.calculation_run(institution_id,facility_id,period);
COMMIT;
-- Owner/superuser can bypass/disable triggers. Independent audit export still
-- required. Composite FK guards tenant linking but is NOT SELECT isolation:
-- repository filtering, non-owner roles and independently tested RLS required.
