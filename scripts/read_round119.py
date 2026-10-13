"""Current-only scientific reconstruction under the explicit MB-PC extension."""
from round119_common import *
from round119_evidence import extension,event_chain
import collections,csv,json,copy
import round118_call_logs as logs
import read_round118 as old
import read_round116 as inherited
import round114_audit as audit
from round108_decisions import pair

def rebuild_group(number,destination):
    number=int(number);group=read(OUT/'argv_freeze.json')['groups'][number-1]
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    i=read(OUT/group['campaign']/'identity.json');candidate=read(OUT/'candidate_identity.json')
    assert i['candidate_binary_sha256']==candidate['production_PE_SHA']
    assert i['dll_sha256']==candidate['DLL_SHA'] and i['helpers']==candidate['helpers']
    for name,h in i['source_hashes'].items():assert sha(ROOT/name)==h
    for name,h in i['helpers'].items():assert sha(ROOT/name)==h
    recs=collections.defaultdict(list)
    with extension():
        items=[old.item(ROOT,l,i,recs) for l in i['launches']]
        assert all(v['complete'] for v in items),'fixed arm evidence incomplete'
        claims=[q for v in items for q in v['claims']];witnesses=[q for v in items for q in v['ind']['witnesses']]
        final=inherited.reconcile(claims,witnesses)
        assert final==inherited.reconcile(list(reversed(claims)),list(reversed(witnesses)))
        arms=[old.finalize(ROOT,v,final,recs) for v in items]
    data={a['arm']:a for a in arms};pairs=[dict(id=group['id'],**pair(data[c],data[p]))
        for c,p in [('MB-PC','M-B'),('MB-PC','P-GRB'),('M-B','P-GRB')]]
    mechanism=[]
    for v in items:
        with logs.activate(v['view']):mechanism.append(dict(arm=v['l']['arm'],
            **event_chain(ROOT,v['l'],v['d'],v['j'],inherited.core.evidence.controller_tables(v['d'],read(v['d']/'result.json')),v['view'])))
    # A numerical rejection of any proof used for contraction is a correctness
    # failure; a later physical U/floor0 cannot qualify that candidate.
    candidate_used=next(m for m in mechanism if m['arm']=='MB-PC').get('committed',0)>0
    pc_rejections=[q for q in final['rejections'] if q.get('arm')=='MB-PC']
    assert not(candidate_used and pc_rejections),'PROOF_RELIABILITY_PRIORITY: candidate contraction dependency rejected'
    value=dict(group=group,arms=arms,pairs=pairs,mechanism=mechanism,adjudication=final,
        all_three_fixed_arms_once=True,PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],
        default_ENS_changed=False,independent_generalization_claim=False)
    write(dest/'current_core.json',value)
    for name,rows in dict(recs,arms=arms,pairs=pairs,mechanism=mechanism).items():
        if not rows:continue
        fields=list(dict.fromkeys(k for row in rows for k in row))
        with (dest/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fields);w.writeheader()
            for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    return value
def development_admission():
    values=[read(OUT/'reconstruction'/f'group{n:02d}'/'current_core.json') for n in [1,2,3]]
    results=[]
    for v in values:
        by={a['arm']:a for a in v['arms']};pc_mb=next(p for p in v['pairs'] if p['candidate']=='MB-PC' and p['control']=='M-B')
        pc_p=next(p for p in v['pairs'] if p['candidate']=='MB-PC' and p['control']=='P-GRB')
        exposure=next(p for p in v['mechanism'] if p['arm']=='MB-PC')
        results.append(dict(id=v['group']['id'],pc_mb=pc_mb,pc_p=pc_p,exposure=exposure,
            MB_PC_certificate=by['MB-PC']['certificate'],M_B_certificate=by['M-B']['certificate']))
    conditions=dict(nonempty_contraction_and_subsequent_solve=any(p['exposure'].get('committed',0)>0 and
        any(c['next_Optimize_calls'] for c in p['exposure']['contracts']) for p in results),
        material_WIN_or_additional_complete_certificate=any(p['pc_mb']['classification']=='WIN' or
            p['MB_PC_certificate'] and not p['M_B_certificate'] for p in results),
        no_severe_P_regression_and_fewer_than_two_P_LOSS=not any(p['pc_p']['severe_regression'] for p in results) and
            sum(p['pc_p']['classification']=='LOSS' for p in results)<2,
        complete_certificate_count_preserved=sum(p['MB_PC_certificate'] for p in results)>=sum(p['M_B_certificate'] for p in results))
    value=dict(admitted=all(conditions.values()),conditions=conditions,roles=results,
        fixed_confirmation='E50-C1 P-GRB -> MB-PC -> M-B, each 3600',not_statistical_superiority=True)
    write(OUT/'development_admission.json',value)
    if not value['admitted']:
        g=read(OUT/'argv_freeze.json')['groups'][3]
        write(OUT/'confirmation_cancellation.json',dict(group=g,arms=[dict(arm=m,state='CANCELED_NOT_ADMITTED') for m in g['methods']],
            all_three_unrun=True,reason=conditions,not_counted_as_completed=True))
    print(json.dumps(dict(admitted=value['admitted'],conditions=conditions)),flush=True);return value
if __name__=='__main__':
    if sys.argv[1]=='admission':development_admission()
    else:rebuild_group(sys.argv[1],sys.argv[2])
