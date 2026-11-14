"""Independent final arithmetic/identity checks. Pure reads and finite algebra; no solver."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from collections import Counter
import ast,hashlib,json,math,re,time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round166'
PAPER=ROOT/'results/unified_exact_round137'
BEGIN=time.perf_counter()

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def q(v): return F(v['exact']) if isinstance(v,dict) and 'exact' in v else F(v)
def line(ab,x):return ab[0]+ab[1]*x
def meet(ab,cd):return None if ab[1]==cd[1] else (cd[0]-ab[0])/(ab[1]-cd[1])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA256=sha(p))

archive=read(OUT/'review/data_physical_archive.json')
assert len(archive['records'])==50 and not archive['missing'] and archive['new_Optimize']==0
inputs={a['family']:a for a in archive['inputs']}
records={a['record_id']:a for a in archive['records']}
physical=[]
for family,a in inputs.items():
    raw=a['input_text']
    assert hashlib.sha256(raw.encode()).hexdigest()==a['input_SHA']
    fields={}
    for s in raw.splitlines()[1:]:
        if '=' in s:
            k,v=s.split('=',1);fields[k.strip()]=ast.literal_eval(v.strip())
    p=a['physical'];n,m=map(int,raw.splitlines()[0].split()[:2])
    assert (n,m)==(p['n'],p['m'])
    for old,new in [('initial','b'),('target','D'),('capacities','c'),('weights','w')]:assert fields[old]==p[new]
    assert [list(z) for z in fields['points']]==p['xy']
    weights=[F.from_float(w) for w in p['w'][1:]];omega=sum(weights)
    assert omega>0 and list(map(str,[w/omega for w in weights]))==a['normalized_weights']

for rid,r in records.items():
    p=inputs[r['family']]['physical'];n=p['n'];v=r['verified'];ex=v['exact'];Y=v['Y']
    assert r['physical_SHA']==inputs[r['family']]['physical_SHA']
    assert r['source']['input_SHA']==inputs[r['family']]['input_SHA']
    ratio=[F(Y[i],p['D'][i]) for i in range(1,n+1)]
    total=sum(ratio);g=sum(abs(x-y) for x,y in combinations(ratio,2))/(n*total) if total else F(0)
    weights=[F.from_float(w) for w in p['w'][1:]];omega=sum(weights)
    penalty=sum(w*abs(ri-1) for w,ri in zip(weights,ratio));lam=F.from_float(v['lambda_value'])
    for k,value in [('G',g),('P',penalty),('Omega',omega),('p',penalty/omega),('lambda_value',lam),('rho',lam*omega)]:
        assert F(ex[k])==value,(rid,k)
    assert abs(float(g+lam*penalty)-v['F'])<=1e-14
    assert r['lower_qualified'] and r['qualification']['lower_is_global_original_physical_problem']
    for k in ['endpoint_qualified','implementation_qualified','evidence_complete','native_proof_qualified']:
        assert r['qualification'][k],(rid,k)
    assert not r['qualification']['source_rejected']
    stock=p['b'].copy();seen=set();vehicles=set();returns=0;pickups=0;drops=0;durations=[]
    for route in v['routes']:
        k=route['vehicle'];nodes=route['nodes'];assert k not in vehicles and 0<=k<p['m'];vehicles.add(k)
        assert nodes[0]==nodes[-1]==0
        operations={s['station']:s for s in route['operations']}
        assert len(operations)==len(route['operations']) and set(nodes[1:-1])==set(operations)
        load=0;handle=0
        for station in nodes[1:-1]:
            assert 1<=station<=n and station not in seen;seen.add(station)
            op=operations[station];pk,dr=op['pickup'],op['drop']
            assert int(pk)==pk and int(dr)==dr and min(pk,dr)==0 and max(pk,dr)>0
            assert pk>=0 and dr>=0
            stock[station]+=dr-pk;load+=pk-dr
            assert 0<=load<=p['Q'][k] and 0<=stock[station]<=p['c'][station]
            handle+=p['pickup_seconds']*pk+p['drop_seconds']*dr;pickups+=pk;drops+=dr
        returns+=load;handle+=p['drop_seconds']*load
        duration=handle+sum(math.hypot(p['xy'][i][0]-p['xy'][j][0],p['xy'][i][1]-p['xy'][j][1])/1.5 for i,j in zip(nodes,nodes[1:]))
        assert duration<=p['T']+1e-7,(rid,duration,p['T'])
        durations.append(duration)
    assert stock==Y and pickups==v['pickups'] and drops==v['drops'] and returns==v['returns']
    assert sum(Y[1:])==sum(p['b'][1:])-returns
    physical.append(dict(id=rid,source_input_SHA=r['source']['input_SHA'],physical_SHA=r['physical_SHA'],G=str(g),P=str(penalty),rho=str(lam*omega),return_load=returns,maximum_duration=max(durations,default=0)))

env=read(OUT/'analysis/parameter_envelopes.json');margin=q(env['lower_margin']);upper=q(env['upper_margin'])
assert margin==F(1,10**7) and upper==F(1,10**12)
families=[]
for published in env['families']:
    family=published['family'];runs=[r for r in records.values() if r['family']==family and r['parameter_analysis']]
    expected_plans={};anchors={}
    for r in runs:
        e=r['verified']['exact'];ab=(F(e['G']),F(e['p']));x=F(e['rho']);lower=F.from_float(r['global_L'])-margin
        expected_plans.setdefault(ab,set()).add(r['record_id'])
        if x not in anchors or lower>anchors[x][0]:anchors[x]=(lower,{r['record_id']})
        elif lower==anchors[x][0]:anchors[x][1].add(r['record_id'])
    actual_plans={(q(p['a']),q(p['b'])):p for p in published['plans']}
    assert set(actual_plans)==set(expected_plans)
    for ab,ids in expected_plans.items():assert set(actual_plans[ab]['owners'])==ids
    actual_anchors={q(a['x']):(q(a['L']),set(a['sources'])) for a in published['anchors']}
    assert actual_anchors==anchors
    cc=sorted(anchors);low,high=cc[0],cc[-1];assert [q(v) for v in published['rho_range']]==[low,high]
    chords=[]
    for a,b in combinations(cc,2):
        slope=(anchors[b][0]-anchors[a][0])/(b-a);chords.append(((anchors[a][0]-slope*a,slope),a,b))
    got_chords={((q(c['a']),q(c['b'])),q(c['low']),q(c['high'])) for c in published['chords']}
    assert got_chords==set(chords)
    knots=set(cc)
    for ab,cd in combinations(expected_plans,2):
        x=meet(ab,cd)
        if x is not None and low<=x<=high:knots.add(x)
    for (ab,a,b),(cd,c,d) in combinations(chords,2):
        x=meet(ab,cd)
        if x is not None and max(a,c)<=x<=min(b,d):knots.add(x)
    for ab in expected_plans:
        for cd,c,d in chords:
            x=meet(ab,cd)
            if x is not None and c<=x<=d:knots.add(x)
    published_points={q(p['rho']):p for p in published['critical_points']}
    assert set(published_points)==knots
    maxima=[]
    for x in sorted(knots):
        u=min(line(ab,x) for ab in expected_plans);lo=max(line(ab,x) for ab,a,b in chords if a<=x<=b)
        assert u>=lo,(family,'crossing',x)
        point=published_points[x];assert q(point['U_exact_physical'])==u and q(point['U_safe'])==u+upper and q(point['L_safe'])==lo and q(point['gap'])==u+upper-lo
        if low<x<high:
            left=max(line(ab,x) for ab,a,b in chords if a<x<=b)
            right=max(line(ab,x) for ab,a,b in chords if a<=x<b)
            assert left==right==lo,(family,'one-sided discontinuity',x)
        maxima.append((u+upper-lo,x))
    worst=max(z[0] for z in maxima);assert worst==q(published['worst_gap']['gap'])
    assert q(published['worst_gap']['rho']) in [x for gap,x in maxima if gap==worst]
    pp=sorted(knots);supported=set()
    for a,b in zip(pp,pp[1:]):
        mid=(a+b)/2;u=min(line(ab,mid) for ab in expected_plans)
        ids={p['id'] for ab,p in actual_plans.items() if line(ab,mid)==u};supported.update(ids)
        stored=next(i for i in published['intervals'] if q(i['low'])==a and q(i['high'])==b)
        assert set(stored['upper'])==ids
        lower_ids={c['id'] for c in published['chords'] if q(c['low'])<=mid<=q(c['high']) and q(c['a'])+q(c['b'])*mid==max(line(ab,mid) for ab,c,d in chords if c<=mid<=d)}
        assert set(stored['lower'])==lower_ids
    assert supported==set(published['supported'])
    fixed=[]
    for ab,p in actual_plans.items():
        fg=max(line(ab,x)+upper-q(published_points[x]['L_safe']) for x in knots)
        assert fg==q(p['fixed_plan_regret_upper']['gap']);fixed.append(fg)
    assert min(fixed)==q(published['best_fixed']['gap'])
    families.append(dict(family=family,records=len(runs),lines=len(expected_plans),exact_coordinates=list(map(str,cc)),anchor_pairs=len(chords),critical_points=len(knots),supported=len(supported),continuous_LC=True,worst_gap_exact=str(worst),worst_gap=float(worst),best_fixed_gap_exact=str(min(fixed)),best_fixed_gap=float(min(fixed))))

resource=[]
for row in read(OUT/'analysis/resource_intervals.json'):
    l1,u1,l2,u2=[records[rid] for rid in row['sources']]
    ip1=inputs[l1['family']]['physical'];ip2=inputs[l2['family']]['physical']
    assert ip1['T']<ip2['T'] and {k:v for k,v in ip1.items() if k!='T'}=={k:v for k,v in ip2.items() if k!='T'}
    assert F(u1['verified']['exact']['lambda_value'])==F(u2['verified']['exact']['lambda_value'])
    def obj(r):
        e=r['verified']['exact'];return F(e['G'])+F(e['lambda_value'])*F(e['P'])
    lower=max(F(0),F.from_float(l1['global_L'])-margin-obj(u2)-upper)
    higher=obj(u1)+upper-F.from_float(l2['global_L'])+margin
    assert lower==F(row['lower_exact']) and higher==F(row['upper_exact']) and lower>0
    resource.append(dict(base=row['base'],strict=True,lower_exact=str(lower),upper_exact=str(higher),width=float(higher-lower),returned_stock=[u1['verified']['returns'],u2['verified']['returns']]))

arms=read(OUT/'reports/complete_arms.json');pairs=read(OUT/'reports/pairs.json');summary=read(OUT/'reports/summary.json')
assert len(arms)==12 and len(pairs)==6 and len({r['position'] for r in arms})==12
for a in arms:
    assert a['seed']==0 and a['PE_SHA']==summary['PE_SHA'] and a['DLL_SHA']==summary['DLL_SHA'] and a['source_commit']==summary['source_commit']
    assert a['H_complete'] and not a['source_reduced']
    for k in ['certificate_qualified','numbers_qualified','native_proof_qualified','performance_eligible','formal_protocol_qualified','implementation_qualified','model_scope_qualified','evidence_complete']:
        if k=='certificate_qualified' and not a['certificate']:continue
        assert a[k],(a['arm_id'],k)
    assert a['T_produce']<=a['cap_seconds'] and abs(a['T_produce']+a['T_verify']-a['T_total'])<=1e-10
    assert a['native_Optimize']==a['declared_calls']==a['returned_calls']
    assert a['L']<=a['U']+1e-7
    assert (a['T_cert']==a['T_produce']) if a['state']=='CERT' else (a['T_cert'] is None)
    endpoint=ROOT/a['endpoint']['path'];assert sha(endpoint)==a['endpoint']['SHA256']
certs=Counter(a['method'] for a in arms if a['state']=='CERT');assert dict(certs)==summary['CERT']=={'B':3,'C166':2}
assert sum(a['native_Optimize'] for a in arms)==summary['total_native_Optimize']==62
joint=0;substantive=[];deltas=[]
for pair in pairs:
    b=next(a for a in arms if a['id']==pair['id'] and a['method']=='B');c=next(a for a in arms if a['id']==pair['id'] and a['method']=='C166')
    assert b['input_SHA']==c['input_SHA'] and b['H_semantic_SHA']==c['H_semantic_SHA'] and b['H_fleet_SHA']==c['H_fleet_SHA']
    for key in ['U','L']:
        assert b[key]==pair['B_'+key] and c[key]==pair['C166_'+key]
        assert c[key]-b[key]==pair['delta_'+key+'_C166_minus_B']
    actual_joint=b['state']==c['state']=='CERT';assert actual_joint==pair['joint_CERT']
    if actual_joint:
        joint+=1;assert c['T_cert']/b['T_cert']==pair['C166_over_B_T_cert']
        threshold=max(10,.1*min(b['T_cert'],c['T_cert']));assert threshold==pair['substantive_threshold_seconds']
        actual=abs(c['T_cert']-b['T_cert'])>=threshold;assert actual==pair['substantive_difference']
        if actual:substantive.append(pair['id'])
    else:assert pair['C166_over_B_T_cert'] is None
    deltas.append(dict(id=pair['id'],U=c['U']-b['U'],L=c['L']-b['L']))
assert joint==summary['joint_CERT_pairs']==2 and substantive==['R163-X20-S']
assert {d['id'] for d in deltas if d['U']<0 and d['L']<0}=={'R163-C35-U','R163-B35-S'}
assert next(d for d in deltas if d['id']=='R163-X35-S')['U']>0
assert next(d for d in deltas if d['id']=='R163-X35-S')['L']<0

build=read(OUT/'document_build.json');pdfs=[]
for output in build['outputs']:
    p=ROOT/output['path'];assert sha(p)==output['SHA256'];src=ROOT/output['source']['path'];assert sha(src)==output['source']['SHA256']
    pdfs.append(bind(p))
receipt=dict(PASS=True,Optimize=0,seconds=time.perf_counter()-BEGIN,physical_fleets=len(physical),physical_rechecks=physical,
    parameter_families=families,resource_intervals=resource,formal_positions=len(arms),CERT=dict(certs),joint_CERT=joint,substantive_certificate_time_pair=substantive,formal_deltas=deltas,
    inputs=[bind(OUT/p) for p in ['compression_theory.md','decision_analysis.md','analysis/parameter_envelopes.json','analysis/resource_intervals.json','analysis/X35_offline_improvement.json','review/data_physical_archive.json','reports/complete_arms.json','reports/pairs.json','reports/summary.json']],
    paper_inputs=[bind(PAPER/p) for p in ['paper_body.md','model_and_algorithm_appendices.md','mathematical_analysis.md','supplement.md','references.bib','manuscript.md']],PDFs=pdfs)
(OUT/'review/math_final_checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(PASS=True,Optimize=0,fleets=len(physical),families=families,positions=len(arms),CERT=dict(certs),maxima_checked='all exact endpoints/intersections and one-sided LC values')))
