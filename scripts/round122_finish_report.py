"""Post-seal paper tables and finite decision; never optimizes or changes producers."""
from round122_common import *
from round122_decision import decide
import collections,csv,re

def rows(path):
    if not path.exists():return []
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def table(path,items):
    if not items:return
    fields=list(dict.fromkeys(k for r in items for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader()
        for r in items:w.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def finish():
    tick=time.perf_counter();values=[read(OUT/f'reconstruction/group{n:02d}/current_core.json') for n in range(1,9)]
    m=read(OUT/'input_manifest.json');gen=read(OUT/'generation_receipt.json');ident=read(OUT/'candidate_identity.json')
    for p in m['new_roles']:assert sha(ROOT/p['input_path'])==p['input_sha256']
    assert ident['helpers']==helpers() and ident['source_bindings']==bindings()
    arms=[]
    for v in values:
        for a in v['arms']:
            # The inherited endpoint was deliberately evaluated outside its old R108 panel;
            # its legacy formal flag is not a statement about this preregistered panel.
            arms.append(dict(a,legacy_panel_formal_flag=a.get('formal_performance'),formal_performance=True,
                seed=v['group']['seed'],group_number=v['group']['number'],source=v['group']['source'],panel_kind=v['group']['panel_kind']))
    pairs=[p for v in values for p in v['pairs']];assert len(arms)==32 and len(pairs)==48
    valid=m['generated_once'] and gen['unique_input_files_written']==6 and gen['no_H_LP_MIP_or_difficulty_filter'] and not m['exact_historical_SHA_duplicates']
    blockers=[dict(group=a['group_number'],arm=a['arm'],reason='unqualified necessary protocol/numbers') for a in arms if not a['formal_protocol_qualified'] or not a['numbers_qualified']]
    risk=any(v['adjudication']['rejections'] for v in values)
    decision=decide(values,valid,proof_risk=risk,blockers=blockers)
    b=budget();assert not b['unclosed'] and b['paid_outer_seconds']<=TOTAL_LIMIT and b['qualification_seconds']<=QUAL_LIMIT
    write(OUT/'stage_decision.json',decision);write(OUT/'all32_arms.json',arms);write(OUT/'all48_pairs.json',pairs)
    table(OUT/'all32_arms.csv',arms);table(OUT/'all48_pairs.csv',pairs)
    mechanism=[];costs=[];dimensions=[];physical=[];positions=[];proofs=[];startup=[]
    for v in values:
        gn=v['group']['number'];rec=OUT/f'reconstruction/group{gn:02d}';i=read(OUT/v['group']['campaign']/'identity.json')
        counts={q['arm']:q for q in rows(rec/'native_counts.csv')};clocks=rows(rec/'time_partitions.csv')
        for l in i['launches']:
            d=Path(l['destination']);a=next(a for a in arms if a['group_number']==gn and a['arm']==l['arm'])
            p=l['panel'];phys=read(d/'independent_evidence.json')['physical'];result=read(d/'result.json')
            assert abs(phys['F']-a['U'])<=1e-7
            physical.append(dict(group_number=gn,id=l['id'],source=p['source'],arm=l['arm'],seed=l['seed'],G=phys['G'],P=phys['P'],lambda_P=p['lambda']*phys['P'],F=phys['F'],
                U=a['U'],routes=phys['routes'],input_SHA=p['input_sha256'],independent_evidence_SHA=sha(d/'independent_evidence.json')))
            view=read(d/'call_log_views.json');actual=int(counts[l['arm']]['actual_Optimize']);lp=int(counts[l['arm']]['LP']);assert actual==view['actual_Optimize']
            for q in view['bindings']:
                path=ROOT/q['raw_log'];data=path.read_bytes();assert sha(path)==q['raw_log_SHA']
                text=data[q['byte_begin']:q['byte_end']].decode('utf-8');header=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',text);assert header
                dimensions.append(dict(group_number=gn,id=l['id'],arm=l['arm'],seed=l['seed'],call=q['call'],model_SHA=q['model_SHA'],rows=int(header[1]),columns=int(header[2]),nonzeros=int(header[3]),
                    solve_kind=q['solve_kind'],scope=q['true_G_interval'],cutoff=q['cutoff'],types=q['native_types'],actual_log_binding=q))
            costs.append(dict(group_number=gn,id=l['id'],arm=l['arm'],seed=l['seed'],actual_Optimize=actual,LP=lp,MIP=actual-lp,
                time_partition=next(q for q in clocks if q['arm']==l['arm']),T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total']))
            e=next(x for x in v['mechanism'] if x['arm']==l['arm']);epath=d/'external/round120_events.jsonl'
            events=[json.loads(s) for s in epath.read_text(encoding='utf-8').splitlines()] if epath.exists() else []
            controller=rows(d/'external/controller_events.csv')
            if not controller:
                controller=[q for q in rows(rec/'controller_events.csv') if q.get('arm')==l['arm']]
            mechanism.append(dict(group_number=gn,id=l['id'],source=p['source'],seed=l['seed'],own_U=a['U'],own_G=phys['G'],own_lambda_P=p['lambda']*phys['P'],
                full_model_sizes=[q for q in dimensions if q['group_number']==gn and q['arm']==l['arm']],
                nonexposure_events=[q for q in events if q.get('kind')=='not_exposed'],
                original_atomic_split_events=[q for q in controller if q.get('event')=='atomic_split'],
                raw_final_objective_fields={k:x for k,x in result.items() if 'objective' in k.lower() and isinstance(x,(int,float,bool,str,type(None)))},**e))
            positions.append(dict(group_number=gn,id=l['id'],arm=l['arm'],seed=l['seed'],cap=l['cap_seconds'],
                actual_launch=(d/'child_process_origin.json').exists(),sealed=(d/'producer_seal.json').exists(),closeout=(d/'arm_total_receipt.json').exists(),destination=str(d)))
            startup.append(dict(group_number=gn,id=l['id'],arm=l['arm'],**read(d/'child_process_origin.json')))
            proofs.append(dict(group_number=gn,id=l['id'],arm=l['arm'],seed=l['seed'],proof_evidence=a['proof_evidence'],source_reduced=a['source_reduced'],
                certificate=a['certificate'],native_proof_qualified=a['native_proof_qualified'],rejected_calls=a['rejected_calls']))
    write(OUT/'fixed_position_status.json',dict(positions=positions,formal_slots=32,all_actual_once=all(p['actual_launch'] and p['sealed'] and p['closeout'] for p in positions)))
    write(OUT/'own_fleets_and_objective_parts.json',physical);table(OUT/'objective_parts.csv',[{k:v for k,v in r.items() if k!='routes'} for r in physical])
    write(OUT/'mechanism_account.json',dict(mechanism=mechanism,costs=costs,actual_model_dimensions=dimensions,Optimize=0,native_starts=0,
        native_h_fixing_or_branching='unknown',whole_tree_retention='not established',sample_values_not_internal_causal_shares=True,nested_native_seconds_added=False))
    write(OUT/'proof_reliability.json',dict(arms=proofs,group_adjudications=[dict(group_number=v['group']['number'],**v['adjudication']) for v in values],
        unresolved_proof_risk=risk,performed_checks_are_not_a_guarantee_against_all_numerical_error=True))
    byphys={(q['group_number'],q['arm']):q for q in physical};decomposition=[]
    for p in pairs:
        if p['candidate_certified'] or p['control_certified']:continue
        c,t=[byphys[p['group_number'],p[k]] for k in ['candidate','control']]
        dG=c['G']-t['G'];dP=c['lambda_P']-t['lambda_P'];assert abs(dG+dP-p['dU'])<=1e-7
        decomposition.append(dict(p,dG=dG,d_lambda_P=dP,identity_dU_equals_dG_plus_d_lambda_P=True,internal_causal_shares=False))
    write(OUT/'open_endpoint_decomposition.json',decomposition);table(OUT/'open_endpoint_decomposition.csv',decomposition)
    seed0={(p['id'],p['candidate'],p['control']):p for p in pairs if p['seed']==0};sensitivity=[]
    for p in pairs:
        if p['seed']!=1:continue
        old=seed0[p['id'],p['candidate'],p['control']]
        sensitivity.append(dict(id=p['id'],candidate=p['candidate'],control=p['control'],Seed0=old['classification'],Seed1=p['classification'],
            Seed0_severe=old['severe_regression'],Seed1_severe=p['severe_regression'],WIN_to_LOSS=old['classification']=='WIN' and p['classification']=='LOSS'))
    write(OUT/'seed_stratification.json',dict(new_problem_denominator=6,Seed1_same_input_blocks=2,main_Seed0_groups=list(range(1,7)),Seed1_groups=[7,8],
        sensitivity=sensitivity,no_best_of_Seed=True,not_IID_not_factorial=True));table(OUT/'seed_sensitivity.csv',sensitivity)
    negatives=[p for p in pairs if p['classification'] in ['LOSS','MIXED','UNEVALUABLE'] or p['severe_regression']]
    write(OUT/'major_negative_results.json',dict(all_negative_or_mixed_pairs=negatives,all_unexposed_D1=[q for q in mechanism if q['arm']=='MB-D1' and not q.get('actual_extended_Optimize',0)],
        historical_R120_C2_Seed0_severe_M_B_loss_retained=True,historical_R121_all_three_new_open=True))
    layers=[]
    for source in ['CITI','CABI']:
        for V in [20,35,50]:
            aa=[a for a in arms if a['seed']==0 and a['source']==source and a['V']==V]
            layers.append(dict(source=source,V=V,arms=aa,nonfactorial_single_role_cell=True))
    write(OUT/'source_scale_layers.json',layers)
    controller_files=sorted((OUT/'controller').glob('*/launch.json'));controllers={}
    for path in controller_files:
        x=read(path);controllers[x['controller_pid'],x['controller_actual_creation_unix']]=dict(pid=x['controller_pid'],creation_unix=x['controller_actual_creation_unix'])
    write(OUT/'startup_ledger.json',dict(formal_native_children=startup,fee_wrappers_and_children=[dict(label=p.parent.name,launch=read(p),receipt=read(p.parent/'receipt.json')) for p in sorted((OUT/'fees').glob('*/launch.json'))],
        distinct_controller_processes=list(controllers.values()),controller_count=len(controllers),no_hard_process_count_gate=True))
    write(OUT/'resource_summary.json',dict(b,outer_limit_seconds=TOTAL_LIMIT,qualification_soft_seconds=QUAL_PLAN,qualification_authorized_seconds=QUAL_LIMIT,
        formal_nominal_seconds=79200,management_reference_seconds=960,additional_distinct_controller_starts=len(controllers),
        total_observed_or_conservative_starts=b['paid_starts']+len(controllers),nested_native_seconds_added=False,failed_fees_retained=True,
        native_component_times_are_nested=True,engineering_review_publication_scopes='separate measured receipts; no human-time estimate',
        compile=read(OUT/'engineering/reference_compile/receipt.json'),inventory_seconds=read(OUT/'workspace_inventory.json')['elapsed_seconds']))
    lines=['# Round122 first two-source frozen-method paper benchmark','',f'**{decision["execution_stage"]} / {decision["stage"]}**.','',
        'The complete fixed panel contains six new Seed0 problems and two fixed Seed1 repeats: 32 arms and 48 pairs. Cold P-GRB is the primary benchmark. ENS-C stays default; M-B remains the complete reference; no default adoption or automatic next batch follows.','',
        '| Group | Source | Role | V | Seed | Method | own U | qualified L | signed gap | Proof category | T_produce | T_verify | T_total |',
        '|---:|---|---|---:|---:|---|---:|---:|---:|---|---:|---:|---:|']
    for a in arms:lines.append(f'| {a["group_number"]} | {a["source"]} | {a["id"]} | {a["V"]} | {a["seed"]} | {a["arm"]} | '+' | '.join(f'{a[k]:.10g}' for k in ['U','L','gap'])+f' | {a["proof_evidence"]} | '+' | '.join(f'{a[k]:.8g}' for k in ['T_produce','T_verify','T_total'])+' |')
    lines+=['','| Group | Role | Seed | Pair | Class | Severe | Basis |','|---:|---|---:|---|---|---|---|']
    for p in pairs:lines.append(f'| {p["group_number"]} | {p["id"]} | {p["seed"]} | {p["candidate"]}/{p["control"]} | {p["classification"]} | {p["severe_regression"]} | {p["basis"]} |')
    lines+=['','| Role | Seed | D1 installed | Extended calls | beta0 / beta1 | own U | Installation seconds |','|---|---:|---:|---:|---|---:|---:|']
    for q in mechanism:
        if q['arm']!='MB-D1':continue
        pp=q.get('pair');ev=q.get('install_events',[])
        lines.append(f'| {q["id"]} | {q["seed"]} | {q["installed"]} | {q.get("actual_extended_Optimize",0)} | '+(f'{pp["beta0"]:.10g} / {pp["beta1"]:.10g}' if pp else 'no complete installed pair')+f' | {q["own_U"]:.10g} | '+(str(ev[0]['installation_seconds']) if ev else 'not installed')+' |')
    newlarge=[a for a in arms if a['seed']==0 and a['V']>=35 and a['arm']=='MB-D1' and a['certificate'] and not a['own_exact_zero']]
    lines+=['',f'New V35/V50 D1 nonzero certificates: {len(newlarge)}. Zero certificates, reliable open bounds and source-reduced results remain distinct in the proof table.','',
        'All unexposed roles remain in complete-method comparisons. Beta threshold crossing does not establish a native branch being fixed or explain a performance effect. Native incumbent and own physical U are separately retained. The endpoint identities dgap=dU-dL and dU=dG+d(lambda*P) are arithmetic explanations, not causal proportions.',
        '', '| Fixed repeat | Pair | Seed0 | Seed1 | Seed0 severe | Seed1 severe |', '|---|---|---|---|---|---|']
    for q in sensitivity:lines.append(f'| {q["id"]} | {q["candidate"]}/{q["control"]} | {q["Seed0"]} | {q["Seed1"]} | {q["Seed0_severe"]} | {q["Seed1_severe"]} |')
    lines+=['','R121 remains COMPLETE / ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK: three new open problems, new D1/P 3 WIN and D1/M-B TIE/WIN/TIE; Q50 was naturally unexposed. R120 C2 Seed0 severe M-B regression is not erased by a Seed1 win. D0 remains an ablation and MB-PC remains stopped.',
        '',f'Observed fee-level starts: {b["paid_starts"]}; additional distinct controller starts: {len(controllers)}. Paid wrapper outer seconds: {b["paid_outer_seconds"]:.6f}/100000; qualification: {b["qualification_seconds"]:.6f}/6000 (soft plan3000). Process counts are reported observations, not hard gates. Nested native times are not charged twice.',
        '', 'The panel is finite and nonfactorial. Source, size, geometry, stock, Q/T and total weights vary together. Station overlaps are retained; six problems are not six cities or IID samples. Two Seeds do not estimate a population probability. Open caps are censored producer windows and cannot be divided as final proof times. Numerical certificates follow the original floating-point policy.',
        '', 'Raw-backed full model/call/epoch/cutoff/Seed/Start/return, physical fleets, exposure and cost details are in mechanism_account.json and the reconstruction groups. Stage conditions and every veto are explicit in stage_decision.json. Publication/recovery/extra-review receipts attest only their actually completed later scopes. Workspace/storage measures support execution and are not mathematical contributions.']
    (OUT/'final_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'paper_claim_evidence_map.md').write_text('# Claim and evidence map\n\n| Claim | Evidence | Limit |\n|---|---|---|\n| Frozen complete methods and physical objective | paper_algorithm_spec; production_identity | No new algorithm in R122 |\n| Two-source finite panel | recipe/input manifest; independent input review | Six non-IID, nonfactorial roles |\n| Complete performance and tradeoffs | all32_arms; all48_pairs; major_negative_results | No selected-seed or instance winner algorithm |\n| D1 incremental exposure and cost | mechanism_account; full matrices/Start/source scopes | Internal native branching cause unknown |\n| Proof reliability and certification tier | proof_reliability; actual call returns and physical fleets | Floating-point evidence; source-reduced separated |\n| One finite candidate decision | stage_decision; independent all48 review | No significance/default adoption/automatic more samples |\n| Reproducible delivery | public carrier manifest; actual empty-root receipt | Runtime PE/DLL/license excluded; finite explicit dependencies |\n',encoding='utf-8')
    write(OUT/'engineering/report_receipt.json',dict(engineering_seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        report_script_SHA=sha(__file__),raw_producers_unchanged=True))
    print(json.dumps(dict(stage=decision['stage'],arms=len(arms),pairs=len(pairs),budget=b)),flush=True)

if __name__=='__main__':finish()
