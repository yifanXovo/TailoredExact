"""Current-only reconstruction and the predeclared D1 attribution gate."""
from round120_common import *
from round120_evidence import extension,event_chain
import collections,csv,inspect
import read_round118 as old
import read_round116 as inherited
from round108_decisions import pair
PAIRS=[('MB-D1','M-B'),('MB-D1','P-GRB'),('MB-D1','MB-D0'),('MB-D0','M-B'),('MB-D0','P-GRB'),('M-B','P-GRB')]
def complete_H(profile,warm):
    import compare_round112_startup as comparison
    text=inspect.getsource(comparison.compare).replace("values['P-S']","values['M-B']").replace("name=='P-S'","name=='M-B'").replace("control='P-S'","control='M-B'")
    namespace=dict(vars(comparison));exec(compile(text,__file__+'::same_full_H_M_B_control','exec'),namespace)
    return namespace['compare'](ROOT,profile,warm)
def rebuild_group(number,destination):
    number=int(number);g=read(OUT/'argv_freeze.json')['groups'][number-1];dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    i=read(OUT/g['campaign']/'identity.json');candidate=read(OUT/'candidate_identity.json')
    assert i['candidate_binary_sha256']==candidate['production_PE_SHA'] and i['dll_sha256']==candidate['DLL_SHA']
    assert i['helpers']==candidate['helpers']
    for n,h in i['source_hashes'].items():assert sha(ROOT/n)==h
    for n,h in i['helpers'].items():assert sha(ROOT/n)==h
    recs=collections.defaultdict(list)
    with extension():
        items=[old.item(ROOT,l,i,recs) for l in i['launches']];assert len(items)==4 and all(v['complete'] for v in items)
        claims=[q for v in items for q in v['claims']];witnesses=[q for v in items for q in v['ind']['witnesses']]
        final=inherited.reconcile(claims,witnesses);assert final==inherited.reconcile(list(reversed(claims)),list(reversed(witnesses)))
        arms=[old.finalize(ROOT,v,final,recs) for v in items]
    by={a['arm']:a for a in arms};pairs=[dict(id=g['id'],**pair(by[c],by[p])) for c,p in PAIRS]
    mechanism=[dict(arm=v['l']['arm'],**event_chain(ROOT,v['l'],v['d'],v['j'])) for v in items]
    assert not [q for q in final['rejections'] if q.get('arm') in ['MB-D0','MB-D1']],'PROOF_RELIABILITY_PRIORITY: dependent native disjunction proof rejected'
    H=complete_H(i['launches'][0]['panel'],{v['l']['arm']:v['d'] for v in items if v['l']['arm']!='P-GRB'})
    assert all(c['qualified'] for c in H['comparisons'])
    value=dict(group=g,arms=arms,pairs=pairs,mechanism=mechanism,adjudication=final,full_H=H,
        all_four_fixed_arms_once=True,PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],
        default_ENS_changed=False,independent_generalization_claim=False)
    write(dest/'current_core.json',value)
    for name,rows in dict(recs,arms=arms,pairs=pairs,mechanism=mechanism).items():
        if not rows:continue
        fields=list(dict.fromkeys(k for row in rows for k in row))
        with (dest/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fields);writer.writeheader()
            for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    return value
def admission():
    values=[read(OUT/'reconstruction'/f'group{n:02d}/current_core.json') for n in [1,2]];roles=[]
    for v in values:
        by={a['arm']:a for a in v['arms']};p={(q['candidate'],q['control']):q for q in v['pairs']}
        roles.append(dict(id=v['group']['id'],D1_MB=p['MB-D1','M-B'],D1_P=p['MB-D1','P-GRB'],D1_D0=p['MB-D1','MB-D0'],
            D1_certificate=by['MB-D1']['certificate'],MB_certificate=by['M-B']['certificate'],
            exposure=next(x for x in v['mechanism'] if x['arm']=='MB-D1')))
    conditions=dict(all_core_arms_qualified=all(a['formal_protocol_qualified'] for v in values for a in v['arms']),
        actual_D1_registered_installed_completed_native_search=any(x['exposure'].get('installed')==1 and x['exposure'].get('actual_extended_Optimize',0)>0 for x in roles),
        D1_MB_material_complete_gain_or_new_certificate=any(x['D1_MB']['classification']=='WIN' or x['D1_certificate'] and not x['MB_certificate'] for x in roles),
        D1_D0_material_WIN_or_new_certificate=any(x['D1_D0']['classification']=='WIN' for x in roles),
        no_severe_D0_regression=not any(x['D1_D0']['severe_regression'] for x in roles),
        no_severe_P_and_fewer_than_two_P_LOSS=not any(x['D1_P']['severe_regression'] for x in roles) and sum(x['D1_P']['classification']=='LOSS' for x in roles)<2,
        D1_complete_certificate_count_preserved=sum(x['D1_certificate'] for x in roles)>=sum(x['MB_certificate'] for x in roles))
    value=dict(admitted=all(conditions.values()),conditions=conditions,roles=roles,conditional_group='N40 M-B -> D1 -> P -> D0, 5400 each',not_statistical_superiority=True)
    write(OUT/'core_admission.json',value)
    if not value['admitted']:
        g=read(OUT/'argv_freeze.json')['groups'][2];write(OUT/'N40_cancellation.json',dict(group=g,
            arms=[dict(arm=m,state='CANCELED_NOT_ADMITTED') for m in g['methods']],all_four_unrun=True,not_counted_as_completed=True,reason=conditions))
    print(json.dumps(dict(admitted=value['admitted'],conditions=conditions)),flush=True);return value
if __name__=='__main__':
    if sys.argv[1]=='admission':admission()
    else:rebuild_group(sys.argv[1],sys.argv[2])
