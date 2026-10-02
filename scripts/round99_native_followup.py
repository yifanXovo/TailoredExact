"""Finite 12 standalone presolve exports with the production numerical parameters.

Zero Optimize. Preserve initial default-gap exports; do not replace their bytes.
"""
import sys,time,ctypes,json
from round99_gurobi_runtime import gp,binding
from round99_common import *
from round99_factor_diagnostic import MODES,size,signature
from round70_affinity import inherited_core
import round99_idle as admission
def run(label):
    admission.ensure_idle();dest=OUT/'diagnostics'/label;dest.mkdir(parents=True,exist_ok=False)
    tick=time.monotonic();records=[]
    with inherited_core() as affinity,gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();assert gp.gurobi.version()==(13,0,2)
        dll=binding()
        for role in read(OUT/'development_inputs.json')['roles']:
            for mode in MODES:
                source=OUT/'exports'/role['id']/(mode+'.lp')
                assert sha(source)==read(source.with_suffix('.json'))['sha256']
                with gp.read(str(source),env=env) as m:
                    for name,value in dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6).items():setattr(m.Params,name,value)
                    pm=m.presolve();output=dest/(role['id']+'_'+mode+'.lp');pm.write(str(output))
                    families={}
                    for v in pm.getVars():
                        key=v.VarName.split('_')[0]+':'+v.VType;families[key]=families.get(key,0)+1
                    records.append(dict(role=role['id'],mode=mode,model_sha256=sha(source),presolved_sha256=sha(output),
                        original=size(m),standalone=size(pm),families_by_surviving_name=families,
                        numeric_signature=signature(pm),typed_signature=signature(pm,True)))
                    pm.dispose()
    write(dest/'summary.json',dict(passed=True,optimizer_calls=0,actual_presolve_calls=12,records=records,dll=dll,affinity=affinity,
        parameters=dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        outer_seconds=time.monotonic()-tick,source_bindings=bindings(),script_sha256=sha(__file__),
        scope='standalone Model.presolve; internal optimize model and implicit integer markers remain inaccessible'))
    print(json.dumps(dict(passed=True,optimizer_calls=0,actual_presolve_calls=12,dll=dll,records=[dict(role=r['role'],mode=r['mode'],standalone=r['standalone']) for r in records])))
if __name__=='__main__':run(sys.argv[1])
