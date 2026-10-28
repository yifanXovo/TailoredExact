"""Narrow extension of the accepted pure R135 reader for declared -A/B only."""
from round137_common import *
import types
import round135_read as inherited
import round111_seed_audit as original_models

class ArmModels(original_models.ArmModels):
    def model_contract(self,root,p,path,arm):
        if not p.get('round137_delete_ab'):
            return super().model_contract(root,p,path,arm)
        assert arm=='M-B'
        digest,(m,counter,quantities,by_suffix,states,modes)=self.data(path)
        t=m['types'];names=m['order'];data=inherited.core.evidence.instance(root,p)
        assert len(quantities)==2*p['V']*p['M'] and all(t[n]=='C' for n in quantities)
        assert all(t[n] in ('I','B') for n in names if n.startswith(('x_','load_','Y_')))
        assert all(t[n]=='B' for n in names if n.startswith(('mode_','z_','state_')) and not n.startswith('state_g_'))
        assert len(modes)==p['V']*p['M']
        for i in range(1,p['V']+1):
            terms={n:1. for n in by_suffix[str(i)]};assert states[str(i)]
            for n in states[str(i)]:
                amount=abs(data['b'][i]-int(n.rsplit('_',1)[1]))
                if amount:terms[n]=-float(amount)
            assert counter[(tuple(sorted(terms.items())),'=',0.)]==0,('undeleted A',path,i)
            terms={f'z_{k}_{i}':1. for k in range(p['M'])};selector=f'state_{i}_{data["b"][i]}'
            if selector in t:terms[selector]=1.
            assert counter[(tuple(sorted(terms.items())),'=',1.)]==0,('undeleted B',path,i)
        return dict(path=path.relative_to(root).as_posix(),SHA=digest,rows=len(m['rows']),columns=len(names),
            quantity_columns=len(quantities),quantity_type='C',direction_columns=len(modes),
            frozen_A_B_rows_checked=0,deleted_A_B_rows_checked=2*p['V'],
            route_load_Y_integer=True,state_assignment_direction_binary=True),m

def verify(launch,identity):
    # Fresh function namespace per arm. Original code/modules remain untouched;
    # all physical, H, Start, lifecycle, domain and proof predicates are reused.
    api=types.SimpleNamespace(**dict(vars(original_models),ArmModels=ArmModels))
    def ap_contract(model,data,enabled):
        if launch['arm'] in ('P-GRB','P-S'):
            # R135 added a state-formulation AP audit to the R134 reader.
            # Compact P/PS have no state selectors; retain their original
            # canonical, type, physical, lifecycle and Start contracts.
            assert not enabled and not any(n.startswith('state_') for n in model['order'])
            return dict(enabled=False,AP_rows=0,state_coefficients_checked=0,
                not_applicable_original_compact=True,original_R134_contracts_retained=True)
        return inherited.ap_audit.contract(model,data,enabled)
    ns=dict(vars(inherited),ROOT=ROOT,OUT=OUT,DLL=DLL,models=api,
            ap_audit=types.SimpleNamespace(contract=ap_contract))
    run=types.FunctionType(inherited.verify.__code__,ns)
    expected=launch.get('AM_threshold',.08)
    if launch['arm']=='M-B':
        actual=read(Path(launch['destination'])/'round137_parameters.json')
        assert actual==dict(split_threshold=expected,delete_ab=launch['method']=='NO_AB',
            delete_cr=launch['method']=='NO_CR',delete_cg=launch['method']=='NO_CG',loaded_after_presets=True)
        write(Path(launch['destination'])/'round137_control_audit.json',dict(PASS=True,
            parameter_readback_SHA=sha(Path(launch['destination'])/'round137_parameters.json'),
            actual=actual,checked_before_qualification_closeout=True,Optimize=0))
    return run(launch,identity)
