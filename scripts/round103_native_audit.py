"""Read-only exact row/combination validation. No solver imports or Optimize."""
from round103_hull import validate,exact
from round103_common import *
from fractions import Fraction as F
import math

def audit(directory):
    records=[];optimize=dp=selected=submitted=0
    for path in sorted(Path(directory).rglob('*.round103.summary.json')):
        q=read(path);prefix=str(path)[:-len('.summary.json')]
        if q['cache_hit']:
            paid=read(q['paid_evidence']);assert q['canonical_sha256']==paid['canonical_sha256']
            records.append(dict(path=str(path),cache_hit=True));continue
        c=read(prefix+'.contract.json');assert c['source_sha256']==q['source_sha256']
        assert sha(c['source_path'])==c['source_sha256'] and sha(q['canonical_path'])==q['canonical_sha256']
        events=[json.loads(s) for s in Path(prefix+'.calls.jsonl').read_text().splitlines()]
        ob=[r for r in events if r['event']=='Optimize_begin'];orr=[r for r in events if r['event']=='Optimize_return']
        db=[r for r in events if r['event']=='DP_begin'];dr=[r for r in events if r['event']=='DP_return']
        assert len(ob)==len(orr)==q['Optimize_calls'] and len(db)==len(dr)==q['DP_calls']
        assert [r['serial'] for r in ob]==[r['serial'] for r in orr]==list(range(1,len(ob)+1))
        cc=c['column_contract'];resource=cc['resource'];columns=cc['service_columns']
        for begin,r in zip(db,dr):
            p=r['proof'];assert p['vehicle']==begin['vehicle'] and not p['anchors']
            if not p['valid']:
                member=read(prefix+'.vehicle'+str(p['vehicle'])+'.json')
                assert member['status']=='UNKNOWN' and member['reason'] in [
                    'support_unknown:unsupported_resource_dimension_no_bound','support_unknown:witness_memory_limit_no_bound',
                    'support_unknown:weight_range','support_unknown:score_range']
                continue
            validate(resource,p['vehicle'],p['solution'],p['anchors'])
            assert sum(a*b for w,r in zip(p['weights'],p['solution']) for a,b in zip(w,r))==p['upper']
        members=[]
        point=dict(read(prefix+'.point.json')['variables']) if q['root_optimal'] else {}
        for p in sorted(Path(prefix).parent.glob(Path(prefix).name+'.vehicle*.json')):
            result=read(p);k=int(p.name.split('.vehicle')[1].split('.')[0]);combo=result['combination'];mass=sum((exact(r['lambda_raw']) for r in combo),F(0))
            delta=F(0)
            if combo:
                assert mass>0 and all(r['lambda_raw']>0 for r in combo)
                for r in combo:validate(resource,k,r['plan'])
                for i in range(1,len(resource['initial'])):
                    A=min(resource['initial'][i],resource['capacities'][k]);B=min(resource['station_capacity'][i]-resource['initial'][i],resource['capacities'][k])
                    for t,(tag,width) in enumerate(zip(['p','d','z'],[A,B,int(A>0 or B>0)])):
                        value=sum((exact(r['lambda_raw'])*r['plan'][i][t] for r in combo),F(0))/mass
                        error=abs(exact(point[f'{tag}_{k}_{i}'])-value)/(width or 1);delta=max(delta,error)
                assert delta<=exact(result['distance_upper'])
            if result['status']=='INSIDE':assert combo and delta<=exact(1e-8)
            members.append(dict(vehicle=k,status=result['status'],exact_combination_residual=str(delta) if combo else None))
        rowfile=read(prefix+'.rows.json');assert len(rowfile['rows'])==q['reliable_scaled_rows']
        for row in rowfile['rows']:
            proof=row['proofs'][0];w=proof['weights'];coeff=dict(row['coefficients']);k=proof['vehicle'];ratios=[]
            for i in range(1,len(w)):
                for tag,value in zip(['p','d','z'],w[i]):
                    name=f'{tag}_{k}_{i}'
                    if value:ratios.append(exact(coeff.pop(name))/value)
            assert not coeff and ratios and ratios[0]>0 and all(r==ratios[0] for r in ratios)
            assert exact(row['rhs'])==ratios[0]*proof['upper']
            activity=sum((exact(a)*exact(point[name]) for name,a in row['coefficients']),F(0))
            assert activity-exact(row['rhs'])>=exact(row['violation_lower'])>exact(10*q['original_mip_FeasibilityTol'])
        if q['mode']=='submit':assert q['submitted']==len(rowfile['rows'])
        else:assert q['submitted']==0 and q['canonical_sha256']==q['source_sha256']
        optimize+=len(ob);dp+=len(db);selected+=q['selected'];submitted+=q['submitted']
        records.append(dict(path=str(path),cache_hit=False,seconds=q['seconds'],members=members,Optimize_calls=len(ob),DP_calls=len(db),submitted=q['submitted']))
    return dict(passed=True,records=records,auxiliary_Optimize_calls=optimize,DP_calls=dp,selected=selected,submitted=submitted,
        scope='exact binary-rational row scaling/attainment and combination residual; support optimality follows production DP proof, not independent enumeration')
