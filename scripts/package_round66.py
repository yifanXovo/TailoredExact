"""Pack small, reviewable evidence after serial solver queues have stopped."""
import json,shutil,gzip
from pathlib import Path
import round66_research as run
import analyze_round66

def main():
    analyze_round66.analyze()
    manifest=[]
    for e in run.runner.entries():
        source=run.ROOT/e['destination']
        if not e['charged'] or not (source/'completion.json').exists():continue
        destination=run.OUT/'evidence'/str(e['charged_number'])
        destination.mkdir(parents=True,exist_ok=True)
        files=['launch.json','completion.json','phases.csv','heuristic.csv',
            'external/paper_leaf_ledger.csv','external/paper_optimize_ledger.csv',
            'external/initial_decomposition_ledger.csv','external/parent_child_bound_ledger.csv',
            'external/contraction_ledger.csv','external/adaptive_mass_decision_ledger.csv',
            'external/global_bound_trace.csv','external/native_target_ledger.csv','external/lp_status_ledger.csv']
        for name in files:
            original=source/name
            if not original.exists():continue
            dest=destination/name;dest.parent.mkdir(parents=True,exist_ok=True)
            if name.endswith('global_bound_trace.csv'):
                plain=dest;dest=dest.with_suffix('.csv.gz')
                dest.write_bytes(gzip.compress(original.read_bytes(),mtime=0))
                assert gzip.decompress(dest.read_bytes())==original.read_bytes()
                # This removes only our earlier generated compact copy, never raw evidence.
                assert plain.is_relative_to(run.OUT/'evidence')
                if plain.exists():plain.unlink()
            else:shutil.copyfile(original,dest)
            manifest.append(dict(number=e['charged_number'],artifact=str(dest.relative_to(run.OUT)),
                source=str(original.relative_to(run.ROOT)),source_sha256=run.sha(original),
                sha256=run.sha(dest),bytes=dest.stat().st_size))
        if not (source/'result.json').exists():continue
        result=run.read(source/'result.json')
        exact=['algorithm_preset','method','status','objective','upper_bound','lower_bound',
            'strict_certified_original_problem','strict_certificate_rejection_reason','certificate_type','certificate_scope',
            'option_audit_consistent','option_audit_mismatches','preset_experimental_features_enabled',
            'final_process_wall_time_seconds','solver_process_cap_seconds','route_time_limit_seconds',
            'pickup_time_seconds','drop_time_seconds','distance_convention']
        prefixes=['gurobi_','hga_','external_gini_tree_','round65_','round66_']
        selected={k:v for k,v in result.items() if k in exact or any(k.startswith(p) for p in prefixes)}
        run.write(destination/'result_summary.json',selected)
        manifest.append(dict(number=e['charged_number'],artifact=str((destination/'result_summary.json').relative_to(run.OUT)),
            source=str((source/'result.json').relative_to(run.ROOT)),source_sha256=run.sha(source/'result.json'),
            sha256=run.sha(destination/'result_summary.json'),scope='selected exact original fields; routes separately audited'))
    shutil.copyfile(run.BUILD/'tests.log',run.OUT/'tests.log')
    run.write(run.OUT/'evidence_manifest.json',manifest)
    freeze=run.read(run.OUT/'build_v1.json')
    for name,value in {**freeze['working_source'],**freeze['headers']}.items():
        assert run.sha(run.ROOT/name)==value,'Measured solver source changed after freeze: '+name
    files=[run.ROOT/'CMakeLists.txt']
    for directory in ['src','include','tests']:
        files.extend(p for p in (run.ROOT/directory).rglob('*') if p.suffix in ['.cpp','.hpp','.h','.c'])
    run.write(run.OUT/'source_snapshot.json',{str(p.relative_to(run.ROOT)):run.sha(p) for p in files})
    run.write(run.OUT/'analysis_identity.json',dict(analysis=run.sha(Path(analyze_round66.__file__)),
        packaging=run.sha(Path(__file__)),historical_small=run.sha(run.ROOT/'scripts/round66_historical_small.py'),
        q_control=run.sha(run.ROOT/'scripts/round66_q_control.py'),reproduction=run.sha(run.ROOT/'scripts/round66_reproduce.py'),
        solver_binary_unchanged=run.sha(run.BUILD/'ExactEBRP.exe')==run.read(run.OUT/'build_v1.json')['binary']))
    print('Packed',len(manifest),'compact evidence artifacts; raw logs/models/binary remain local')
if __name__=='__main__':main()
