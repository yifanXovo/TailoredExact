"""Small current-only reconstruction; per-call views cover every downstream read."""
from pathlib import Path
import collections,copy,json,sys,time
import round118_call_logs as logs
import read_round116 as inherited
import round114_audit as audit
from round118_data import ROOT,OUT,read,write,sha
from compare_round112_startup import compare as compare_H

def item(root,l,i,recs):
    d=inherited.portable(root,l['destination'])
    if not (d/'arm_total_receipt.json').exists():return inherited.reconstruct_arm(root,l,i,recs)
    j=audit.journal(root,l,d,read(d/'observations.json'));view=logs.build(root,l,d,j,read(d/'result.json'))
    assert read(d/'call_log_views.json')['bindings']==view['bindings']
    with logs.activate(view):value=inherited.reconstruct_arm(root,l,i,recs)
    value['view']=view;return value

def finalize(root,value,final,recs):
    with logs.activate(value.get('view')):arm=inherited.finalize_arm(root,value,final,recs)
    if value['complete']:
        if value['l']['id']=='N40-R1-S':
            data=inherited.core.evidence.instance(root,value['l']['panel'])
            assert sum(data['b'][1:])<sum(data['D'][1:]) and not value['ind']['own_exact_zero'],'positive-input own-zero requires input/stock replay investigation'
        offset=read(value['d']/'native_end_receipt.json')['complete_seconds_until_native_end']-read(value['d']/'completion.json')['fully_observed_end_to_end_seconds']
        hits=[w for w in value['ind']['witnesses'] if abs(w['F']-arm['U'])<=1e-7]
        first=min(hits,key=lambda w:w['available']) if hits else None
        record=recs['target_discovery'][-1]
        record.update(target_objective=arm['U'],first_verified_target_record_sequence=first.get('sequence') if first else None,
            target_record_available_upper_seconds=first['available']+max(0.,offset) if first else None,
            target_record_source=first['source'] if first else None,open_endpoint_target_also_reported=True)
    return arm

def disposition(arms,pairs,H,complete,final):
    if not complete:return dict(execution_stage='BLOCKED',research_disposition=None,reason='incomplete required execution/evidence; no algorithm denial')
    primary=next(q for q in pairs if q['candidate']=='M-B' and q['control']=='P-GRB')
    control=next(q for q in pairs if q['candidate']=='M-B' and q['control']=='P-S')
    mb=next(a for a in arms if a['arm']=='M-B');same=next(h for h in H if h['candidate']=='M-B')
    if final['rejections']:stage='PROOF_RELIABILITY_PRIORITY'
    elif primary['classification']=='LOSS':stage='PRIMARY_BENCHMARK_RISK_ON_THIS_ROLE'
    elif mb['proof_evidence']=='CLEAN_NONZERO_CERTIFICATE' and primary['classification']==control['classification']=='WIN' and same['attribution_eligible']:
        stage='NONZERO_PROOF_INCREMENT_ON_THIS_ROLE'
    else:stage='LIMITED_OR_MIXED_ROLE_EVIDENCE'
    return dict(execution_stage='COMPLETE',research_disposition=stage,one_problem_not_four_samples=True,
        M_B_P=primary['classification'],M_B_P_S=control['classification'],P_S_attribution_eligible=same['attribution_eligible'],
        ENS_loss_not_hidden_veto=True,default_ENS_changed=False,automatic_next_draw_or_extension=False)

