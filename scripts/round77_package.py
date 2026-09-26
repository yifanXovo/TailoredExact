"""Direct lossless bundles for the frozen D7 panel; no per-event archive copies."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time
import sys
import round73_bundle_formal as prior_bundle
from round77_analyze import campaign_summary
from round76_qualify import ROOT, sha, write
OUT=ROOT/'results/unified_exact_round77/campaign'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def main():
    start=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    audit=read(OUT/'audit.json');assert audit['all_checks_passed']
    mechanism=read(OUT/'mechanism_audit.json');assert mechanism['all_checks_passed']
    frozen=read(OUT/'identity.json');summary=campaign_summary()
    dest=OUT/'bundles';assert not dest.exists(),'Never replace a delivery';dest.mkdir()
    groups=[(f'run_{r["number"]}',ROOT/r['destination']) for r in frozen['launches']]
    groups.append(('reference',OUT/'reference'))
    bundles=[]
    for label,folder in groups:
        path=dest/(label+'.tar.gz');members=[]
        with path.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
                for source in sorted(folder.rglob('*')):
                    if not source.is_file():continue
                    data=source.read_bytes();name=source.relative_to(folder).as_posix()
                    info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
                    tf.addfile(info,io.BytesIO(data))
                    members.append(dict(member=name,source=source.relative_to(ROOT).as_posix(),
                        source_sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        bundles.append(dict(path=path.relative_to(OUT).as_posix(),sha256=sha(path),
                            bytes=path.stat().st_size,members=members))
    manifest=dict(schema='round77-lossless-bundles-v1',bundles=bundles,
        source_audit_sha256=sha(OUT/'audit.json'),identity_sha256=sha(OUT/'identity.json'),
        mechanism_audit_sha256=sha(OUT/'mechanism_audit.json'))
    prior_bundle.OUT=OUT
    assert prior_bundle.verify(manifest)==sum(len(b['members']) for b in bundles)
    write(OUT/'bundle_manifest.json',manifest)
    delivery=dict(all_members_hash_verified=True,bundles=len(bundles),
        original_files=sum(len(b['members']) for b in bundles),
        raw_bytes=sum(r['bytes'] for b in bundles for r in b['members']),
        delivered_bytes=sum(b['bytes'] for b in bundles),optimizer_calls=0,
        wall_seconds=time.perf_counter()-start,script_sha256=sha(__file__),
        inherited_verifier_sha256=sha(prior_bundle.__file__),
        verification_command='python scripts/round77_package.py --verify-only')
    write(OUT/'delivery.json',delivery)
    q=read(OUT.parent/'qualification.json')
    correction=read(OUT/'supervisor_scope_correction.json') if (OUT/'supervisor_scope_correction.json').exists() else None
    failures=[read(p) for p in (OUT.parent/'postprocess_failures').glob('*.json')]
    write(OUT.parent/'resource_summary.json',dict(inherited_ctests=58,newly_executed_ctests=0,
        new_builds=0,new_native_fixture_calls=0,new_full_runs=3,
        actual_full_optimize_calls=audit['actual_optimize_calls'],
        full_run_wall_seconds=summary['total_wall_seconds'],
        offline_replay_seconds=summary['offline_replay_seconds']+(correction['original_audit']['offline_replay_seconds'] if correction else 0),
        original_failed_adapter_audit_seconds=correction['original_audit']['offline_replay_seconds'] if correction else 0,
        supervisor_correction_nested_in_offline_replay_seconds=True,
        preflight_including_reference_seconds=q['preflight_wall_including_reference_seconds'],
        reference_builds=1,reference_optimize_calls=0,reference_wall_seconds=q['reference_wall_seconds'],
        independent_audit_seconds=audit['wall_seconds'],mechanism_audit_seconds=mechanism['wall_seconds'],
        retained_supervisor_exceptions=int(correction is not None),
        supervisor_scope_replay_seconds=correction['wall_seconds'] if correction else 0,
        failed_offline_commands=len(failures),
        failed_offline_command_wall_seconds=sum(f['command_wall_seconds'] for f in failures),
        package_seconds=delivery['wall_seconds'],
        stage_complete=False,overall_goal_complete=False))
    print(json.dumps(delivery,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['--verify-only']:
        start=time.perf_counter();prior_bundle.OUT=OUT
        files=prior_bundle.verify(read(OUT/'bundle_manifest.json'))
        print(json.dumps(dict(verified_files=files,wall_seconds=time.perf_counter()-start,
            optimizer_calls=0,extracted_files=0)))
    else:
        assert not sys.argv[1:]
        main()
