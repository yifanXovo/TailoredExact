"""Two finite RX20 LP precision confirmations; primary algorithms stay unchanged."""
from round140_common import *
import inspect
import round140_lp as primary

def prepare():
    assert not budget()['unclosed'] and not (OUT/'LP_precision_plan.json').exists()
    scope=read(OUT/'roots/R-X20-S-T1/scope.json')
    write(OUT/'LP_precision_plan.json',dict(UTC=utc(),positions=[
        dict(position=i,role='R-X20-S-T1',variant=v,seed=0,cap_seconds=120)
        for i,v in enumerate(['tc_stock','tc2_stock'],1)],
        reason='Primary RX20 numerical increment is only 6.4e-6 and its dual violation is about 1.36e-7 at default tolerance; confirm this small effect without changing complete-method parameters',
        FeasibilityTol=1e-9,OptimalityTol=1e-9,Seed=0,Threads=1,serial=True,
        scope_SHA=sha(OUT/'roots/R-X20-S-T1/scope.json'),stock_LP_SHA=sha(scope['stock_model']),
        inherited_solver_source_SHA=sha(primary.__file__),probe_source_SHA=sha(__file__),before_new_Optimize=True))

def solve(position):
    plan=read(OUT/'LP_precision_plan.json')
    assert plan['inherited_solver_source_SHA']==sha(primary.__file__) and plan['probe_source_SHA']==sha(__file__)
    source=inspect.getsource(primary.solve)
    changes=[("OUT/'LP_plan.json'","OUT/'LP_precision_plan.json'",2),
        ("OUT/'LP'/","OUT/'LP_precision'/",1),
        ('m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6','m.Params.FeasibilityTol=1e-9;m.Params.OptimalityTol=1e-9',1),
        ('Seed=m.Params.Seed,Threads=m.Params.Threads','Seed=m.Params.Seed,Threads=m.Params.Threads,FeasibilityTol=m.Params.FeasibilityTol,OptimalityTol=m.Params.OptimalityTol,precision_probe_source_SHA=sha(ROOT/\'scripts/round140_lp_precision.py\')',1)]
    for before,after,count in changes:
        assert source.count(before)==count,(before,source.count(before));source=source.replace(before,after)
    namespace=dict(vars(primary));exec(compile(source,__file__+'::registered_precision_only','exec'),namespace)
    namespace['solve'](position)

def run():
    assert not budget()['unclosed']
    for a in read(OUT/'LP_precision_plan.json')['positions']:
        label=f'LP_precision_{a["position"]:02}'
        assert metered(label,'diagnostic',[primary.LP_PYTHON,ROOT/'scripts/round140_lp_precision.py','solve',a['position']],reservation=150,timeout=180)==0
    results=[read(p) for p in sorted((OUT/'LP_precision').glob('*/result.json'))]
    assert len(results)==2 and all(a['status']=='NUMERICAL_OPTIMAL_CONTINUOUS_LP' for a in results)
    write(OUT/'reports/LP_precision.json',dict(UTC=utc(),results=results,
        delta=results[1]['L']-results[0]['L'],new_LP_Optimize=2,MIP_Optimize=0,
        complete_algorithm_tolerances_unchanged=True,not_replacement_of_primary_results=True))

if __name__=='__main__':
    if sys.argv[1]=='solve':solve(int(sys.argv[2]))
    else:globals()[sys.argv[1]]()
