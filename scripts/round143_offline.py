"""Reconstruct fixed-point RN certificates from R140, with zero Optimize.

The separately named offline ZIP was not supplied locally. This bounded exact
checker rebuilds the twelve point checks from the original hash-bound carrier.
It does not claim rational optimality of the inherited complete LP matrices.
"""
import bisect,gzip
from fractions import Fraction as F
from itertools import combinations
from round143_common import *
from round143_qualify import actual_spec
import round108_reader as core

def station(c,states,lt,ut,reverse=False):
    # Piecewise-linear exact attainable endpoint with the observed selectors.
    states=[(y,s) for y,s in states if s];mass=sum((s for y,s in states),F(0))
    a=lt*mass;base=c*sum((y*lt*s for y,s in states),F(0));segments=[]
    for y,s in sorted(states,reverse=reverse):
        b=a+(ut-lt)*s;segments.append((a,b,c*y,base-c*y*a));base+=c*y*(b-a);a=b
    return dict(segments=segments,breaks=[v[0] for v in segments]+[a],mass=mass,states=states,c=c)

def value(site,t):
    k=max(0,min(len(site['segments'])-1,bisect.bisect_right(site['breaks'],t)-1));a,b,slope,intercept=site['segments'][k]
    return slope*t+intercept

def interval(c,states,lt,ut):
    low={i:station(c[i],states[i],lt,ut) for i in c};high={i:station(c[i],states[i],lt,ut,True) for i in c}
    tl=max([lt]+[lt*low[i]['mass'] for i in c]);tu=min([ut]+[ut*low[i]['mass'] for i in c]);assert tl<=tu
    breaks=sorted({tl,tu}|{x for sites in (low,high) for s in sites.values() for x in s['breaks'] if tl<x<tu})
    feasible=[]
    for a,b in zip(breaks,breaks[1:]):
        lower_a=sum((value(s,a) for s in low.values()),F(0));lower_b=sum((value(s,b) for s in low.values()),F(0))
        upper_a=sum((value(s,a) for s in high.values()),F(0));upper_b=sum((value(s,b) for s in high.values()),F(0))
        left,right=a,b
        # Both endpoint sums are increasing in t because c>0 and y>=0.
        if lower_a>1 or upper_b<1:continue
        if lower_b>1:right=min(right,a+(1-lower_a)*(b-a)/(lower_b-lower_a))
        if upper_a<1:left=max(left,a+(1-upper_a)*(b-a)/(upper_b-upper_a))
        if left<=right:feasible.extend([left,right])
    assert feasible
    tl,tu=min(feasible),max(feasible)
    return low,high,sorted({tl,tu}|{t for t in breaks if tl<t<tu})

def waterfill(l,u):
    breaks=sorted(set(l.values())|set(u.values()))
    def values(z):return {i:max(l[i],min(z,u[i])) for i in l}
    for z in breaks:
        p=values(z)
        if sum(p.values())==1:return p
    for a,b in zip(breaks,breaks[1:]):
        va,vb=values(a),values(b);sa,sb=sum(va.values()),sum(vb.values())
        if sa<=1<=sb and sb>sa:return values(a+(1-sa)*(b-a)/(sb-sa))
    return None

def extreme_w(states,lt,ut,t,reverse=False):
    w={y:lt*s for y,s in states};extra=t-sum(w.values())
    for y,s in sorted(states,reverse=reverse):
        add=min(extra,(ut-lt)*s);w[y]+=add;extra-=add
    assert extra==0;return w

