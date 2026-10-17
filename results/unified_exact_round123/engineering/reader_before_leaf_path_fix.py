"""Portable no-Optimize current-core reconstruction and existing-record checkpoints."""
from pathlib import Path
import argparse,collections,csv,inspect,json,math,time
import round123_common as c
from round123_evidence import extension
import read_round118 as old
import read_round116 as inherited
from round108_decisions import pair
import compare_round112_startup as startup

def full_H(root,p,warm):
    source=inspect.getsource(startup.compare).replace("values['P-S']","values['M-B']").replace("name=='P-S'","name=='M-B'").replace("control='P-S'","control='M-B'")
    namespace=dict(vars(startup));exec(compile(source,__file__+'::same_paid_H','exec'),namespace)
    return namespace['compare'](root,p,warm)

def checkpoints(item,arm,damaged):
    if not item['complete']:return []
    d=item['d']; j=item['j']; label=item['label']
    offset=max(0.,c.read(d/'native_end_receipt.json')['complete_seconds_until_native_end']-
        c.read(d/'completion.json')['fully_observed_end_to_end_seconds'])
    observations=c.read(d/'observations.json'); rows=[]
    for point in [3600,7200,10800,14400,18000]:
        if arm['T_produce']<=point:
            rows.append(dict(label,checkpoint_seconds=point,source='actual_sealed_endpoint_before_checkpoint',
                actual_record_available_upper_seconds=arm['T_produce'],U_final=arm['U'],L=arm['L'],gap=arm['gap'],
                certificate=arm['certificate'],continued_computation_record=False,
                certificate_evidence_qualified_at_T_total=arm['T_total'],final_result_not_backfilled_before_availability=True))
            continue
        prior=[r for r in observations if r['effective_available_seconds']+offset<=point]
        ws=[w for w in j['witnesses'] if w['available']+offset<=point]
        bs=[b for b in j['bounds'] if b['global_available'] and b['call'] not in damaged and b['available']+offset<=point]
        last_w=max(ws,key=lambda w:(w['available'],w['sequence'])) if ws else None
        best=min(ws,key=lambda w:(w['F'],w['available'],w['sequence'])) if ws else None
        best_b=max(bs,key=lambda b:(b['global_bound'],-b['available'])) if bs else None
        identity=next((r for r in prior if r['payload']['kind']=='identity'),None)
        L=best_b['global_bound'] if best_b else 0. if identity and not damaged else None
        rows.append(dict(label,checkpoint_seconds=point,source='last_prior_existing_committed_records',
            last_any_record_sequence=prior[-1]['sequence'] if prior else None,
            last_any_record_available_upper_seconds=prior[-1]['effective_available_seconds']+offset if prior else None,
            last_witness_F=last_w['F'] if last_w else None,last_witness_G=last_w['G'] if last_w else None,
            last_witness_sequence=last_w['sequence'] if last_w else None,
            last_witness_available_upper_seconds=last_w['available']+offset if last_w else None,
            observed_best_F=best['F'] if best else None,observed_best_G=best['G'] if best else None,
            observed_best_sequence=best['sequence'] if best else None,
            observed_best_available_upper_seconds=best['available']+offset if best else None,
            L=L,L_source='already_available_qualified_global_bound_record' if best_b else 'original_identity_nonnegative_floor' if L==0 else 'unknown',
            L_sequence=best_b['sequence'] if best_b else identity['sequence'] if identity and L==0 else None,
            L_available_upper_seconds=best_b['available']+offset if best_b else identity['effective_available_seconds']+offset if identity and L==0 else None,
            descriptive_best_gap=best['F']-L if best and L is not None else None,
            certificate=False,source_reduced=bool(damaged),offset_is_conservative_upper_seconds=offset,
            no_final_API_bound_backfill=True,unknown_internal_discovery_time=True))
    return rows

def decision(arms,adjudication):
    complete=len(arms)==3 and {a['arm'] for a in arms}==set(c.METHODS) and all(a['formal_protocol_qualified'] and a['actually_executed'] for a in arms)
    if adjudication['rejections']:stage='PROOF_RELIABILITY_PRIORITY'
    elif not complete:stage='BLOCKED'
    else:
        by={a['arm']:a for a in arms}
        if by['M-B']['certificate'] and by['M-B']['U']>0:stage='MB_NONZERO_V50_PROOF_OBSERVED'
        elif by['P-GRB']['certificate'] or by['ENS-C']['certificate']:stage='REFERENCE_PROOF_OBSERVED_MB_REMAINS_OPEN'
        else:stage='FINITE_LONG_WINDOW_PROOF_LIMIT_RECORDED'
    return dict(formal_group_execution_stage='COMPLETE' if complete else 'BLOCKED',research_disposition=stage,
        formal_arms=len(arms),formal_arm_denominator=3,known_problems=1,new_independent_problems=0,
        default_ENS_changed=False,D1_selection_closed=True,no_extra_window_Seed_input_variant_or_group=True,
        paper_and_additional_review_delivery_status='reported separately in final stage_decision.json')

