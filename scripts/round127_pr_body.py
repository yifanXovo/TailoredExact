"""English stacked-Draft description from sealed results and actual receipts."""
from round127_common import *
def body():
    s=read(OUT/'stratified_summary.json');selection=read(OUT/'tuning_selection.json');q=selection['selected'];b=budget()
    values='\n'.join('| '+key+' | '+str(value['classes'])+' | '+str(value['directions'])+' |' for key,value in s['core_by_comparison'].items())
    recovery=read(OUT/'public_restore_receipt.json') if (OUT/'public_restore_receipt.json').exists() else None
    text=f'''This is the complete Round127 v3 replacement study, stacked on `codex/round126-small-instance-certification`. Frozen M-B / GI-TBC remains the sole paper algorithm. Production defaults are unchanged; the added research controls are off by default.

The original 36 E0 arms are retained: twelve six-problem Seed1 arms and twenty-four tiny Seed/repeat arms. The added design specifies at most 21 E1 core arms and all 36 bounded offline P-training positions. E0 is byte-frozen; E1 training/core use one separately qualified executable and the same 13.0.2 DLL. Evaluation has nine distinct inputs; training has three separate inputs. Shared arms, repeated Seeds and different executables are not independent problems.

Execution is **PARTIAL**: the required MD inclusive-root/own-U0-Start guarantee conflicts with the retained documented no-strict-improver equality closure, so all three MD formal arms were blocked before evaluation. This is not a D-effect result or a blanket revocation of frozen MB's proof policy. All unaffected prescribed positions completed; there are {s['observed_formal_arms']} actual formal arms and {s['PT_aliases']} PT aliases. No replacement experiment, outcome-driven retry, cap extension or additional tuning configuration was added.

The predeclared six-configuration screen selected **{q['id']}**, MIPFocus={q['MIPFocus']}, Cuts={q['Cuts']}, using all36 complete qualified training positions. Selection was committed before E1 evaluation. {'PT is the same P observation and has no independent denominator.' if q['id']=='q0' else 'The one selected parameter file was applied unchanged to every held-out known role, including adverse outcomes.'} Open penalties are never substituted for certification times.

Seed1: {s['main']['classes']}; tiny: {s['tiny']['classes']}. All time directions use unrounded complete production cost. Ratios use only both-certified intersections; both-open stays undetermined and blocked/invalid evidence stays unevaluable.

| Core comparison | Nonalias typed statuses (including blocked entries) | Directions |
| --- | --- | --- |
{values}

Validation includes E0/E1 default full-model/type/objective equivalence, filename/directory invariance, exact declared row/column deletions at root and child scopes, complete H/fleet replay, physical boundary vectors, actual parameter readback with cold Starts, all sealed endpoints/clocks, independent finite selection/comparison review, and saved-root-point explanations without extra Optimize. Numerical certificates retain the original tolerance/coverage contract; these finite checks are not universal rational matrix proofs.

The first nine training receipts retain their original omitted import prefix. One fixed complete clock for all36 uses the recorded parent admission marker and sealed end; no arm was rerun and no fee prefix is charged twice. The complete reading manuscript/PDF retains the R125 mathematical derivations and R122/R123/R126 positive and negative history. Source/identity bindings and finite raw carriers exclude executables, DLLs, licenses, credentials, fonts and external full papers.

Current outer accounting: {b['paid_outer_seconds']:.3f} / 54000 seconds, including separately labeled conservative administrative allowances; nested H/LP/MIP seconds are not added again. The only next priority is substantive review of the MD inclusive-root/retained-closure specification; this PR executes no follow-up algorithm or expanded experiment.

'''
    text+=f"One anonymous public recovery passed from science commit `{recovery['commit']}`, with {recovery['files']} files, all finite carrier checks and zero Optimize/native starts. The recovery receipt is in `results/unified_exact_round127/public_restore_receipt.json`.\n" if recovery else 'The single necessary anonymous science-commit recovery will be recorded after this Draft PR is published.\n'
    text+='\nEvidence entry point: `results/unified_exact_round127/final_report.md`; four-axis tables in `stratified_summary.json`, full per-arm/pair CSVs, complete manuscript/PDF, review actions and finite export manifest.\n'
    return text
if __name__=='__main__':
    target=TEMP/'PR_BODY.md';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body(),encoding='utf-8');print(str(target))
