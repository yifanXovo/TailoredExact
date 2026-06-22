# Experimental Two-Track Assessment

Round 16 keeps the two-track elementary/relaxed route-load implementation as an
experimental appendix component, not part of `paper-bpc-core`.

## Evidence Reviewed

Round 14 introduced the two-track metadata and lower-bound-only relaxed column
path. Round 15 added projection-safe non-elementary relaxed columns and
relaxed-RMP CG. Round 16 reran selected V12 and generated benchmark rows under
`paper-bpc-experimental` and compared them with `paper-bpc-core`.

| Instance | Core LB | Experimental LB | Core UB | Experimental UB | Certificate-valid relaxed improvement |
|---|---:|---:|---:|---:|---|
| V12 M1 average | 0.336357248340 | 0.344296397770 | 0.368581603155 | 0.368581603155 | no |
| V12 M2 average | 0.698710208326 | 0.698710208326 | 0.719065249476 | 0.719065249476 | no |

The V12 M1 experimental row improved the reported lower bound, but the relaxed
RMP certificate condition was not met by a closed relaxed pricing proof. The
V12 M2 row matched the core lower bound. Generated V50/V100 diagnostic rows
still produced zero valid global lower bound under the large diagnostic path.

## Safety Status

Relaxed columns remain lower-bound-only. They are blocked from route-pool
incumbents, exported route plans, and candidate reconstruction unless explicitly
elementary feasible. This path is safe for diagnostics, but not yet reliable as
main paper certificate evidence.

## Recommendation

Keep two-track relaxed-RMP as appendix/experimental and disabled in
`paper-bpc-core`. Promote it only after at least one nontrivial benchmark shows
a certificate-valid lower-bound improvement with closed ng-relaxed pricing.
