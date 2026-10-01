# Enterprise control review — synthetic on-premises prototype

This is a simulated engineering review using JPMC credit-control, Morgan Stanley model-risk and Goldman Sachs engineering lenses. It does not describe those firms' private systems, establish affiliation or certify regulatory compliance.

## Findings and implemented mitigations

The previous API accepted actor names supplied in JSON and exposed data without authentication. Changing an `approver` string could evade maker/checker controls. Current protected `/v1/` routes authenticate an issued bearer credential and derive actor, institution and roles server-side. Supplied legacy actor fields are ignored. No credentials configured means no API access.

Read access requires reader; imports, proposals, checklist changes and recompute require maker; approvals, renewal decisions and closure require checker. Tenant scope applies to direct requests, mutation object lookups and list routes. Generic cases without a resolvable underlying facility are denied. Generic approval records an approval-case decision only: it does not automatically activate a rule.

Document replacements cannot cross facilities. Mutation bodies have a 256 KiB streaming cap including requests without Content-Length. Original synthetic plain-text bytes are preserved under a SHA-256 digest, verified on retrieval, and served only through a facility/document-authorised endpoint as an attachment. Hash possession is not access permission. This is not PDF upload storage or malware inspection. Files remain plaintext on the approved local volume; encrypted volumes and access permissions are production gates. Monthly periods, finite nonnegative bounded amounts and margins in [0,1] are checked. Validation responses omit submitted values/document contents. Responses forbid caching and use a restrictive content security policy. API documentation endpoints are disabled. Health reveals no account records.

Closure additionally requires latest recorded outstanding present and zero, and an authenticated checker who did not change the checklist. Checklist booleans remain attestations, not verification of release documents. The balance remains synthetic reported data; production closure requires a fresh authoritative loan-ledger record and approved evidence.

Imported financial snapshots and computation receipts preserve history alongside current views. Transaction middleware serialises requests, rolls back failed mutations and commits before sending successful responses. The process writer lease prevents two processes sharing the snapshot; run one worker. These controls do not make JSON storage a production database or make local audit records tamper-proof.

## Credential setup

Generate high-entropy tokens, at least 32 characters, outside source control. Store SHA-256 hashes of those random tokens (not human passwords). Configure `CASSANDRE_AUTH_FILE` to a read-only mounted JSON file, or `CASSANDRE_AUTH_CREDENTIALS` for local development:

```json
[
  {"actor":"maker.operator", "institution_id":"SIM-BANK-001", "roles":["reader","maker"], "token_sha256":"REPLACE_WITH_64_CHARACTER_LOWERCASE_SHA256"},
  {"actor":"checker.operator", "institution_id":"SIM-BANK-001", "roles":["reader","checker"], "token_sha256":"REPLACE_WITH_ANOTHER_64_CHARACTER_LOWERCASE_SHA256"}
]
```

Never reuse example/test credentials. Only the issued token is supplied as `Authorization: Bearer ...`. Credential file changes apply on the next request. Roles and institution cannot be selected by the browser. The UI holds tokens in page memory, not localStorage. Use a bank-approved TLS reverse proxy even on a private network; tokens sent over HTTP can be intercepted. No public real-bank deployment is authorised by this prototype.

## Legal evidence and scope

As researched 1 October 2026:

- [Commercial Banks Managing Risks in Outsourcing Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13139): core sanction/KYC decision functions remain with the bank; need-to-know access, client separation, audit/access rights, continuity and exit matter. Material IT outsourcing and software licence acquisition have different scope; bank counsel must classify the actual deployment.
- [NBFC Managing Risks in Outsourcing Directions 2025](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12941): applicability varies by layer; do not copy a bank compliance profile unchanged.
- [FREE-AI committee report](https://rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=1306): recommendations, not approval for an algorithm or autonomous credit decision.
- [DPDP Rules official Gazette](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf): staged commencement; most operational rules are scheduled eighteen months after publication. Verify both Act sections and Rules dates before asserting current legal duties. Directors/guarantors may have personal data in business files.
- Current July 2026 bank/NBFC cybersecurity consolidation must be checked rather than relying solely on superseded 2023 directions. Official pages identified: [commercial bank notification](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13643), [NBFC direction](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13592). Full text was not retrievable in this review; these links are a verification gate, not a claim of completed clause-level compliance.

## Production gates and residual risks

Before real records: bank SSO/MFA and session policy, portfolio/branch access controls, independent legal scope review, independent penetration test, rate limits, secrets rotation, encrypted volumes/backups, bank-managed keys, production transactional database, externally protected audit evidence, support access governance, restoration and exit tests, data-retention matrix and incident-response/reporting ownership. There is no bank connector, document vault/OCR, regulator-certified rule engine, trained model or NPA writeback in this implementation.

The local bearer mechanism is a prototype service control, not bank identity integration. No default training or sending bank data to external models is implemented. No architecture can guarantee all ambiguities detected or zero leakage. Blockchain does not authenticate the truth of borrower evidence; it is unnecessary for the current single-bank prototype.

Security regression tests cover missing credentials, role bypass, actor spoofing/self-approval, tenant enumeration/fetch/import, invalid numeric/period data, validation redaction, oversize bodies, cross-facility replacement and cache policy. Workflow tests use explicitly issued test credentials, never a server authentication bypass.
