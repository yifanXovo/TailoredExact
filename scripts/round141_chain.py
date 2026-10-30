"""Independent pure binding of every count floor to its actual qualified LP.

No solver/Native load, no raw mutation, and no producer reentry. Run only on a
sealed/verified arm. Count proofs remain separate from Gini proof pieces.
"""
from round141_common import *
from fractions import Fraction as F
from round141_math import model_counts,serializable,membership
from round141_read import count_scope
import round108_reader as core

def check(destination):
    tick=time.perf_counter();d=Path(destination)
    assert read(d/'producer_receipt.json')['native_stopped_no_reentry']
    assert (d/'verification_closeout.json').exists()
    observations=read(d/'observations.json');payloads=[r['payload'] for r in observations]
    calls={p['call']:p for p in payloads if p['kind']=='call'}
    events=[json.loads(s) for s in (d/'external/round141_events.jsonl').read_text().splitlines()]
    outcome=read(d/'round141_outcome.json')
    selected=[r for r in events if r['kind']=='root_count_selected']
    pairs=[r for r in events if r['kind']=='pair_ready']
    probes=[r for r in events if r['kind']=='count_probe_returned']
    assert len(selected)<=1 and len(pairs)<=1 and len(probes)<=2
    if not pairs:
        assert not outcome['pair_ready']
        result=dict(PASS=True,triggered=bool(selected),pair_ready=False,reason=outcome['reason'],
            existing_parent_bound_retained=True,Optimize=0)
        write(d/'round141_chain_audit.json',result);return result
    choice=selected[0];pair=pairs[0];assert len(probes)==2 and all(p['qualified'] for p in probes)
    threshold=int(choice['threshold_units'])*F(2)**choice['threshold_exponent']
    root_calls=[s for s in calls.values() if s['model_sha256']==choice['root_SHA']]
    assert len(root_calls)==1
    root_call=root_calls[0];root_path=core.portable(ROOT,root_call['model_path']);assert sha(root_path)==choice['root_SHA']
    root=core.lp_model(root_path)
    # The source support and loaded dyadic ratios are read from the actual
    # matrix. The physical inventory budget is recovered from its input plan.
    identity=read(d.parents[1]/'identity.json');p=identity['launches'][0]['panel']
    B=p['total_initial'];raw=model_counts(root,max(0,B-sum(p['Q_vector'])),B)
    add=json.loads(json.dumps(serializable(raw)))
    interval=[r for r in add['thresholds'] if F(r['t'])==threshold];assert len(interval)==1
    assert (interval[0]['ell'],interval[0]['u'])==(choice['ell'],choice['u'])
    material=''.join(format(float(F(add['ratios'][str(i)])),'.17g')+':'+''.join(str(y)+',' for y in add['supports'][str(i)])+';'
        for i in range(1,p['V']+1))
    assert hashlib.sha256(material.encode()).hexdigest()==choice['support_SHA']
    formal=read(d/'external/round141_root_selectors.json')
    assert formal['model_SHA']==choice['root_SHA'] and formal['extra_Optimize']==0
    all_selectors={f'state_{i}_{y}' for i,ys in add['supports'].items() for y in ys}
    assert set(formal['selectors'])==all_selectors
    K=math.fsum(formal['selectors'][k] for k in membership(add,threshold))
    assert abs(K-choice['K_star'])<1e-11
    assert choice['ell']<=choice['pivot']<choice['u']
    sides=[]
    for side in [0,1]:
        probe=next(v for v in probes if v['side']==side)
        cid=probe['call'];source=calls[cid];scope=count_scope(source)
        assert source['model_sha256']==probe['model_SHA'] and source['native_preconditions']
        assert scope['side']==side and scope['threshold']==threshold and scope['pivot']==choice['pivot']
        assert scope['root_SHA']==choice['root_SHA'] and scope['support_SHA']==choice['support_SHA']
        assert scope['supports']=={int(i):ys for i,ys in add['supports'].items()}
        assert scope['ratios']=={int(i):F(c) for i,c in add['ratios'].items()}
        assert source['cover']==[] and source['cutoff']==choice['model_cutoff']
        assert (source['lower_g'],source['upper_g'])==(root_call['lower_g'],root_call['upper_g'])
        bound=[b for b in payloads if b['kind']=='bound' and b['call']==cid and b['local_available']]
        if probe['status']=='OPTIMAL':
            assert any(b['native_bound']==probe['raw_bound'] for b in bound)
            assert all(not b['global_available'] for b in bound)
        else:
            assert probe['status']=='INFEASIBLE' and probe['raw_bound']==source['cutoff']
            assert any(q['kind']=='native_infeasible' and q['call']==cid and q['qualified'] for q in payloads)
        beta=max(0.,math.nextafter(min(probe['raw_bound'],source['cutoff'])-1e-7,-math.inf))
        assert probe['beta']==beta and pair['beta'+str(side)]==beta
        assert not probe['physical_side_deleted']
        quality=[q for q in payloads if q['kind']=='native_quality' and q['call']==cid];assert len(quality)==1
        sides.append(dict(side=side,call=cid,model_SHA=source['model_sha256'],raw_bound=probe['raw_bound'],
            beta=beta,settings_SHA=hashlib.sha256(json.dumps(source['settings'],sort_keys=True).encode()).hexdigest()))
    assert pair['cover']==min(s['beta'] for s in sides)
    # All physical/source/quality/type checks were performed by the complete
    # reader on the unfiltered seven-call (or larger) chain, not this event file.
    complete=read(d/'round141_control_audit.json');assert complete['PASS']
    result=dict(PASS=True,triggered=True,pair_ready=True,choice=choice,sides=sides,cover=pair['cover'],
        verification_closeout_SHA=sha(d/'verification_closeout.json'),complete_control_audit_SHA=sha(d/'round141_control_audit.json'),
        source_input_SHA=p['input_sha256'],pure_reader_SHA=sha(__file__),Optimize=0,Native_load=0,
        seconds=time.perf_counter()-tick)
    write(d/'round141_chain_audit.json',result);return result

if __name__=='__main__':
    matrix=read(OUT/f'{sys.argv[1]}_matrix.json')
    group=matrix['groups'][int(sys.argv[2])-1]
    print(json.dumps(check(group['launch']['destination'])),flush=True)
