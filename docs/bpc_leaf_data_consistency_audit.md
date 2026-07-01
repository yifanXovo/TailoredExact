# BPC Leaf Data Consistency Audit

`scripts/audit_bpc_leaf_data.py` checks BPC validation artifacts against the
frozen target manifest.

The audit verifies:

- final JSON exists;
- target leaf gamma range matches the manifest;
- `algorithm_preset` is `paper-gf-bpc-core`;
- interval oracle is not used for the BPC-core result;
- the result reports pricing calls and exact-pricing closure status.

The audit is intentionally conservative.  A noncertified BPC leaf can pass the
data audit if it honestly reports the same leaf, no oracle certificate, and no
sealed provenance violation.  It does not imply the leaf closed; exact closure
still requires `pricing_closure_certified_exact=true` and a BPC certificate
basis.
