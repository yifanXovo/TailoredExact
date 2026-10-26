"""English stacked-Draft description from sealed results and actual receipts."""
from round127_common import *
def body():
    s=read(OUT/'stratified_summary.json');selection=read(OUT/'tuning_selection.json');q=selection['selected'];b=budget()
    values='\n'.join('| '+key+' | '+str(value['classes'])+' | '+str(value['directions'])+' |' for key,value in s['core_by_comparison'].items())
    recovery=read(OUT/'public_restore_receipt.json') if (OUT/'public_restore_receipt.json').exists() else None
    tiny_notes='\n'.join(f"- {t['id']}: {t['both_certified_pairs']}/6 both-certified, {t['P_only_count']} P-only, {t['dt_ge10_count']} observed MB delays >=10 seconds; median delta={str(t['median_dt'])+' seconds' if t['median_dt'] is not None else 'N/A'} ({t['median_scope']})." for t in s['tiny_risks'])
    repaired=OUT/'tiny/07_SM-B10-B_S0_R1/raw/01_SM-B10-B_S0_R1_MB'
    repaired_producer=read(repaired/'producer_receipt.json');repaired_total=read(repaired/'arm_total_receipt.json')
    text=f'''This is the complete Round127 v3 replacement study, stacked on `codex/round126-small-instance-certification`. Frozen M-B / GI-TBC remains the sole paper algorithm. Production defaults are unchanged; the added research controls are off by default.

The original 36 E0 arms are retained: twelve six-problem Seed1 arms and twenty-four tiny Seed/repeat arms. The added design specifies at most 21 E1 core arms and all 36 bounded offline P-training positions. E0 is byte-frozen; E1 training/core use one separately qualified executable and the same 13.0.2 DLL. P/PT are independently paid cold compact runs without H or a Start; each MB-type arm independently pays H. E1 has its own fresh P/MB comparators. Evaluation has nine distinct inputs; training has three separate inputs. The six main, twelve tiny and 21 core typed entries share arms and repeated inputs, so 39 entries are not 39 independent trials.

Execution is **PARTIAL**: the required MD inclusive-root/own-U0-Start guarantee conflicts with the retained documented no-strict-improver equality closure, so all three MD formal arms were blocked before evaluation. This is not a D-effect result or a blanket revocation of frozen MB's proof policy. All unaffected prescribed positions completed; there are {s['observed_formal_arms']} actual formal arms and {s['PT_aliases']} PT aliases. No replacement experiment, outcome-driven retry, cap extension or additional tuning configuration was added.

The predeclared six-configuration screen selected **{q['id']}**, MIPFocus={q['MIPFocus']}, Cuts={q['Cuts']}, using all36 complete qualified training positions. Selection was committed before any formal evaluation. {'PT is the same P observation and has no independent denominator.' if q['id']=='q0' else 'The one selected parameter file was applied unchanged to every held-out known role, including adverse outcomes.'} Open penalties are never substituted for certification times.

Seed1: {s['main']['classes']}, directions {s['main']['directions']}; tiny: {s['tiny']['classes']}, directions {s['tiny']['directions']}. All time directions and >=10-second flags use unrounded complete production cost, including small reverse directions. Ratios use only both-certified intersections; both-open stays undetermined and blocked/invalid evidence stays unevaluable.

{tiny_notes}

The evidence is mixed within its stated scope. Seed1 retains MB's five certifications while P changes from three at Seed0 to two. Two tiny observations favor P by less than 0.1 seconds. In the same-build core panel, deleting C_R or three-station rows is faster in both certified roles (on K2, MR 743.130 and MS2 679.866 seconds versus MB 966.283); C_G supports MB with one faster both-certified result and one MB-only certificate. All executed K3 methods remain open. Although q2 improved the training count from three to four, PT has zero held-out certifications versus default P's one, so this screen has not demonstrated held-out baseline enhancement. MB/PT retains two MB-only certificates and one both-open result, with no both-certified speed ratio.

| Core comparison | Nonalias typed statuses (including blocked entries) | Directions |
| --- | --- | --- |
{values}

Validation includes E0/E1 default full-model/type/objective equivalence, filename/directory invariance, exact declared row/column deletions at root and child scopes, complete H/fleet replay, physical boundary vectors, actual parameter readback and zero Starts in P/PT, all sealed endpoints/clocks, independent finite selection/comparison review, and saved-root-point explanations without extra Optimize. Component interpretation additionally requires actual target-row exposure, complete identical H actions/fleet and matched root scope; other timing observations remain whole-method diagnostics. Numerical certificates retain the original tolerance/coverage contract; these finite checks are not universal rational matrix proofs.

All nine saved-root deletion checks match H/scope and actual deletions. No ordinary deleted row is violated at those saved points, all three MG W-extension intersections are nonempty, and the LP values agree within the recorded tolerance. This is finite point evidence, not global row redundancy or a monotonic MIP-time claim.

The first nine training receipts retain their original omitted import prefix. One fixed complete clock for all36 uses the recorded parent admission marker and sealed end; no arm was rerun and no fee prefix is charged twice. The complete reading manuscript/PDF retains the R125 mathematical derivations and R122/R123/R126 positive and negative history. Source/identity bindings and finite raw carriers exclude executables, DLLs, licenses, credentials, fonts and external full papers.

Tiny07 MB was produced only once at {repaired_producer['T_produce']:.9f} seconds. Its empty-vehicle handoff serialization was corrected only in the post-seal reader; full verification and an independent finite physical/model/return/cover check passed without a native retry. All failed audit/review attempts and fees remain. The actual recovery-inclusive T_verify={repaired_total['T_verify']:.9f} and T_total={repaired_total['T_total']:.9f} seconds are retained separately from its original production/certification cost.

Current outer accounting: {b['paid_outer_seconds']:.3f} / 54000 seconds, including separately labeled conservative administrative allowances; nested H/LP/MIP seconds are not added again. The only next priority is substantive review of the MD inclusive-root/retained-closure specification; this PR executes no follow-up algorithm or expanded experiment.

'''
    text+=f"One anonymous public recovery passed from science commit `{recovery['commit']}`, with {recovery['files']} files, all finite carrier checks and zero Optimize/native starts. The recovery receipt is in `results/unified_exact_round127/public_restore_receipt.json`.\n" if recovery else 'The single necessary anonymous science-commit recovery will be recorded after this Draft PR is published.\n'
    text+='\nEvidence entry point: `results/unified_exact_round127/final_report.md`; four-axis tables in `stratified_summary.json`, full per-arm/pair CSVs, complete manuscript/PDF, review actions and finite export manifest.\n'
    return text
if __name__=='__main__':
    target=TEMP/'PR_BODY.md';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body(),encoding='utf-8');print(str(target))
