# Evidence storage audit

Round 55 stores mathematical contracts, decisions, proofs, compact CSV/JSON
tables, documentation, and reproduction commands in Git.  Native logs, model
exports, progress traces, and other bulky solver artifacts remain local under
`local_raw/`; every local file is individually inventoried with SHA-256.

- compact committed files inventoried: 171
- compact bytes: 524071
- local-raw files inventoried: 8061
- local-raw bytes: 1215728960
- temporary working evidence under `tmp/`: excluded from scientific evidence
- inventory self-files: excluded from their own hash set to avoid circularity

The compact tables record executable identity, caps, status, bounds, Work,
time, certificates, and artifact locations.  Raw evidence is reproducible from
the frozen manifests and commands; it is not required in the Git history.
