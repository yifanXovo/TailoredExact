"""R97 serial experiments, with frozen per-batch source and input identities.

Reuses the qualified R90 supervisor and R86 original-physics/scope verifier.
All labels are fresh; audit failure stops the batch without rerunning a solver.
"""
import argparse, collections, ctypes, json, subprocess
from pathlib import Path
import round90_lp_g_g3 as r90
import round94_lpg_formal_recovery_v3 as scope
import round96_external as ext
from round96_prepare import read, write, sha, evidence
from round97_build import ROOT, OUT, BUILD

def bindings():
    paths=[ROOT/'CMakeLists.txt']+sorted((ROOT/'src').rglob('*.cpp'))+sorted((ROOT/'include').rglob('*.hpp'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}

def event_audit(launch):
    folder=Path(launch['destination'])/'external/round97'
    if not folder.exists():return dict(events=0,reason='no_native_session')
    rows=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
    assert not any(r['kind']=='failure' for r in rows),[r for r in rows if r['kind']=='failure']
    events=[r for r in rows if r['kind']=='solution']
    assert [r['event'] for r in events]==list(range(1,len(events)+1))
    checked=[]
    for path in sorted(folder.glob('*.json')):
        value=read(path)
        if 'routes' not in value:continue
        result=evidence.physical_module.physical(launch['panel'],value)
        assert result['original_T_feasible'];checked.append(dict(path=path.name,sha256=sha(path),F=result['F']))
    for e in events:
        assert not e['status'].startswith('exception:'),e
        if 'mapped_vector' in e:assert sha(folder/e['mapped_vector'])==e['mapped_vector_sha256']
        if launch['arm']!='FEEDBACK':assert 'submission_return_code' not in e
    counts=collections.Counter(e['status'] for e in events)
    return dict(events=len(events),status_counts=dict(counts),physical_witnesses=checked,
        verified_candidates=sum(e['kind']=='predeadline_verified_candidate' for e in rows),
        strict_closure_improvements=sum(e.get('candidate_F',float('inf'))<e.get('input_F',0)-1e-9 for e in events),
        post_start_events=sum(e.get('matches_supplied_start_physical_state') is False and e.get('nodes',0)>0 for e in events),
        vector_observations=sum(e['kind']=='submitted_vector_observed' for e in rows),
        native_incumbent_changes=sum(e['kind']=='native_incumbent_change' for e in rows),
        archive_handoffs=sum(e['kind']=='archive_handoff' for e in rows),
        complete_callback_seconds=sum(e.get('complete_new_callback_seconds',0) for e in rows),
        closure_seconds=sum(e.get('closure_seconds',0) for e in events),
        mapping_validation_seconds=sum(e.get('mapping_validation_seconds',0) for e in events))

def auditor(launch, observations, completion, identity):
    checked=scope.scope_receipt(launch,observations)
    normal=completion['stop_reason']=='normal_return'
    dest=Path(launch['destination']);result=read(dest/'result.json') if normal else None
    audited=evidence.audit(ROOT,launch['panel'],observations,identity['candidate_binary_sha256'])
    evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,observations,result,
        completion['stop_reason'],launch['panel'].get('reference',{}))
    if normal:
        expected='custom' if launch['arm']=='P-GRB' else 'research-round97-ensc-native-'+launch['mode']
        assert result['algorithm_preset']==expected,(result['algorithm_preset'],expected)
        audited['five_native_parameter_readback']=scope.v2.parameter_readback(result,
            require_call=checked['native_calls']>0,arm='P-GRB' if launch['arm']=='P-GRB' else 'ENS-C')
    if launch['arm']!='P-GRB':audited['round97']=event_audit(launch)
    else:
        reference=launch['panel']['reference']
        assert sha(dest/'compact.lp')==reference['canonical_sha256']
        if normal:
            assert result['gurobi_hga_start_requested'] is False
            assert result['gurobi_optimize_count']==1
            assert result['gurobi_num_vars']==reference['columns'] and result['gurobi_num_constrs']==reference['rows']
    audited.update(passed=True,native_scope_adapter=checked,lp_g_split_evidence=None)
    return audited

def prepare(label):
    ext.ensure_idle();camp=OUT/label;assert not camp.exists()
    assert label=='qualification02','Only the revised declared qualification batch is admitted by this revision'
    # Development-only functional windows; no complete-performance conclusion.
    schedule=[('F5','SHADOW',300),('F5','FEEDBACK',300),('F2','FEEDBACK',240)]
    prior=read(ROOT/'results/unified_exact_round96/primal/identity.json')
    binary=BUILD/'ExactEBRP.exe'
    prereg=dict(candidate_binary=binary.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(binary),common=ext.COMMON)
    launches=[]
    for role,arm,cap in schedule:
        panel=dict(next(r['panel'] for r in prior['launches'] if r['id']==role))
        panel['cap_seconds']=cap;panel['instance_path']=panel['input_path']
        assert sha(ROOT/panel['input_path'])==panel['input_sha256']
        mode={'OFF':'observe','SHADOW':'shadow','FEEDBACK':'feedback'}[arm]
        dest=camp/'raw'/f'{len(launches)+1:02d}_{role}_{arm}'
        command=r90.command_for(prereg,panel,'ENS-C',dest)+['--round97-native-closure',mode]
        launches.append(dict(number=len(launches)+1,id=role,arm=arm,mode=mode,panel=panel,
            destination=str(dest),stage='qualification',cap_seconds=cap,hard_stop_seconds=cap-2,command=command))
    dll=Path('D:/gurobi1302/win64/bin/gurobi130.dll');api=ctypes.CDLL(str(dll));version=[ctypes.c_int() for _ in range(3)]
    api.GRBversion(*[ctypes.byref(v) for v in version]);assert [v.value for v in version]==[13,0,2]
    identity=dict(schema='round97-qualification-v1',source_ref=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_hashes=bindings(),candidate_binary_sha256=sha(binary),dll_sha256=sha(dll),
        gurobi_version=[v.value for v in version],cmake_cache_sha256=sha(BUILD/'CMakeCache.txt'),
        prereg_sha256=sha(OUT/'research_state.md'),runner_sha256=sha(__file__),prereg=prereg,launches=launches,
        maximum_starts=len(launches),maximum_process_seconds=sum(x[2] for x in schedule),
        question='Real post-start MIPSOL decode, physical closure, full current-model mapping, legal feedback and continued native proof. Not final performance qualification.',
        audit_reference_scope='Unchanged R96 original compact reference exports only; no old solver times reused.')
    write(camp/'identity.json',identity);print(json.dumps(dict(prepared=label,starts=len(launches),seconds=840)))

def run(label,number):
    ext.ensure_idle();camp=OUT/label;identity=read(camp/'identity.json')
    assert identity['source_hashes']==bindings(),'source changed after batch freeze'
    assert identity['runner_sha256']==sha(__file__)
    assert identity['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert identity['dll_sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')
    summary=camp/'summary.jsonl';rows=[json.loads(s) for s in summary.read_text().splitlines()] if summary.exists() else []
    assert len(rows)==number-1 and all(r['audit_passed'] for r in rows)
    launch=identity['launches'][number-1]
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=camp;r90.audit_launch=auditor
    r90.run_one(launch,identity['prereg'],identity)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);p.add_argument('label');p.add_argument('--number',type=int)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.label)
    else:run(a.label,a.number)
