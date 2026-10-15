"""Publish an honest incomplete-batch report; never infer unrun performance."""
from round121_common import ROOT,OUT,read,write,sha
from round121_blocked_core import reconstruct
from round121_finish_report import table
import time,json

def finish():
    tick=time.perf_counter();v=reconstruct();b=v['resource'];m=read(OUT/'input_manifest.json')
    write(OUT/'blocked_current_core.json',v);write(OUT/'stage_decision.json',v['stage'])
    write(OUT/'all16_arms.json',v['formal_slots']);write(OUT/'all18_pairs.json',v['pair_slots'])
    table(OUT/'all16_arms.csv',v['formal_slots']);table(OUT/'all18_pairs.csv',v['pair_slots'])
    write(OUT/'fixed_position_status.json',dict(positions=v['formal_slots'],formal_slots=16,actual_formal_arms=0,
        all_actual_once=False,all_formal_positions_not_started=True,reason=v['stage']['blockers'][0]))
    write(OUT/'qualification/actual_CLI_status.json',dict(positions=[dict(arm=q['arm'],seed=q['seed'],state=q['state'],
        canonical_closeout_complete=q.get('canonical_closeout_complete',False)) for q in v['qualification']],
        actual_CLI=2,H100_four_Seed1_actual_CLI=False,actual_arms=['P-GRB','M-B'],
        H100_D0_Seed1_not_started=True,H100_D1_Seed1_not_started=True,
        MB_temporary_review_does_not_replace_failed_original_closeout=True,performance_admission=False))
    write(OUT/'seed_stratification.json',dict(planned_new_problem_denominator=3,measured_new_problems=0,
        planned_known_Seed1_blocks=2,measured_known_Seed1_blocks=0,planned_formal_arms=16,actual_formal_arms=0,
        planned_pairs=18,evaluable_pairs=0,Seed0_history_separate=True,
        Seed_sensitivity='UNAVAILABLE: no formal Seed1 block started',no_best_of_Seeds=True,
        same_known_city_not_IID=True,no_pooled_mean_or_win_rate=True))
    write(OUT/'mechanism_account.json',dict(formal_mechanism=[],formal_costs=[],new_D1_exposure=0,
        new_D1_native_types_rows_Start_physical_endpoint='UNAVAILABLE: not executed',native_h_fixing_or_branching='unknown',
        installation_not_inferred_from_flag=True,qualification_core='blocked_current_core.json',Optimize=0))
    write(OUT/'resource_summary.json',dict(b,total_limits=[40,48000],qualification_limits=[8,1800],
        formal_nominal_seconds=37200,management_reserved_seconds=600,formal_seconds_spent=0,
        actual_qualification_parents=4,actual_reference_exporters=1,actual_H100_CLI=2,fees=v['fees'],
        last_reviewed_minimum_needed_starts=2,qualification_remaining_starts=1,
        all_failed_starts_charged=True,nested_native_seconds_added=False,
        engineering_separate=True,human_seconds='unknown',
        engineering_total='not claimed; compilation, static review, publication and recovery have scoped receipts'))
    lines=['# Round121 frozen D1 confirmation — blocked before formal admission','',
        '**Execution: BLOCKED. Decision: BLOCKED.** No formal arm was started and no performance gate was evaluated.', '',
        'The R120 production source, PE and pinned DLL are unchanged. Three prospective inputs were generated exactly once after the recipe commit, without H/LP/MIP or difficulty screening. The planned 16 arms and 18 comparison positions remain visible, with every result explicitly NOT_STARTED / UNEVALUABLE. They do not count as completed evidence.', '',
        'Qualification did not close. Four parent attempts, one successful zero-Optimize reference exporter and two real H100 Seed1 CLI children consumed 7 of the 8 permitted conservative starts. The last independently reviewed minimum needed a fresh supervisor plus the never-started D1 child (2 starts), while only 1 remains. The total budget has room; its qualification sublimit cannot be exceeded or bypassed by relabelling a supervisor. No further native launch is authorized by this batch.', '',
        '| Attempt | Actual children | Charged starts | Outer seconds | Result |', '|---|---|---:|---:|---|']
    why={
      'qualification01':('none','Synthetic zero fixture omitted reported F; stopped before exporter/CLI.'),
      'qualification02':('reference exporter; P-GRB','P sealed normally; read-only audit rejected Python int0 with an is-False identity test.'),
      'qualification03':('M-B','P requalified; M-B sealed normally; nested model-parser cache owner caused a read-only KeyError.'),
      'qualification04':('none','Read-only M-B replay encountered the existing failed audit.json and exclusive-x write; D1 never started.')}
    for fee in v['fees']:
        children,reason=why[fee['name']]
        lines.append(f'| {fee["name"]} | {children} | {fee["starts"]} | {fee["outer_seconds"]:.9f} | {reason} |')
    lines += ['', 'The first two adapter issues were repaired only in the read-only layer, with original helper versions, raw results, seals and fees retained. A different executor replayed the full P and M-B audit/readout in a temporary output overlay and checked complete physical fleets. That overlay did not exercise the original directory exclusive-write conflict. M-B retains its failed canonical audit and incomplete original closeout; the successful temporary review is not substituted for that receipt. This engineering failure is not a solver failure, proof contradiction, scientific LOSS or evidence against D1 performance.', '',
        '| Qualification role | Seed | Actual CLI | Producer seconds | Original closeout |', '|---|---:|---|---:|---|']
    for q in v['qualification']:
        lines.append(f'| {q["arm"]} | {q["seed"]} | {q["state"]} | '+(f'{q["T_produce"]:.9f}' if 'T_produce' in q else 'unavailable')+f' | {q.get("canonical_closeout_complete",False)} |')
    lines += ['', 'H100 is V20. Its D0 and D1 Seed1 CLI positions are both NOT_STARTED. R120 D0 native model/three-row/Start evidence was independently checked for the earlier proposed composed minimum, but cannot be called a current Seed1 run. There is no new D1 physical endpoint, actual three-row installation, native h type/Start exposure or extended search to review. The prior pre-contract ACCEPT was limited to attempting qualification and has not become performance admission.', '',
        '| Group | Role | Seed | Cap | Fixed method order | Formal status |', '|---:|---|---:|---:|---|---|']
    for g in read(OUT/'argv_freeze.json')['groups']:
        lines.append(f'| {g["number"]} | {g["id"]} | {g["seed"]} | {g["cap_seconds"]} | '+ ' → '.join(g['methods'])+' | all NOT_STARTED |')
    lines += ['', 'All 18 pair slots are UNEVALUABLE because both formal endpoints are absent. No U/L/gap, certification time, severe flag, D1-versus-M-B certificate count comparison, Seed flip, success fraction or support/veto statistic is inferred. The zero observed certificate counts in the frozen decision function are bookkeeping for an empty cohort, not a tied performance result. The priority is the unresolved qualification/resource barrier.', '',
        '| New input | V/M | Initial / target total | sum(w) | lambda sum(w) | Producer cap | SHA256 |', '|---|---|---:|---:|---:|---:|---|']
    for p in m['new_roles']:
        lines.append(f'| {p["id"]} | {p["V"]}/{p["M"]} | {p["total_initial"]}/{p["total_target"]} | {p["sum_weights"]:.6f} | {p["lambda_sum_weights"]:.8f} | {p["cap_seconds"]} | {p["input_sha256"]} |')
    lines += ['', 'The three inputs are unmeasured prospective subsets of the same known Capital Bikeshare source, not three new cities or IID draws. All 15 overlaps with the R116/R118 subsets were independently recalculated. Lambda*sum(w), geography, stock and physical conditions vary together; no pure size effect is claimed.', '',
        'The two saved R120 D0 maximum-violation witnesses both become D1-feasible by setting h=0 with all original coordinates fixed. Actual full rows, serialized coefficients, bounds and ObjCon were checked with zero Optimize. This limits the projection interpretation of those points while retaining R120 extended-space nonredundancy and equal original-objective LP optima; it does not prove strict original-variable projection shrinkage or root-LP objective improvement.', '',
        'R120 remains a 12-arm development result: F2 D1/D0/M-B certified in 208.144945/476.407599/774.409291 seconds; C2 D1/M-B was a severe LOSS and D1/P a nonsevere LOSS; N40 remained open with primal/gap gains and slightly weaker LB. Those observations are separate history, not substitutes for this batch. R119 MB-PC remains stopped. ENS-C remains default, M-B is retained, D0 is only the planned F2 Seed1 ablation, and no automatic next batch is scheduled.', '',
        f'Final charged budget: {b["paid_starts"]}/40 conservative starts, {b["paid_outer_seconds"]:.9f}/48000 outer seconds; qualification {b["qualification_starts"]}/8 and {b["qualification_seconds"]:.9f}/1800. Four failures are charged without refund; child native times are nested rather than added again. Static mathematics, compilation, independent review, safe publication and empty-root reconstruction are separate engineering scopes. Human time is unknown.', '',
        'The additional review and one public export/empty-root reconstruction concern this finite blocked current evidence only. They cannot reconstruct non-existent formal solver records or satisfy the unavailable new-D1 endpoint check. Recovery and remote receipts are separate from the scientific payload they inspect. All parent origins are persisted; exact child OS creation-time coverage is limited, with M-B precise creation time not found in a persistent receipt. The pre-launch marker is not an OS child-creation timestamp.', '',
        'This round does not answer whether frozen D1 merits a broader paper benchmark. It ends without a performance decision; the frozen configuration is neither promoted nor rejected scientifically.']
    (OUT/'final_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'qualification_summary.md').write_text('''# R121 qualification: BLOCKED

Actual Seed1 CLI: H100 P-GRB and M-B only; both producers sealed normally. H100 D0 and D1 were NOT_STARTED. No formal arm started and no performance admission exists.

Four failed qualification parents plus one zero-Optimize reference exporter and two CLI children cost 7 conservative starts / 445.13650035858154 outer seconds. The remaining one qualification start cannot cover the final reviewed parent+D1 minimum of two starts. Total surplus cannot raise the 8-start sublimit.

P-GRB canonical closeout completed. M-B retains a failed canonical audit and incomplete closeout. The final read-only predicates passed a different executor's temporary full audit/readout, but that overlay did not cover the original exclusive-write collision; it does not replace original closeout. Production PE/source, sealed required bytes and producer clocks remain unchanged. Exact child OS creation-time coverage is limited: M-B precise creation time was not found in a persistent receipt.

Failures: missing F in artificial zero fixture; int0 versus is-False readout; nested parser cache owner mismatch; existing audit.json exclusive-x write. All fees, prior helper source versions and failed artifacts are retained. These are engineering/qualification failures, not solver failures, proof contradictions or scientific losses.

See final_report.md, qualification/actual_CLI_status.json, all four fees, review/qualification_blocked_review.json and blocked_current_core.json. No new D1 physical endpoint, three-row installation, native h/Start exposure or formal performance comparison exists.
''',encoding='utf-8')
    (OUT/'paper_claim_evidence_map.md').write_text('''# Round121 paper claims and evidence

Current execution/stage is BLOCKED before formal admission. No new performance claim is supported.

| Scope | Evidence | Limit |
|---|---|---|
| Frozen original problem, full H and D1 integration | paper_algorithm_spec.md; mathematical_contract.md; source/PE/DLL identities | R120 configuration unchanged; numerical conditional certificates |
| Three prospective same-source inputs | recipe commit, manifest, generation receipt, mappings and overlaps | Unmeasured; one known city; three planned problems, not IID cities |
| R120 development results | retained R120 final report and preflight 18-pair replay | C2 severe M-B loss retained; not R121 confirmation |
| Fixed Seed1 checks and D0 ablation | all16_arms / all18_pairs planned slots | All formal positions NOT_STARTED; all comparisons UNEVALUABLE |
| Current actual qualification | H100 P/MB seals; blocked_current_core; separate temporary full reviews | D0/D1 unrun; MB canonical closeout incomplete; no performance admission |
| Old h witness clarification | minimal saved matrices and actual D1 rows; h-only replay | Both points repair at h=0; no strict projection claim or new LP |
| Complete proof/Start/physical boundary | inherited R118/R120 specification and actual partial qualification | No new D1 endpoint, installed rows or internal h-branching evidence |
| Resource and stage | four failed-parent fees; independent blocked review; stage_decision | 7/8 starts spent, 1 remains versus 2 needed; total surplus does not lift sublimit |
| ENS default and R119 stop | preserved specification/reports | No default change, MB removal, D0 promotion or automatic new batch |
''',encoding='utf-8')
    spec=(OUT/'paper_algorithm_spec.md').read_text(encoding='utf-8')
    pending='This is prospective setup; performance and stage are pending.'
    replacement='R121 is BLOCKED before formal admission: 0/16 formal arms and 0/18 evaluable pairs. The frozen inputs and run table remain prospective, with no new performance conclusion or default change. See final_report.md and the complete failure/fee ledger.'
    if pending in spec:spec=spec.replace(pending,replacement)
    elif replacement not in spec:spec+='\n\n'+replacement+'\n'
    (OUT/'paper_algorithm_spec.md').write_text(spec,encoding='utf-8')
    write(OUT/'engineering/blocked_report_receipt.json',dict(seconds=time.perf_counter()-tick,Optimize=0,native_starts=0))
    print(json.dumps(dict(stage='BLOCKED',formal_arms=0,evaluable_pairs=0,planned_arms=16,planned_pairs=18,budget=b)))

if __name__=='__main__':finish()
