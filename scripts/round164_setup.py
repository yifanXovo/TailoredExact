"""Reuse the six immutable inputs; freeze targets before any new Optimize."""
from round164_common import *
import copy, csv, io, platform, shutil, zipfile

TABLES=[Path('C:/Users/Administrator/Desktop/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
        Path('C:/Users/Administrator/Desktop/Research/docs/tempfiles/GI_TBC_vs_P_GRB_All_Tested_Instances.csv')]

def run():
    assert not (OUT/'protocol.json').exists()
    assert sha(INPUT_MANIFEST)==INPUT_MANIFEST_SHA
    assert sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    protect()
    goal=Path('C:/Users/Administrator/Downloads/TailoredExact_Round164_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    manifest=read(INPUT_MANIFEST);assert len(manifest['roles'])==6
    roles=[]
    for old in manifest['roles']:
        assert sha(ROOT/old['input_path'])==old['input_sha256']
        p=copy.deepcopy(old);p.update(exposed=True,known=True,
            panel_kind='R163 cohort finite solver-seed confirmation')
        # Seed is an arm property. Never leave an inherited Seed0 default here.
        p.pop('gurobi_seed');roles.append(p)
    write(OUT/'input_references.json',dict(source_commit=R163_SCIENCE,
        source_manifest=INPUT_MANIFEST.relative_to(ROOT).as_posix(),source_manifest_SHA256=INPUT_MANIFEST_SHA,
        original_snapshot_unchanged=True,roles=roles,mathematical_inputs=6,regenerated_inputs=0))
    old=read(ROOT/'results/unified_exact_round163/method_freeze.json')
    ptemplate=copy.deepcopy(old['P_template'])
    ptemplate[ptemplate.index('--gurobi-seed')+1]='${seed}'
    write(OUT/'method_freeze.json',dict(UTC=utc(),B=old['B'],P_template=ptemplate,
        authority=dict(commit=BASE,path='results/unified_exact_round163/method_freeze.json',
                       SHA256=sha(ROOT/'results/unified_exact_round163/method_freeze.json')),
        Gurobi_Seeds=[1,2],H_seed=20260626,Threads=1,MIPThreads=1,MIPFocus=0,Cuts=-1,
        Presolve=-1,requested_gaps=0,affinity_mask=4,Native_NodeLimit='unlimited',
        cold_P_NumStart=0,clean_independent_templates=True,AP=False,AM=.08,maximum_depth=8,minimum_width=1e-4,
        native_limit_offset=6,outer_hard_stop_offset=2,shutdown_margin=30,
        scientific_reservation_margin=300,outer_fault_timeout_margin=900,
        source_and_PE_unchanged=True,Eplus_executed=False,no_cross_arm_information=True))
    candidate=read(ROOT/'results/unified_exact_round163/candidate_manifest.json')
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name
    candidate=copy.deepcopy(candidate);candidate.update(schema='round164-reused-common-production-v1',UTC=utc(),base=BASE)
    write(OUT/'candidate_manifest.json',candidate)
    oldarms=read(ROOT/'results/unified_exact_round163/reports/complete_arms.json')
    refs=[]
    for p in roles:
        pair={a['method']:a for a in oldarms if a['id']==p['id'] and a['method'] in ('B','P')}
        assert set(pair)=={'B','P'} and all(a['performance_eligible'] for a in pair.values())
        refs.append(dict(id=p['id'],u_ref=min(pair['B']['U'],pair['P']['U']),
            U_B_Seed0=pair['B']['U'],U_P_Seed0=pair['P']['U'],known_feasible_target_not_optimum=True,
            source_commit=R163_SCIENCE,path='results/unified_exact_round163/reports/complete_arms.json',
            offline_only=True,production_Start_cutoff_stopping_condition=False))
    write(OUT/'primal_targets_frozen.json',dict(UTC=utc(),before_any_new_Optimize=True,
        qualification_tolerance=1e-7,rule='min of the two qualified full-precision R163 Seed0 physical U',targets=refs,
        first_saved_verifiable_witness_only=True,no_interpolation_or_postverification_backdating=True,
        unavailable_event_clocks='retain interval, upper bound, or unknown; never fabricate an exact first time'))
    zpath=ROOT/'results/unified_exact_round163/artifacts/new_evidence_01.zip'
    assert sha(zpath)=='365d892c8d3593ddcf8c98f88fa220d96f7afb889b0b6f47ba86f09006aa3512'
    extracted=[]
    with zipfile.ZipFile(zpath) as z:
        for role in [p['id'] for p in roles]+['qualification-tiny-transfer']:
            for name in ['build.json','original.lp']:
                member=f'results/unified_exact_round163/qualification/references/{role}/{name}'
                raw=z.read(member);target=OUT/'qualification/references'/role/name
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                extracted.append(dict(commit=R163_SCIENCE,archive=zpath.relative_to(ROOT).as_posix(),
                    member=member,SHA256=sha(target),bytes=len(raw),Optimize=0))
    write(OUT/'qualification/inherited_references.json',dict(archives_opened=1,members=extracted,
        old_producer_replayed=False,full_old_archive_expanded=False))
    tiny=read(ROOT/'results/unified_exact_round163/qualification/smoke_panel.json')
    tiny.pop('gurobi_seed');tiny.update(exposed=True,known=True)
    write(OUT/'qualification/tiny_panel.json',tiny)
    snapshots=[]
    for i,path in enumerate(TABLES):
        raw=path.read_bytes();encoding='gb18030';data=list(csv.reader(io.StringIO(raw.decode(encoding),newline='')))
        assert len(data[0])==28 and all(len(r)==28 for r in data)
        backup=TEMP/f'master_before_{i}.csv';backup.write_bytes(raw)
        snapshots.append(dict(path=str(path),SHA256=sha(path),bytes=len(raw),encoding=encoding,
            rows=len(data)-1,header=data[0],local_backup=str(backup)))
    write(OUT/'main_table_discovery.json',dict(UTC=utc(),tables=snapshots,
        inspected_roots=['C:/Users/Administrator','E:/codes/ExactEBRP-work'],
        supplied_94_row_version_found=False,available_rows=[s['rows'] for s in snapshots],
        preserve_existing_bytes=True,classification_policy='retain existing labels; new classification blank, with endpoint facts',
        pending_historical_union=[dict(round=138,id='R-B35-S-T2',seed=1,cap=2400),
            dict(round=155,id='N-B35-S',cap=7200),dict(round=156,id='R-X35-S-T2',cap=7200)],
        expected_qualified_increment_pairs=12,no_invented_94_row_file=True))
    write(OUT/'environment_freeze.json',dict(UTC=utc(),platform=platform.platform(),node=platform.node(),
        processor=platform.processor(),logical_cpus=os.cpu_count(),affinity_mask=4,observer_affinity_mask=1,
        PE=str(PE),PE_SHA256=PE_SHA,DLL=str(DLL),DLL_SHA256=DLL_SHA,Gurobi_version='13.0.2',
        interpreter=str(PYTHON),python_version=sys.version,rebuild=False,
        original_R163_runtime_retained=True,experiment_design_only_no_hardware_algorithm_switch=True))
    write(OUT/'protocol.json',dict(UTC=utc(),round=164,base=BASE,methods=['B','P'],Gurobi_Seeds=[1,2],
        H_seed=20260626,mathematical_inputs=6,new_formal_arms=24,new_pairs=12,nominal_production_seconds=43200,
        total_scientific_capacity_seconds=57600,allocations=dict(qualification=1800,panel_and_verification=50400,
            final_readback=1800,repair=3600),reservation_is_not_Native_extension=True,
        serial=True,order='positions1..6; odd: S1 B/P S2 P/B; even: S1 P/B S2 B/P',
        complete_both_seeds_unconditionally=True,technical_failures_retained_no_healthy_arm_replay=True,
        evaluation=dict(endpoint_tolerance=1e-7,delta_U='B minus P; negative favors B',
            delta_L='B minus P; positive favors B',certificate_time='paid producer close, joint CERT only',
            material_time_difference='max(10 seconds, 10% of faster paid time)',
            seed_summary='within each of six configurations; median/range are descriptive, not new endpoints',
            no_IID_or_significance_claim=True,no_best_seed_selection=True),
        no_Eplus_retest_or_robustness_extrapolation=True,no_new_algorithm_core=True,
        no_extra_seed_mechanism_or_budget_grid=True,primal_target_in_production=False))
    print(json.dumps(dict(PASS=True,inputs=6,targets=6,table_rows=[s['rows'] for s in snapshots],Optimize=0)))

if __name__=='__main__':run()
