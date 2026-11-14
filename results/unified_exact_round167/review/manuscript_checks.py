"""Independent source/data readback for the Round167 manuscript review.

Read-only inputs; no model construction, enumeration oracle or solver call.
Writes only this review's result file.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import hashlib, json, re, subprocess, time

ROOT=Path(__file__).resolve().parents[3]
REVIEW=Path(__file__).resolve().parent
PAPER=ROOT/'results/unified_exact_round137'
BASE='d497052216d5ae55b6ae0139ea30910cee2e5865'
begin=time.perf_counter()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def source(p): return Path(p).read_text(encoding='utf-8-sig')
body=source(PAPER/'paper_body.md')
app=source(PAPER/'model_and_algorithm_appendices.md')
supp=source(PAPER/'supplement.md')
bib=source(PAPER/'references.bib')
companion=source(PAPER/'mathematical_analysis.md')
def table(text,n):
    a=re.search(r'^\*\*Table '+str(n)+r'\.',text,re.M)
    assert a,('missing table',n)
    rest=text[a.start():]
    p=rest.index('\n|')+1
    rows=[]
    for line in rest[p:].splitlines():
        if not line.startswith('|'): break
        rows.append([x.strip() for x in line.strip('|').split('|')])
    return rows[2:]
def rounded(display,actual):
    d=Decimal(display)
    unit=Decimal(1).scaleb(d.as_tuple().exponent)
    assert abs(d-Decimal(str(actual)))<=unit/2+Decimal('1e-13'),(display,actual)
    return True
assert re.findall(r'^## (\d+)\.',body,re.M)==list('123456')
assert re.findall(r'^\*\*Table (\d+)\.',body,re.M)==[str(i) for i in range(1,11)]
assert all(phrase in body for phrase in ['HGA-TGBC','own startup','OPEN','C35','E+','loaded return','unloading'])
assert 'S_{\\rm AM}' in body and 'Algorithm 1' in body
assert '## A.11 ' in app and 'Proposition A11' in app
assert all(p in supp for p in ['S167.1','S167.2','S167.3','#### S6.','#### S11.'])

pairs=load(ROOT/'results/unified_exact_round166/reports/pairs.json')
byshort={p['id'].removeprefix('R163-'):p for p in pairs}
c166=[]
for row in table(body,6):
    original=byshort[row[0]]
    for r,label in [(1,'B'),(2,'C166')]:
        m=re.fullmatch(r'(CERT|OPEN);\s*([\d.]+)\s*/\s*([\d.]+)',row[r])
        assert m,row
        assert m[1]==original[label+'_state']
        rounded(m[2],original[label+'_U']);rounded(m[3],original[label+'_L'])
    costs=row[3].split('/')
    rounded(costs[0].strip(),original['B_T_produce'])
    rounded(costs[1].strip(),original['C166_T_produce'])
    if original['B_state']=='OPEN':assert original['B_T_cert'] is None
    if original['C166_state']=='OPEN':assert original['C166_T_cert'] is None
    c166.append(dict(input=row[0],states=[original['B_state'],original['C166_state']],display_readback=True))
assert len(c166)==6

resource=load(ROOT/'results/unified_exact_round166/analysis/resource_intervals.json')
bybase={r['base']:r for r in resource}
resource_checks=[]
for row in table(body,8):
    r=bybase[row[0]]
    m=re.fullmatch(r'\[([\d.]+),\s*([\d.]+)\]',row[2]);assert m,row
    lo,hi=Fraction(m[1]),Fraction(m[2])
    assert lo<=Fraction(r['lower_exact']) and hi>=Fraction(r['upper_exact'])
    assert lo>0
    resource_checks.append(dict(base=row[0],outward_lower=m[1],outward_upper=m[2],guarded_original_source=True))
assert len(resource_checks)==4
assert [(r['operations_T1']['returns'],r['operations_T2']['returns']) for r in resource]==[(0,0),(1,0),(2,3),(1,0)]
assert [(r['operations_T1']['pickups'],r['operations_T2']['pickups']) for r in resource]==[(30,43),(16,22),(41,60),(29,42)]
assert all(r['operations_T2']['G']<r['operations_T1']['G'] and r['operations_T2']['p']<r['operations_T1']['p'] for r in resource)

envelopes=load(ROOT/'results/unified_exact_round166/analysis/parameter_envelopes.json')['families']
param_checks=[]
for row,f in zip(table(body,10),envelopes):
    assert f['family'].endswith(row[0]),(f['family'],row[0])
    display=Fraction(row[-1]);exact=Fraction(f['worst_gap']['gap']['exact'])
    assert display>=exact and display-exact<Fraction(1,10**8)
    assert row[2]==str(f['records'])+' / '+str(f['unique_component_lines'])
    assert f['all_fleet_owners_preserved'] and f['no_new_solver'] and f['no_grid']
    param_checks.append(dict(family=f['family'],display=row[-1],original_worst_gap=f['worst_gap']['gap']['value'],upward=True))
assert len(param_checks)==4

positions=load(ROOT/'results/unified_exact_round167/positions.json')
q=load(ROOT/'results/unified_exact_round167/qualification.json')
assert len(positions)==88 and q['actual_Optimize']==88
triples=q['triples'];strict=[t for t in triples if t['level']>0 and t['delta_D167_C166']>1e-7]
assert [(t['frame'],t['level']) for t in strict]==[('R163-X20-S_root',2),('R163-B35-S_root',1),('R163-B35-S_root',2)]
maxdiff=max(abs(t['values']['D167']-t['values']['R_abs']) for t in triples)
assert maxdiff<2.23e-16
for t in triples:
    frame,lev=t['frame'],t['level']
    ds=next(p for p in positions if p['id']==f'{frame}_F{lev}_D167')['prepare']
    rs=next(p for p in positions if p['id']==f'{frame}_F{lev}_R_abs')['prepare']
    assert ds['columns']>rs['columns'] and ds['rows']>rs['rows']
assert 'Native branches' in body and 'offline prototype' in body
assert 'no particular cause is established' in body

old=subprocess.check_output(['git','show',BASE+':results/unified_exact_round137/paper_body.md'],cwd=ROOT).decode('utf-8-sig').replace('\r\n','\n')
assert table(body,4)==table(old,8),'historical Seed0 B/E+/P rows changed'
assert table(body,5)==table(old,9),'historical Seed paired-difference rows changed'
images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',body)
assert set(images)=={'figures/three_seed_endpoints.png','figures/resource_endpoints.png','figures/parameter_quality_bands.png'}
for im in images:
    p=PAPER/im
    oldbytes=subprocess.check_output(['git','show',BASE+':results/unified_exact_round137/'+im],cwd=ROOT)
    assert p.read_bytes()==oldbytes
keys=set(re.findall(r'@\w+\{([^,]+),',bib))
cited=set(re.findall(r'(?<![A-Za-z0-9])@([A-Za-z][\w.-]*)','\n'.join([body,app,supp,companion])))
assert cited<=keys,cited-keys
assert not re.search(r'^\s*note=.*(?:read|checked|rechecked|inspected|internal|Round\d)',bib,re.I|re.M)
checks=dict(UTC=datetime.now(timezone.utc).isoformat(),reviewer='/root/manuscript_review',PASS=True,Optimize=0,
    elapsed_seconds=time.perf_counter()-begin,scope='independent read-only manuscript/source/data check; no historical recomputation or new optimization',
    whitespace_words_before=len(old.split()),whitespace_words_after=len(body.split()),
    source_SHA256={name:sha(PAPER/name) for name in ['paper_body.md','model_and_algorithm_appendices.md','mathematical_analysis.md','supplement.md','references.bib']},
    main_sections=6,main_tables=10,retained_historical_seed_tables_exact=True,
    C166_six_rows=c166,resource_intervals=resource_checks,continuous_parameters=param_checks,
    D167_strict_conditions=[dict(frame=t['frame'],level=t['level'],delta=t['delta_D167_C166']) for t in strict],
    D167_R_abs_max_difference=maxdiff,existing_figures_byte_unchanged=images,undefined_citations=[],
    PDF_review='pending new Round167 PDF build; existing PDF not treated as current')
(REVIEW/'manuscript_checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:checks[k] for k in ['PASS','Optimize','elapsed_seconds','whitespace_words_before','whitespace_words_after','D167_R_abs_max_difference']}))
