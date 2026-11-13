"""Independent, read-only model/data comparison. No solver imports/calls."""
from pathlib import Path
from collections import Counter
import json,re,hashlib

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round166'
Q=OUT/'qualification'
aux=re.compile(r'\b(?:state_(?:g_)?\d+_\d+|r166_[tq]_\d+_\d+|bit_\d+_\d+|prod_\d+_\d+)\b')

def model(path):
    text=path.read_text(encoding='utf-8-sig')
    rows=[s.split(':',1)[1].strip() for s in text.splitlines() if re.match(r'\s*c\d+:',s)]
    clean=Counter(s for s in rows if not aux.search(s))
    # The short old V+s_b=1 row becomes a pure V=1 when b is absent.
    # Such a common row is part of the replaced local block; the new direct
    # V=sum v*t convention retains the t columns in that equivalent relation.
    initial={}
    for s in rows:
        m=re.match(r'^Y_(\d+) .* = (\d+)$',s)
        if m and re.search(r'\bd_\d+_\d+\b',s) and re.search(r'\bp_\d+_\d+\b',s):
            initial[int(m[1])]=int(m[2])
    support={}
    for station,value in re.findall(r'\b(?:state_|r166_t_)(\d+)_(\d+)\b',text):
        support.setdefault(int(station),set()).add(int(value))
    pure_v=[s for s in clean if re.fullmatch(r'(?:z_\d+_\d+\s*(?:\+\s*)?)+=\s*[01](?:\.0*)?',s)]
    for s in pure_v:
        stations=set(map(int,re.findall(r'\bz_\d+_(\d+)\b',s)))
        assert len(stations)==1
        station=next(iter(stations));rhs=float(s.rsplit('=',1)[1])
        assert (rhs==0 and support[station]=={initial[station]}) or (rhs==1 and initial[station] not in support[station]),s
    for s in pure_v: del clean[s]
    sections={};name=None
    for line in text.splitlines():
        if line in ('Bounds','General','Binaries','End'):name=line;sections.setdefault(name,[]);continue
        if name and line.strip() and not aux.search(line):sections[name].append(line.strip())
    return dict(text=text,clean=clean,sections=sections,pure_v=pure_v)

pairs=json.loads((Q/'LP_pairs.json').read_text(encoding='utf-8-sig'))
checks=[]
for p in pairs:
    a=model(Q/'global'/(p['id']+'_B')/'model.lp')
    b=model(Q/'global'/(p['id']+'_C166')/'model.lp')
    ns=len(set(re.findall(r'\bstate_(\d+_\d+)\b',a['text'])))
    ks=len(set(re.findall(r'\br166_t_(\d+_\d+)\b',b['text'])))
    ds=len(set(re.findall(r'\bbit_(\d+_\d+)\b',b['text'])))
    stations=len(set(re.findall(r'\br166_t_(\d+)_\d+\b',b['text'])))
    column_delta=2*ks+2*ds-2*ns
    row_delta=2*ks+7*ds-2*ns+2*stations
    r=dict(id=p['id'],N_sum=ns,K_sum=ks,d_sum=ds,stations=stations,
        common_rows_equal=a['clean']==b['clean'],
        common_sections_equal=a['sections']==b['sections'],
        B_only_rows=list((a['clean']-b['clean']).elements()),
        C166_only_rows=list((b['clean']-a['clean']).elements()),
        B_pure_joint_visit_rows=a['pure_v'],
        C166_pure_joint_visit_rows=b['pure_v'],
        symbolic_column_delta=column_delta,actual_column_delta=p['C166']['columns']-p['B']['columns'],
        symbolic_row_delta=row_delta,actual_row_delta=p['C166']['rows']-p['B']['rows'],
        signed_LP_delta=p['C166']['objective']-p['B']['objective'],
        B_SHA256=hashlib.sha256(a['text'].encode()).hexdigest(),
        C166_SHA256=hashlib.sha256(b['text'].encode()).hexdigest())
    assert r['common_rows_equal'] and r['common_sections_equal'],r
    assert row_delta==r['actual_row_delta'] and column_delta==r['actual_column_delta'],r
    assert abs(r['signed_LP_delta'])<=1e-7 and p['B']['LP_evidence'] and p['C166']['LP_evidence'],r
    checks.append(r)

rows=(Q/'local/local.csv').read_text().splitlines()[1:]
values={}
for line in rows:
    cols=line.split(',');values[tuple(map(int,cols[:3]))]=float(cols[4])
for cfg in range(8):
    for objective in range(2):
        assert abs(values[cfg,0,objective]-values[cfg,1,objective])<=1e-7
        assert abs(values[cfg,0,objective]-values[cfg,2,objective])<=1e-7
        assert values[cfg,3,objective]<=values[cfg,0,objective]+1e-7
assert values[0,0,0]==1 and values[0,3,0]==0
assert values[0,0,1]==-1 and values[0,3,1]==-2
result=dict(PASS=True,Optimize=0,reader='independent math agent',
    scope='Eight actual complete B/C166 matrices; literal common-row/objective/bound/type equality after replacement blocks and equivalent absent-initial visit convention; symbolic row/column counts; local LP relations',
    pairs=checks,local_calls_read=len(rows),max_abs_LP_delta=max(abs(p['signed_LP_delta']) for p in checks))
(OUT/'review/math_admission_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(PASS=True,pairs=len(checks),local_rows=len(rows),max_abs_LP_delta=result['max_abs_LP_delta'])))
