"""One finite exact NC-PC reconstruction from the four sealed R144 source points.

This is proof/diagnostic only. It never imports a commercial runtime, optimizes,
or writes a row into a fresh algorithm run.
"""
import collections,re,gzip
from fractions import Fraction as F
import round108_reader as parser
from round140_math import model_counts
from round145_common import *
configure()

def box_dual(coefficients,point,L,U,b):
    """Exact one-dimensional station-box value and legal mass multipliers."""
    delta=U-L;assert delta>0;groups={};masses={}
    for i in sorted({i for i,y in coefficients}):
        weights=collections.defaultdict(F)
        for (j,y),k in coefficients.items():
            if j!=i:continue
            s=F(point[f'state_{i}_{y}']);assert s>=0
            if s:weights[k]+=s
        groups[i]=sorted(weights.items());masses[i]=sum(weights.values(),F(0));assert groups[i]
    lo=max([L]+[L*m for m in masses.values()]);hi=min([U]+[U*m for m in masses.values()]);assert lo<=hi
    def interval(i,t):
        values=groups[i];rem=(t-L*masses[i])/delta
        if rem<=0:return None,values[0][0]
        if rem>=masses[i]:return values[-1][0],None
        cumulative=F(0)
        for j,(k,weight) in enumerate(values):
            cumulative+=weight
            if rem<cumulative:return k,k
            if rem==cumulative:return k,values[j+1][0]
        raise AssertionError('quantile')
    events=collections.defaultdict(F)
    for i,values in groups.items():
        cumulative=F(0)
        for j,(k,weight) in enumerate(values[:-1]):
            cumulative+=weight;t=L*masses[i]+delta*cumulative
            if lo<t<hi:events[t]+=values[j+1][0]-k
    slope=b+sum((interval(i,lo)[1] if interval(i,lo)[1] is not None else groups[i][-1][0]) for i in groups)
    star=lo if slope>=0 else hi
    if slope<0:
        for t,change in sorted(events.items()):
            slope+=change
            if slope>=0:star=t;break
    limits={i:interval(i,star) for i in groups}
    multipliers={i:(a if a is not None else z) for i,(a,z) in limits.items()}
    gamma=b+sum(multipliers.values(),F(0))
    compatible=(star==L and gamma>=0) or (star==U and gamma<=0) or gamma==0
    if not compatible:
        remaining=-gamma
        for i,(lower,upper) in limits.items():
            if remaining>0:
                amount=remaining if upper is None else min(remaining,upper-multipliers[i])
            else:
                amount=remaining if lower is None else max(remaining,lower-multipliers[i])
            multipliers[i]+=amount;remaining-=amount
            if not remaining:break
        assert remaining==0
    gamma=b+sum(multipliers.values(),F(0));constant=min(L*gamma,U*gamma)
    a={(i,y):min(L*(k-multipliers[i]),U*(k-multipliers[i])) for (i,y),k in coefficients.items()}
    value=constant+sum(v*F(point[f'state_{i}_{y}']) for (i,y),v in a.items())
    primal=b*star
    for i,values in groups.items():
        primal+=L*sum(k*weight for k,weight in values);remaining=star-L*masses[i]
        for k,weight in values:
            amount=min(remaining,delta*weight);primal+=k*amount;remaining-=amount
        assert remaining==0
    assert value==primal,(value,primal)
    return multipliers,constant,a,value,star

def main():
    configure();assert not budget()['unclosed'];tick=time.perf_counter();facts=[]
    previous=ROOT/'results/unified_exact_round144'
    roles=[('K-35-U','pilot',2,.0862352641105),('R-X20-S-T1','pilot',4,.0125145224432),
        ('K-20-S','resource_k20',2,.1139059369152),('R-B35-S-T2','resource',2,.1340443111542)]
    for role,batch,position,expected in roles:
        folder=previous/('campaign_'+batch)/f'{position:03}'
        identity=read(folder/'identity.json');launch=identity['launches'][0];assert launch['id']==role
        raw=Path(launch['destination'])/'external';evidence=read(raw/'round144_projection.json');source=raw/'models/round144_RN_source.lp'
        assert sha(source)==evidence['source_SHA'];columns={c['name']:c for c in evidence['variables']};point={k:c['X'] for k,c in columns.items()}
        point_matrix=source;point_evidence=raw/'round144_projection.json';point_kind='sealed complete production RN source'
        p=launch['panel'];B=p['total_initial'];bm=max(0,B-sum(p['Q_vector']));counts=model_counts(parser.lp_model(source),bm,B)
        coefficients=counts['TC2'];b=counts['constant'];L,U=F(columns['rn_t']['LB']),F(columns['rn_t']['UB']);n=p['V']
        if role=='R-X20-S-T1':
            # The supplied RX20 signal identifies the standalone saved LP,
            # whose degenerate optimum differs from the complete run's point.
            saved=previous/'LP'/f'{role}_base';scope=read(saved/'source_scope.json');spec=scope['RN']
            assert counts['supports']=={int(i):ys for i,ys in spec['supports'].items()}
            assert counts['ratios']=={int(i):F(v) for i,v in spec['c_binary64'].items()}
            assert (L,U)==(F(spec['L_t']),F(spec['U_t']))
            point_matrix=saved/'source.mps';point_evidence=saved/'source_solution.json.gz'
            assert sha(point_matrix)==scope['model_SHA'] and read(saved/'result.json')['qualified']
            point=json.loads(gzip.decompress(point_evidence.read_bytes()));point_kind='sealed standalone production-capped RN LP'
        lam,const,a,value,star=box_dual(coefficients,point,L,U,b)
        violation=value-n*F(point['G']);old_H=sum(F(v) for k,v in point.items() if re.fullmatch(r'h_\d+_\d+',k))
        old_rhs=b+sum(k*F(point[f'state_{i}_{y}']) for (i,y),k in coefficients.items())
        assert violation>0 and old_rhs>old_H
        terms={'G':str(F(n))};terms.update({f'state_{i}_{y}':str(-v) for (i,y),v in a.items() if v})
        facts.append(dict(role=role,source=str(point_matrix.relative_to(ROOT)),source_SHA=sha(point_matrix),
            evidence_SHA=sha(point_evidence),point_kind=point_kind,count_matrix=str(source.relative_to(ROOT)),count_matrix_SHA=sha(source),
            original_x_violation_exact=str(violation),violation_per_n=float(violation/n),
            goal_reported_violation_per_n=expected,difference_from_goal=float(violation/n)-expected,
            old_TC2_violation_exact=str(old_rhs-old_H),t_station_box_minimizer_exact=str(star),
            station_multipliers_exact={i:str(v) for i,v in lam.items()},row=dict(sense='>',rhs_exact=str(const),terms_exact=terms),
            count_constant_exact=str(b),L_t_exact=str(L),U_t_exact=str(U),
            exact_box_primal_dual_identity=True,all_extensions_of_original_x_excluded=True,
            source_point_only_not_reoptimized_objective=True))
    assert 'gurobipy' not in sys.modules
    write(OUT/'math/saved_point_NC_PC.json',dict(PASS=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,facts=facts,
        NC_identity='Ideal exact NC2 aggregates from actual binary64 c interpreted as rationals; distinct from production R140-down floating NC rows',
        selector_masses_preserved_without_normalization=True,
        scope='Finite exact reconstruction of the supplied motivating NC-PC signals; no production cut pool, extra algorithm or LP gain claim',
        no_supplemental_zip_byte_identity_claimed=True))
    print(json.dumps([{k:r[k] for k in ['role','violation_per_n','difference_from_goal']} for r in facts]))
if __name__=='__main__':main()
