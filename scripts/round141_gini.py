"""Rebuild actual Gini midpoint controls with the verified existing writer PE."""
from round141_common import *
from round141_math import ROLES
from round140_qualify import expected_counts
import collections
import round108_reader as core

def exports():
    build=read(ROOT/'results/unified_exact_round140/candidate_build.json')
    exporter=Path(build['exporter_PE'])
    assert sha(exporter)==build['exporter_SHA'] and sha(DLL)==DLL_SHA
    for path,digest in build['source_hashes'].items():assert sha(ROOT/path)==digest,path
    write(OUT/'gini_export_identity.json',dict(UTC=utc(),PE=str(exporter),PE_SHA=sha(exporter),
        measured_source='81ab886e23220be97a858e66961056cef727d074',source_hashes_checked=len(build['source_hashes']),
        DLL_SHA=DLL_SHA,new_compiles=0,Optimize=0))
    for role in ROLES:
        scope=read(OUT/'domains'/role/'scope.json');p=scope['panel']
        a,b=scope['alpha'],scope['beta'];mid=a+(b-a)/2
        for label,lo,hi in [('parent',a,b),('low',a,mid),('high',mid,b)]:
            target=OUT/'domains'/role/'gini'/label
            cmd=[exporter,ROOT/p['input_path'],p['T_seconds'],lo,hi,scope['validated_U'],'ms2',target,p['lambda'],'tc2_stock']
            assert metered(f'gini_export_{role}_{label}','diagnostic',cmd,30,45)==0

def verify_and_plan():
    records=[];positions=[]
    for role in ROLES:
        scope=read(OUT/'domains'/role/'scope.json');p=scope['panel']
        source=core.lp_model(Path(scope['stock_model']))
        expected=collections.Counter(source['rows'])+collections.Counter(expected_counts(source,scope['Bminus'],scope['B'],'tc2'))
        parent=core.lp_model(OUT/'domains'/role/'gini/parent/original.lp')
        comparison=dict(role=role,source_stock_SHA=scope['stock_SHA'],
            root_same_rows=expected==collections.Counter(parent['rows']),
            root_same_bounds=source['bounds']==parent['bounds'],
            root_same_types=source['types']==parent['types'],
            root_same_objective=source['objective']==parent['objective'])
        assert all(v for k,v in comparison.items() if k.startswith('root_same')),comparison
        records.append(comparison)
        for side in ['low','high']:
            source_lp=OUT/'domains'/role/'gini'/side/'original.lp'
            child=core.lp_model(source_lp)
            assert source['objective']==child['objective']
            # Child finite supports may shrink; full writer reconstructs every
            # common-factor/stock/count row at the child g interval and cutoff.
            positions.append(dict(label=f'gini_{role}_{side}',role=role,variant='gini_reference',side=side,
                source_lp=str(source_lp),source_lp_SHA=sha(source_lp),
                g_interval=list(child['bounds']['G']),validated_U=scope['validated_U'],
                cap_seconds=90,Seed=0,Threads=1))
    write(OUT/'gini_match.json',dict(UTC=utc(),PASS=True,roles=records,Optimize=0,
        meaning='exported parent is exactly the source-matched stock+TC+TC2 row multiset/bounds/types/objective'))
    write(OUT/'gini_plan.json',dict(positions=positions))

def solve():
    for spec in read(OUT/'gini_plan.json')['positions']:
        assert metered(spec['label'],'diagnostic',[LP_PYTHON,ROOT/'scripts/round141_lp.py','one',json.dumps(spec)],110,120)==0

if __name__=='__main__':globals()[sys.argv[1]]()
