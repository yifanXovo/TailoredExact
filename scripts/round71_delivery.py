"""Check packaged bytes and source bindings; separate from mathematical QA."""
import csv,gzip,time
import package_round71 as package
run=package.run

def main():
    started=time.perf_counter();package.bind();frozen,protocol=run.assert_frozen()
    assert not (run.OUT/'active_run.lock').exists(),'Verify after the optimizer queue stops'
    records=list(csv.DictReader((run.OUT/'runs.csv').open(encoding='utf-8')))
    completed=[e for e in run.runner.entries() if e['charged']]
    assert all((run.ROOT/e['destination']/'completion.json').exists() for e in completed)
    assert len(records)==len(completed)
    manifest=run.read(run.OUT/'evidence_manifest.json')
    assert len({e['artifact'] for e in manifest})==len(manifest)
    lossless=summaries=total=0
    for e in manifest:
        artifact=run.OUT/e['artifact'];source=run.ROOT/e['source']
        assert run.sha(artifact)==e['sha256'],str(artifact)
        assert run.sha(source)==e['source_sha256'],str(source)
        total+=artifact.stat().st_size
        if artifact.name=='result_summary.json':
            raw=run.read(source);selected=run.read(artifact)
            assert all(k in raw and v==raw[k] for k,v in selected.items()),str(artifact)
            summaries+=1
        else:
            decoded=gzip.decompress(artifact.read_bytes()) if artifact.suffix=='.gz' else artifact.read_bytes()
            assert decoded==source.read_bytes(),str(artifact)
            lossless+=1
    snapshot=run.read(run.OUT/'source_snapshot.json');assert snapshot==frozen['source']
    for name,digest in snapshot.items():assert run.sha(run.ROOT/name)==digest,name
    for p in protocol['panel']:assert run.sha(run.ROOT/p['instance_path'])==p['input_sha256'],p['id']
    result=dict(artifact_count=len(manifest),lossless_artifacts=lossless,exact_result_summaries=summaries,
        compact_bytes=total,source_files=len(snapshot),input_settings=len(protocol['panel']),
        completed_experiments=len(completed),artifact_hashes_and_content_passed=True,
        source_and_input_hashes_passed=True,optimizer_calls=0,wall_seconds=time.perf_counter()-started,
        script_sha256=run.sha(__file__),manifest_sha256=run.sha(run.OUT/'evidence_manifest.json'),
        scope='Delivery integrity only; route/model/Start/coverage validity is established by the separate package audit')
    run.write(run.OUT/'delivery_verification.json',result);print(result)

if __name__=='__main__':main()
