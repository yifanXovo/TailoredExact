"""Retain the accepted physical/H/Start/proof reader and check actual TC2 rows."""
from round140_common import *
import types,csv
import round137_read as accepted
from round140_qualify import exact_matrix

def verify(launch,identity):
    d=Path(launch['destination']);counts=launch['counts'];stock=launch['stock']
    class ArmModels(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            fact,model=super().model_contract(root,p,path,arm)
            added,_=exact_matrix(path,p,counts,stock,False)
            fact['round140_counts']=added
            return fact,model
    actual=read(d/'round140_parameters.json')
    assert actual==dict(counts=counts,stock=stock,placement='both',gurobi_seed=launch['seed'],H_seed=20260626,loaded_after_presets=True)
    run=types.FunctionType(accepted.verify.__code__,dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=ArmModels))
    value=run(launch,identity)
    write(d/'round140_control_audit.json',dict(PASS=True,actual=actual,Optimize=0,
        all_used_LP_target_terminal_matrices_checked=True,inherited_R137_physical_H_Start_lifecycle_certificate_checks=True))
    return value
