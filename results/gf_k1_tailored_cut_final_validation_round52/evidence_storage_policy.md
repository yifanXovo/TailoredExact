# Round 52 evidence storage policy

Commit source, tests, frozen manifests, proofs, concise cut ledgers, summary
CSV/JSON, hashes, reproduction commands, and compact archives where useful.
Do not commit every native log or full raw model tree. Large native evidence may
remain local only when its path, size, SHA-256, generating command, executable
hash, and compact committed representative are inventoried. No raw historical
evidence may be rewritten. Every entered-stage row must be represented in a
committed compact ledger; missing entered rows force `round52_incomplete`.
Secret/license scanning, source-scope auditing, evidence hashing, cap auditing,
and preservation auditing are publication gates.
