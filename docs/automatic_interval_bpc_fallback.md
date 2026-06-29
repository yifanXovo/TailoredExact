# Automatic Interval BPC Fallback

Automatic BPC interval fallback is intentionally not part of the default sealed
V20 preset. It can be requested with `--auto-interval-bpc-fallback true` after
automatic interval-oracle attempts.

## Certificate Rule

BPC fallback can close an interval only if the BPC tree proves the interval
lower bound with exact pricing closure at every node used for the certificate.
Generated columns and route-pool recombination are upper-bound-only evidence.

Rows where fallback starts but exact pricing does not close remain
noncertified. The sealed preset currently records requested automatic fallback
as diagnostic unless a future implementation imports exact-pricing-closed
interval certificates through the full-ledger merge audit.
