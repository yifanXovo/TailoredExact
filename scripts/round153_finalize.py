"""Finite final evidence processing, executed inside one outer fee receipt.

No producer, compiler or Optimize is launched. The audit performs its declared
model reads; this file binds frozen identities and formats completed evidence.
"""
from round153_common import *


def sources():
    candidate=read(OUT/'candidate_manifest.json');matrix=read(OUT/'confirmation_matrix.json')
    helper=read(OUT/'helper_manifest.json');checked={}
    for mapping in [candidate['source_hashes'],matrix['helpers'],helper['helper_dependencies']]:
        for name,digest in mapping.items():
            if name in checked:assert checked[name]==digest
            else:assert sha(ROOT/name)==digest;checked[name]=digest
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert matrix['helper_manifest_SHA']==sha(OUT/'helper_manifest.json')
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA']
    assert sha(DLL)==DLL_SHA==candidate['DLL_SHA']
    stable={}
    for name in ['scripts/paper_s2.py','config/gi_tbc_round137.json']:
        old=subprocess.run(['git','show',BASE+':'+name],cwd=ROOT,check=True,capture_output=True).stdout
        digest=hashlib.sha256(old).hexdigest();assert sha(ROOT/name)==digest;stable[name]=digest
    current={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'scripts').glob('round153*.py'))}
    snapshots=[];source_bytes={}
    for p in sorted((OUT/'engineering/source_snapshots').glob('*.json')):
        snapshot=read(p)
        for name,digest in snapshot['files'].items():
            if digest not in source_bytes:
                q=OUT/'engineering/source_bytes'/f'{digest}.py.txt';assert sha(q)==digest
                source_bytes[digest]=dict(path=q.relative_to(ROOT).as_posix(),bytes=q.stat().st_size)
        snapshots.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),files=len(snapshot['files'])))
    coverage=[]
    for launch_path in sorted((OUT/'fees').glob('*/launch.json')):
        label=launch_path.parent.name;snapshot=OUT/'engineering/source_snapshots'/f'{label}.json'
        coverage.append(dict(fee_label=label,launch_SHA=sha(launch_path),snapshot_SHA=sha(snapshot) if snapshot.exists() else None,
            binding='per-launch source snapshot' if snapshot.exists() else
                'frozen confirmation matrix and candidate/helper manifests' if label.startswith('confirmation_') else
                'separate fee/build record; no per-launch source snapshot claimed'))
    record=dict(UTC=utc(),delivery_worktree_head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,
        check=True,capture_output=True,text=True).stdout.strip(),fixed_R152_base=BASE,fixed_R152_science=SCIENCE,
        production_measured_source_commit=candidate['source_commit'],production_PE=candidate['production_PE'],
        production_PE_SHA=candidate['production_PE_SHA'],DLL=str(DLL),DLL_SHA=DLL_SHA,
        frozen_candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
        frozen_helper_manifest_SHA=sha(OUT/'helper_manifest.json'),frozen_matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        checked_frozen_files=checked,unchanged_stable_entry_and_profile=stable,
        current_research_scripts=current,per_experiment_source_snapshots=snapshots,unique_source_bytes=source_bytes,
        source_snapshot_coverage=coverage,missing_snapshot_labels=[c['fee_label'] for c in coverage if c['snapshot_SHA'] is None],
        snapshot_inventory_is_not_a_claim_of_universal_snapshot_coverage=True,
        offline_versions_are_bound_per_run_not_retroactively_to_latest_source=True,
        source_snapshot_and_identity_bookkeeping_before_outer_receipts_not_separately_timed=True,
        untimed_setup_is_disclosed_measurement_gap_not_zero_cost=True,
        no_solver_compiler_or_producer=True)
    write(OUT/'source_manifest.json',record)
    print(json.dumps(dict(frozen_files=len(checked),research_scripts=len(current),source_snapshots=len(snapshots),
        unique_saved_sources=len(source_bytes),stable_entry_unchanged=True)),flush=True)


def run(label):
    from round153_audit import run as audit
    from round153_reports import science,research,complete
    configure();decision=read(OUT/'candidate_decision.json')
    assert decision['science_evidence'] and len(decision['science_evidence'])==3
    audit(label);science();research();complete();sources()
    assert not read(OUT/'reports/complete_arms.json')['missing_positions']
    write(OUT/'qualification'/label/'postprocessing.json',dict(PASS=True,UTC=utc(),
        scientific_audit_SHA=sha(OUT/'qualification'/label/'result.json'),source_manifest_SHA=sha(OUT/'source_manifest.json'),
        reports={p.name:sha(p) for p in sorted((OUT/'reports').glob('*')) if p.is_file() and p.name!='costs.csv'},
        no_Optimize_or_performance_rerun=True))


if __name__=='__main__':run(*sys.argv[1:])
