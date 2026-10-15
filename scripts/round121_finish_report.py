"""Post-native fixed decision, Seed layers, endpoints and complete cost report."""
from round121_common import *
from round121_decision import decide
import csv,re,math
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
    tick=time.perf_counter();values=[read(OUT/f'reconstruction/group{n:02d}/current_core.json') for n in range(1,6)]
    arms=[dict(a,seed=v['group']['seed'],panel_kind=v['group']['panel_kind']) for v in values for a in v['arms']]
    pairs=[p for v in values for p in v['pairs']];assert len(arms)==16 and len(pairs)==18
    m=read(OUT/'input_manifest.json');generation=read(OUT/'generation_receipt.json')
    new_identity=m['generated_once'] and generation['unique_new_input_files_written']==3 and generation['no_H_LP_MIP_or_difficulty_filter'] and not m['exact_historical_SHA_duplicates']
    for p in m['new_roles']:assert sha(ROOT/p['input_path'])==p['input_sha256']
    blockers=[dict(id=a['id'],arm=a['arm'],formal_protocol_qualified=a.get('formal_protocol_qualified'),numbers_qualified=a.get('numbers_qualified')) for a in arms if not a.get('formal_protocol_qualified') or not a.get('numbers_qualified')]
    risk=any(v['adjudication']['rejections'] for v in values)
    decision=decide(values,new_identity,proof_risk=risk,blockers=blockers)
    b=budget();assert not b['unclosed'] and b['paid_starts']<=40 and b['paid_outer_seconds']<=48000
    assert b['qualification_starts']<=8 and b['qualification_seconds']<=1800
    write(OUT/'stage_decision.json',decision);write(OUT/'all16_arms.json',arms);write(OUT/'all18_pairs.json',pairs)
    table(OUT/'all16_arms.csv',arms);table(OUT/'all18_pairs.csv',pairs)
    positions=[]
    for plan in read(OUT/'argv_freeze.json')['plans']:
        if not plan['name'].startswith('campaign/'):continue
        for l in read(OUT/plan['name']/'identity.json')['launches']:
            d=Path(l['destination']);positions.append(dict(id=l['id'],arm=l['arm'],seed=l['seed'],cap=l['cap_seconds'],actual_launch=(d/'launch.json').exists(),
                sealed=(d/'producer_seal.json').exists(),closeout=(d/'arm_total_receipt.json').exists(),destination=l['destination']))
    write(OUT/'fixed_position_status.json',dict(positions=positions,formal_slots=16,all_actual_once=all(p['actual_launch'] and p['sealed'] and p['closeout'] for p in positions)))
    mechanism=[];costs=[];dimensions=[];physical=[]
    for v in values:
        rec=OUT/f'reconstruction/group{v["group"]["number"]:02d}';i=read(OUT/v['group']['campaign']/'identity.json')
        counts={q['arm']:q for q in rows(rec/'native_counts.csv')};clocks=rows(rec/'time_partitions.csv')
        for l in i['launches']:
            d=Path(l['destination']);phys=read(d/'independent_evidence.json')['physical'];a=next(a for a in v['arms'] if a['arm']==l['arm'])
            physical.append(dict(id=l['id'],arm=l['arm'],seed=l['seed'],G=phys['G'],P=phys['P'],lambda_P=l['panel']['lambda']*phys['P'],F=phys['F'],
                U=a['U'],routes=phys['routes'],input_SHA=l['panel']['input_sha256'],independent_evidence_SHA=sha(d/'independent_evidence.json')))
            view=read(d/'call_log_views.json');actual=int(counts[l['arm']]['actual_Optimize']);lp=int(counts[l['arm']]['LP'])
            assert actual==view['actual_Optimize']
            for q in view['bindings']:
                path=ROOT/q['raw_log'];data=path.read_bytes();assert sha(path)==q['raw_log_SHA']
                text=data[q['byte_begin']:q['byte_end']].decode('utf-8');header=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',text)
                assert header
                dimensions.append(dict(id=l['id'],arm=l['arm'],seed=l['seed'],call=q['call'],model_SHA=q['model_SHA'],rows=int(header[1]),columns=int(header[2]),
                    nonzeros=int(header[3]),solve_kind=q['solve_kind'],scope=q['true_G_interval'],cutoff=q['cutoff'],types=q['native_types'],actual_log_binding=q))
            costs.append(dict(id=l['id'],arm=l['arm'],seed=l['seed'],actual_Optimize=actual,LP=lp,MIP=actual-lp,
                time_partition=next(q for q in clocks if q['arm']==l['arm']),T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total']))
        mechanism.extend(dict(id=v['group']['id'],seed=v['group']['seed'],**x) for x in v['mechanism'])
    write(OUT/'own_fleets_and_objective_parts.json',physical);table(OUT/'objective_parts.csv',[{k:v for k,v in r.items() if k!='routes'} for r in physical])
    write(OUT/'mechanism_account.json',dict(mechanism=mechanism,costs=costs,actual_model_dimensions=dimensions,Optimize=0,native_starts=0,
        native_h_fixing_or_branching='unknown',whole_tree_retention='not established',sample_values_not_internal_causal_shares=True,nested_native_seconds_added=False))
    previous=read(OUT/'preflight_R120_pair_replay.json');oldpairs={ (p['id'],p['candidate'],p['control']):p for g in previous['saved_groups'] for p in g['pairs']}
    sensitivity=[]
    for p in pairs:
        if p['seed']!=1:continue
        old=oldpairs.get((p['id'],p['candidate'],p['control']))
        if old:sensitivity.append(dict(id=p['id'],candidate=p['candidate'],control=p['control'],Seed0=old['classification'],Seed1=p['classification'],
            WIN_to_LOSS=old['classification']=='WIN' and p['classification']=='LOSS',Seed0_severe=old['severe_regression'],Seed1_severe=p['severe_regression']))
    strata=dict(new_problems=[v['group']['id'] for v in values if v['group']['number'] in [2,4,5]],new_problem_denominator=3,
        known_Seed1_roles=['F2','R98-C2'],known_Seed1_block_denominator=2,arm_denominator=16,pair_denominator=18,
        same_city_source_not_IID=True,Seed0_history_separate=previous['saved_groups'],sensitivity=sensitivity,no_best_of_Seeds=True,no_pooled_exact_mean_or_win_rate=True)
    write(OUT/'seed_stratification.json',strata);table(OUT/'seed_sensitivity.csv',sensitivity)
    decomposition=[dict(p,interpretation='primal U improvement with weaker L' if p['dU']<0 and p['dL']<0 else 'endpoint identity; no internal causal shares') for p in pairs if not p['candidate_certified'] and not p['control_certified']]
    write(OUT/'open_endpoint_decomposition.json',decomposition)
    engineering=[]
    for p in (OUT/'engineering').glob('reference_compile*/receipt.json'):engineering.append(dict(path=p.relative_to(ROOT).as_posix(),**read(p)))
    write(OUT/'resource_summary.json',dict(b,total_limits=[40,48000],qualification_limits=[8,1800],formal_nominal_seconds=37200,management_reserve=600,
        failed_fees_retained=True,failed_declared_attempts_not_refunded=True,nested_native_seconds_added=False,engineering_separate=True,
        compiler_receipts=engineering,known_compile_seconds=sum(r['seconds'] for r in engineering),human_seconds='unknown',engineering_total='not claimed; scoped receipts'))
    stage=decision['stage'];lines=['# Round121 frozen D1 confirmation','',f'**{decision["execution_stage"]} — {stage}**.','',
        'All 16 fixed positions and 18 pairs completed with the R120 production PE and pinned DLL. Cold P-GRB is the primary benchmark; M-B is the direct complete-method control. ENS-C remains default, D0 remains the single F2 Seed1 ablation, and R119 MB-PC remains stopped.',
        '', 'Three once-generated inputs from the same known Capital Bikeshare source are the new-problem layer. F2 and R98-C2 Seed1 are separate known-role sensitivity checks. These are finite candidate/resource criteria, not statistical significance or a universal speed claim.','',
        '| Layer | Role | Seed | Method | own U | qualified L | signed gap | Certificate | T_produce | T_verify | T_total |',
        '|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|']
    for a in arms:lines.append(f'| {"known Seed" if a["seed"] else "new input"} | {a["id"]} | {a["seed"]} | {a["arm"]} | '+' | '.join(f'{a[k]:.10g}' for k in ['U','L','gap'])+f' | {a["certificate"]} | '+' | '.join(f'{a[k]:.9g}' for k in ['T_produce','T_verify','T_total'])+' |')
    lines+=['','| Role | Seed | Pair | Class | Severe | Basis |','|---|---:|---|---|---|---|']
    for p in pairs:lines.append(f'| {p["id"]} | {p["seed"]} | {p["candidate"]}/{p["control"]} | {p["classification"]} | {p["severe_regression"]} | {p["basis"]} |')
    lines+=['','The frozen veto and support conditions are recorded individually in stage_decision.json. Ordinary material LOSS and severe LOSS are both retained. Open caps are censored producer windows and are never reported as final certification times.',
        '', '| Role | Seed | Method | LP/MIP | H seconds | LP seconds | MIP seconds | Actual rows/columns/nonzeros |','|---|---:|---|---:|---:|---:|---:|---|']
    for c in costs:
        t=c['time_partition'];sizes=sorted({f'{d["rows"]}/{d["columns"]}/{d["nonzeros"]}' for d in dimensions if d['id']==c['id'] and d['arm']==c['arm']})
        lines.append(f'| {c["id"]} | {c["seed"]} | {c["arm"]} | {c["LP"]}/{c["MIP"]} | '+' | '.join(f'{float(t[k]):.9g}' for k in ['H_seconds','LP_inclusive_seconds','MIP_inclusive_seconds'])+' | '+(', '.join(sizes) if sizes else 'no native exposure')+' |')
    lines+=['','| Role | Extension | Installed | Extended calls | beta0 / beta1 | Installation seconds |','|---|---|---:|---:|---|---:|']
    for e in mechanism:
        if not e['enabled']:continue
        p=e.get('pair');events=e.get('install_events',[])
        lines.append(f'| {e["id"]} | {e["arm"]} | {e["installed"]} | {e.get("actual_extended_Optimize",0)} | '+(f'{p["beta0"]:.17g} / {p["beta1"]:.17g}' if p else 'unavailable')+' | '+(str(events[0]['installation_seconds']) if events else 'uninstalled')+' |')
    lines+=['','All H, model/LP/MIP/Start, installation, online checks, callbacks, native cleanup and producer sealing are paid in T_produce. Post-seal T_verify and T_total are separate; native component times are nested and not added again. Cross-arm reconciliation is group cost. Call-scoped saved byte spans supply the dimensions above, including reused logs.',
        '', 'Installation, expanded native search, sampled h/native objective, internal h fixing/branching, and full performance are distinct. Actual model/ObjCon/types/Start/scope/source-proof and target/terminal identities are preserved in mechanism_account.json and raw-backed reconstruction. Native h fixing/branching remains unknown; no entire-tree preservation or single-Optimize complete method is claimed.',
        '', 'For each open pair, dgap=dU−dL is checked exactly to numerical arithmetic tolerance. Objective parts G and lambda*P are listed separately in objective_parts.csv. Improved U with weaker L is a primal endpoint benefit; these arithmetic decompositions are not internal causal shares. Record availability is an observed upper time bound, not an internal first discovery.',
        '', 'Both saved R120 D0 maximum-violation points can be repaired for D1 by changing only h to zero under the actual complete matrices and ObjCon, with every original coordinate held fixed (review/pre_contract.json and minimal saved sources). The old extended-space nonredundancy and equal original-objective LP minima remain true. These two witnesses do not establish strict original-coordinate projection shrinkage or a general performance theorem. No new LP/native diagnostic was run.',
        '', 'The two Seed layers and every Seed0-to-Seed1 classification are retained in seed_stratification.json; WIN-to-LOSS transitions are labelled sensitive. No best-of-two-Seed selection, pooled exact mean time or overall independent-sample win rate is formed. R120 C2 severe direct-M-B loss remains part of the development record.',
        '',f'Budget: {b["paid_starts"]}/40 conservative starts and {b["paid_outer_seconds"]:.6f}/48000 outer seconds; qualification {b["qualification_starts"]}/8 and {b["qualification_seconds"]:.6f}/1800. Failed preparation/compile/native declarations remain disclosed; compilation, zero-solve mathematics, publication, recovery and extra review have separate scoped receipts. Human time is unknown.',
        '', 'No new city, independent IID sample, default adoption, universal acceleration, rational-exact solver certificate or automated next batch is claimed. The one stage decision closes this batch. Scientific payload, actual public reconstruction, extra review and remote publication receipts have separate scopes.']
    (OUT/'final_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    claim=['# Paper claims and evidence','',f'Current stage: `{stage}`.','',
        '| Claim/scope | Evidence | Limitation |','|---|---|---|',
        '| Original BRP and frozen full H/controller | paper_algorithm_spec.md; mathematical_contract.md; source/PE identities | Original objective/physical replay; numerical certificates |',
        '| R120 project-specific D1 integration | preserved R120 native qualification and 12 development arms | Standard disjunction is existing theory; C2 severe M-B loss retained |',
        '| Three prospective same-source inputs | committed recipe; generation_receipt; 9 arms in all16_arms | Three problems, same known city, overlap table; no selection by difficulty |',
        '| Known-role Seed sensitivity | F2/R98-C2 Seed1 and seed_stratification | Two blocks, not new problems or probability estimates |',
        '| Conditional information | one F2 Seed1 D1/D0 pair | D0 is an ablation, not another selected candidate |',
        '| Actual native exposure and physical endpoints | mechanism_account; complete types/Starts/ObjCon/scope/source rows | h fixing/branching and internal cause unknown |',
        '| Saved-point h reselection | review/pre_contract and minimal full matrices | Both h=0 repairs; no strict projection-shrinkage inference |',
        '| ENS default/history | R118 specification; preserved R120/R119 reports | No ENS formal arm this round; old cost not a same-build R121 comparison |',
        '| Frozen decision and risks | all18_pairs; stage_decision; full negative data | Finite candidate/resource screen; no statistical significance |']
    (OUT/'paper_claim_evidence_map.md').write_text('\n'.join(claim)+'\n',encoding='utf-8')
    spec=(OUT/'paper_algorithm_spec.md').read_text(encoding='utf-8')
    spec=spec.replace('This is prospective setup; performance and stage are pending.',f'All 16 fixed R121 arms are complete; the finite stage is {stage}. The full result and all negative outcomes are in final_report.md. No default change follows.')
    (OUT/'paper_algorithm_spec.md').write_text(spec,encoding='utf-8')
    write(OUT/'engineering/report_receipt.json',dict(seconds=time.perf_counter()-tick,Optimize=0,native_starts=0))
    print(json.dumps(dict(stage=stage,arms=len(arms),pairs=len(pairs),budget=b)),flush=True)
if __name__=='__main__':finish()
