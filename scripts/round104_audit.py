"""Pure exact row/attempt accounting; repeated support is not independent DP."""
from round104_common import *
from round103_hull import validate,exact
from fractions import Fraction as F
def audit(directory):
    records=[];optimize=dp=submitted=0
    for path in sorted(Path(directory).rglob('*.round104.summary.json')):
        q=read(path);prefix=str(path).removesuffix('.summary.json')
        if q['cache_hit']:
            paid=read(q['paid_evidence']);assert paid['canonical_sha256']==q['canonical_sha256']
            records.append(dict(path=str(path),cache_hit=True));continue
        c=read(prefix+'.contract.json');assert sha(c['source_path'])==c['source_sha256']==q['source_sha256']
        assert sha(q['canonical_path'])==q['canonical_sha256']
        events=[json.loads(s) for s in Path(prefix+'.calls.jsonl').read_text().splitlines()]
        ob=[r for r in events if r['event']=='Optimize_begin'];orr=[r for r in events if r['event']=='Optimize_return']
        db=[r for r in events if r['event']=='DP_begin'];dr=[r for r in events if r['event']=='DP_return']
        assert len(ob)==len(orr)==q['Optimize_calls'] and len(db)==len(dr)==q['DP_calls']
        assert [r['serial'] for r in ob]==[r['serial'] for r in orr]==list(range(1,len(ob)+1))
        resource=c['column_contract']['resource']
        for begin,r in zip(db,dr):
            proof=r['proof'];assert proof['vehicle']==begin['vehicle']
            if proof['valid']:
                validate(resource,proof['vehicle'],proof['solution'],proof.get('anchors',[]))
                assert sum(a*b for w,p in zip(proof['weights'],proof['solution']) for a,b in zip(w,p))==proof['upper']
            else:assert proof['reason'] in ['unsupported_resource_dimension_no_bound','witness_memory_limit_no_bound','weight_range','score_range']
        pool=read(prefix+'.pool.rows.json')['rows'];chosen=read(prefix+'.rows.json')['rows'];dual=read(prefix+'.dual.json')
        assert len(pool)==q['pool_rows'] and len(chosen)==q['reliable_scaled_rows']
        for row in pool+chosen:
            proof=row['proofs'][0];coeff=dict(row['coefficients']);k=proof['vehicle'];ratios=[]
            for i,w in enumerate(proof['weights'][1:],1):
                for tag,a in zip(['p','d','z'],w):
                    if a:ratios.append(exact(coeff.pop(f'{tag}_{k}_{i}'))/a)
            assert not coeff and ratios and ratios[0]>0 and all(v==ratios[0] for v in ratios)
            assert exact(row['rhs'])==ratios[0]*proof['upper']
        if q['qualification'].startswith('reoptimized'):
            expected=[r for r,p in zip(pool,dual['Pi']) if p<0]
            assert [(r['coefficients'],r['rhs']) for r in expected]==[(r['coefficients'],r['rhs']) for r in chosen]
            assert abs(q['compressed_objective']-q['finite_pool_objective'])<=1e-7
        if q['mode']=='shadow':assert q['submitted']==0 and q['canonical_sha256']==q['source_sha256']
        else:assert q['mode']=='active' and q['submitted']==len(chosen)
        optimize+=len(ob);dp+=len(db);submitted+=q['submitted']
        records.append(dict(path=str(path),cache_hit=False,seconds=q['seconds'],pool_rows=len(pool),chosen=len(chosen),
            qualification=q['qualification'],pool_stop=q['pool_stop'],pool_bound=q['finite_pool_objective'],compressed_bound=q['compressed_objective']))
    return dict(passed=True,records=records,auxiliary_Optimize_calls=optimize,DP_calls=dp,submitted=submitted,
        scope='exact dyadic source support scaling and attempts; attaining witness not independent support proof; native B&B separately audited')
