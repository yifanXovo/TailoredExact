"""Independent exact finite-intersection check of the recovered decision archive."""
from pathlib import Path
from fractions import Fraction as F
import itertools,json,time
BASE=Path(__file__).resolve().parent
DATA=json.loads((BASE/'data_physical_archive.json').read_text())
def ff(x):return float(x)
def fs(x):return str(x.numerator)+'/'+str(x.denominator)
def line(x,m):return m['a']+m['b']*x
def cross(m,n):return (n['a']-m['a'])/(m['b']-n['b']) if m['b']!=n['b'] else None
def serial(d):
    if isinstance(d,F):return dict(value=float(d),rational=fs(d))
    if isinstance(d,list):return [serial(x) for x in d]
    if isinstance(d,dict):return {k:serial(v) for k,v in d.items()}
    return d
out=[]
for family in ['R134:K-15-S','R134:UC-B20-B','R137:R-B20-S-T1','R137:R-X35-S-T2']:
    rows=[r for r in DATA['records'] if r['family']==family and r['parameter_analysis']]
    lines={};coords={}
    for r in rows:
        ex=r['verified']['exact'];a,b,x=F(ex['G']),F(ex['p']),F(ex['rho']);key=(a,b)
        if key not in lines:lines[key]=dict(id='line'+str(len(lines)+1),a=a,b=b,owners=[])
        lines[key]['owners'].append(r['record_id'])
        # The exact rho uses the actual binary64 scalar times exact loaded weight sum.
        # Same rho combines only exact-equal coordinates, never display equality.
        lv=F.from_float(r['global_L'])-F(1,10_000_000)
        if x not in coords or lv>coords[x]['L']:coords[x]=dict(x=x,L=lv,source=r['record_id'])
    ll=list(lines.values());cc=sorted(coords.values(),key=lambda q:q['x']);ch=[]
    for i,j in itertools.combinations(cc,2):
        b=(j['L']-i['L'])/(j['x']-i['x']);a=i['L']-b*i['x']
        ch.append(dict(id='chord'+str(len(ch)+1),a=a,b=b,low=i['x'],high=j['x'],owners=[i['source'],j['source']]))
    low,high=cc[0]['x'],cc[-1]['x'];points={low,high,*[q['x'] for q in cc]}
    for a,b in itertools.combinations(ll,2):
        x=cross(a,b)
        if x is not None and low<=x<=high:points.add(x)
    for a,b in itertools.combinations(ch,2):
        x=cross(a,b)
        if x is not None and max(a['low'],b['low'])<=x<=min(a['high'],b['high']):points.add(x)
    vals=[]
    for x in sorted(points):
        u=min(line(x,m) for m in ll);lb=max(line(x,m) for m in ch if m['low']<=x<=m['high'])
        assert u>=lb,('unsafe crossing',family,x,u,lb)
        vals.append(dict(rho=x,U=u,L=lb,gap=u-lb,upper_ids=[m['id'] for m in ll if line(x,m)==u],lower_ids=[m['id'] for m in ch if m['low']<=x<=m['high'] and line(x,m)==lb]))
    support=[]
    pp=sorted(points)
    for l,h in zip(pp,pp[1:]):
        x=(l+h)/2;u=min(line(x,m) for m in ll)
        support.append(dict(low=l,high=h,ids=[m['id'] for m in ll if line(x,m)==u]))
    worst=max(vals,key=lambda q:q['gap'])
    dominated=[m['id'] for m in ll if any(n['a']<=m['a'] and n['b']<=m['b'] and (n['a']<m['a'] or n['b']<m['b']) for n in ll)]
    supported=sorted({mid for s in support for mid in s['ids']})
    fixed=[]
    for m in ll:
        w=max((dict(rho=q['rho'],gap=line(q['rho'],m)-q['L']) for q in vals),key=lambda q:q['gap'])
        fixed.append(dict(id=m['id'],max_regret_upper=w))
    out.append(dict(family=family,records=len(rows),unique_objective_lines=len(ll),range=[low,high],coordinates=cc,lines=ll,chords=ch,critical_points=vals,support_intervals=support,supported=supported,dominated=dominated,worst_envelope_gap=worst,best_fixed_plan=min(fixed,key=lambda q:q['max_regret_upper']['gap']),all_fixed=fixed,numeric_policy='exact rational G and p from physical inventories and actual binary64 weights; original qualified L reduced by 1e-7; all active line/chord intersections, no grid'))
(BASE/'data_envelope_check.json').write_text(json.dumps(serial(out),indent=2)+'\n')
for r in out:
 print(r['family'],'records',r['records'],'lines',r['unique_objective_lines'],'supported',r['supported'],'dominated',r['dominated'],'range',list(map(float,r['range'])),'max_gap',float(r['worst_envelope_gap']['gap']),'at',float(r['worst_envelope_gap']['rho']),'best_fixed',r['best_fixed_plan']['id'],float(r['best_fixed_plan']['max_regret_upper']['gap']))

