"""Read-only actual main06 fault facts; no recovery or solver is executed."""
from round109_common import ROOT,OUT,read,write,sha,budget
from pathlib import Path
import math,sys
import round108_reader as core
import round109_numerical_recovery as old

def run(destination):
    identity=read(OUT/'campaign/identity.json');entries=identity['launches'][15:18]
    assert [(v['number'],v['arm']) for v in entries]==[(16,'ENS-C'),(17,'P-GRB'),(18,'M-B')]
    facts=[]
    for launch in entries[:2]:
        d=core.portable(ROOT,launch['destination']);r=read(d/'result.json');c=read(d/'completion.json');p=launch['panel']
        assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
        phys=core.full_fleet(ROOT,p,r);q=core.evidence.instance(ROOT,p)
        assert phys['F']==phys['G']==phys['P']==0. and phys['Y'][1:]==q['D'][1:]
        facts.append(dict(number=launch['number'],arm=launch['arm'],physical=phys,result_objective=r['objective'],raw_strict_certificate=r['strict_certified_original_problem']))
    launch=entries[1];d=core.portable(ROOT,launch['destination']);r=read(d/'result.json');c=read(d/'completion.json');p=launch['panel']
    observations=read(d/'observations.json');calls=[v['payload'] for v in observations if v['payload']['kind']=='call']
    bounds=[v['payload'] for v in observations if v['payload']['kind']=='bound'];fail=[v['payload'] for v in observations if v['payload']['kind']=='failure']
    assert len(calls)==1 and [(v['sequence'],v['native_bound']) for v in bounds]==[(3,0.),(37,1.816725899087706e-6)]
    assert fail==[dict(schema=1,sequence=142,kind='failure',reason='full_bound_witness_inconsistency')]
    assert not any(v['payload']['kind']=='returned' for v in observations)
    assert r['gurobi_optimize_count']==1 and r['gurobi_optimize_return_code']==0 and r['gurobi_status']==2 and r['gurobi_solver_finalization_reached'] is True
    assert r['native_mip_best_bound']==r['native_mip_objective']==0.
    model_info,model=core.model_contract(ROOT,p,d/'compact.lp','P-GRB');q=core.evidence.instance(ROOT,p)
    floor=old.floor(p['lambda'],q['w'][1:],q['D'][1:],model['objective'],model['bounds'])
    old.scope(calls[0],c,read(d/'launch.json')['command'],launch['command'],sha(d/'compact.lp'))
    assert sha(d/'compact.lp')==p['reference']['canonical_sha256']
    fee=read(OUT/'fees/main06/receipt.json');ens=read(core.portable(ROOT,entries[0]['destination'])/'whole_arm_receipt.json')
    lower=c['fully_observed_end_to_end_seconds'];upper=math.ceil((fee['outer_seconds']-ens['complete_seconds'])*1e6)/1e6
    old.interval(lower,upper,launch['cap_seconds']);assert not (d/'whole_arm_receipt.json').exists()
    assert fee['exit_code']==1 and fee['actual_native_children_with_launch']==2 and fee['conservative_process_starts']==4
    assert not core.portable(ROOT,entries[2]['destination']).exists()
    files=[d/n for n in ['result.json','completion.json','audit.json','launch.json','observations.json','native.log','compact.lp']]
    value=dict(diagnostic_only=True,recovery_applied=False,solver_calls=0,own_zero_fleets=facts,
        native_call=calls[0],raw_bounds=bounds,raw_journal_failure=fail,raw_return_journal_missing=True,
        successful_actual_optimize_return_source='gurobi_optimize_return_code0 plus matching OPTIMAL native log and finalized normal process; independent source/lifecycle audit pending',
        own_full_domain_floor=floor,own_floor_does_not_use_ENS_data=True,cold_model=model_info,
        P_complete_seconds=None,P_complete_seconds_interval=[lower,upper],original_missing_whole_receipt_preserved=True,
        original_failed_audit_preserved=True,raw_file_SHA={v.relative_to(ROOT).as_posix():sha(v) for v in files},
        closed_budget=budget(),unstarted_prepaid_child=entries[2],
        proposed_accounting_only_recovery='Prepend sole prepaid child18 to already planned main07 wrapper, then19-21 in original order; no new wrapper or native argv, no refund; not admitted yet')
    write(Path(destination)/'facts.json',value);print('Actual main06 own physical zero/floor, invalid callback, missing journal return and recorded clock interval verified; no recovery applied.')

if __name__=='__main__':run(sys.argv[1])
