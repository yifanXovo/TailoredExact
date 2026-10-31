"""Reuse stable R137 physical/proof/lifecycle checks; add RN-specific checks."""
import types
import round137_read as accepted
from round143_qualify import actual_spec,check_matrix
from round143_common import *

def verify(launch,identity):
    d=Path(launch['destination']);enabled=launch['RN'];facts=[]
    audits=[read(p) for p in d.rglob('*.round143.native.json')]
    if enabled:
        assert read(d/'round143_parameters.json')==dict(RN=True,Seed=launch['seed'],H_seed=20260626,stock=False,counts='off',AP=False)
        assert audits and all(a['PASS'] and a['Optimize_extra']==0 for a in audits)
    else:assert not audits and not (d/'round143_parameters.json').exists()
    class Models(accepted.ArmModels):
        def model_contract(self,root,p,path,arm):
            fact,m=super().model_contract(root,p,path,arm)
            B=p['total_initial'];bm=max(0,B-sum(p['Q_vector']))
            if enabled:
                s=actual_spec(m,bm,B);wanted=check_matrix(m,s)
                bound=[a for a in audits if a['model_SHA']==fact['SHA']]
                assert bound and all(a['added_rows_checked']==len(wanted) and a['added_columns_checked']==len([k for k in m['order'] if k.startswith('rn_')]) for a in bound)
                facts.append(dict(model_SHA=fact['SHA'],RN_rows=len(wanted),RN_columns=bound[0]['added_columns_checked'],
                    S_L_exact=s['S_L_exact'],S_U_exact=s['S_U_exact'],applicable=s['applicable'],native_receipts=len(bound)))
            else:assert not any(k.startswith('rn_') for k in m['order'])
            return fact,m
    ns=dict(vars(accepted),ROOT=ROOT,OUT=OUT,ArmModels=Models)
    run=types.FunctionType(accepted.verify.__code__,ns)
    # All RN-specific work runs before the inherited complete T_verify stop.
    value=run(launch,identity)
    write(d/'round143_control_audit.json',dict(PASS=True,RN=enabled,models=facts,native_audits=audits,
        inherited_complete_H_Start_physical_scope_quality_lifecycle=True,Optimize=0,Native_load=0))
    return value

if __name__=='__main__':
    matrix=read(OUT/f'{sys.argv[1]}_matrix.json');g=matrix['groups'][int(sys.argv[2])-1]
    identity=read(OUT/g['group']/'identity.json');print(json.dumps(verify(g['launch'],identity)['arm']))
