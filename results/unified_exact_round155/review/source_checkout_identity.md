# Fixed source references and actual checkout bytes

`final_provenance_v1` failed its strict inherited-source byte comparison at
`scripts/round111_seed_audit.py`; its actual fee was 3.5576203998643905s.
The failed receipt/source snapshot is retained. No source or prior raw
evidence was changed to make that check pass.

The separately metered `source_checkout_diagnostic_v1` established that the
fixed base blob has 7179 bytes and no CRLF sequences, while the actual
working file has 7300 bytes and 121 CRLF sequences. Replacing each LF byte
in the fixed blob by CRLF exactly reconstructs the working file. The fixed
SHA256 is `528ab1b02b90c5d4d82113c15e617278114dcf72f1cb79f15dc4be42a92ac667`;
the working SHA256 is
`da70eb1a01cdcf988fcfe0963ef39692d513cc5ae20ecae18835832bed45e2c5`.
The diagnostic cost 0.1454771999269724s, with no Optimize or Native model
read and no file change.

The revised provenance reader retains strict identity for input/data
references. For inherited Python modules only, it permits either exact
identity or an exactly reconstructible LF-to-CRLF/CRLF-to-LF conversion.
Any other byte difference still fails. The reference index keeps the fixed
Git blob's commit, hash and size, plus the explicit checkout transformation
and actual working hash/size. It neither substitutes the working hash for
the fixed Git blob hash nor repacks old source files. The later factual
reader independently reconstructs and compares each declared mapping.

This is a source-checkout identity repair, not an algorithm change, a
numerical tolerance change or a rerun of a scientific experiment. The
revised whole dependency readback remains pending until its actual receipt
and manifest exist.

## Actual final readback: 2026-11-06T10:14:21.986052+00:00

Actual final outcome: final_provenance_v2 PASS, closed fee 11.39311489998363s. The manifests contain 338 references, 156 inherited static Python dependencies and 23 exactly reconstructed checkout newline transformations. The separately executed final_evidence_readback_v1 also passes and independently reconstructs those mappings. No old source was edited and no old carrier downloaded/repacked. The preceding pending statement describes the earlier preparation time only.