def rebuild(root,destination,qualification=False,campaign_name=None):
    root=Path(root).resolve();out=root/'results/unified_exact_round118';dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();camp=out/(campaign_name or ('qualification/cli01' if qualification else 'campaign'));i=read(camp/'identity.json')
    candidate=read(out/'candidate_identity.json');production=read(out/'production_identity.json')
    assert i['candidate_binary_sha256']==candidate['production_PE_SHA']==production['production_PE_SHA']
    assert i['dll_sha256']==candidate['DLL_SHA']==production['DLL_SHA'] and i['helpers']==candidate['helpers']
    for name,h in i['source_hashes'].items():assert sha(root/name)==h
    for name,h in i['helpers'].items():assert sha(root/name)==h
    assert i['runner_sha256']==sha(root/'scripts/round118_campaign.py')
    assert i['prereg_sha256']==sha(out/'protocol.json')
    recs=collections.defaultdict(list);items=[item(root,l,i,recs) for l in i['launches']]
    claims=[q for v in items if v['complete'] for q in v['claims']]
    witnesses=[q for v in items if v['complete'] for q in v['ind']['witnesses']]
    final=inherited.reconcile(claims,witnesses);assert final==inherited.reconcile(list(reversed(claims)),list(reversed(witnesses)))
    arms=[finalize(root,v,final,recs) for v in items];by={v['l']['arm']:v for v in items}
    same=[]
    if all(v['complete'] for v in items) and 'P-S' in by:
        methods=['P-S','M-B'] if qualification else ['P-S','ENS-C','M-B']
        H=compare_H(root,i['launches'][0]['panel'],{m:by[m]['d'] for m in methods})
        for h in H['comparisons']:
            exposed=by[h['candidate']]['j']['started']>0 and by['P-S']['j']['started']>0
            h.update(formal=not qualification,backend_exposed=exposed,attribution_eligible=h['qualified'] and exposed,
                attribution_reason='MATCHED_H_BACKENDS_EXPOSED' if h['qualified'] and exposed else 'H_NOT_COMPLETED' if not h['full_H_complete'] else 'BACKEND_NOT_EXPOSED' if h['qualified'] else 'START_MISMATCH')
            same.append(h)
        write(dest/'same_H_fleets.json',H)
    pairs=[]
    if not qualification:
        lookup={a['arm']:a for a in arms}
        for A,C in inherited.PAIRS:
            a,c=lookup[A],lookup[C];h=next((h for h in same if h['candidate']==A),None) if C=='P-S' else None
            comparison=inherited.pair(a,c) if a['formal_protocol_qualified'] and c['formal_protocol_qualified'] else dict(
                candidate=A,control=C,classification='UNEVALUABLE',evaluable=False,severe_regression=None,
                basis='required execution/qualification missing',candidate_U=a.get('U'),control_U=c.get('U'),
                candidate_gap=a.get('gap'),control_gap=c.get('gap'),certified_time_ratio=None)
            pairs.append(dict(comparison,id='N40-R1-S',main_clock='T_produce',
                candidate_proof_evidence=a['proof_evidence'],control_proof_evidence=c['proof_evidence'],
                backend_attribution_eligible=h['attribution_eligible'] if h else None,
                backend_attribution_reason=h['attribution_reason'] if h else None))
    complete=all(v['complete'] and a['formal_protocol_qualified'] for v,a in zip(items,arms))
    decision=disposition(arms,pairs,same,complete,final) if not qualification else dict(execution_stage='COMPLETE' if complete else 'BLOCKED',not_performance=True)
    core=dict(arms=arms,pairs=pairs,same_H=same,group_reconciliation=final,decision=decision)
    write(dest/'current_core.json',core)
    for key,rows in recs.items():inherited.table(dest/(key+'.csv'),rows)
    inherited.table(dest/'arms.csv',arms);inherited.table(dest/'pairs.csv',pairs);inherited.table(dest/'same_H.csv',same)
    write(dest/'summary.json',dict(passed=complete,qualification=qualification,arm_count=len(arms),pair_count=len(pairs),decision=decision,
        no_solver_or_library_import=True,no_original_root_fallback=True,engineering_seconds=time.perf_counter()-tick,
        scientific_core_SHA=sha(dest/'current_core.json')))
    print(json.dumps(dict(complete=complete,arms=len(arms),pairs=len(pairs),decision=decision)))
    return core

if __name__=='__main__':rebuild(ROOT,OUT/sys.argv[1],'--qualification' in sys.argv[2:])
