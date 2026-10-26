"""Current-only R121 reconstruction using the unchanged physical/cover rules."""
from round122_common import *
from round122_evidence import extension,event_chain
import collections,csv,inspect
import read_round118 as old
import read_round116 as inherited
import read_round120 as prior
from round108_decisions import pair
F2_PAIRS=prior.PAIRS
TRIPLE_PAIRS=[('MB-D1','M-B'),('MB-D1','P-GRB'),('M-B','P-GRB')]
def complete_H(profile,warm):return prior.complete_H(profile,warm)
def rebuild_group(number,destination):
    number=int(number);g=read(OUT/'argv_freeze.json')['groups'][number-1];dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    i=read(OUT/g['campaign']/'identity.json');candidate=read(OUT/'candidate_identity.json')
    assert i['candidate_binary_sha256']==candidate['production_PE_SHA'] and i['dll_sha256']==candidate['DLL_SHA']
    assert i['helpers']==candidate['helpers']
    for n,h in i['source_hashes'].items():assert sha(ROOT/n)==h
    for n,h in i['helpers'].items():assert sha(ROOT/n)==h
    recs=collections.defaultdict(list)
    with extension():
        items=[old.item(ROOT,l,i,recs) for l in i['launches']]
        assert len(items)==len(g['methods']) and all(v['complete'] for v in items)
        claims=[q for v in items for q in v['claims']];witnesses=[q for v in items for q in v['ind']['witnesses']]
        final=inherited.reconcile(claims,witnesses);assert final==inherited.reconcile(list(reversed(claims)),list(reversed(witnesses)))
        arms=[old.finalize(ROOT,v,final,recs) for v in items]
        mechanism=[dict(arm=v['l']['arm'],**event_chain(ROOT,v['l'],v['d'],v['j'])) for v in items]
    by={a['arm']:a for a in arms};pairs=[]
    for c,p in PAIRS:
        a,b=by[c],by[p];comparison=pair(a,b)
        dU=a['U']-b['U'];dL=a['L']-b['L'];dgap=a['gap']-b['gap']
        assert abs(dgap-(dU-dL))<=1e-12
        pairs.append(dict(id=g['id'],group_number=number,seed=g['seed'],**comparison,dU=dU,dL=dL,dgap=dgap,identity_dgap_equals_dU_minus_dL=True,causal_shares=False))
    assert not [q for q in final['rejections'] if q.get('arm') in ['MB-D0','MB-D1']],'PROOF_RELIABILITY_PRIORITY: dependent source rejected'
    H=complete_H(i['launches'][0]['panel'],{v['l']['arm']:v['d'] for v in items if v['l']['arm']!='P-GRB'})
    assert all(c['qualified'] for c in H['comparisons'])
    value=dict(group=g,arms=arms,pairs=pairs,mechanism=mechanism,adjudication=final,full_H=H,
        all_fixed_arms_once=True,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,default_ENS_changed=False,independent_generalization_claim=False)
    write(dest/'current_core.json',value)
    for name,rows in dict(recs,arms=arms,pairs=pairs,mechanism=mechanism).items():
        if not rows:continue
        fields=list(dict.fromkeys(k for row in rows for k in row))
        with (dest/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fields);writer.writeheader()
            for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    return value
if __name__=='__main__':rebuild_group(sys.argv[1],sys.argv[2])
