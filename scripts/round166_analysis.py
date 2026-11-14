"""Deterministic offline finite intersections, never an optimization algorithm."""
from round166_common import *
from fractions import Fraction as F
from itertools import combinations
import csv,math,os
MARGIN=F(1,10_000_000)
U_MARGIN=F(1,10**12)
def line(a,x):return a['a']+a['b']*x
def crossing(a,b):return None if a['b']==b['b'] else (b['a']-a['a'])/(a['b']-b['b'])
def serial(v):
    if isinstance(v,F):return dict(exact=str(v),value=float(v))
    if isinstance(v,list):return [serial(x) for x in v]
    if isinstance(v,dict):return {k:serial(x) for k,x in v.items()}
    return v
def csvout(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def analyze():
    start=time.perf_counter();data=read(OUT/'review/data_physical_archive.json');records=data['records']
    folder=OUT/'analysis';folder.mkdir(exist_ok=True)
    results=[];table=[];points_csv=[];lines_csv=[]
    for family in ['R134:K-15-S','R134:UC-B20-B','R137:R-B20-S-T1','R137:R-X35-S-T2']:
        runs=[r for r in records if r['family']==family and r['parameter_analysis']]
        assert len({r['physical_SHA'] for r in runs})==1
        objective_lines={};coords={}
        for r in runs:
            assert r['lower_qualified'] and r['qualification']['lower_is_global_original_physical_problem']
            assert not r['qualification']['source_rejected']
            e=r['verified']['exact'];G,p,x=F(e['G']),F(e['p']),F(e['rho']);key=(G,p)
            if key not in objective_lines:objective_lines[key]=dict(id='plan'+str(len(objective_lines)+1),a=G,b=p,owners=[])
            objective_lines[key]['owners'].append(r['record_id'])
            L=F.from_float(r['global_L'])-MARGIN
            if x not in coords:coords[x]=dict(x=x,L=L,sources=[r['record_id']],all_sources=[r['record_id']])
            else:
                coords[x]['all_sources'].append(r['record_id'])
                if L>coords[x]['L']:coords[x].update(L=L,sources=[r['record_id']])
                elif L==coords[x]['L']:coords[x]['sources'].append(r['record_id'])
        plans=list(objective_lines.values());anchors=sorted(coords.values(),key=lambda r:r['x']);chords=[]
        low,high=anchors[0]['x'],anchors[-1]['x'];assert low<high
        for left,right in combinations(anchors,2):
            slope=(right['L']-left['L'])/(right['x']-left['x'])
            chords.append(dict(id='chord'+str(len(chords)+1),a=left['L']-slope*left['x'],b=slope,
                low=left['x'],high=right['x'],sources=[left['sources'],right['sources']]))
        knots={a['x'] for a in anchors}
        for a,b in combinations(plans,2):
            x=crossing(a,b)
            if x is not None and low<=x<=high:knots.add(x)
        for a,b in combinations(chords,2):
            x=crossing(a,b)
            if x is not None and max(a['low'],b['low'])<=x<=min(a['high'],b['high']):knots.add(x)
        for a,b in ((a,b) for a in plans for b in chords):
            x=crossing(a,b)
            if x is not None and b['low']<=x<=b['high']:knots.add(x)
        points=[]
        for x in sorted(knots):
            U=min(line(a,x) for a in plans);L=max(line(c,x) for c in chords if c['low']<=x<=c['high'])
            assert U>=L,('source/numerical investigation required, never clip',family,x,U,L)
            points.append(dict(rho=x,U_exact_physical=U,U_safe=U+U_MARGIN,L_safe=L,gap=U+U_MARGIN-L,
                upper=[a['id'] for a in plans if line(a,x)==U],lower=[c['id'] for c in chords if c['low']<=x<=c['high'] and line(c,x)==L]))
        intervals=[]
        for left,right in zip(sorted(knots),sorted(knots)[1:]):
            mid=(left+right)/2;U=min(line(a,mid) for a in plans);L=max(line(c,mid) for c in chords if c['low']<=mid<=c['high'])
            intervals.append(dict(low=left,high=right,upper=[a['id'] for a in plans if line(a,mid)==U],
                lower=[c['id'] for c in chords if c['low']<=mid<=c['high'] and line(c,mid)==L]))
        for a in plans:
            a['dominated_by']=[b['id'] for b in plans if b['a']<=a['a'] and b['b']<=a['b'] and (b['a']<a['a'] or b['b']<a['b'])]
            a['supported_intervals']=[dict(low=i['low'],high=i['high']) for i in intervals if a['id'] in i['upper']]
            gap=max(((line(a,q['rho'])+U_MARGIN-q['L_safe'],q['rho']) for q in points))
            a['fixed_plan_regret_upper']=dict(gap=gap[0],rho=gap[1])
            lines_csv.append(dict(family=family,plan=a['id'],G=float(a['a']),p=float(a['b']),G_exact=str(a['a']),p_exact=str(a['b']),owners=';'.join(a['owners']),dominated_by=';'.join(a['dominated_by']),supported=bool(a['supported_intervals'])))
        worst=max(points,key=lambda p:p['gap']);supported=sorted({p for i in intervals for p in i['upper']})
        best_fixed=min(plans,key=lambda a:a['fixed_plan_regret_upper']['gap'])
        results.append(dict(family=family,records=len(runs),unique_component_lines=len(plans),physical_SHA=runs[0]['physical_SHA'],
            rho_range=[low,high],plans=plans,anchors=anchors,chords=chords,critical_points=points,intervals=intervals,
            supported=supported,worst_gap=worst,best_fixed=dict(id=best_fixed['id'],**best_fixed['fixed_plan_regret_upper']),
            all_fleet_owners_preserved=True,no_new_solver=True,no_grid=True))
        table.append(dict(family=family,rho_low=float(low),rho_high=float(high),runs=len(runs),component_lines=len(plans),supported_lines=len(supported),
            worst_absolute_regret_upper=float(worst['gap']),worst_rho=float(worst['rho']),best_fixed_plan=best_fixed['id'],best_fixed_regret_upper=float(best_fixed['fixed_plan_regret_upper']['gap'])))
        points_csv += [dict(family=family,rho=float(p['rho']),rho_exact=str(p['rho']),U=float(p['U_safe']),L=float(p['L_safe']),gap=float(p['gap']),upper=';'.join(p['upper']),lower=';'.join(p['lower'])) for p in points]
    # Independently written review algebra agrees up to our explicit U rounding guard.
    independent=read(OUT/'review/data_envelope_check.json')
    for ours,theirs in zip(results,independent):
        assert ours['family']==theirs['family'] and abs(float(ours['worst_gap']['gap'])-theirs['worst_envelope_gap']['gap']['value']-float(U_MARGIN))<1e-15
    write(folder/'parameter_envelopes.json',serial(dict(UTC=utc(),lower_margin=MARGIN,upper_margin=U_MARGIN,
        coordinate='exact actual loaded binary64 lambda times exact sum of loaded binary64 weights; floating display retained in original archive',families=results)))
    csvout(folder/'parameter_summary.csv',table);csvout(folder/'parameter_lines.csv',lines_csv);csvout(folder/'parameter_intersections.csv',points_csv)
    resource=[]
    for r in read(OUT/'review/data_resource_pairs.json'):
        assert r['physical_nested_verified'];a=F.from_float(r['L1'])-MARGIN;b=F.from_float(r['L2'])-MARGIN
        u1=F(r['B_operations_T1']['exact']['G'])+F(r['B_operations_T1']['exact']['lambda_value'])*F(r['B_operations_T1']['exact']['P'])+U_MARGIN
        u2=F(r['B_operations_T2']['exact']['G'])+F(r['B_operations_T2']['exact']['lambda_value'])*F(r['B_operations_T2']['exact']['P'])+U_MARGIN
        # This experiment's selected U sources are B; never assume that silently.
        assert r['upper1_source']==r['B_T1'] and r['upper2_source']==r['B_T2']
        lo=max(F(0),a-u2);hi=u1-b;assert lo<=hi and lo>0
        row=dict(base=r['base'],T1=r['T1'],T2=r['T2'],raw_lower=r['lower_improvement'],raw_upper=r['upper_improvement'],raw_width=r['width'],
            safe_lower=float(lo),safe_upper=float(hi),safe_width=float(hi-lo),lower_exact=str(lo),upper_exact=str(hi),
            sources=[r[k] for k in ['lower1_source','upper1_source','lower2_source','upper2_source']],
            operations_T1=r['B_operations_T1'],operations_T2=r['B_operations_T2'])
        resource.append(row)
    write(folder/'resource_intervals.json',resource)
    csvout(folder/'resource_intervals.csv',[{k:v for k,v in r.items() if k not in ['sources','operations_T1','operations_T2']} for r in resource])
    old=next(r for r in records if r['record_id']=='R137:B2:59');new=next(r for r in records if r['record_id']=='R137:B3:71')
    e=old['verified']['exact'];n=new['verified']['exact'];rho=F(e['rho']);value=F(n['G'])+rho*F(n['p']);before=F(e['G'])+rho*F(e['p'])
    assert F(n['G'])<F(e['G']) and F(n['p'])<F(e['p'])
    write(folder/'X35_offline_improvement.json',serial(dict(old_owner=old['record_id'],new_owner=new['record_id'],actual_rho=rho,
        old_original_U=old['original']['U'],recomputed_old=before,reweighted_feasible=value,known_improvement=before-value,
        original_U_or_clock_backfilled=False,formal_Start_injection=False)))
    write(folder/'analysis_receipt.json',dict(UTC=utc(),seconds=time.perf_counter()-start,Optimize=0,
        archive=bind(OUT/'review/data_physical_archive.json'),families=4,full_fleets=50,parameter_records=32,
        qualified_margin=float(MARGIN),upper_rounding_guard=float(U_MARGIN),source_crossing_found=False,independent_algebra_matches=True))
    print(json.dumps(dict(parameter=table,resource=[{k:r[k] for k in ['base','safe_lower','safe_upper','safe_width']} for r in resource]),indent=2))
if __name__=='__main__':analyze()
