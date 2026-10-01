# Assumptions and required validation

| Area | Current boundary | Required before expansion |
|---|---|---|
| Data | Synthetic identifiers and two seeded active facilities | bank-approved corpus and complete lifecycle evidence |
| Persistence | Single-process JSON snapshot, local POSIX disk | tested transactional PostgreSQL repository/migrations, capacity/HA and key management |
| Identity | Independently issued local bearer tokens with hashed server configuration | bank SSO/MFA, sessions, revocation and branch/portfolio/authority mapping |
| Terms | Illustrative margins, aggregate exclusions and headroom covenant | exact facility sanction/agreement/amendment sources and approved definitions |
| Documents | Bounded synthetic evidence; no PDF/OCR parser | bank-approved DMS/scan intake, malware isolation, original custody, source-page review |
| Bank feeds | No real BOB/Union adapters; bank-brand folders are discovery placeholders | approved API or export/SFTP schema, permissions, completeness and reconciliation |
| Conduct | Advisory commercial-bank CC profile, explicit complete-feed requirement | bank validation of day-end data, effective caps and boundary interpretations; separate NBFC profile |
| Audit | Local records and checksums; administrator can alter host | independent protected audit archive, signatures/keys, retention and integrity drill |
| Deployment | Docker configuration supplied; Docker absent during review | target-host build, image scan, network/volume/TLS and recovery verification |
| ML | Transparent synthetic heuristic only | lawful labelled data, leakage-free evaluation and independent model governance |
| Blockchain | Not implemented | real multi-institution trust need and justified privacy/legal/governance design |

Bank names and simulated institutional review personas do not imply access, affiliation or approval. Public vendor capabilities do not prove a given bank has enabled those modules. Hidden liabilities, inaccessible amendments and plausible forged records cannot be guaranteed detectable.
