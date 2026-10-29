# Independent qualification and finite LP-plan review

Reviewer: `/root/independent_review`; 2026-10-29 (Asia/Shanghai).
Decision: **ACCEPT the registered 20 short, serial Seed0 LP positions.**
This review does not admit a full-algorithm matrix or infer performance from
saved-point violations. It performed zero Optimize calls and loaded no solver.

## Bound records

| Record | SHA256 |
|---|---|
| `qualification/matrix_checks.json` | `140d0a771579c2e28edda1d044e4eb8a188c55f8c6be36757caf4f26ba757351` |
| `roots/plan.json` | `89cbe3e7cc3036b490d6ac3be3077996f36c099a4126fb7ded95dfa2c5ed731b` |
| `math/exact.json` | `35e509b6a6f830d3e0acb84f44c9f02807126a33233fa720e94fedc0b58f269a` |
| `scripts/round138_lp.py` as reviewed | `85fbb7f43bb3e657648073735133b3e314c01f0e6303cd03bf4801384b884da3` |
| `scripts/round138_qualify.py` | `b8212400f088110d85a47e79793b61eccd753d88498d381ec3980b0a1fa86bfd` |
| `scripts/round138_math.py` | `3d1480db5c58703a81c0eb221a29ea6b9ad6c19ff719ace187dd7ad7d70ebea6` |

The LP plan was recorded at `2026-10-28T17:55:36.377232+00:00`.
The first recorded LP launch was later, at
`2026-10-28T17:55:53.407128+00:00`. These are retained UTC record times,
corresponding to 2026-10-29 in the client timezone.

## Qualification checked

I read the validator and actual emitted models. For each of the seven domains
(root, low child, high child, cutoff refresh, collapsed interval, tiny alpha,
near-one interval), I independently re-read historical and new-off canonical
models and confirmed semantic equality; the actual off/stock file hashes match
their retained records. The validator explicitly compares order, types, bounds,
objective and the complete multiset of rows, and proves exactly four additions,
zero removals and zero new columns when stock RLT is enabled.

Its exact-Fraction comparisons retain every variable coefficient, including
alpha=1e-13, and verify outward RHS errors. The tests include a depot stock of
50000 that is excluded from B, heterogeneous targets and Q=(20,25,30), and a
physical witness returning loads (20,0,15). The endpoint product checks test
the four new rows; they do not claim that choosing a g below the witness's true
Gini makes the complete epigraph feasible. Mathematical validity does not
require equating the auxiliary g to true Gini at every completion.

## Tiny and zero-stock checks

The retained exact file uses the declared original matrices, old state penalty
and R88 extensions, with all noncomparison auxiliaries allowed their explicit
matching extensions. Its four objectives and integer full-extension checks
agree with the earlier independent mathematical review. These are exact finite
algebraic checks, separate from numerical LP optimization.

I additionally checked the zero-inventory boundary from the unchanged saved
enumeration without regenerating it. J2 saved joint index 27 and J3 index 34
both use saved car-pair [1,14]. `integer_extension` gives Y=(0,0,0,0), legal
loaded returns, g=0, all e_i=1 and all inventory products zero. Exact row replay
passes all 583 original rows and 284/298 bounds, with zero residuals or
violations. The old R88 B1/B2 algebraic extensions also pass 38/70 rows.
The new stock-row slacks are (0,9/4,0,0), and TC is tight. Thus the zero-stock
case and the stipulated S=0 convention have a concrete complete witness.

## LP comparison checked

The plan contains four roles and sixteen core positions, plus four GS controls:

| Role | Physical T | Actual lambda | Variants |
|---|---:|---:|---|
| K-35-U | 10800 | 0.15 | base, stock, TC, TC+stock, independent GS, shared GS |
| R-X20-S-T1 | 4800 | 0.12676060979965992 | same six |
| R-X35-S-T2 | 6300 | 0.0754049775127276 | base, stock, TC, TC+stock |
| K-20-S | 5400 | 0.15 | same four |

Every position explicitly uses Seed0, one thread and a 120s native LP cap;
the runner is serial with affinity mask 4. The nominal native cap sum is 2400s;
the runner's 150s outer reservations total 3000s and are not additional nested
solver charges. AP remains off. TC is a same-domain LP control and has not been
implicitly selected for the full candidate.

I checked each role's actual input SHA and both source model SHAs against every
plan entry. All variants retain the same alpha, beta, native cutoff, physical T,
objective coefficient and inventory support. The resource lambdas remain
exactly `1/Omega`, rather than being replaced by 0.15. Native beta/cutoff is
retained even where independent physical U recomputation differs in the final
binary64 bits (R-X20, R-X35 and K-20). Their `_exact_cutoff` exports were used;
the original export discrepancy is not hidden by a comparison tolerance.
The same independently validated U is used to report each role's gaps.

The TC control uses the inherited all-station threshold-count construction,
with actual loaded ratio coefficients and downward coefficient rounding. Each
GS control uses the same safe S upper bound, obtained by a fractional inventory
knapsack over the actual supports and physical stock budget. Its recorded
binary64 upper value encloses the exact rational bound. The four McCormick
directions and `Hsum<=n*W` are correct; no reverse-H row, S bucket or controller
change is present. The independent control adds W, whereas the shared control
uses the existing ratio-weighted inventory products. Each variant reoptimizes
all noncomparison variables in a fresh model with no imported Start.

## Reporting and evidence follow-up

- Compute the new comparison delta against the newly solved same-domain base;
  the diagnostic field `delta_saved` refers to the historical saved root value.
- Preserve ordinary zero gains, numerical quality, all attempted positions and
  total outer process costs. Only completed numerical optimal LPs support the
  planned objective comparison; a cutoff or unfinished primal value would not.
- Bind the additions and construction-script bytes to the final evidence.
  The plan already binds input/base/stock hashes; the then-reviewed additions
  hashes below make its TC/GS construction unambiguous. Capturing the final
  in-memory modified model before Optimize would improve direct inspection
  without another solve.
- Any full paired pilot/matrix still requires a uniform candidate choice and
  explicit command/source/cap/Seed admission based on the resulting LP evidence.

| `roots/<role>/additions.json` | SHA256 at review |
|---|---|
| K-35-U | `71e2cacae6ce4bd318c84e86c08d8c3f09d73a408001c21675ac32cfb6f84a32` |
| R-X20-S-T1 | `343a7d3243a35120b45fb76f5afcf0f24b321bb8d2e60797ff66960bd3c8a3f6` |
| R-X35-S-T2 | `6daa0f5becb473fce028b494ac852355607c9ad1a57560016447cc852ea3768a` |
| K-20-S | `8c322aebd84b18b9e962ac96ac3004a83a9b5673f4291532c97f8108193a3320` |
