# Independent repaired-build Seed1 admission

Decision: **ACCEPT** the new exact matrix SHA256
`60f9c2fdb91c1ccdc94b4d9bc32a60cb48fd507e212118dedcb586dd2bbdaebc`.
Reviewer: `/root/independent_review`; 2026-10-29 (Asia/Shanghai).
The earlier unused matrix/gate remains in `repair/seed1_pre_coefficient_fix`.
This review started no Optimize or commercial library.

## Repair and preserved primary identity

The actual tiny-alpha native readback failure is a real coefficient-transport
failure and is retained with its 4.3128927000798285s diagnostic cost. Its repair
only scales a new stock row when its nonzero slope is below 1e-12, by the
smallest positive power of two bringing that slope to at least 1e-12.
Every coefficient and the already outward RHS receive the same finite exact
`ldexp` scale. This preserves the row's outward validity. Ordinary domains
retain scale one and the same row text; no tolerance or proof policy changes.

V2 source is `04506fa613446d2ef2bd19794f778909422c51fd`; its PE SHA256 is
`f4c764ff7164bf042ef612403f82b850698b97c80018bf06b2feff1167d65403`.
Only `src/CplexBaseline.cpp` differs in production source. I checked current
V2 source, PE, build object hashes and all 316 entries of the preserved V1
source/helper carrier. The original V1 source `839283773...`, PE, primary
manifest/matrix and all eleven measured primary results keep their identity.

Actual qualification contains seven V2 domains and 25 unique used V1 models,
32 native reads with zero Optimize. The tiny-alpha rows use scales
(16,1,1,16); every other qualification row uses one. The V1 bridge covers all
33 original STOCK call contracts, whose positive endpoint minimum is
0.21232492258182034. None enters the repaired branch, and actual native
coefficient/RHS maps match all four intended rows. No primary run was repeated.

The metadata amendment separates inherited V1 build/qualification/time from
V2 records. I verified that its preserved before-records differ only in the
declared identity fields/bindings, with native results unchanged. The current
V2 manifest SHA is
`aea824a4d1e1b85ef7e4f77fa8b447599791db516cb99ab2ab77cf7089823317`.

## New four-position matrix

| Position | Role | Method | Physical T | Lambda | Compute cap |
|---|---|---|---:|---:|---:|
| 1 | K-20-S | BASE | 5400 | 0.15 | 1200 |
| 2 | K-20-S | STOCK V2 | 5400 | 0.15 | 1200 |
| 3 | R-B35-S-T2 | STOCK V2 | 7200 | 0.055125275219827186 | 2400 |
| 4 | R-B35-S-T2 | BASE | 7200 | 0.055125275219827186 | 2400 |

The same two unique roles test the main certificate benefit and largest Seed0
upper-endpoint regression; the second pair reverses method order. Exact
commands differ from their respective Seed0 method only in Seed, fresh output
directory and the explicitly declared STOCK V2 executable. Input hashes,
physical/objective doubles, caps, AM .08, AP/TC off, H and proof policy remain.
Actual CLI, panel, launch and prereg all specify Gurobi Seed1. H remains 20260626,
with one thread and affinity 4. Both methods pay their independent complete
lifecycle. No incoming Start, solution, bound or tree path appears.

All four identity hashes and selection/matrix/script/private-reader/repair
helper/manifest/bridge bindings matched. All four raw destinations and fee
labels were absent. The unused original script, selection, matrix, gate and
identities were preserved before re-registration.

The private admission keeps the original primary gate and frozen helper
checks, adjudicates historical V1 source against its exact preserved carrier,
and separately checks current V2 source/PE. The private row-reader adapter
changes only the expected four-row generator while retaining the inherited
type, physical, H, Start, modern baseline lifecycle and proof checks. Its
closure/super dispatch and namespace isolation were statically reviewed.
Run the planned pure row-reader preflight before native launch.

The matrix's `source_and_PE_unchanged` is interpreted within this qualified
new V2 matrix. STOCK explicitly records a build change from primary V1. This
second-Seed evidence must not be described as an isolated Seed-only comparison,
and it must never replace ordinary adverse/open primary outcomes.

At review there was no open fee. Charged computation was 12209.893986799987s,
with 74190.10601320001s remaining, covering the 7200s maximum new caps.
Keep failure/repair costs and all version identities. Actual Seed1 results and
later integrated paper/public/PR/cleanup acceptance remain separate.
