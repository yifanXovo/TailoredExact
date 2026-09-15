# Unified exact BRP research — resume here

Latest completed stage: Round69, draft PR130:
https://github.com/yifanXovo/TailoredExact/pull/130 . Evidence commit
d37ba536a99c5dc828d7d2a7f9a11d2b2d6fe3be; remote identities verified.
Branch codex/round69-vds-validation, based on Round68 final07c6e899. Read
results/unified_exact_round69/final_report.md, long_validation.md and status.md.
All16 runs complete,14580.595s paid wall,63 experiment Optimize calls,zero
failures. Same frozen VD-S binary and unchanged C++; inherited45 tests, no new
qualification. Eight Starts accepted/full-vector observed;43 initial-witness
model checks and full physical/frontier audits pass;236 compact artifacts.
No active optimizer queue. Interim remote checkpoint is dcab0020.

D3 repeats its certificate in84.687s. N12 repairs a non-startup K1-R loss and
is close to P. E7/S12 retain startup regressions. D6's3600 VD-S endpoint has
37.9339% less gap than P and54.5658% less than K1-R, with both bounds better
than P. Its large HGA timing variation and worse600 checkpoint are disclosed;
no actual time is subtracted or clean timing stability claimed. D7 at1200
retains and strengthens K1 protection:85.3013% less gap than P,34.3321% less
than K1-R, same candidate UB and stronger LB. All six long runs remain open.
These are design/public historical data, not sealed independent confirmation.

Round69 publication is complete. Startup is the remaining immediate target;
isolated uncompiled/untested
source/test drafts are in ignored build/round70_draft. They were never applied
to measured source. Any uniform common-core measurement needs new controls
for every arm. Overall goal remains unmet; continue bounded research after
publication. Never package a frozen stage against later modified C++ sources.

Previous completed stage: Round68 on codex/round68-vdp-verified-start, based on completed
Round67 PR128 final a47e86a57a1f68ca6e515877193cb8696d1aa13e. Owned checkout
E:/codes/ExactEBRP-round66. Complete, draft PR129:
https://github.com/yifanXovo/TailoredExact/pull/129 . Implementation/evidence
commit cb8d7ce560d460dfa87537cc3352c1ffe66a8e40.
Read results/unified_exact_round68/final_report.md and status.md.
VD-S adds complete paid-witness native Starts to VD-P, including retained LP
models and actual-row/readback/MIPSOL checks. All8 Starts accepted/observed.
45/45 CTests;20 runs,94 native calls,4735.860s paid wall, zero failures.
D3 cert84.172s versus all controls open300; D6 modest aligned P improvement
below material threshold; C2 cert123.640s preserved; D4 cert54.453s slower than
VD-P40.062 but much faster than K1-R129.657, P open. Useful default-off candidate.
No confirmation, extra repeat or long comparison yet. Overall goal remains unmet.
Next: separate bounded validation plan, limited repeat and informative long
window; startup work needs an admissible rule. Never package a frozen stage
against later modified source. Every substantive stage gets its own draft PR.

Completed Round67 on codex/round67-log-inventory-states, using the same owned
E:/codes/ExactEBRP-round66 checkout, based on Round66's final7c3b189 commit.
Read results/unified_exact_round67/final_report.md and status.md.
LOG replaces VD-P selector integrality with uniform binary offset codes; all
Round66 ARC and Round65 resource mechanisms are off. A shared zero-handling
domain bug was fixed before experiments. New presets explicitly require metric
travel.44/44 CTests passed. Build/round67 is separate from frozen build/round66.
All16 performance runs plus6 correctness micros completed,113 experiment native
calls,5157.483s paid process wall, zero failures. No confirmation or long-run
extension opened. VD-P certifies D4 in39.891s and C2 in132.656s and nearly matches
P's D6 gap, but loses most K1 D3 protection. LOG retains D4/C2 benefits but is
materially worse than P on D6. Default-off, overall goal unmet. Round67 draft
PR128: https://github.com/yifanXovo/TailoredExact/pull/128 . Implementation/evidence commit 1aa398ef31d8de22bc62049ca08f3adad0affd09. Next stage isolates full existing-witness native
Start integration with VD-P; see provisional_integration_question.md and its
official API review. No new experimental phase until a separate plan is saved.

User contract: results/unified_exact_round66/task_contract.txt (verbatim).
Round66 baseline: Round65 PR126, 112d6b26905848557048d52083d3709b46e15750.
Previous completed stage: Round66, codex/round66-arc-load-replacement,
E:/codes/ExactEBRP-round66. The original Round61 working directory is preserved.
Draft PR: https://github.com/yifanXovo/TailoredExact/pull/127 .
Implementation/evidence commit: 4ba0d30cc871c5affd6c88db3f1dbd956fd3096b.

Read results/unified_exact_round66/final_report.md, research_map.md and status.md
before further work. Full historical reports R51–65 already read; do not restart
the audit. Completed Round66 tested exact replacement of node load recurrences
with arc-load flow, compared to paid K1-R and unmodified official P-GRB.

R65 credit/projection decisions are inadmissible formal algorithm components
under the new contract. They are off. Reliability means verified candidate
retention and immediate zero-objective termination only. No default/main merge.

Stage66 resource plan and practical effect thresholds were written before runs.
The write-ahead process ledger is the authority on attempts and actual cost.
Round66 acceptance: exact, default-off, mixed development results. D4 certifies
107.375s versus K1-R129.391 and Q-PLUS152.766; C2 gap at300 improves28.2%
against K1-R and60.4% against P-GRB. D6 gap at600 remains18.7% worse than P;
the primary proof deficit is not repaired. E7/E8 differences mostly startup.
All19 experiments audited, 17 performance+2 micro, 94 experiment optimize calls,
3696.157 seconds paid process wall; seven build-only exports separately.
No confirmation or3600-second comparison opened. Actual result tables preserve
all negative and positive evidence. Do not impose a new per-point K1 veto.

Next stage: inventory-state product representation, with ARC off. Reassess VD-P
under the new P-GRB-led criterion and compare a logarithmic state encoding with
the same LP projection. See next_hypothesis.md. Near-zero LP-gain sensitivity
in the D4 Q-PLUS controller is an additional open attribution issue. Declare the
new stage's bounded resource plan before optimization; don't inherit R65 budgets.
Overall target remains active and unmet. A stage draft PR is not completion.
