# Round 53 evidence storage policy

Commit source, tests, pre-result freezes, exactness proofs, compact row/model/
activity/callback ledgers, summary CSV/JSON, hashes, final reports, and
reproduction commands. Native logs and full model trees remain local-only
unless a compact archive is specifically useful. Every local-only group must
be inventoried with deterministic SHA-256 tree identity, size, file count,
generating command, executable hash, and a committed representative ledger.
Historical raw evidence is immutable. Missing entered-stage rows force
`round53_incomplete`. Source-scope, secret/license, cap, certificate,
preservation, and evidence-hash audits are publication gates.
