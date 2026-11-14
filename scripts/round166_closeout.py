"""Actual scientific costs, protected-tree readback and zero-delete closeout."""
from round166_common import *
import argparse,shutil,os

def protection():
    checks=[]
    for old in read(OUT/'entry_state.json')['protected']:
        root=Path(old['root']);head=git('rev-parse','HEAD',cwd=root)
        status=git('status','--porcelain=v1','-uno',cwd=root)
        checked=[]
        for f in old['dirty_files']:
            p=root/f['path'];assert p.is_file() and sha(p)==f['SHA256'],('protected dirty byte change',p)
            checked.append(dict(path=f['path'],SHA256=f['SHA256'],unchanged=True))
        assert head==old['HEAD'] and status==old['status'],('protected tracked state changed',root)
        checks.append(dict(root=str(root),HEAD=head,tracked_status_unchanged=True,
            hashed_dirty_files=checked,dirty_status_lines=len(status.splitlines()),
            entry_hash_coverage_note='The initial helper stripped the first status line leading space and omitted that first dirty-file hash. HEAD/status and every saved dirty hash are compared; no complete byte baseline is claimed for the omitted file.' if len(status.splitlines())>len(checked) else 'complete saved tracked-dirty hash coverage'))
    # The bounded entry CSV identities are outside the new scientific outputs.
    csv_checks=[]
    for entry in read(OUT/'CSV_entry.json'):
        p=Path(entry['path']);p=p if p.is_absolute() else ROOT/p
        assert p.is_file() and sha(p)==entry['SHA256'] and p.stat().st_size==entry['bytes'],('protected CSV changed',p)
        csv_checks.append(dict(path=str(p),SHA256=entry['SHA256'],unchanged=True))
    value=dict(UTC=utc(),PASS=True,checks=checks,CSV_checks=csv_checks,
        writes_to_protected_trees=0,resets=0,stashes=0,force_pushes=0,deleted_old_objects=0)
    old_pe=WORK/'build-cache/round162/complete_v2/ExactEBRP.exe'
    assert sha(old_pe)=='fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93'
    value['historical_measured_PE_unchanged']=bind(old_pe)
    write(OUT/'protected_tree_check.json',value);return value

def cost():
    s=read(OUT/'reports/summary.json');assert s['complete']
    q=read(OUT/'qualification.json');entry=read(OUT/'entry_state.json')
    now=datetime.now(timezone.utc);start=datetime.fromisoformat(entry['work_start_UTC']);elapsed=(now-start).total_seconds()
    assert elapsed<=57600
    formal=[]
    for f in sorted((OUT/'fees').glob('???.json')):
        r=read(f);assert r['status']=='COMPLETE';formal.append(r)
    assert len(formal)==12
    drivers=read(OUT/'qualification/driver_calls.json')
    value=dict(UTC=utc(),work_start_UTC=entry['work_start_UTC'],science_cost_snapshot_UTC=now.isoformat(),
        capacity_seconds=57600,conservative_shared_outer_seconds=elapsed,capacity_remaining_lower_bound=57600-elapsed,
        budget_policy='Shared wall window counts parallel agent work once. Early mixed Git IO is conservatively included. All work through this snapshot fits capacity even without excluding ordinary IO.',
        diagnostic=dict(actual_native_Optimize=q['actual_Optimize'],limit_Optimize=120,
            complete_outer_window_seconds=q['diagnostic_window_seconds'],limit_outer_seconds=3600,
            driver_process_seconds=sum(r['seconds'] for r in drivers),
            native_cost_is_nested=True,healthy_reader_failures_preserved=True,producer_repeats_for_reader_errors=0),
        formal=dict(positions=12,source_build=s['source_commit'],PE_SHA=s['PE_SHA'],
            actual_native_Optimize=s['total_native_Optimize'],nominal_cap_sum=21600,reservation_sum=25200,
            watchdog='producer cap+900 fault-only; never expands evaluation budget',
            actual_fresh_wrapper_outer_seconds=s['actual_wrapper_outer_seconds'],
            actual_T_produce={m:s['method_produce_seconds'][m] for m in ['B','C166']},
            actual_T_verify={m:s['method_verify_seconds'][m] for m in ['B','C166']},
            actual_produce_plus_verify=s['actual_produce_plus_verify'],
            wrapper_management_difference=s['actual_wrapper_outer_seconds']-s['actual_produce_plus_verify'],
            per_position= [dict(position=f['position'],status=f['status'],actual_wrapper_seconds=f['seconds'],producer_cap=f['producer_cap'],reservation=f['reservation'],watchdog=f['watchdog']) for f in formal]),
        total_new_native_Optimize=q['actual_Optimize']+s['total_native_Optimize'],
        offline_parameter_resource_Optimize=0,figures_document_review_Optimize=0,
        no_new_full_root_or_Eplus_or_Seed_study=True,
        explanatory_counters='Runtime/Work/nodes/H/build/read are nested within paid outer work, not added again.',
        Git_and_public_transfer_IO='Measured delivery operations are recorded separately in delivery_io.json; they do not replace solver fees. The conservative wall-cap test also includes them until the last cost snapshot.')
    write(OUT/'cost_report.json',value);print('Conservative shared wall seconds:',round(elapsed,3),'; capacity remaining at least',round(57600-elapsed,3))

def cleanup():
    assert read(OUT/'public_recovery.json')['PASS']
    before=shutil.disk_usage(WORK);retained=[]
    for p in [ROOT,WORK/'build-cache/round166',WORK/'temp/round166',Path(read(OUT/'public_recovery.json')['fresh_empty_root'])]:
        if p.exists():
            files=[]
            for folder,dirs,names in os.walk(p,followlinks=False):
                dirs[:]=[name for name in dirs if not (os.stat(Path(folder)/name,follow_symlinks=False).st_file_attributes & 0x400)]
                files.extend(Path(folder)/name for name in names if not (os.stat(Path(folder)/name,follow_symlinks=False).st_file_attributes & 0x400))
            retained.append(dict(path=str(p),files=len(files),logical_bytes=sum(q.stat().st_size for q in files)))
    # Zero deletion is an explicitly allowed cleanup disposition.
    after=shutil.disk_usage(WORK)
    value=dict(UTC=utc(),screening='bounded to this worktree, round166 build/temp and its actual public recovery',
        public_recovery=bind(OUT/'public_recovery.json'),actions=[],deleted_files=0,deleted_logical_bytes=0,
        disposition='Retain raw, new carriers, source, own PE, failures, QA and recovered bytes for the live Draft; zero deletion.',
        retained=retained,E_volume_free_before=before.free,E_volume_free_after=after.free,
        observed_free_delta=after.free-before.free,claimed_bytes_freed_by_deletion=0,
        external_dependency_junctions_followed=False,
        protected_tree_readback=protection(),old_round_cleanup_authorized_or_performed=False)
    write(OUT/'cleanup_record.json',value);print('Bounded cleanup complete: zero deletion; protected tracked state/recorded dirty bytes and both located CSVs unchanged.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['cost','protection','cleanup']);args=parser.parse_args();globals()[args.action]()
