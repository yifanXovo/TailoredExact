"""One-shot prospective data freeze and read-only R87 witness recovery. No Optimize."""
import argparse
import csv
import hashlib
import json
import math
import statistics
import time
from pathlib import Path

import generate_citibike443_regional_v1 as citi
import round86_native_evidence as evidence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round96'
DATA = ROOT / 'reference/round96_external'
VERSION = 'round96-external-v1'
ROLES = [
    dict(id='H1', V=20, M=2, Q=20, geometry='three_clusters', inventory='surplus', T_seconds=5400, cap_seconds=1800),
    dict(id='H2', V=20, M=3, Q=15, geometry='anisotropic_cloud', inventory='shortage', T_seconds=3600, cap_seconds=1800),
    dict(id='H3', V=30, M=3, Q=25, geometry='radial_spokes', inventory='shortage', T_seconds=7200, cap_seconds=3600),
    dict(id='H4', V=30, M=2, Q=35, geometry='bent_corridor', inventory='balanced', T_seconds=10800, cap_seconds=1800),
    dict(id='H5', V=50, M=4, Q=25, geometry='separated_islands', inventory='shortage', T_seconds=7200, cap_seconds=7200),
    dict(id='H6', V=50, M=5, Q=20, geometry='offset_annulus', inventory='surplus', T_seconds=3600, cap_seconds=3600),
]
ORDERS = [('P-GRB','ENS-C','LP-G'), ('LP-G','ENS-C','P-GRB'), ('ENS-C','P-GRB','LP-G'),
          ('P-GRB','LP-G','ENS-C'), ('ENS-C','LP-G','P-GRB'), ('LP-G','P-GRB','ENS-C')]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')

def recipe():
    return dict(version=VERSION, roles=ROLES, orders=ORDERS,
                source_sha256=sha(__file__), seed='SHA256(round96-external-v1|id|field), first 8 bytes / 2^64',
                policy='Keep all six outcomes; no reseed, replacement, resize or T adjustment. No optimizer-informed selection.',
                lambda_value=.15, pickup_seconds=60, drop_seconds=60,
                maximum_formal_starts=18, maximum_formal_seconds=3*sum(r['cap_seconds'] for r in ROLES),
                structural_design='H3/H5 shortage excludes F=0 analytically; proof difficulty is only a hypothesis.',
                writer_sha256=sha(citi.__file__), optimizer_calls=0)

def unit(r, name):
    return int.from_bytes(hashlib.sha256(f'{VERSION}|{r["id"]}|{name}'.encode()).digest()[:8], 'big') / 2**64
def integer(r, name, a, b): return a + int(unit(r, name)*(b-a+1))

def landscape(r):
    n=r['V']; pts=[]
    for j in range(n):
        u,v=unit(r,f'x{j}'),unit(r,f'y{j}'); angle=2*math.pi*u
        g=r['geometry']
        if g=='three_clusters':
            cx,cy=[(-700,-250),(600,-250),(0,700)][j%3]; x,y=cx+250*(u-.5),cy+250*(v-.5)
        elif g=='anisotropic_cloud': x,y=2400*(u-.5),500*(v-.5)
        elif g=='radial_spokes':
            a=2*math.pi*(j%5)/5+.08*(v-.5); radius=150+1100*u; x,y=radius*math.cos(a),radius*math.sin(a)
        elif g=='bent_corridor':
            t=2200*u; x,y=(t-1100,100*(v-.5)) if t<1100 else (100*(v-.5),t-1100)
        elif g=='separated_islands':
            cx,cy=[(-1050,-550),(950,-550),(-850,650),(1050,800)][j%4]; x,y=cx+400*(u-.5),cy+400*(v-.5)
        else:
            radius=850+550*v; x,y=radius*math.cos(angle)+250,radius*math.sin(angle)-150
        pts.append([round(584400+x,3),round(4511800+y,3)])
    target=[integer(r,f'd{j}',14,28) for j in range(n)]
    capacity=[d+16 for d in target]; initial=target.copy()
    order=sorted(range(n),key=lambda j:(unit(r,f'pair{j}'),j))
    for j in range(0,n,2):
        a,b=order[j:j+2]; transfer=integer(r,f'transfer{j}',4,9); shift=integer(r,f'shift{j}',2,4)
        initial[a]+=transfer+(shift if r['inventory']=='surplus' else 0)
        initial[b]-=transfer+(shift if r['inventory']=='shortage' else 0)
    weights=[round(.25+.75*unit(r,f'w{j}'),6) for j in range(n)]
    return dict(V=n, depot=dict(coordinate_utm18n_meters=[round(statistics.fmean(p[k] for p in pts),3) for k in (0,1)],
        capacity_placeholder=100000,initial_placeholder=50000,target_placeholder=0),
        capacities=capacity, initial=initial,target=target,weights=weights,
        min_ratio=[round(.7*min(b,d)/d,4) for b,d in zip(initial,target)],points_utm18n_meters=pts)

