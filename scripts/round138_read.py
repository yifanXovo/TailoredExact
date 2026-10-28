"""Retain the accepted R137 physical/proof reader; audit only the new rows."""
from round138_common import *
from round138_setup import stock_rows
import collections, types
import round137_read as accepted

class ArmModels(accepted.ArmModels):
    def model_contract(self,root,p,path,arm):
        fact,model=super().model_contract(root,p,path,arm)
        data=accepted.inherited.core.evidence.instance(root,p)
        alpha,beta=model['bounds']['G'];B=sum(data['b'][1:]);Bminus=max(0,B-sum(p['Q_vector']))
        expected=collections.Counter(stock_rows(p['V'],alpha,beta,Bminus,B))
        counts=collections.Counter(model['rows'])
        if p.get('round138_stock_rlt'):
            assert not expected-counts,('missing or stale stock RLT',path,alpha,beta)
        else:assert not expected&counts,('unexpected stock RLT in baseline',path)
        fact['stock_RLT']=dict(enabled=p.get('round138_stock_rlt',False),rows=4 if p.get('round138_stock_rlt') else 0,
            actual_alpha=alpha,actual_beta=beta,B=B,Bminus=Bminus,actual_canonical_rows_checked=True)
        return fact,model

def verify(launch,identity):
    ns=dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=ArmModels)
    run=types.FunctionType(accepted.verify.__code__,ns)
    d=Path(launch['destination']);enabled=launch['panel'].get('round138_stock_rlt',False)
    if enabled:
        actual=read(d/'round138_parameters.json')
        assert actual==dict(stock_rlt=True,gurobi_seed=launch['seed'],H_seed=20260626,loaded_after_presets=True)
    else:assert not (d/'round138_parameters.json').exists()
    value=run(launch,identity)
    write(d/'round138_control_audit.json',dict(PASS=True,stock_rlt=enabled,Seed=launch['seed'],H_seed=20260626,
        inherited_R137_physical_H_Start_lifecycle_and_certificate_checks=True,
        all_used_models_stock_rows_checked=True,Optimize=0))
    return value
