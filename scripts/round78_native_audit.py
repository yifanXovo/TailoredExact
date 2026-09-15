"""Independent physical and submitted-vector checks for the two new CLI arms."""
import time
from pathlib import Path
from round78_qualify import ROOT,OUT,read,write,sha
from round68_start_audit import actual_vector_check,mapping
import analyze_round61 as physical

def main():
    started=time.perf_counter();destination=OUT/'native_integration_audit.json'
    assert not destination.exists() and not (OUT/'qualification_active.lock').exists()
    q=read(OUT/'qualification_v1_audit.json');assert q['passed']
    physical.ROOT=ROOT;mapping.run.ROOT=ROOT;mapping.audit.physical_module.ROOT=ROOT
    build=ROOT/'build/round78/v1'
    closure=list(build.glob('round78_balanced_cli_*'));control=list(build.glob('round76_closure_cli_*'))
    assert len(closure)==len(control)==1
    p=dict(instance_path='tests/data/round59_tiny.txt',lambda_=.15)
    p.update({'lambda':.15,'T_seconds':3,'pickup_seconds':0,'drop_seconds':0})
    records=[]
    for arm,root in [('BDS-C',closure[0]),('JDS-C',control[0])]:
        folder=root/arm;result=read(folder/'result.json')
        if arm=='JDS-C':
            assert not (folder/'hga.csv.balanced').exists()
            assert 'Round78 balanced descent' not in '\n'.join(result.get('notes',[]))
        checked=physical.physical(p,result)
        assert checked['original_T_feasible'] and abs(checked['F']-5/24)<1e-10
        assert result['strict_certified_original_problem'] and abs(result['lower_bound']-5/24)<1e-7
        metas=list((folder/'external').rglob('*.round68.start.json'));assert len(metas)==1
        meta=metas[0];data=read(meta)
        models=[path for path in (folder/'external').rglob('*.lp') if sha(path)==data['model_sha256']]
        assert models
        model=models[0];log=Path(str(meta).removesuffix('.round68.start.json'))
        witness=read(folder/'external'/(data['source']+'_witness.json'))
        check=mapping.check_model(p,witness,model)
        assert check['compatible_interval'] and check['compatible_cutoff'] and check['all_bounds_types_rows_valid']
        assert all(data[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid','submitted',
                                     'exact_vector_observed_in_mipsol','integer_vector_observed_in_mipsol'])
        assert data['status']=='accepted_by_native_log' and 'Loaded user MIP start with objective' in log.read_text(encoding='utf-8')
        actual=actual_vector_check(p,witness,model,Path(str(log)+'.round68.start.values.csv'))
        assert actual['actual_rows']==data['checked_rows']==167
        records.append(dict(arm=arm,physical=checked,start_metadata_sha256=sha(meta),model_sha256=sha(model),
            model=str(model.relative_to(ROOT)),independent_actual_vector=actual,native_metadata=data))
    report=dict(passed=True,arms=records,optimizer_calls=0,offline_wall_seconds=time.perf_counter()-started,
        script_sha256=sha(__file__),mapping_sha256=sha(mapping.__file__),
        scope='Actual new native CLI integration on tiny known optimum5/24, not a performance result')
    write(destination,report);print({k:v for k,v in report.items() if k!='arms'})

if __name__=='__main__':main()
