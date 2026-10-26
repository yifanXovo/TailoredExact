"""Run after all optimizers stop: compact receipts and hashes of local bulky artifacts."""
import csv,shutil
from pathlib import Path
import round65_research as r

def main():
    if (r.OUT/'active_run.lock').exists():raise RuntimeError('do not package during performance')
    entries=r.runner.entries();index=[]
    active=r.read(r.OUT/r.read(r.OUT/'active_build.json')['file'])
    for name,expected in active['source_files'].items():assert r.sha(r.ROOT/name)==expected,('C++ source changed since active measurement',name)
    # Some measured Windows files have mixed CRLF/LF after patching. Preserve
    # raw build hashes and bind their LF-normalized text for clean Git checkouts.
    import hashlib
    r.write(r.OUT/'source_checkout_binding.json',dict(build=r.read(r.OUT/'active_build.json'),
        normalization='CRLF to LF only; no other byte change',sources={name:dict(
            measured_sha256=expected,lf_sha256=hashlib.sha256((r.ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest())
            for name,expected in active['source_files'].items()}))
    keys=['status','objective','F','upper_bound','lower_bound','strict_certified_original_problem',
          'strict_certificate_class','strict_certificate_rejection_reason','incumbent_generation_time_seconds',
          'primal_heuristic','external_gini_tree_optimize_count','external_gini_tree_lp_optimize_count',
          'external_gini_tree_split_count','external_gini_tree_final_leaf_count','external_gini_tree_open_leaf_count',
          'external_gini_tree_failure_reason','external_gini_tree_internal_budget_scheduling',
          'external_gini_tree_backend_parameter_roundtrip_valid','external_gini_tree_warm_start_enabled',
          'external_gini_tree_warm_start_submitted_count','gurobi_model_fingerprint','gurobi_canonical_model_sha256',
          'gurobi_native_domain_audit_passed','gurobi_lifecycle_valid','gurobi_obj_bound_c','gurobi_hga_start_requested',
          'initial_upper_bound','algorithm_preset','diagnostic_scope','notes',
          'hga_total_generations','hga_decoder_calls']
    for e in entries:
        folder=r.ROOT/e['destination']
        if not (folder/'completion.json').exists():raise RuntimeError('unfinished launch '+str(folder))
        result=r.read(folder/'result.json') if (folder/'result.json').exists() else {}
        label=str(e['charged_number']) if e['charged'] else 'build-'+e['id']
        receipt=dict(launch=e,completion=r.read(folder/'completion.json'),result={k:v for k,v in result.items()
                     if k in keys or k.startswith(('gurobi_','verified_incumbent_'))})
        r.write(r.OUT/'receipts'/(label+'.json'),receipt)
        # These small ledgers preserve domains/statuses without full model copies.
        for name in ['external/paper_leaf_ledger.csv','external/parent_child_bound_ledger.csv',
                     'external/initial_decomposition_ledger.csv','external/paper_tree_events.csv',
                     'external/projection/proof_calls.csv','external/projection/row_use.csv',
                     'external/projection/calls.csv','external/projection/failures.txt','phases.csv',
                     'hga_events.csv','ub_events.csv','heuristic.csv','hga_timing.json']:
            source=folder/name
            if source.exists():
                target=r.OUT/'receipts'/label/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        hga=folder/'hga.csv'
        if hga.exists():
            # Preserve the complete logical trajectory, omitting redundant timing columns.
            target=r.OUT/'receipts'/label/'hga.csv';target.parent.mkdir(parents=True,exist_ok=True)
            with hga.open(encoding='utf-8-sig',newline='') as f,target.open('w',encoding='utf-8',newline='') as g:
                writer=csv.DictWriter(g,fieldnames=['generation','best_fitness','strict_improvement'])
                writer.writeheader();writer.writerows({k:x[k] for k in writer.fieldnames} for x in csv.DictReader(f))
        if e.get('arm')=='P-GRB':
            # Native parameter declaration only; full search log remains locally hashed.
            lines=(folder/'native.log').read_text(encoding='utf-8',errors='replace').splitlines(keepends=True)
            stop=next((i for i,line in enumerate(lines) if line.startswith('Coefficient statistics:')),len(lines))
            (r.OUT/'receipts'/label/'native.log').write_text(''.join(lines[:stop]),encoding='utf-8')
        for path in folder.rglob('*'):
            if path.is_file():index.append(dict(path=str(path.relative_to(r.ROOT)),bytes=path.stat().st_size,sha256=r.sha(path)))
    for freeze in sorted(r.OUT.glob('build_freeze_*.json')):
        version=r.read(freeze)['version']
        build=r.BUILD if freeze.name==r.read(r.OUT/'active_build.json')['file'] else r.ROOT/('build/round65-'+version)
        target=r.OUT/'tests'/('tests_'+version+'.log');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(build/'tests.log',target)
        assert r.sha(target)==r.read(freeze)['tests_sha256']
        for name,expected in r.read(freeze)['executables'].items():
            path=build/name;actual=r.sha(path);assert actual==expected
            index.append(dict(path=str(path.relative_to(r.ROOT)),bytes=path.stat().st_size,sha256=actual))
    for timing in [r.OUT/'hga_timing_build.json',r.OUT/'hga_decoder_timing_build.json']:
        if not timing.exists():continue
        binding=r.read(timing)
        assert binding['solver_build']==r.read(r.OUT/'active_build.json')
        assert r.sha(r.ROOT/binding['source'])==binding['source_sha256']
        for name in ['executable','core_archive']:
            path=r.ROOT/binding[name];actual=r.sha(path);assert actual==binding[name+'_sha256']
            index.append(dict(path=str(path.relative_to(r.ROOT)),bytes=path.stat().st_size,sha256=actual))
        directory=(r.ROOT/binding['executable']).parent
        shutil.copyfile(directory/'build.log',r.OUT/'tests'/(timing.stem+'.log'))
        instrumentation=binding.get('instrumentation',{})
        if instrumentation:
            for name in ['source','runner_source']:
                key='original_sha256' if name=='source' else name+'_sha256'
                assert r.sha(r.ROOT/instrumentation[name])==instrumentation[key]
            for name in ['transformed_header','runner_object']:
                path=r.ROOT/instrumentation[name];actual=r.sha(path)
                assert actual==instrumentation[name+'_sha256']
                index.append(dict(path=str(path.relative_to(r.ROOT)),bytes=path.stat().st_size,sha256=actual))
            shutil.copyfile(directory/'adapter_build.log',r.OUT/'tests/hga_decoder_adapter_build.log')
    with (r.OUT/'local_artifact_index.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader();writer.writerows(index)
    with (r.OUT/'runs.csv').open(encoding='utf-8',newline='') as f: verified_runs=list(csv.DictReader(f))
    r.write(r.OUT/'audit_receipt.json',dict(charged_launches=sum(e['charged'] for e in entries),
            build_only_launches=sum(not e['charged'] for e in entries),native_micros=sum(e['kind']=='native-micro' for e in entries),
            hga_timing_diagnostics=sum(e['kind']=='hga-timing-diagnostic' for e in entries),
            optimizer_calls_total_known=sum(int(e.get('optimizer_calls') or 0) for e in verified_runs),
            runs_missing_optimizer_counts=[e['number'] for e in verified_runs if not e.get('optimizer_calls')],
            maximum_launches=72,maximum_micros=4,ledger_sha256=r.sha(r.OUT/'processes.jsonl'),
            local_artifact_index_sha256=r.sha(r.OUT/'local_artifact_index.csv'),optimizer_running=False,
            source_checkout_binding_sha256=r.sha(r.OUT/'source_checkout_binding.json'),
            final_cpp_source_matches_active_build=True,
            source_check_scope='measured solver src/include/tests; standalone timing harness has a separate binding'))
    print('packaged',len(entries),'receipts;',len(index),'local hashes')
if __name__=='__main__':main()
