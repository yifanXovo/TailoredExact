"""Seed-aware compatibility adapter around the audited R100/R94/R86 readers.

Every actual setting is checked against the frozen arm before projecting only
the seed metadata to the old validator's Seed0 convention. Original committed
records/result files are never edited. Physical, mathematical, scope and native
return checks run unchanged. The published readback remains the actual seed.
"""
import copy
import round100_campaign as original
import round94_lpg_formal_recovery_v3 as legacy_scope
import round94_lpg_contemporary as legacy_parameters
import round86_native_evidence as native
import round109_seed_scope as computed
from round109_common import ROOT,write

_native_audit=native.audit
_scope_receipt=legacy_scope.scope_receipt
_parameters=legacy_parameters.parameter_readback
_active_seed=0
_active_proof=None
SETTINGS=dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,
    FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)

def expected(seed):
    assert type(seed) is int and seed in [0,1]
    return dict(SETTINGS,Seed=seed)

def checked_projection(records,seed):
    wanted=expected(seed)
    for record in records:
        if record['payload']['kind']=='call':assert record['payload']['settings']==wanted,'actual native per-arm Seed/settings mismatch'
    proof=_active_proof or dict(recovered_calls=[])
    assert seed==0 or _active_proof is not None,'Seed1 requires a strict computed prerequisite proof'
    return computed.projected_records(records,proof,legacy_seed=True)

def native_audit(root,panel,records,binary_hash):
    seed=panel['gurobi_seed'];projected=checked_projection(records,seed)
    result=_native_audit(root,panel,projected,binary_hash)
    result['actual_frozen_seed']=seed
    result['actual_native_settings']=[r['payload']['settings'] for r in records if r['payload']['kind']=='call']
    result['legacy_seed_metadata_projection_only']=not bool(_active_proof['recovered_calls'])
    result['computed_native_scope_prerequisites']=_active_proof
    return result

def scope_receipt(launch,records):
    seed=launch['panel']['gurobi_seed'];result=_scope_receipt(launch,checked_projection(records,seed))
    result['settings']=expected(seed);result['actual_frozen_seed']=seed
    return result

def parameter_readback(result,*,require_call,arm):
    seed=_active_seed
    if require_call:
        for suffix in ['requested','effective']:assert result['gurobi_seed_'+suffix]==seed
        assert result['gurobi_seed_set_return_code']==result['gurobi_seed_get_return_code']==0
    projected=dict(result)
    for suffix in ['requested','effective']:
        if 'gurobi_seed_'+suffix in projected:projected['gurobi_seed_'+suffix]=0
    values=_parameters(projected,require_call=require_call,arm=arm)
    if require_call:
        values['seed']={suffix:result['gurobi_seed_'+suffix] for suffix in ['requested','effective','set_return_code','get_return_code']}
    return values

def adapter(launch,records,completion,identity):
    global _active_seed,_active_proof
    _active_seed=launch['panel']['gurobi_seed']
    _active_proof=computed.qualify(ROOT,launch,records,completion,identity)
    if _active_seed==1:write(computed.portable(ROOT,launch['destination'])/'computed_seed_scope.json',_active_proof)
    native.audit=native_audit;legacy_scope.scope_receipt=scope_receipt;legacy_parameters.parameter_readback=parameter_readback
    try:return original.adapter(launch,records,completion,identity)
    finally:
        native.audit=_native_audit;legacy_scope.scope_receipt=_scope_receipt;legacy_parameters.parameter_readback=_parameters
        _active_proof=None
