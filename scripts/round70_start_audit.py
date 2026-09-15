"""Round70 Start-decision loop; original actual-vector and route mapper reused."""
import math,re,time
import analyze_round68 as audit
from round68_start_audit import actual_vector_check,mapping
import round70_research as run

def main():
    assert not (run.OUT/'active_run.lock').exists(),'Run audit between optimizer queues'
    started=time.monotonic();records=[];controls=0
    for entry in run.runner.entries():
        folder=run.ROOT/entry['destination']
        if not entry['charged'] or not (folder/'completion.json').exists():continue
        metadata=list(folder.glob('external/**/*.round68.start.json'))
        if entry['arm'] not in ['VD-S','DS']:
            assert not metadata,'Control unexpectedly enabled new Start path';controls+=1;continue
        p=run.panel()[entry['id']]
        calls=[r for r in audit.rows(folder/'external/paper_optimize_ledger.csv') if r['solve_kind']!='LP']
        assert len(metadata)==len(calls),'Every actual VD-S/DS MIP needs an explicit Start decision'
        models={run.sha(path):path for path in folder.glob('external/models/*.lp')}
        for call in calls:
            log=run.ROOT/call['native_log'];meta=log.with_name(log.name+'.round68.start.json')
            data=run.read(meta);assert data['leaf']==call['leaf_id']
            assert data['model_sha256']==call['model_sha256']
            assert data['retained_model']==(call['in_memory_model_reused']=='1')
            assert 0<=data['native_deadline_remaining_at_optimize']<=float(call['global_deadline_remaining_at_launch'])+1e-6
            model=models[data['model_sha256']]
            witness_path=folder/'external'/(data['source']+'_witness.json')
            witness=run.read(witness_path)
            check=mapping.check_model(p,witness,model)
            vector=log.with_name(log.name+'.round68.start.values.csv')
            eligible=check['compatible_interval'] and check.get('compatible_cutoff',False)
            assert data['submitted']==eligible
            native=log.read_text(encoding='utf-8',errors='strict')
            accepted=bool(re.search(r'Loaded user MIP start with objective',native))
            if eligible:
                assert check['all_bounds_types_rows_valid']
                assert all(data[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid'])
                actual=actual_vector_check(p,witness,model,vector)
                assert actual['actual_rows']==data['checked_rows']
                assert abs(data['objective']-audit.physical_module.physical(p,witness)['F'])<=1e-7
                assert not data['status'].startswith('round68_start_')
                assert (data['status']=='accepted_by_native_log')==accepted
            else:
                assert data['status'].startswith('ineligible:') and not vector.exists()
                assert not data['exact_vector_observed_in_mipsol'] and not data['integer_vector_observed_in_mipsol']
                actual={}
            record=dict(number=entry['charged_number'],id=entry['id'],arm=entry['arm'],leaf=call['leaf_id'],
                solve_kind=call['solve_kind'],metadata=str(meta.relative_to(run.ROOT)),metadata_sha256=run.sha(meta),
                model=str(model.relative_to(run.ROOT)),model_sha256=run.sha(model),
                witness=str(witness_path.relative_to(run.ROOT)),witness_sha256=run.sha(witness_path),
                eligible=eligible,native_log_accepted=accepted)
            record.update(data);record.update(actual);records.append(record)
    run.write(run.OUT/'start_checks.json',dict(checks=records,controls_checked=controls,
        actual_mip_decisions=len(records),eligible=sum(r['eligible'] for r in records),
        accepted=sum(r['native_log_accepted'] for r in records),
        exact_vectors_observed=sum(r['exact_vector_observed_in_mipsol'] for r in records),
        integer_vectors_observed=sum(r['integer_vector_observed_in_mipsol'] for r in records),
        offline_wall_seconds=time.monotonic()-started,optimizer_calls=0,
        observer_scope='MIPSOL comparison flags are C++ observer evidence; independent audit checks retained submitted/readback CSV, not unretained full native event vectors',
        script_sha256=run.sha(__file__),shared_mapping_sha256=run.sha(mapping.__file__)))
    print('Start decisions',len(records),'eligible',sum(r['eligible'] for r in records),
        'native accepted',sum(r['native_log_accepted'] for r in records),'control runs',controls)
if __name__=='__main__':main()