def freeze():
    write(OUT/'generation_recipe.json', recipe())

def generate():
    frozen=read(OUT/'generation_recipe.json')
    assert frozen==json.loads(json.dumps(recipe())), 'recipe/source changed'
    assert not DATA.exists(), 'never regenerate'
    DATA.mkdir(); roles=[]
    for r,order in zip(ROLES,ORDERS):
        obj=landscape(r); path=DATA/(r['id']+'.txt')
        path.write_text(citi.instance_text(obj,r['M'],r['Q']),encoding='utf-8',newline='\n')
        parsed=citi.parse_instance_mirror(path)
        assert all(0<=b<=c and 0<d<=c for b,d,c in zip(obj['initial'],obj['target'],obj['capacities']))
        assert len(set(map(tuple,parsed['points'])))==r['V']+1
        roles.append(dict(r,input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
            input_sha256=sha(path),scenario_id=VERSION+'_'+r['id'],method_order=order,
            pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
            total_initial=sum(obj['initial']),total_target=sum(obj['target']),
            zero_excluded_by_stock_shortage=sum(obj['initial'])<sum(obj['target'])))
    write(OUT/'external_inputs.json',dict(recipe_sha256=sha(OUT/'generation_recipe.json'),roles=roles,optimizer_calls=0))

def recover():
    start=time.perf_counter()
    identity=read(ROOT/'results/unified_exact_round87/campaign/identity.json')
    rows=list(csv.DictReader((ROOT/'results/unified_exact_round87/witness_index.csv').open()))
    endpoints=list(csv.DictReader((ROOT/'results/unified_exact_round87/endpoints.csv').open()))
    cases=[]; refs=[]
    for rid in ('D7','U6','F5'):
        selected=[r for r in rows if r['id']==rid and r['arm']=='ENS-C']
        # Preregistered informative times: best available at 3600s, then best final.
        early=min((r for r in selected if float(r['available_seconds'])<=3600),key=lambda r:float(r['objective']))
        final=min(selected,key=lambda r:float(r['objective']))
        for label,row in [('at3600',early),('final',final)]:
            launch=next(x for x in identity['launches'] if x['number']==int(row['number']))
            src=Path(launch['destination'])/'journal'/f'event_{row["sequence"]}.commit'
            rec=evidence.receipt(src,float(row['available_seconds']),launch['cap'])
            event=rec['payload']; p=launch['panel']; checked=evidence.physical_module.physical(p,event)
            assert checked['original_T_feasible'] and abs(checked['F']-float(row['objective']))<1e-12
            path=OUT/'witnesses'/f'{rid}_{label}.json';write(path,event)
            cases.append(dict(id=f'{rid}_{label}',role=rid,panel=p,witness_path=path.relative_to(ROOT).as_posix(),
                witness_sha256=sha(path),source=str(src),source_commit_sha256=sha(src),
                source_payload_sha256=rec['sha256'],sequence=rec['sequence'],observed_seconds=float(row['available_seconds']),
                source_time=rec['data_close_seconds'],verified=checked,cap_seconds=300))
        bestp=min((r for r in rows if r['id']==rid and r['arm']=='P-GRB'),key=lambda r:float(r['objective']))
        launch=next(x for x in identity['launches'] if x['number']==int(bestp['number']))
        src=Path(launch['destination'])/'journal'/f'event_{bestp["sequence"]}.commit'
        rec=evidence.receipt(src,float(bestp['available_seconds']),launch['cap'])
        check=evidence.physical_module.physical(launch['panel'],rec['payload']);assert check['original_T_feasible']
        path=OUT/'witnesses'/f'{rid}_reference_P.json';write(path,rec['payload'])
        refs.append(dict(role=rid,U_ref=check['F'],ENS_final=float(final['objective']),
                         provable_incumbent_suboptimality_at_least=max(0,float(final['objective'])-check['F']),
                         witness_path=path.relative_to(ROOT).as_posix(),witness_sha256=sha(path),source=str(src),
                         scope='offline comparison only, never formal Start or combined certificate'))
    write(OUT/'fixed_route_cases.json',dict(cases=cases,offline_references=refs,optimizer_calls=0,
        diagnostic_starts=6,maximum_diagnostic_seconds=1800,elapsed_before_write=time.perf_counter()-start))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['freeze','generate','recover'])
    globals()[parser.parse_args().action]()
