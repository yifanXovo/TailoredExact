# Narrow generator and final-entry review

Separate reviewer `/root/independent_review`, 2026-10-27 (Asia/Shanghai).
Read-only source/small-metadata checks during active arm013; no heavy reader
import, raw enumeration, solver, build, aggregation, archive, PDF or native load.
Only this review file was written. This is not final stage acceptance.

## Future generator correction: PASS

The new `b1_route_time` table exactly matches the preregistered six values:
compact/regional T=3600/5400 (n15), 5400/7200 (n20), 7200/10800 (n35).
An isolated AST extraction of that pure table function confirms all six cases;
all six new B1 inputs and their frozen launch T values match it. No generator
module was imported and no input was regenerated.

The historical generator at the manifest's recorded recipe commit
`efd1a92c97c0e54866a270cf6f5bae29670f7f32` independently hashes to
`b0afb6de9beb697a3616839713aa5bd9bb57b43f2db60153f34ee3e39afb8630`,
matching source_recipe and future_generator_table_fix. The current corrected
file hashes to
`d06a75f729bd57eb2664328dc039d55001a422d7a349cbad03a5e6a4bed4866f`.
The recipe's actual byte hash still matches input_manifest.recipe_SHA.

The original multiplier would have produced n20 regional T8100. Its actual
N-X20-B metadata was corrected to the preregistered7200 before matrix admission
and before native runs, as the retained pregeneration correction records.
Its input SHA remains the recorded `c211a113...81684`. The later source-table
fix is correctly labelled future-only; it does not claim the corrected source
performed the once-only historical draw. Keep both identities and that receipt.
The old recipe source-hash guard intentionally remains: current corrected code
must not silently masquerade as the historical generator when replaying that
old recipe. Frozen actual inputs/settings are the current evidence authority.

`round137_setup.py` is absent from the frozen execution helper graph and the
production source-hash set. The measured matrix remains
`26f295da36097cd662b9c2ca049ab2452f0b295dfcdb12dd4b726ff25190c894`.
This source-only correction requires no measured identity change or native run.

## Current entry and smallest later promotion

`paper_s2.py` still defaults to `config/paper_s2.json`, whose default PE is
historical R135. The new `config/gi_tbc_round137.json` already names GI-TBC,
records S2 as historical alias and ms2 as implementation, retains AP off and
ENS-C compatibility default, and matches the actual Round137 production-source
commit/PE SHA. Its argv and normalized-flags map are exactly the historical
accepted vector; this is a versioned entry change, not a new algorithm.

Dependency distinction matters: neither `paper_s2.py` nor either config file is
a measured Python helper or production translation unit. However the frozen
candidate explicitly records **config_SHA of paper_s2.json**, and the planned
source capsule includes both configs as required configuration files. Preserve
that file's historical bytes and the candidate binding; do not replace it in
place or rewrite frozen metadata to promote a new display name.

After experiments and final scientific review, the smallest promotion is:

1. Point the existing thin `paper_s2.py` default CONFIG to the versioned
   `gi_tbc_round137.json`; update its human-facing description/help/errors to
   GI-TBC and retain the existing filename/CLI as the S2 compatibility alias.
   Keep the existing dry-run behavior, output refusal, complete-vector check,
   PE/DLL binding and producer-versus-formal-audit distinction.
2. In the new GI-TBC config, label the inherited R135 `authority` explicitly as
   argv provenance and add current candidate/matrix authority. Do not describe
   the old16-launch comparison as a new Round137 verification. Record the
   unified .08/depth8/width1e-4/H policy as stage metadata if useful.
3. Update the current mainline/release guide to the formal GI-TBC name and
   actual versioned config/source/PE, keeping S2 historical, ms2 implementation,
   AP off and bare-executable ENS-C compatibility behavior explicit. Validate
   final expanded dry-run vectors against actual current default S2 launches
   without Optimize. No new wrapper family or CLI refactor is needed.

Do not perform this promotion while the current queue is running. It needs no
experiment rerun, source/PE rebuild or reinterpretation of earlier results.
