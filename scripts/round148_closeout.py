"""Final navigation and English Draft PR prose from fixed saved science."""
from round148_common import *


def resume():
    assert not budget()['unclosed']
    decision=read(OUT/'candidate_decision.json');full=read(OUT/'reports/full.json')
    cost=read(OUT/'cost_report.json');m=read(OUT/'candidate_manifest.json')
    text=f'''# Round148 scientific and delivery record

Science is complete. Decision: **{decision['decision']}** (goal outcome 2).
The valid shared-first-moment family and all five positive matched LP gains
are retained as research. K35 improves supported L 2.3005% with .4608% worse
U, but RB35 loses 10.5802% in U and has a serious signed-gap regression.
Do not promote this uniform one-row root mechanism. Preserve R147's limited
standalone-D candidate and stable R137. No further experiment is queued.

## Actual scope and cost

Five new matched standalone LPs reuse five sealed complete GD models on
three instances, with zero baseline reoptimization and no extra closure
round. Four full own-H arms form same-new-PE K35 and RB35-T2 cap2400 pairs.
One short K20 cap90 producer is health qualification, not performance.
All {full['complete_Native_Optimize']} complete/qualification Native calls
returned; the five standalone LP calls are separate. No source LP, new
column, extra seed, proof/stock/RN grid or AM rescue was run.

Charged new outer cost: **{cost['charged_new_experiment_seconds']:.9f}s /
18000s**. All own H, construction, solves, qualifications, failures and
necessary supplementary verification are charged once. The fee includes
disclosed conservative reviewer observations and a 5s allowance for
unmeasured startup/serialization. Build cost is
{cost['build_seconds_separate']:.9f}s separately. Nested Runtime/Work is not
added twice; offline mathematics/authoring and public I/O are separate.
Open T_cert values are null, and cap/verification differences are not speed.

## Frozen identities and actual mechanism

Production CPP source: `{m['source_commit']}`.
New PE: `{m['production_PE']}`.
PE SHA256: `{m['production_PE_SHA']}`.
DLL SHA256: `{m['DLL_SHA']}`.
K35 executed wrapper commit: `33f6cc3ee`; RB35 wrapper commit: `116f4309c`.
See candidate_manifest.json, identity_index.json, frozen matrices and
producer identities for full hashes. Scientific/publication commits are
separate and pinned in publication_pin.json / actual PR readback.

Bare --round148-shared-s defaults off. The separate research entry/profile
are scripts/paper_s2_shared_s.py / config/gi_tbc_shared_s_round148.json;
--shared-s off selects the same-new-PE D control. Each candidate takes its
own normal root primal, appends at most one finite low affine/moment row,
discards old backend/LP/child-cache identity, migrates GD expected rows to
the new SHA without duplicating them, and solves at most one extra root LP.
All later compatible models inherit the row. Old entries/profiles retain
their bytes and meanings. All actual flags, source scope, signed rows,
Native readbacks, complete/nonminimal Starts and accepted R134 proofs pass.

## Engineering and evidence preservation

The initial short producer exposed the old one-LP/one-control-status reader
assumption. A narrow cover view omits only its original root's never-installed
bound; all calls remain in the Native/model/quality/lifecycle/cost audit.
The same sealed producer was verified without another Optimize.

After K35, the R148-local zero-GD context was corrected to choose the current
source by SHA. Fixtures cover suffix/older-generation interference,
missing/duplicate SHA and call negatives, positive-S/zero-GD support and
H/no-model omission. Synthetic support/call fixtures are unit data, not
Native results or full routing models. A real sealed sample confirms LP
kind by its actual ledger, not raw pre-relaxation integer preconditions.
Attempted full reentry after an accepted closeout was rejected and is
charged. No closeout was deleted/bypassed. Only an auxiliary root arithmetic
derivative was regenerated before the old guard, with identical domain/
coefficients and a new arithmetic timing; all producer and accepted
verification component hashes remain unchanged. An early R148 guard now
prevents that write. See engineering/reader_closed_reentry_disposition.json.

All new failures remain in the current carriers. Existing R146/R147 costs
and TC/STOCK/RN/AM historical positive/negative results remain historical.
Neither old performance panels nor preliminary rank/eta screens are rerun.

## Workspace and publication

Active tree: E:\\codes\\ExactEBRP-work\\worktrees\\paper-current.
All new build/raw/temp/restore assets remain under E:\\codes\\ExactEBRP-work.
The protected original E:\\codes\\ExactEBRP and user modifications are retained.
WORKSPACE_POLICY requires bounded current-round post-PR screening and safe
cleanup; zero deletion is acceptable. Preserve unique raw/failures, necessary
PE/DLL, active tree and old histories. Never repeat an existing fee label or
sealed producer. Never merge, force-push, delete an old branch or change defaults.

The entry main has not absorbed R147, so the verified temporary Draft PR
base is codex/round147-gd-independent-value. New carriers contain necessary
incremental evidence; old inputs are fixed-commit/member-hash references.
Anonymous bounded public byte/member recovery uses zero Optimize, compile
or commercial Native load. Final PR/readback, public recovery and actual
cleanup receipts are appended below when completed, without recursively
rewriting the fixed scientific carriers.
'''
    if (OUT/'PR_readback.json').exists():
        pr=read(OUT/'PR_readback.json')
        text+=f"\n## Actual late delivery\n\nEnglish Draft PR [{pr['number']}]({pr['url']}) is {pr['state']}, Draft={pr['draft']}, merged={pr['merged']}. Base `{pr['base']}`; snapshot head `{pr['head_sha']}`.\n"
    if (OUT/'public_restore_receipt.json').exists():
        r=read(OUT/'public_restore_receipt.json')
        text+=f"\nPublic recovery PASS={r['PASS']}: {len(r.get('archives',[]))} new carriers, {r.get('new_members_checked')} new members and {r.get('inherited_members_checked')} fixed inherited members; {r['seconds']:.6f}s pure I/O, zero Optimize/compile/Native.\n"
    if (OUT/'cleanup_record.json').exists():
        r=read(OUT/'cleanup_record.json')
        text+=f"\nBounded current-round cleanup complete: {len(r['deleted_paths'])} deleted paths, {r['deleted_logical_bytes']} bytes deleted. Unique raw/failures, required runtime and active trees remain. No old history or user content deleted. Actual logical bytes and observed volume change are in cleanup_record.json.\n"
    (OUT/'RESUME.md').write_text(text,encoding='utf-8',newline='\n')


