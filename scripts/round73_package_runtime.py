"""Lossless, independently replayed runtime checkpoint; zero new Optimize calls."""
import csv
import gzip
import json
import math
from pathlib import Path
import time
import round73_native_evidence as evidence
from round73_qualify import ROOT, OUT as STAGE, sha, write
OUT=STAGE/'runtime_revision'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    frozen=read(OUT/'identity.json');summary=read(OUT/'summary.json')
    assert summary['completed']==6 and all(r['audit']['passed'] for r in summary['records'])
    assert sha(ROOT/'scripts/round73_runtime_diagnostic.py')==frozen['driver_sha256']
    assert sha(evidence.__file__)==frozen['reader_sha256']
    assert sha(evidence.physical_module.__file__)==frozen['physical_sha256']
    assert sha(ROOT/'build/round73/v6/ExactEBRP.exe')==frozen['binary_sha256']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    manifest=[];checks=[]
    def archive(source,relative):
        target=OUT/'evidence'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        raw=source.read_bytes()
        if target.exists():assert gzip.decompress(target.read_bytes())==raw
        else:target.write_bytes(gzip.compress(raw,mtime=0))
        assert gzip.decompress(target.read_bytes())==raw
        manifest.append(dict(source=str(source.relative_to(ROOT)),artifact=str(target.relative_to(OUT)),
            source_sha256=sha(source),artifact_sha256=sha(target),raw_bytes=len(raw),bytes=target.stat().st_size))
    calls=0;witnesses=0;full_bounds=0;rejection_tests=0
    for launch,done in zip(frozen['launches'],summary['records']):
        folder=ROOT/launch['destination'];p=launch['panel']
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        records=read(folder/'observations.json')
        for record in records:
            path=folder/'journal'/f'event_{record["sequence"]}.commit'
            checked=evidence.receipt(path,record['first_observed_seconds'],launch['cap'])
            assert checked==record
        replay=evidence.audit(ROOT,p,records,frozen['binary_sha256'])
        assert all(replay[k]==done['audit'][k] for k in replay)
        original_calls=[r['payload'] for r in records if r['payload']['kind']=='call']
        for c in original_calls:
            log=Path(c['native_log_path'])
            native_count=log.read_text(encoding='utf-8',errors='replace').count('Optimize a model')
            assert native_count==1,(log,native_count)
            calls+=native_count
            if launch['arm']=='P-GRB':
                ref=frozen['references'][p['id']]
                assert sha(Path(c['model_path']))==ref['canonical_sha256']
        uncommitted=[f.name for f in (folder/'journal').glob('*.json') if not f.with_suffix('.commit').exists()]
        observed={f'event_{r["sequence"]}.commit' for r in records}
        unseen=[f.name for f in (folder/'journal').glob('*.commit') if f.name not in observed]
        # Extra post-kill files are retained but never promoted or backdated.
        if not launch['forced']:assert not uncommitted and not unseen
        bad=folder/'journal/event_1.commit'
        try:evidence.receipt(bad,31,30)
        except AssertionError:rejection_tests+=1
        else:raise AssertionError('postcutoff read accepted')
        full=next((c for c in original_calls if c['full_original']),None)
        if full:
            try:evidence.replay_bound(full,replay['UB']+1,replay['witnesses'])
            except AssertionError:rejection_tests+=1
            else:raise AssertionError('contradictory full native bound accepted')
        for c in original_calls:
            if c['native_preconditions'] and not c['full_original']:
                # A prospective child or foreign leaf cannot strengthen the
                # complete frozen cover merely because its bound is large.
                malformed=dict(c,leaf='not_in_this_live_frontier')
                try:evidence.replay_bound(malformed,.01,replay['witnesses'])
                except AssertionError:rejection_tests+=1
                else:raise AssertionError('foreign active leaf accepted')
        checks.append(dict(number=launch['number'],id=p['id'],arm=launch['arm'],
            forced=launch['forced'],UB=replay['UB'],LB=replay['LB'],gap=replay['gap'],
            uncommitted_data=uncommitted,unseen_receipts=unseen,
            physical_witnesses=replay['physical_witnesses'],native_calls=len(original_calls),
            global_native_bound_events=replay['global_native_bound_events'],
            normal_certificate=done['audit'].get('normal_result_certificate',False),
            recovered_certificate=False,wall_seconds=done['wall_seconds']))
        witnesses+=replay['physical_witnesses'];full_bounds+=replay['global_native_bound_events']
        for source in sorted(folder.rglob('*')):
            if source.is_file():archive(source,Path('diagnoses')/str(launch['number'])/(str(source.relative_to(folder))+'.gz'))
    for source in sorted((OUT/'reference').rglob('*')):
        if source.is_file():archive(source,Path('reference')/(str(source.relative_to(OUT/'reference'))+'.gz'))
    qual=[]
    for version in ['v5','v6']:
        build=ROOT/'build/round73'/version;q=read(STAGE/f'qualification_{version}.json')
        text=(build/'tests.log').read_text(encoding='utf-8')
        assert ('100% tests passed, 0 tests failed out of 54' in text)==(version=='v6')
        native=0
        for fixture in list(build.glob('round*_cli_*'))+list(build.glob('round68*')):
            if not fixture.is_dir():continue
            ledger=fixture/'external/paper_optimize_ledger.csv'
            if ledger.exists():
                native+=len(list(csv.DictReader(ledger.open(encoding='utf-8'))))
        # The independent Round68 native fixture uses3 calls and stores them
        # under its own isolated directory, outside the four CLI ledgers.
        assert native==72,(version,native)
        native+=3
        qual.append(dict(version=version,native_calls=native,passed=version=='v6',
            wall_seconds=sum(a['wall_seconds'] for a in q['attempts']),source=q['identity']['source_commit']))
        for name in ['configure.log','build.log','tests.log']:
            archive(build/name,Path('qualification')/version/(name+'.gz'))
        for folder in sorted(build.iterdir()):
            if folder.is_dir() and (folder.name.startswith('native_evidence_test_') or folder.name.startswith('round68') or
                    '_cli_' in folder.name):
                for source in sorted(folder.rglob('*')):
                    if source.is_file():archive(source,Path('qualification')/version/(str(source.relative_to(build))+'.gz'))
    refs=sum(read(p)['wall_seconds'] for p in (OUT/'reference').glob('*/completion.json'))
    write(OUT/'checks.json',checks);write(OUT/'evidence_manifest.json',manifest)
    audit=dict(native_diagnoses=6,actual_optimize_calls=calls,physical_witnesses=witnesses,
        full_domain_native_bound_events=full_bounds,negative_replay_checks=rejection_tests,
        artifacts=len(manifest),raw_bytes=sum(r['raw_bytes'] for r in manifest),
        compressed_bytes=sum(r['bytes'] for r in manifest),qualification=qual,
        reference_builds=3,reference_optimizer_calls=0,reference_wall_seconds=refs,
        wall_seconds=time.perf_counter()-started,all_checks_passed=True,script_sha256=sha(__file__))
    write(OUT/'audit.json',audit)
    prior=read(STAGE/'combined_resource_summary.json')
    # The preceding startup checkpoint remains immutable and separately named.
    write(STAGE/'runtime_resource_summary.json',dict(startup_checkpoint=prior,total_startup_launches=20,
        total_startup_wall_seconds=prior['total_startup_wall_seconds'],
        total_qualification_batches=6,failed_qualification_batches=3,latest_passed_tests=54,
        total_qualification_native_calls=prior['total_qualification_native_calls']+sum(q['native_calls'] for q in qual),
        total_qualification_wall_seconds=prior['total_qualification_wall_seconds']+sum(q['wall_seconds'] for q in qual),
        native_diagnoses=6,native_diagnosis_optimize_calls=calls,native_diagnosis_wall_seconds=summary['total_wall_seconds'],
        reference_builds=3,reference_optimizer_calls=0,reference_wall_seconds=refs,
        native_diagnosis_offline_replay_seconds=summary['offline_replay_seconds'],package_audit_seconds=audit['wall_seconds'],
        formal_performance_launches=0,stage_complete=False))
    print(json.dumps(dict(audit=audit,checks=checks),indent=2))


if __name__=='__main__':main()
