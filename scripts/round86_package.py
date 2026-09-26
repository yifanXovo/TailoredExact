"""Twenty-one new run trees plus original references; inherited qualification stays bound."""
import gzip
import hashlib
import io
import json
import sys
import tarfile
import time
from pathlib import Path
from round83_qualify import ROOT,sha,read,write
import round83_package as inherited_package

OUT=ROOT/'results/unified_exact_round86'


def verify():
    original=inherited_package.OUT
    try:
        inherited_package.OUT=OUT
        return inherited_package.verify()
    finally:
        inherited_package.OUT=original


def main():
    started=time.perf_counter()
    if '--verify-only' in sys.argv:
        result=verify();result['wall_seconds']=time.perf_counter()-started
        print(json.dumps(result));return
    campaign=OUT/'campaign'
    assert not (campaign/'active_run.lock').exists()
    assert read(campaign/'driver_completion.json')['all_valid']
    for name in ['audit.json','mechanism_audit.json','confirmation_audit.json']:
        assert read(campaign/name)['all_checks_passed']
    assert not (OUT/'bundle_manifest.json').exists() and not (OUT/'bundles').exists()
    prior=ROOT/'results/unified_exact_round83'
    prior_manifest=read(prior/'bundle_manifest.json')
    inherited=[]
    for name in ['measured_source_bytes','qualification_v1','startup']:
        bundle=next(b for b in prior_manifest['bundles'] if Path(b['path']).name==name+'.tar.gz')
        assert sha(ROOT/bundle['path'])==bundle['sha256']
        inherited.append(bundle)
    write(OUT/'inherited_evidence.json',dict(stage=83,published_draft_pr=144,
        published_commit='131d09280a1563243d0201e68367b26baf5079c3',
        manifest_path=str((prior/'bundle_manifest.json').relative_to(ROOT)),
        manifest_sha256=sha(prior/'bundle_manifest.json'),
        member_manifest_sha256=sha(prior/'bundle_members.json.gz'),bundles=inherited,
        qualification_sha256=sha(prior/'qualification_v1.json'),
        qualification_audit_sha256=sha(prior/'qualification_v1_audit.json'),
        startup_completion_sha256=sha(prior/'startup/completion_summary.json'),
        scope='Published byte-bound qualified source, qualification and diagnostic startup evidence; no new qualification or startup process, no duplicate charge or copied performance row.'))
    frozen=read(campaign/'identity.json')
    assert len(frozen['launches'])==12
    (OUT/'bundles').mkdir();bundles=[]
    def package(name,files):
        path=OUT/'bundles'/(name+'.tar.gz');members=[]
        assert len({name for _,name in files})==len(files)
        with tarfile.open(path,'w:gz',compresslevel=9) as archive:
            for source,member in sorted(files,key=lambda item:item[1]):
                assert source.suffix.lower() not in ['.lic','.exe','.dll','.pem','.key'],source
                data=source.read_bytes();info=tarfile.TarInfo(member)
                info.size=len(data);info.mtime=0;info.mode=0o644
                archive.addfile(info,io.BytesIO(data))
                members.append(dict(source=str(source),member=member,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        bundles.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size,files=members))
    for launch in frozen['launches']:
        raw=ROOT/launch['destination']
        package(f"full_run_{launch['number']}",[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    raw=campaign/'reference'
    package('full_reference',[(p,p.relative_to(raw).as_posix()) for p in sorted(raw.rglob('*')) if p.is_file()])
    assert len(bundles)==13
    manifest=dict(bundles=bundles,
        source_scope='All twelve original complete-run trees and four original compact exports. Exact source/qualification/startup inherited from byte-bound R83 bundles; no executable, license or new qualification.',
        inherited_evidence_sha256=sha(OUT/'inherited_evidence.json'),
        raw_files=sum(len(b['files']) for b in bundles),
        raw_bytes=sum(r['bytes'] for b in bundles for r in b['files']),
        delivered_bytes=sum(b['bytes'] for b in bundles),script_sha256=sha(__file__),
        verifier_sha256=sha(inherited_package.__file__))
    member_path=OUT/'bundle_members.json.gz'
    member_path.write_bytes(gzip.compress((json.dumps(manifest,indent=2)+'\n').encode('utf-8'),compresslevel=9,mtime=0))
    index={k:v for k,v in manifest.items() if k!='bundles'}
    index['bundles']=[{**{k:v for k,v in b.items() if k!='files'},'file_count':len(b['files'])} for b in bundles]
    index.update(member_manifest_file=member_path.name,member_manifest_sha256=sha(member_path),
        member_manifest_bytes=member_path.stat().st_size,
        manifest_format='Per-member source/path/bytes/SHA256 in gzip JSON; compact index.')
    write(OUT/'bundle_manifest.json',index)
    result=verify();result['package_and_verify_seconds']=time.perf_counter()-started
    result.update({k:manifest[k] for k in ['raw_files','raw_bytes','delivered_bytes']})
    write(OUT/'delivery.json',result)
    full=read(campaign/'summary.json');audit=read(campaign/'audit.json')
    mechanism=read(campaign/'mechanism_audit.json');confirmation=read(campaign/'confirmation_audit.json')
    preflight=read(OUT/'full_preflight.json')
    resource=dict(new_qualification_calls=0,new_release_builds=0,new_ctests=0,new_native_fixture_calls=0,
        inherited_qualification_tests=62,inherited_qualification_calls_not_charged_again=165,
        new_startup_processes=0,new_full_runs=full['completed'],full_run_seconds=full['total_wall_seconds'],
        full_run_optimize_calls=audit['actual_optimize_calls'],total_new_optimize_calls=audit['actual_optimize_calls'],
        native_calls_returned=sum(r['audit']['native_calls_returned'] for r in full['records']),
        full_run_offline_replay_seconds=full['offline_replay_seconds'],
        full_preflight_seconds=preflight['preflight_wall_including_reference_seconds'],
        full_reference_seconds_nested=preflight['reference_wall_seconds'],
        full_reference_optimize_calls=0,final_audit_seconds=audit['wall_seconds'],
        mechanism_audit_seconds=mechanism['wall_seconds'],confirmation_audit_seconds=confirmation['wall_seconds'],
        generation_seconds=read(OUT/'generation.json')['wall_seconds'],
        offline_validation_seconds=sum(read(OUT/n)['wall_seconds'] for n in ['offline_validation.json','offline_validation_v2.json']),
        new_inputs_generated=4,package_and_verify_seconds=result['package_and_verify_seconds'],
        stage_complete=False,overall_goal_complete=False,reset_credits_consumed_by_this_agent=0,
        scope='All paid original processes and measured offline steps; inherited and nested work is not added again. Interactive work is not a complete machine-time census.')
    write(OUT/'resource_summary.json',resource)
    print(json.dumps(result))


if __name__=='__main__':main()
