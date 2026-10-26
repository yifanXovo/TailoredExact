"""Reuse qualified independent audits, explicitly binding every shared module.

No optimizer calls. All outputs stay in the new Round69 evidence directory.
"""
import package_round68 as shared
import round69_research as run
import gzip

def bind():
    shared.run=run
    shared.analyze_round68.run=run
    shared.round68_start_audit.run=run
    shared.round68_start_audit.audit=shared.analyze_round68
    shared.round67_witness_model_audit.run=run
    shared.round67_witness_model_audit.audit.run=run
    shared.analyze_round68.physical_module.ROOT=run.ROOT
    run.runner.ROOT=run.ROOT
    run.runner.OUT=run.OUT
    run.runner.RAW=run.RAW
    run.runner.BUILD=run.BUILD
    run.runner.LEDGER=run.OUT/'processes.jsonl'

def main():
    bind()
    shared.main()
    manifest=run.read(run.OUT/'evidence_manifest.json')
    added=0
    for entry in run.runner.entries():
        source=run.ROOT/entry['destination']
        original=source/'hga.csv'
        if not entry['charged'] or not (source/'completion.json').exists() or not original.exists():continue
        destination=run.OUT/'evidence'/str(entry['charged_number'])/'hga.csv.gz'
        destination.write_bytes(gzip.compress(original.read_bytes(),mtime=0))
        assert gzip.decompress(destination.read_bytes())==original.read_bytes()
        manifest.append(dict(number=entry['charged_number'],artifact=str(destination.relative_to(run.OUT)),
            source=str(original.relative_to(run.ROOT)),source_sha256=run.sha(original),sha256=run.sha(destination),
            bytes=destination.stat().st_size,scope='Lossless generation-completion times for HGA publication provenance'))
        added+=1
    run.write(run.OUT/'evidence_manifest.json',manifest)
    import round69_hga_provenance
    round69_hga_provenance.main()
    path=run.OUT/'analysis_identity.json'
    identity=run.read(path)
    identity['round69_binding_wrapper']=run.sha(__file__)
    identity['inherited_round68_reproduction']=identity.pop('reproduction')
    identity['reproduction']=run.sha(run.ROOT/'scripts/round69_reproduce.py')
    identity['reproduction_scope']='Round69 helper makes fresh bounded outputs from identical qualified bytes; inherited tests are not claimed as new batches'
    identity['hga_provenance']=run.sha(run.ROOT/'scripts/round69_hga_provenance.py')
    identity['checkpoints']=run.sha(run.ROOT/'scripts/round69_checkpoints.py')
    identity['startup_attribution']=run.sha(run.ROOT/'scripts/round69_startup_telemetry.py')
    identity['light_endpoint_checks']=run.sha(run.ROOT/'scripts/round69_endpoint.py')
    identity['read_only_host_topology']=run.sha(run.ROOT/'scripts/round69_topology.py')
    identity['stage_report']=run.sha(run.ROOT/'scripts/round69_report.py')
    run.write(path,identity)
    print('Round69 total compact artifacts',len(manifest),'including',added,'HGA generation traces')

if __name__=='__main__':main()
