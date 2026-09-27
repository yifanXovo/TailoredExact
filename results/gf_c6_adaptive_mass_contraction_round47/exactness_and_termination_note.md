# Exactness and termination

AM changes neither root coverage nor feasible sets; split, native-target, and
exact-close remain existing valid C6 alternatives. AMC removes only an LP-
proven-empty half and records this exclusion in certificate-aware coverage
metadata. Active endpoints remain gap-free relative to the feasible domain.
Inherited bounds are monotone, the global minimum remains valid, and each
transition either closes, strengthens, splits, or strictly contracts a finite
interval. The existing finite-tree and terminal-MIP termination argument and
zero-gap certificate gate therefore remain unchanged. Neither AM nor AMC adds
an LP, MIP, CGLP, or parametric query.