def rebuild(root,destination,qualification=False):
    tick=time.perf_counter();root=Path(root).resolve();out=root/'results/unified_exact_round123';dest=Path(destination)
    dest.mkdir(parents=True,exist_ok=False);camp='qualification/h100_seed0' if qualification else 'campaign/group01'
    i=c.read(out/camp/'identity.json');candidate=c.read(out/'candidate_identity.json');prod=c.read(out/'production_identity.json')
    assert i['helpers']==candidate['helpers'] and i['source_hashes']==candidate['source_bindings']==prod['source_bindings']
    for name,digest in {**i['helpers'],**i['source_hashes']}.items():assert c.sha(root/name)==digest,name
    assert i['candidate_binary_sha256']==candidate['production_PE_SHA']==c.PE_SHA and i['dll_sha256']==c.DLL_SHA
    assert i['prereg_sha256']==c.sha(out/'protocol.json') and i['runner_sha256']==c.sha(root/'scripts/round123_runner.py')
    assert [l['arm'] for l in i['launches']]==c.METHODS
    recs=collections.defaultdict(list)
    with extension():
        items=[old.item(root,l,i,recs) for l in i['launches']]
        claims=[p for v in items if v['complete'] for p in v['claims']]
        witnesses=[w for v in items if v['complete'] for w in v['ind']['witnesses']]
        adjudication=inherited.reconcile(claims,witnesses)
        assert adjudication==inherited.reconcile(list(reversed(claims)),list(reversed(witnesses)))
        arms=[old.finalize(root,v,adjudication,recs) for v in items]
    by={a['arm']:a for a in arms}; pairs=[]; trajectories=[]; obligations=[]; fleets=[]
    for A,B in c.PAIRS:
        a,b=by[A],by[B]
        if a['certificate_qualified'] and b['certificate_qualified']:q=pair(a,b)
        else:q=dict(candidate=A,control=B,classification='UNEVALUABLE',evaluable=False,severe_regression=None,certified_time_ratio=None,basis='required_qualification_missing')
        good=all(a.get(k) is not None and b.get(k) is not None for k in ['U','L','gap'])
        delta=dict(dU=a['U']-b['U'],dL=a['L']-b['L'],dgap=a['gap']-b['gap']) if good else dict(dU=None,dL=None,dgap=None)
        if good:assert abs(delta['dgap']-(delta['dU']-delta['dL']))<1e-12
        pairs.append(dict(id=i['launches'][0]['id'],seed=0,**q,**delta,main_clock='T_produce',causal_decomposition=False))
    for v,a in zip(items,arms):
        if not v['complete']:continue
        l=v['l'];d=v['d'];j=v['j'];phys=v['ind']['physical']
        damage={q['call'] for q in adjudication['damaged_calls'] if q['arm']==l['arm']}
        trajectories.extend(checkpoints(v,a,damage))
        observed=[dict(F=w['F'],G=w['G'],sequence=w['sequence'],available=w['available'],source=w['source']) for w in j['witnesses']]
        best=min(observed+[dict(F=phys['F'],G=phys['G'],sequence=None,available=a['T_produce'],source='sealed_final_fleet')],key=lambda w:w['F'])
        fleets.append(dict(arm=l['arm'],final_physical=phys,final_U=a['U'],historical_minimum_observed_F=best,
            observed_witness_count=len(observed),historical_minimum_does_not_replace_main_endpoint=True))
        ctl=v['controller'];leaves=ctl['controller_leaves'];active=[r for r in leaves if r['status'] not in ['replaced','coalesced']]
        live=[r for r in active if r['status'] not in ['empty','closed']]
        compatible=[]
        for cid,call in j['calls'].items():
            compatible.append(dict(call=cid,leaf=call['leaf'],model_SHA=call['model_sha256'],full_original=call['full_original'],
                lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff'],
                own_final_G=phys['G'],own_final_F=phys['F'],
                exact_g_embedding_interval_compatible=call['full_original'] or call['lower_g']-1e-7<=phys['G']<=call['upper_g']+1e-7,
                cutoff_compatible=call['full_original'] or phys['F']<=call['cutoff']+1e-7,
                actually_returned=cid in j['returned_ids'],explicit_not_started=cid in j['not_started_ids']))
        obligations.append(dict(arm=l['arm'],U=a['U'],L=a['L'],certificate=a['certificate'],
            full_original_single_call=l['arm']=='P-GRB',qualified_cover=v['ep'].get('cover'),active_cover=active,
            unresolved_leaves=live,final_controlling_leaf=min(live,key=lambda r:float(r['lower_bound'])) if live else None,
            own_final_fleet_and_call_domains=compatible,controller_events=ctl['controller_events'],
            chronological_cover=v['ep'].get('chronological_cover'),native_calls=ctl['controller_native'],
            internal_search_cause='unknown unless directly recorded'))
    warm={v['l']['arm']:v['d'] for v in items if v['complete'] and v['l']['arm']!='P-GRB'}
    H=full_H(root,i['launches'][0]['panel'],warm) if set(warm)=={'M-B','ENS-C'} else None
    value=dict(group=c.read(out/'argv_freeze.json')['groups'][0],qualification=qualification,arms=arms,pairs=pairs,
        adjudication=adjudication,full_H=H,own_fleets=fleets,proof_obligations=obligations,checkpoints=trajectories,
        decision=decision(arms,adjudication),PE_SHA=c.PE_SHA,DLL_SHA=c.DLL_SHA,default_ENS_changed=False)
    c.write(dest/'current_core.json',value)
    for name,data in dict(recs,arms=arms,pairs=pairs,checkpoints=trajectories).items():
        if data:
            fields=list(dict.fromkeys(k for row in data for k in row))
            with (dest/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fields);writer.writeheader()
                writer.writerows({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in data)
    c.write(dest/'reconstruction_receipt.json',dict(UTC=c.utc(),seconds=time.perf_counter()-tick,script_SHA=c.sha(__file__),
        core_SHA=c.sha(dest/'current_core.json'),no_Optimize=True,no_original_root_fallback=True,
        native_processes_launched=0,installed_solver_library_used=False,qualification=qualification))
    print(json.dumps(dict(arms=len(arms),pairs=len(pairs),decision=value['decision'],seconds=time.perf_counter()-tick)))
    return value

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(c.ROOT));parser.add_argument('--out',required=True);parser.add_argument('--qualification',action='store_true')
    args=parser.parse_args();rebuild(args.root,args.out,args.qualification)