def prbody(commit):
    assert len(commit)==40
    d=read(OUT/'candidate_decision.json');c=read(OUT/'cost_report.json');m=read(OUT/'candidate_manifest.json')
    u=f'https://github.com/yifanXovo/TailoredExact/blob/{commit}/results/unified_exact_round148'
    body=f'''Independent state-conditioned GD minima can lose the fact that all stations share one total S. This adds a default-off original-selector affine root row that retains that common first moment, with a low-only finite endpoint/kink oracle, signed conservative transport, current own-root primal binding, cache/SHA invalidation and GD expected-row migration. It adds no columns or source LP and retains both old GD rows. Previous entries/profiles and stable R137 preserve their meanings.

Five saved complete GD LPs on three physical instances gain after one appended row: K20 BASE/joint/STOCK +.002269286408/+.002459563403/+.004554385894, K35 BASE +.005381130879, RX20 BASE +.016631649658. Baseline optima are reused without Optimize and no old variable is fixed. Numerical LP values, saved-point violations, the isolated two-station strictness example and complete search are separate claims; the family enforces first moments, not a full common atomic distribution or routing hull.

{d['complete_discussion']}

Decision: **{d['decision']}**. {d['decision_discussion']}

The study stops after four full same-new-PE own-H arms (two hard-role pairs), one short health producer and five matched LPs. All 28 complete/qualification Native calls returned; the five standalone calls are separate. Seed0/Threads1, H seed20260626, original physical objectives/horizons, AM=.08, depth8, width1e-4, pair-only and AP-off remain. New experimental outer charge is **{c['charged_new_experiment_seconds']:.9f}s / 18000s**, with build {c['build_seconds_separate']:.9f}s separately. Failures and necessary verification are counted once; nested runtimes/Work and old costs are not added again. No K20/RX, extra seed, more-cut, high-deviation, RN/STOCK or AM rescue panel is queued.

Focused qualification covers exact actual-slope coefficient direction, positive-S/zero-old-GD, signed Native readback, complete/nonminimal Start, compatible children, OFF and real own-root append/reoptimization. Narrow reader repairs retain all calls and immutable closeouts; a rejected closed reentry and its auxiliary arithmetic derivative are fully disclosed. Stable and historical stronger TC/STOCK/RN results remain visible. This is a finite known-Seed0 study, not a robustness or historical-best claim.

Fixed science `{commit}`:

- [Report]({u}/final_report.md), [mathematics]({u}/mathematical_analysis.md), [LP evidence]({u}/LP_report.md)
- [Decision]({u}/candidate_decision.json), [complete results]({u}/reports/full.json), [verified trajectories]({u}/reports/verified_U_trajectories.csv)
- [Paper section]({u}/manuscript.tex), [independent review]({u}/review/final_scientific_review.json), [cost]({u}/cost_report.json), [carriers]({u}/carrier_manifest.json)

Production source `{m['source_commit']}`, PE SHA256 `{m['production_PE_SHA']}`. Wrapper, production, scientific and delivery identities are separate. Main has not absorbed R147; the verified temporary base is `codex/round147-gd-independent-value`. This remains an English Draft PR with no automatic merge/default replacement. Bounded anonymous public byte/member recovery and current-round-only cleanup are in the [latest delivery record](https://github.com/yifanXovo/TailoredExact/blob/codex/round148-shared-denominator-gd/results/unified_exact_round148/RESUME.md). All new assets stay in ExactEBRP-work; original user bytes and old history are protected.
'''
    (OUT/'PR_description.md').write_text(body,encoding='utf-8',newline='\n')


if __name__=='__main__':
    if sys.argv[1]=='prbody':prbody(sys.argv[2])
    else:resume()
