"""Narrative and scope tables from the already raw-rebuilt Round108 reports."""
import argparse, csv, hashlib, json
from pathlib import Path

BASE='b5db3f038f64215766a54498d8acc82e384de733'
ROUND='results/unified_exact_round108'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write_text(path,text):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def table(path,data):
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(data[0]));w.writeheader();w.writerows(data)
def fmt(value):
    if value in ['',None]:return 'null'
    v=float(value)
    return f'{v:.3e}' if abs(v)<1e-8 and v else f'{v:.10f}'
def evidence_link(path):return f'https://github.com/yifanXovo/TailoredExact/blob/{BASE}/{path}'

def finish(root):
    root=Path(root).resolve();out=root/ROUND;report=out/'reports_final';summary=read(report/'summary.json')
    selection=read(report/'selection_decision.json');gate=read(report/'admission_decision.json')
    assert read(out/'selection_decision.json')==selection and read(out/'admission_decision.json')==gate
    arms=rows(report/'arms.csv');pairs=rows(report/'pairs.csv');mechanisms=rows(report/'mechanism_summary.csv');stage=selection['stage']
    cancelled=selection['cancelled_arms'];manifest=read(out/'input_manifest.json')
    interpretations={
        'SELECT_MB_FOR_BROAD_EVALUATION':'The exact frozen M-B is selected for broader paper evaluation. This is a resource/candidate decision, not proof of stable generalization or completed paper qualification. ENS-C remains the default.',
        'STOP_MB_REOPENING_AT_BRIDGE':'The complete bridge does not justify paying for the fifteen confirmation arms. All fifteen were cancelled before native launch. This closes this reopening, without rejecting every M-B variant or qualifying ENS on the untouched inputs.',
        'NO_NEW_UNIFORM_CANDIDATE_SELECTED':'The bridge admitted confirmation, but the prespecified positive conditions were not met or became unreachable. No new uniform candidate is selected. M-B retains its scoped research record; ENS is the current reference and is not automatically qualified on unmeasured inputs.'}
    lines=[f'# Round108: {stage}','',interpretations[stage],'',
        'The study compares only original cold P-GRB, full ENS-C and the inherited R100 M-B. There is no production source change, new cut, new algorithm variant, tuning, instance dispatcher or default replacement. The added work is a current comparable build, frozen input/measurement protocol, conditional confirmation and auditable selection.','',
        '## Current complete paired results','',
        '| Stage / role | Arm | Physical T | Cap | Complete seconds | Own physical U | Qualified complete-cover L | Signed U-L | Certified |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for a in arms:lines.append(f'| {a["campaign"]} / {a["id"]} | {a["arm"]} | {a["T_seconds"]} | {a["cap_seconds"]} | {float(a["complete_seconds"]):.3f} | {fmt(a["U"])} | {fmt(a["L"])} | {fmt(a["gap"])} | {a["certificate"]} |')
    lines+=['','Every U has its own full fleet and independently recomputed inventory, objective, empty departure, prefix/return capacity, unique nonzero one-direction integer service and closed travel/handling duration. No cross-arm UB, Start, route, cut or cache is used. Tiny signed negative gaps remain visible; invalid contradictions are rejected. Relative gap is null at the original 1e-12 zero tolerance and for missing/unqualified values. Complete certification is reconstructed from scope/cover, actual native statuses/provenance and physical U, never from a zero summary gap alone.','',
        '| Role | M-B vs P | Severe P regression | M-B vs ENS | Severe ENS regression |',
        '|---|---|---|---|---|']
    for role in ['F2','C2','S12','B24','L48','F5','N36']:
        p=next((p for p in pairs if p['id']==role and p['control']=='P-GRB'),None);e=next((p for p in pairs if p['id']==role and p['control']=='ENS-C'),None)
        lines.append(f'| {role} | {p["classification"] if p else "NOT_STARTED_CANCELLED"} | {p["severe_regression"] if p else "not observed"} | {e["classification"] if e else "NOT_STARTED_CANCELLED"} | {e["severe_regression"] if e else "not observed"} |')
    certificate_wins=[p['id'] for p in pairs if p['control']=='P-GRB' and p['classification']=='WIN' and p['basis']=='candidate_only_complete_certificate']
    other_wins=[f'{p["id"]} ({p["basis"]})' for p in pairs if p['control']=='P-GRB' and p['classification']=='WIN' and p['basis']!='candidate_only_complete_certificate']
    lines+=['',f'Material P gains established by complete certification within the window: {", ".join(certificate_wins) or "none"}. Other material P gains: {", ".join(other_wins) or "none"}. Certificate-priority gains do not require the own UB difference separately to reach the dual-uncertified UB threshold. Complete time ratios are reported only when both methods certify.']
    risks=[p for p in pairs if p['classification'] in ['LOSS','MIXED']]
    if risks:
        lines+=['','Observed losses and mixed tradeoffs:']
        for p in risks:
            if p['candidate_certified']=='True' and p['control_certified']=='True':
                detail=f'complete time increase {float(p["candidate_seconds"])-float(p["control_seconds"]):.6f}s, threshold {float(p["a_t"]):.6f}s'
            else:
                detail=f'own U {fmt(p["candidate_U"])} versus {fmt(p["control_U"])}, signed gap {fmt(p["candidate_gap"])} versus {fmt(p["control_gap"])}, candidate/control certificates {p["candidate_certified"]}/{p["control_certified"]}'
            lines.append(f'- {p["id"]} versus {p["control"]}: {p["classification"]}; {detail}; severe regression={p["severe_regression"]}.')
    s12=next((p for p in pairs if p['id']=='S12' and p['control']=='P-GRB'),None)
    if s12 and s12['basis']=='both_complete_certificate_time':
        lines+=['',f'S12 is {s12["classification"]}: the complete P time benefit is {float(s12["time_improvement"]):.6f}s against its {float(s12["a_t"]):.6f}s materiality floor. Its small easy certified result is retained without substitution.']
    lines+=['',f'Exact prospective four-role count: WIN={selection["unseen_WIN"]}, LOSS={selection["unseen_LOSS"]}; denominator remains S12/B24/L48/N36. Complete formal arms={len(arms)}; cancelled arms={len(cancelled)}. F2/C2 are development bridges, F5 is known stress, and H100 is functional qualification. The 21 registered arms are not 21 independent new samples. No cross-instance mean of unnormalized objectives or precise speedup of censored proof times is reported.','',
        f'F2 gate={gate["gates"]["F2"]["passed"]}; C2 gate={gate["gates"]["C2"]["passed"]}; joint admission={gate["bridge_pass"]}. All six current bridge arms were completed. Relative ENS dominance is not a hidden condition. Pair thresholds, certificate priority, absolute materiality, severe-risk definitions, and exact early-cancellation conditions remain the preregistered rules. `pairs.csv` and `worst_losses.csv` disclose all ENS losses and MIXED tradeoffs.','',
        '## Prospective inputs and observed mechanism scope','',
        'S12/N36 retain their original R106 bytes. Independent retained-history scans used their exact path/SHA, distinguished unrelated old S12 aliases, and found no prior solver/LP measurement. B24/L48 were single deterministic draws under `round108-uniform-candidate-confirmation-v1`, using existing landscape/writer code and no solver, difficulty screening or reseeding. A depot-inclusive parser assertion failed before any new draw; that failure and same-recipe repair are preserved. These are new draws/structure combinations, not new cities or independent data-generating distributions.','',
        'B24 has balanced original/target station totals; any legal zero result is retained rather than replaced. L48 has positive weights, lambda .15 and original stock below target total. Empty-departure stock conservation therefore prevents every target ratio from being one, excluding F=0 without establishing difficulty. Measured confirmation evidence becomes seen evidence for later design.','',
        '`controller_*`, `frontier.csv`, `leaf_obligations.csv`, `native_calls.csv`, `models.csv`, `starts.csv` and `native_type_readbacks.csv` report actual startup, original lookahead LP/partial/terminal calls, AM actions/targets, active covers, epochs and declared/restored domains. A lookahead child LP is not a committed multileaf split. M-B keeps integer routes and does not use R107 assignment-event or route-oracle counts. Actual submitted Start CSVs check every column/type/bound/row; native full-model counts confirm MIP restoration. Native accepted physical witnesses pass the unchanged all-quantity guard before decoding and are independently checked as integer operations. This is not retention of every native branch variable or a native-tree identity claim.','',
        '`time_partitions.csv` separates startup-before-exact, original LP native inclusive, MIP/callback native inclusive, controller/model/mapping/write residual and prelaunch/postexit audit. AM/mapping/callback parts lacking an independent timer remain merged. Nested native seconds are not added to fees. `checkpoints.csv` marks only actual observed 300/600/900/1200/1800/3600/5400 windows; reserve-ending and early-completed missing checkpoints are not extrapolated. `optimal_witness_bounds.csv` exists only for roles with reliable original Fstar and uses a safe [0, committed-observation upper] interval, not exact first native discovery time.','',
        'Actual formal mechanism exposure (counts from raw returned-call/AM/cover ledgers):','',
        '| Role | Arm | LP | Partial target MIP | Terminal MIP | AM actions | Maximum open relevant leaves |',
        '|---|---|---:|---:|---:|---|---:|']
    for m in mechanisms:
        if m['campaign'].startswith('qualification'):continue
        lines.append(f'| {m["id"]} | {m["arm"]} | {m["LP_calls"]} | {m["partial_target_MIP_calls"]} | {m["terminal_MIP_calls"]} | {m["AM_action_counts"]} | {m["maximum_open_relevant_leaves"]} |')
    multi=[f'{m["id"]} / {m["arm"]}' for m in mechanisms if not m['campaign'].startswith('qualification') and m['multiple_open_relevant_leaves_observed']=='True']
    lines+=['',f'Current original-controller exposure with multiple open relevant leaves: {", ".join(multi) or "none"}. Partial-target counts include original child-bound and next-leaf targets, with separate subcounts in the raw-rebuilt mechanism table. A saved open leaf is discharged only after its complete true-G partition and already available bounds independently exclude improvement of the own physical U. This finite M-B/ENS exposure does not reopen the stopped R107 assignment/STRUCT configuration or establish a causal split/type/A-B speed attribution.']
    lines+=['','## Inheritance, resources and recovery','',
        f'The [R100 candidate freeze]({evidence_link("results/unified_exact_round100/candidate_freeze.json")}), [report]({evidence_link("results/unified_exact_round100/final_report.md")}) and [frozen mathematics]({evidence_link("results/unified_exact_round100/mathematical_algorithm.md")}) establish the inherited candidate, implicit p/d integrality and valid A/B. R100 M-B had F2/C1 ENS delays and weaker F5 ENS quality, alongside P gains on C2/N2 and certification roles. This round cannot separately identify p/d declaration and A/B contributions or infer native speed from root LP strength.','',
        f'[R107 report]({evidence_link("results/unified_exact_round107/final_report.md")}) preserves STOP_TESTED_CONFIGURATION: F2 ENS certified at 539.500s while FRONTIER did not; C2 GLOBAL/FRONTIER U≈.3750564073 and L≈.1891247571 versus P U≈.1983028486. Both FRONTIER runs exposed three original lookahead LPs, root partial target/requeue/cache and root terminal, with no actual multiactive-leaf split. Noninitial cross-request cache/remap exposure was 0. Integer-operation/Y event prefixes 104 (F2) / 2465 (C2) matched GLOBAL; complete native trees, bases and all-variable identity were not established. That tested AM/backend combination is not reopened here.','',
        f'Measured production source content is inherited R107 delivery `{BASE}`. Current PE SHA `{summary["PE_SHA"]}`; actual Gurobi 13.0.2 DLL SHA `{summary["DLL_SHA"]}`. Source/tool/input/full argv bindings are in `candidate_identity.json` and campaign identities. Threads 1 / Seed 0 / Presolve Auto, gaps 0, FeasibilityTol/OptimalityTol 1e-6 and IntFeasTol 1e-5 are read back. The running F2-P actual PE/DLL module sample is retained. Pure reader repairs do not rerun performance. The original decision reader and later actual engineering attempts have source snapshots and receipts; the initial route-I/B diagnostic failure retains its traceback, but its exact whole-script snapshot and elapsed time were not captured. `reproduce.md` records this limitation.','',
        'The independent through-F5 audit initially rejected a source-vehicle comparison because it omitted the inherited equal-capacity route normalization before Start mapping. The existing mapper stably orders nonempty routes by operation count within each capacity class and assigns ascending vehicle IDs. The corrected independent audit checks the complete x/conn/z/mode/p/d/load/ord/Y/state/G vector against that precisely normalized own fleet, in addition to all native columns, types, bounds, rows and objective. The failed audit and exact source/receipt/diagnosis are retained; 24 finite normalization cases and R100 function/call-site bindings passed. Production, performance commands, primary reconstruction and selection rules were unchanged; no performance rerun was used.','',
        'Historical measured identities are not current performance arms: R107 production source `bb0017620008f9c98e40ba032d022f52f4f23788`, PE `364501ac3dd2599834ee2bf40ccceca2d6c01bbb761cdc706f141832619088a2`; R100 frozen source `b5d6d83bb8fc74682de6f1f6862c2e687712f4cf`, PE `fd2a30ea0bdba13dda7c19ee69e8c1f7f874482f3dad7cb2c1df48c4d7404f64`. Historical file paths and exact byte SHA values are pinned separately in the public carrier manifest.','',
        f'Additional retained family decisions use the public [R98]({evidence_link("results/unified_exact_round98/final_report.md")}), [R99]({evidence_link("results/unified_exact_round99/final_report.md")}), [R102]({evidence_link("results/unified_exact_round102/final_report.md")}), [R105]({evidence_link("results/unified_exact_round105/final_report.md")}) and [R106]({evidence_link("results/unified_exact_round106/final_report.md")}) reports, with exact dependency SHA values in the same manifest. R102 remains a genuine service-resource increment with mixed results and research opt-in/default-off status; it is not relabelled as a stopped family.','',
        f'Paid conservative starts={summary["conservative_starts"]}/48; outer solver fee={summary["outer_solver_fee_seconds"]:.9f}/80000 seconds. Actual Optimize={summary["actual_Optimize"]}, returned={summary["Optimize_returned"]}, IIS=0, route-oracle=0. Qualification, every native child and enclosing wrapper are charged once; unused preregistered fallback children remain conservatively charged. Failures and cancellations are retained. Build, reader, independent review, packaging and recovery are engineering work.','',
        'The complete raw carrier and precise small public historical dependencies are described in `compact_evidence/manifest.json` and `reproduce.md`. Actual export to a new public-only directory, new isolated restoration, exact all-field CSV/decision comparisons and independent isolated physics/cover/selection review have separate public receipts. No PE, DLL, license file or credentials are distributed. This is evidence/mathematical reconstruction, not an independent engine performance rerun.','',
        'The remaining evidence and historical mechanism decisions are in `reports_final/candidate_evidence_gap.csv` and `reports_final/stopped_mechanism_families.csv`. A positive stage requires broader prospective paper evidence for this same uniform candidate; a negative stage does not automatically fund another M-B/STRUCT mechanism layer.']
    input_lines=['','Frozen role identities and exact input bytes:','',
        '| Role / identity | V/M | Q | Physical T | Cap | Order | Input SHA256 |',
        '|---|---|---|---:|---:|---|---|']
    for p in manifest['roles']:
        input_lines.append(f'| {p["id"]} / {p["role_identity"]} | {p["V"]}/{p["M"]} | {p["Q_vector"]} | {p["T_seconds"]} | {p["cap_seconds"]} | {", ".join(p["method_order"])} | `{p["input_sha256"]}` |')
    input_lines+=['','All roles use pickup/drop 60 seconds and lambda .15. Source input and prototype identities are pinned before the first formal arm.']
    for role in ['B24','L48']:
        landscape=read(root/'reference/round108_confirmation'/f'{role}_landscape.json')
        input_lines.append(f'{role}: station-only original/target stock totals {sum(landscape["initial"])}/{sum(landscape["target"])}, weight range [{min(landscape["weights"]):.6f}, {max(landscape["weights"]):.6f}]. Depot placeholders are excluded.')
    index=lines.index('## Prospective inputs and observed mechanism scope')
    lines[index+1:index+1]=input_lines
    write_text(out/'final_report.md','\n'.join(lines)+'\n')
    print(json.dumps(dict(stage=stage,arms=len(arms),cancelled=len(cancelled))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();finish(a.root)