def main():
    tick=time.perf_counter();results=[]
    for role in ['K-35-U','R-X20-S-T1','K-20-S','R-X35-S-T2']:
        folder=OUT/'inherited/roots'/role;parsed=core.lp_model(folder/'inherited/original.lp')
        scope=read(folder/'scope.json');B=scope['B'];bm=scope['Bminus']
        spec=actual_spec(parsed,bm,B);lt,ut=F(spec['L_t']),F(spec['U_t']);c={int(i):F(v) for i,v in spec['c_binary64'].items()}
        for variant in ['base','stock','tc_stock']:
            p=json.loads(gzip.decompress((folder/variant/'solution.json.gz').read_bytes()));g=F(p['G'])
            source=folder/'inherited/original.lp'
            if variant!='base':
                source=next(q for q in [folder/'stock_export_exact_cutoff/original.lp',folder/'stock_export/original.lp'] if q.exists())
            original=core.lp_model(source);matched=actual_spec(original,bm,B)
            assert all(matched[k]==spec[k] for k in ['c_binary64','supports','L_t','U_t'])
            if variant=='tc_stock':
                terms={name:1. for name in original['order'] if name.startswith('h_')}
                terms.update({name:-v for name,v in read(folder/'additions.json')['TC'].items() if v})
                original['rows'].append((tuple(sorted(terms.items())),'>=',0.))
            record=read(folder/variant/'result.json')
            assert len(original['rows'])==record['after']['rows'] and len(original['order'])==record['after']['columns']
            assert sum(len(terms) for terms,sense,rhs in original['rows'])==record['after']['nonzeros']
            from round143_qualify import point_residual
            # This is an inherited continuous point: integer-type residuals do
            # not apply until the original integer model is being evaluated.
            original['types']={k:'C' for k in original['order']}
            primal=point_residual(original,p);assert max(primal.values())<=1e-6
            objective=original['objective'][1]+math.fsum(a*p[k] for k,a in original['objective'][0])
            assert abs(objective-record['L'])<=1e-8
            states={i:[(y,F(p[f'state_{i}_{y}'])) for y in spec['supports'][i]] for i in c}
            low,high,ts=interval(c,states,lt,ut)
            certificate=dict(role=role,variant=variant,old_g=float(g),old_g_exact=str(g),
                block_base_model_SHA=sha(folder/'inherited/original.lp'),actual_variant_source_SHA=sha(source),
                inherited_complete_model_SHA=record['model_SHA'],inherited_result_SHA=sha(folder/variant/'result.json'),
                variant_matrix_recipe='actual BASE' if variant=='base' else 'actual stock' if variant=='stock' else 'actual stock plus original TC row',
                variant_complete_matrix_saved_point_residual=primal,variant_complete_objective=objective,
                source_point_SHA=sha(folder/variant/'solution.json.gz'),actual_variant_c_support_and_t_bounds_match=True,
                block='Actual production compact RN bounds; conservative directed t endpoints and redundant finite caps',
                L_t=float(lt),U_t=float(ut),feasible_t_interval=[str(ts[0]),str(ts[-1])],breakpoint_count=len(ts),Optimize=0)
            if role in ('K-35-U','R-X20-S-T1'):
                mean={i:c[i]*sum((y*s for y,s in states[i]),F(0)) for i in c}
                def tied_ranks(v):
                    order=sorted(c,key=lambda i:(v[i],i));ranks={};start=0
                    while start<len(order):
                        end=start
                        while end+1<len(order) and v[order[end+1]]==v[order[start]]:end+=1
                        for k in range(start,end+1):ranks[order[k]]=start+end-len(c)+1
                        start=end+1
                    return ranks
                candidates=sorted(set(ts)|{ts[0]+(ts[-1]-ts[0])*k/64 for k in range(65)})
                supports=[]
                for t in candidates:
                    v=waterfill({i:value(low[i],t) for i in c},{i:value(high[i],t) for i in c})
                    if v is not None:
                        G=sum((abs(v[i]-v[j]) for i,j in combinations(c,2)),F(0))/len(c)
                        supports.append((G,t,tied_ranks(v)))
                ranks_list=[tied_ranks(mean)]+[r for G,t,r in sorted(supports,key=lambda x:(x[0],x[1]))[:4]]
                # Every selected rank/eta defines an independent valid support;
                # maximizing over this finite family is offline certificate search.
                best=None
                for ranks in ranks_list:
                    for eta in sorted(set(ranks.values())):
                        scores=[]
                        for t in ts:
                            rhs=F(eta)+sum((min((ranks[i]-eta)*value(low[i],t),(ranks[i]-eta)*value(high[i],t)) for i in c),F(0))
                            scores.append((rhs/len(c),t))
                        lb,t=min(scores)
                        if best is None or lb>best[0]:best=(lb,t,eta,ranks)
                lb,t,eta,ranks=best;assert lb>g,(role,variant,float(lb),float(g))
                certificate.update(status='FIXED_SELECTOR_EXCLUDED',rank_coefficients=ranks,eta=eta,
                    g_lower_exact=str(lb),g_lower=float(lb),separation=float(lb-g),minimizing_t=str(t),
                    proof='Rank support min over all exact endpoint/backpack/normalization breakpoints of the complete feasible t interval')
            else:
                # A grid may FIND a feasible extension; it never proves exclusion.
                candidates=sorted(set(ts)|{ts[0]+(ts[-1]-ts[0])*k/128 for k in range(129)})
                best=None
                for t in candidates:
                    l={i:value(low[i],t) for i in c};u={i:value(high[i],t) for i in c};v=waterfill(l,u)
                    if v is None:continue
                    G=sum((abs(v[i]-v[j]) for i,j in combinations(c,2)),F(0))/len(c)
                    if best is None or G<best[0]:best=(G,t,v,l,u)
                    if G<g:break
                assert best and best[0]<=g,(role,variant,best and float(best[0]),float(g))
                G,t,v,l,u=best;new={'rn_t':float(t)}
                exact_max=F(0)
                for i in c:
                    wl=extreme_w(states[i],lt,ut,t);wu=extreme_w(states[i],lt,ut,t,True)
                    theta=(v[i]-l[i])/(u[i]-l[i]) if u[i]>l[i] else F(0)
                    w={y:(1-theta)*wl[y]+theta*wu[y] for y in wl}
                    assert sum(w.values())==t and c[i]*sum((y*w[y] for y in w),F(0))==v[i]
                    for y,s in states[i]:assert lt*s<=w.get(y,0)<=ut*s
                    for y in spec['supports'][i]:new[f'rn_w_{i}_{y}']=float(w.get(y,F(0)))
                    new[f'rn_Y_{i}']=float(v[i]/c[i])
                for i,j in combinations(c,2):new[f'rn_h_{i}_{j}']=float(abs(v[i]-v[j]))
                # Direct numerical residual of actual binary64 coefficients/columns.
                full=dict(p,**new);from round143_qualify import expected_rows
                violation=0.
                for r in expected_rows(spec):
                    lhs=math.fsum(a*full[k] for k,a in r['terms'].items())
                    violation=max(violation,max(0,r['rhs']-lhs) if r['sense']=='>' else max(0,lhs-r['rhs']) if r['sense']=='<' else abs(lhs-r['rhs']))
                assert violation<=1e-12
                target=OUT/'math/extensions'/f'{role}_{variant}.json.gz';target.parent.mkdir(parents=True,exist_ok=True)
                with gzip.open(target,'wt',encoding='utf-8') as f:json.dump(new,f,separators=(',',':'))
                certificate.update(status='SAME_OLD_POINT_EXTENSION',normalized_G=float(G),gini_slack=float(g-G),
                    t=float(t),linear_residual=violation,new_columns_SHA=sha(target),new_columns_path=target.relative_to(OUT).as_posix(),
                    exact_station_mass_and_normalization=True,old_columns_and_objective_unchanged=True)
            results.append(certificate);print(role,variant,certificate['status'],flush=True)
    write(OUT/'math/offline_point_checks.json',dict(PASS=True,results=results,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,
        original_carrier_SHA=CARRIER_SHA,reconstructed_due_to_missing_separate_zip=True,
        rational_complete_LP_optimality_claimed=False))

if __name__=='__main__':main()
