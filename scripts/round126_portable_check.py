"""Finite public reconstruction: six input draws, sealed clocks and six pair arithmetic.

This is not a new native solve or a rational audit of all native matrices.
"""
from pathlib import Path
import ast,csv,hashlib,json,math,sys,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round126'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check():
    started=time.perf_counter();sys.path.insert(0,str(ROOT/'scripts'))
    import round126_data as data
    recipe=read(OUT/'source_recipe.json');manifest=read(OUT/'input_manifest.json')
    for n,h in recipe['generation_dependencies'].items():assert sha(ROOT/n)==h,(n,'generation dependency identity')
    stations=data.source.load_sources();rebuilt=ROOT/'rebuilt_inputs';rebuilt.mkdir(exist_ok=False)
    draws=[]
    for p in data.ROLES:
        data.configure(p['source']);ss=stations[p['source']]
        selection=data.old.build_selection(ss,p['V'],p['geometry'],p['replicate'])
        selection.update(schema='round126-geographic-selection-v1',selection_id=p['selection_id'],generator_version=data.VERSION)
        landscape=data.landscape_math.landscape(selection,p['inventory'],ss)
        data.landscape_math.assert_equivalent(selection,p['inventory'],ss,landscape)
        lines=data.old.instance_text(landscape,p['M'],p['Q_vector'][0]).splitlines()
        lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        target=rebuilt/(p['id']+'.txt');target.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8',newline='\n')
        saved=next(q for q in manifest['roles'] if q['id']==p['id'])
        assert sha(target)==saved['input_sha256']==sha(ROOT/saved['input_path'])
        assert selection['selected_source_station_row_indices']==read(ROOT/saved['selection_path'])['selected_source_station_row_indices']
        parsed=data.old.parse_instance_mirror(target)
        # JSON arrays and the parser's Python coordinate tuples encode the same ordered data.
        assert json.loads(json.dumps(parsed))==read(OUT/'inputs'/(p['id']+'_parsed.json'))
        positive=data.positivity(parsed,p)
        if p['inventory']=='shortage':assert positive['positive_objective_proved'] and positive['positive_floor_decimal']>0
        draws.append(dict(id=p['id'],SHA=sha(target),selection_id=selection['selection_id'],inventory_material=landscape['seed_derivation_material']))
    # Compile only the pure classification function, not the native/reader import graph.
    tree=ast.parse((ROOT/'scripts/read_round126.py').read_text(encoding='utf-8-sig'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='certification_pair')
    namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen_pure_pair','exec'),namespace)
    rebuilt_pairs=[];arms=[];seals=0
    for n in range(1,7):
        c=read(OUT/f'reconstruction/group{n:02d}/current_core.json');i=read(OUT/f'campaign/group{n:02d}/identity.json')
        by={a['arm']:a for a in c['arms']}
        for l in i['launches']:
            d=OUT/f'campaign/group{n:02d}/raw'/Path(l['destination']).name
            seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json')
            assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
            for name,h in seal['required_SHA'].items():assert sha(d/name)==h,(n,l['arm'],name)
            a=by[l['arm']]
            assert abs(a['T_produce']-(producer['t_produce_perf']-producer['t0_perf']))<1e-8
            assert abs(a['T_verify']-(total['t_verified_perf']-producer['t_produce_perf']))<1e-8
            assert abs(a['T_total']-a['T_produce']-a['T_verify'])<1e-8
            assert a['T_cert']==(a['T_produce'] if a['certificate'] and a['formal_protocol_qualified'] else None)
            # Read the endpoint, not the inherited audit's earlier observational top-level fields.
            endpoint=read(d/'audit.json')['endpoint']
            assert endpoint['certificate']==a['certificate']
            assert abs(endpoint['U']-a['U'])<=1e-7 and abs(endpoint['L']-a['L'])<=1e-7
            assert abs(a['gap']-(a['U']-a['L']))<1e-15
            if a['certificate'] and not a['own_exact_zero']:assert -1e-7<=a['gap']<=1e-7
            seals+=1;arms.append(a)
        pair=namespace['certification_pair'](by['M-B'],by['P-GRB'])
        assert pair==c['pair'],'pair changed'
        rebuilt_pairs.append(pair)
    with (OUT/'certification_pairs.csv').open(newline='',encoding='utf-8-sig') as f:published=list(csv.DictReader(f))
    assert len(published)==6 and len(arms)==12 and len(draws)==6
    for p,row in zip(rebuilt_pairs,published):
        assert p['classification']==row['classification'] and p['id']==row['id']
        for key in ['MB_T_cert','P_T_cert','speedup','observed_P_minus_MB_seconds']:
            assert (None if row[key]=='' else float(row[key]))==p[key],(p['id'],key)
    s=read(OUT/'certification_summary.json')
    assert s['categories']=={key:sum(p['classification']==key for p in rebuilt_pairs) for key in s['categories']}
    return dict(status='PASS',input_draws=draws,pairs=rebuilt_pairs,producer_seals_verified=seals,
        scope='Input-generation identity and pure paired arithmetic, all sealed clocks/endpoints; no full native matrix re-audit or new proof.',
        native_starts=0,Optimize=0,production_compilations=0,seconds=time.perf_counter()-started)

if __name__=='__main__':
    result=check();path=ROOT/'portable_check_receipt.json';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['input_draws','pairs']}))
