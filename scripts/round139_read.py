"""Add only placement checks to the accepted complete physical/proof reader."""
from round139_common import *
import collections,csv,types
import round137_read as accepted
from round138_repair import scaled_rows

def verify(launch,identity):
    d=Path(launch['destination']);placement=launch['placement']
    calls=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='')))
    expected={}
    for call in calls:
        lp=call['solve_kind']=='LP'
        stock=placement=='both' or placement==('lp-only' if lp else 'mip-only')
        key=call['model_sha256']
        if key in expected: assert expected[key]==stock,'same SHA assigned conflicting matrices'
        expected[key]=stock
    class ArmModels(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            fact,model=super().model_contract(root,p,path,arm)
            digest=sha(path);assert digest in expected,(path,digest)
            data=accepted.inherited.core.evidence.instance(root,p)
            alpha,beta=model['bounds']['G'];B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']))
            rows=collections.Counter(scaled_rows(p['V'],alpha,beta,Bm,B))
            count=collections.Counter(model['rows']);enabled=expected[digest]
            if enabled: assert not rows-count,('missing/stale stock rows',path)
            else: assert not rows&count,('unexpected stock rows',path)
            fact['stock_RLT']=dict(enabled=enabled,rows=4 if enabled else 0,
                placement=placement,alpha=alpha,beta=beta,B=B,Bminus=Bm,actual_canonical_rows_checked=True)
            return fact,model
    actual=read(d/'round139_parameters.json')
    assert actual==dict(placement=placement,LP_stock=placement in ['both','lp-only'],
        MIP_stock=placement in ['both','mip-only'],gurobi_seed=launch['seed'],H_seed=20260626,loaded_after_presets=True)
    assert not (d/'round138_parameters.json').exists(),'new switch must not masquerade as legacy identity'
    run=types.FunctionType(accepted.verify.__code__,dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=ArmModels))
    value=run(launch,identity)
    write(d/'round139_control_audit.json',dict(PASS=True,actual=actual,model_stock=expected,
        inherited_R137_physical_H_Start_lifecycle_and_certificate_checks=True,
        all_used_LP_target_terminal_matrices_checked=True,Optimize=0))
    return value
