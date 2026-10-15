"""Post-run finite stage decision and concise complete result report."""
from round120_common import *
import csv,re
def finish():
    tick=time.perf_counter();values=[read(OUT/'reconstruction'/f'group{n:02d}/current_core.json') for n in [1,2]]
    gate=read(OUT/'core_admission.json')
    if gate['admitted']:
        values.append(read(OUT/'reconstruction/group03/current_core.json'))
    else:assert read(OUT/'N40_cancellation.json')['all_four_unrun']
    arms=[a for v in values for a in v['arms']];pairs=[p for v in values for p in v['pairs']]
    pp=[p for p in pairs if p['candidate']=='MB-D1' and p['control']=='P-GRB']
    mb=[p for p in pairs if p['candidate']=='MB-D1' and p['control']=='M-B']
    d0=[p for p in pairs if p['candidate']=='MB-D1' and p['control']=='MB-D0']
    certificates={m:sum(a['certificate'] for a in arms if a['arm']==m) for m in ['P-GRB','M-B','MB-D0','MB-D1']}
    severe_P=any(p['severe_regression'] for p in pp)
    uncompensated_certificate_loss=certificates['MB-D1']<certificates['M-B']
    positive=any(p['classification']=='WIN' for p in mb)
    conditional=any(p['classification']=='WIN' for p in d0)
    blockers=[dict(id=a['id'],arm=a['arm'],formal_protocol_qualified=a.get('formal_protocol_qualified'),
        native_proof_qualified=a.get('native_proof_qualified'),numbers_qualified=a.get('numbers_qualified'))
        for a in arms if not a.get('formal_protocol_qualified') or not a.get('native_proof_qualified') or not a.get('numbers_qualified')]
    if blockers:
        stage='BLOCKED';reason='A required current formal protocol, numerical endpoint or native proof is unqualified; correctness and necessary evidence have priority.'
    elif severe_P or uncompensated_certificate_loss:
        stage='STOP_TESTED_NATIVE_DISJUNCTION';reason='Severe primary P risk or uncompensated complete-certificate loss.'
    elif gate['admitted'] and len(values)==3 and positive and conditional:
        stage='ADVANCE_NATIVE_PROOF_DISJUNCTION_TO_CONFIRMATION';reason='Full core admission and all fixed N40 follow-up obligations completed with preserved finite complete-method and conditional-information signals.'
    elif positive:
        stage='RETAIN_NATIVE_ENCODING_WITHOUT_CONDITIONAL_ATTRIBUTION';reason='Finite complete-method positive signal, with conditional contribution or risk exchange unresolved under the predeclared admission gate.'
    else:
        stage='STOP_TESTED_NATIVE_DISJUNCTION';reason='The exposed complete-method comparison does not retain a material D1/M-B gain.'
    b=budget();assert not b['unclosed'] and b['paid_starts']<=40 and b['paid_outer_seconds']<=48000
    assert b['qualification_starts']<=16 and b['qualification_seconds']<=3600
    write(OUT/'stage_decision.json',dict(stage=stage,reason=reason,core_admission=gate['conditions'],formal_arms=len(arms),
        fixed_N40_completed=len(values)==3,fixed_N40_canceled=len(values)==2,certificate_counts=certificates,
        severe_P_risk=severe_P,uncompensated_M_B_certificate_loss=uncompensated_certificate_loss,
        finite_D1_M_B_positive_signal=positive,finite_D1_D0_conditional_signal=conditional,
        correctness_or_necessary_evidence_blockers=blockers,
        default_ENS_changed=False,R119_STOP_preserved=True,MB_PC_still_default_off=True,
        no_automatic_variant_or_expansion=True,one_stage_exit=True))
    compilation=[]
    for p in sorted((OUT/'engineering').glob('*_receipt.json')):
        if not any(q in p.name for q in ['build','configure']):continue
        r=read(p);assert r['Optimize']==0
        compilation.append(dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p),**r))
    write(OUT/'resource_summary.json',dict(b,maximum_starts=40,maximum_outer_seconds=48000,
        qualification_maximum_starts=16,qualification_maximum_outer_seconds=3600,failed_fees_retained=True,
        never_started_positions_not_charged_as_process_launches=True,all_actual_or_uncertain_child_starts_charged=True,
        outer_upper_includes_exit_observation_delay=True,nested_native_seconds_added=False,engineering_separate=True,
        compilation_receipts=compilation,recorded_compile_configure_seconds=sum(r['seconds'] for r in compilation),
        later_packing_recovery_review_and_remote_receipts_separate=True,engineering_total_seconds='not claimed; separately scoped receipts',human_seconds='unknown'))
    mechanism=[];costs=[];dimensions=[]
    for v in values:
        d=OUT/'reconstruction'/f'group{v["group"]["number"]:02d}'
        native=list(csv.DictReader((d/'controller_native.csv').open(encoding='utf-8')))
        observed=list(csv.DictReader((d/'native_calls.csv').open(encoding='utf-8')))
        counts={q['arm']:q for q in csv.DictReader((d/'native_counts.csv').open(encoding='utf-8'))}
        clocks=list(csv.DictReader((d/'time_partitions.csv').open(encoding='utf-8')))
        for a in v['arms']:
            calls=[q for q in native if q['arm']==a['arm']]
            samples=[q for q in observed if q['arm']==a['arm']];count=counts[a['arm']]
            actual=int(count['actual_Optimize']);lp=int(count['LP']);assert actual==len(samples)
            for q in samples:
                text=(ROOT/q['path']).read_text(encoding='utf-8-sig',errors='replace')
                headers=re.findall(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',text)
                nnz=int(headers[-1][2]) if headers else 'unknown'
                if headers:assert int(headers[-1][0])==int(q['rows']) and int(headers[-1][1])==int(q['columns'])
                dimensions.append(dict(id=v['group']['id'],arm=a['arm'],call=int(q['call']),model_SHA=q['model_SHA'],
                    rows=int(q['rows']) if q['rows'] else 'unknown',columns=int(q['columns']) if q['columns'] else 'unknown',
                    nonzeros=nnz,actual_native_log=q['path'],native_header_observed=bool(headers)))
            costs.append(dict(id=v['group']['id'],arm=a['arm'],actual_Optimize=actual,LP=lp,MIP=actual-lp,
                unique_models=len({q['model_SHA'] for q in samples}),
                time_partition=[q for q in clocks if q['arm']==a['arm']],controller_calls=calls,actual_native_calls=samples))
        mechanism.extend(dict(id=v['group']['id'],**m) for m in v['mechanism'])
    write(OUT/'mechanism_account.json',dict(mechanism=mechanism,costs=costs,actual_model_dimensions=dimensions,Optimize=0,new_native_starts=0,
        native_objective_sample_scope='MIPSOL solution objective and separately verified physical F/G; a sample alone does not attest solver incumbent acceptance, cutoff propagation, h fixing or branching',
        no_unrun_counterfactual_cost_subtraction=True,no_whole_tree_retention_or_internal_h_fixing_claim=True))
    lines=['# Round120 fixed native proof experiment','',f'**{stage}**. {reason}','',
        'MB-D1 uses one binary root selector and three static pre-Optimize rows from this run\'s paid complete root-child LPs. MB-D0 removes only conditionality while retaining the common floor and identical added column/row count. Cold P-GRB is primary; frozen M-B is the direct complete-method control. ENS-C remains default and R119 MB-PC remains stopped.',
        '', 'F2 retains the same nonzero original-problem certificate with lower D1 T_produce than M-B and D0. C2 D1/M-B is a severe LOSS and D1/P a nonsevere LOSS; the fixed admission gate still holds. All N40 methods remain open: D1 improves own U and gap, while its lower bound is weaker than M-B and D0. This supports only the stated finite confirmation stage, not a V40 proof closure or a default change.',
        '',f'All {len(arms)} current formal positions use PE `{sha(PE)}` and the pinned Gurobi13.0.2 DLL. No historical incumbent, bound or diagnostic Start entered a formal run.','',
        '| Role | Method | own U | qualified L | signed gap | Original certificate | T_produce | T_verify | T_total |',
        '|---|---|---:|---:|---:|---|---:|---:|---:|']
    for v in values:
        for a in v['arms']:
            lines.append('| '+str(v['group']['id'])+' | '+str(a['arm'])+' | '+' | '.join(f'{a[k]:.10g}' for k in ['U','L','gap'])+
                f' | {a["certificate"]} | '+ ' | '.join(f'{a[k]:.9g}' for k in ['T_produce','T_verify','T_total'])+' |')
    lines+=['','| Role | Pair | Classification | Severe regression | Basis |','|---|---|---|---|---|']
    for p in pairs:lines.append(f'| {p["id"]} | {p["candidate"]}/{p["control"]} | {p["classification"]} | {p["severe_regression"]} | {p["basis"]} |')
    lines+=['','| Role | Method | LP / MIP calls | H seconds | LP native seconds | MIP native seconds | Recorded rows / columns / nonzeros |',
        '|---|---|---:|---:|---:|---:|---|']
    for c in costs:
        t=c['time_partition'][0];sizes=sorted({str(q['rows'])+'/'+str(q['columns'])+'/'+str(q['nonzeros']) for q in dimensions if q['id']==c['id'] and q['arm']==c['arm']})
        lines.append(f'| {c["id"]} | {c["arm"]} | {c["LP"]} / {c["MIP"]} | '+
            ' | '.join(f'{float(t[k]):.9g}' for k in ['H_seconds','LP_inclusive_seconds','MIP_inclusive_seconds'])+' | '+', '.join(sizes)+' |')
    lines+=['','Native times are nested inside T_produce. Model construction, installation, online checks, callbacks, output and cleanup remain charged in T_produce; source event clocks and the full residual/closeout partitions are retained. These values are not added to T_produce again.',
        '', '| Role | Extension | beta0 | beta1 | Root installation seconds | Completed extended calls |',
        '|---|---|---:|---:|---:|---:|']
    for m in mechanism:
        if not m['enabled']:continue
        p=m.get('pair');events=m.get('install_events',[])
        lines.append(f'| {m["id"]} | {m["arm"]} | '+
            (f'{p["beta0"]:.17g} | {p["beta1"]:.17g}' if p else 'uninstalled | uninstalled')+
            ' | '+(f'{events[0]["installation_seconds"]:.9g}' if events else 'uninstalled')+f' | {m.get("actual_extended_Optimize",0)} |')
    lines+=['','All six fixed pairs per role are shown. Complete certificates have priority and original materiality/severe rules were replayed on all nine R119 published pairs. Signed gaps are retained; two open endpoints do not predict a final certification-time ratio.',
        '', 'The complete diagnostic LPs have equal D0/D1 original objectives (.6105472608488204 on F2 and approximately .162005382167712 on C2), but full feasible D0 primal points violate the actual D1 row by .10368547236475856 and .03176182992417159. Every original route/resource/inventory row and bound was checked. This proves nonredundancy in the extended (original variables, h) LP; it alone establishes neither a stronger original-objective minimum nor an integer-search or complete-method gain.',
        '', 'Static installation, complete-LP nonredundancy, sampled native row activity, actual native objective/physical F, and h fixing/branching are distinct. Actual native samples and model/Start/size/call/epoch identities are retained in mechanism_account.json and reconstructed tables. h fixing/branching is unknown; an incumbent h value or numeric crossing is not its observation. The original target/terminal requests and necessary epoch/domain artifacts remain; no entire-tree preservation or single-Optimize complete method is claimed.',
        '', 'D1/D0 is the finite conditional-information comparison. D0/M-B mixes the common floor and selector effects. D0 is an ablation and is not promoted after results. ']
    lines += ['The four fixed N40 positions completed in their predeclared order; N40 is a known difficult follow-up, not an independent sample.' if len(values)==3 else
        'All four fixed N40 positions are CANCELED_NOT_ADMITTED and unrun. No E50, extra Seed, instance or window extension was executed.']
    lines += ['', 'The original-core R119 tail supplement passed in R120 with zero Optimize and preserves the old R119 failed test. The first new zero-Optimize native qualification failed a synthetic LP-text objective-offset expectation. Its raw files/cost are retained; actual ObjCon/API/MPS qualification then passed without changing the production PE. Complete independent physical enumeration/actual matrix embeddings, all-column types/Starts, one real C++ chain and six H100 CLI positions passed. The chain certified nonzero1.2 using three original LPs and one extended MIP. H100 D0/D1 each submitted binary-h complete Starts and used the same extended SHA for original target and terminal. All full H comparisons agree.',
        '',f'Budget: {b["paid_starts"]}/40 conservative starts, {b["paid_outer_seconds"]:.6f}/48000 outer seconds; qualification {b["qualification_starts"]}/16 and {b["qualification_seconds"]:.6f}/3600. Failed starts and necessary supervision/verification are charged; native nested times are not added again. Pure compilation, mathematics, packing/export/recovery are separately recorded engineering work. Human time is unknown, not zero.',
        '', 'These are finite known-role numerical results. Standard disjunction/convexification is not new general theory. No default promotion, merge, parameter grid, automated next research or broad stability claim follows this exit. Scientific payload, export/recovery, separate extra review and remote receipts are separate artifacts.']
    (OUT/'final_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write(OUT/'paper_claim_evidence_map.json',dict(original_problem='R118 full specification preserved in R120 paper_algorithm_spec.md',
        new_formulation='mathematical_contract.md, actual native matrices/types/Starts and scoped returned source proofs',
        numerical_coefficient_safety='exact decimal/binary64 endpoint audits plus fixed1e-7 source margin; not rational solver certification',
        LP_information='six complete-model LPs and saved full primal/matrix residuals',
        conditional_complete_method_attribution=d0,complete_method_primary_pairs=pp,complete_method_direct_pairs=mb,
        internal_h_fixing_branching='unknown',scientific_stage=stage,default_adoption=False,new_general_theory_claim=False))
    write(OUT/'engineering/report_receipt.json',dict(Optimize=0,native_starts=0,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(stage=stage,formal_arms=len(arms),certificates=certificates,budget=b)),flush=True)
if __name__=='__main__':finish()
