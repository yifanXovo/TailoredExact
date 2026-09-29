"""R97 serial experiments, with frozen per-batch source and input identities.

Reuses the qualified R90 supervisor and R86 original-physics/scope verifier.
All labels are fresh; audit failure stops the batch without rerunning a solver.
"""
import argparse, collections, ctypes, hashlib, json, subprocess, sys
from pathlib import Path
import round90_lp_g_g3 as r90
import round94_lpg_formal_recovery_v3 as scope
import round96_external as ext
from round96_prepare import read, write, sha, evidence, citi
from round97_build import ROOT, OUT
BUILD = ROOT/'build/research/round97-native-closure-v2'

def helper_bindings():
    paths = {Path(__file__).resolve()}
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == '.py' and path.is_relative_to(ROOT/'scripts'):
                paths.add(path)
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}

def ready_build():
    evidence = read(OUT/'production_v2_identity.json')
    assert evidence['source_hashes'] == bindings()
    assert evidence['binary_path'] == (BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix()
    assert evidence['binary_sha256'] == sha(BUILD/'ExactEBRP.exe')
    assert evidence['micro_gates_passed'] is True
    assert evidence['development01_analysis_sha256'] == sha(OUT/'development01_analysis/identity.json')
    for path, expected in evidence['qualification_gate_hashes'].items():
        assert sha(ROOT/path) == expected, path
    return evidence

def bindings():
    paths=[ROOT/'CMakeLists.txt']+sorted((ROOT/'src').rglob('*.cpp'))+sorted((ROOT/'include').rglob('*.hpp'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}

def normalized_hash(routes, capacities):
    def triple(operation):
        values=([operation[k] for k in ('station','pickup','drop')]
                if isinstance(operation,dict) else list(operation))
        assert len(values)==3 and all(type(v) is int for v in values)
        return values
    def serialization(items):
        text = ''
        for route in sorted(items, key=lambda r: r['vehicle']):
            text += 'v='+str(route['vehicle'])+';nodes='+''.join(str(n)+',' for n in route['nodes'])+';ops='
            for station,pickup,drop in sorted(map(triple,route['operations']), key=lambda op: op[0]):
                text += str(station)+':'+str(pickup)+':'+str(drop)+','
            text += '|'
        return text
    normalized = []
    for capacity in sorted(set(capacities)):
        vehicles = [k for k,q in enumerate(capacities) if q==capacity]
        used = [dict(r) for r in routes if capacities[r['vehicle']]==capacity and r['operations']]
        used.sort(key=lambda r: (-len(r['operations']), serialization([dict(r,vehicle=0)])))
        assert len(used)<=len(vehicles)
        normalized.extend(dict(r,vehicle=k) for r,k in zip(used,vehicles))
    return hashlib.sha256(serialization(normalized).encode()).hexdigest()

def event_audit(launch):
    folder=Path(launch['destination'])/'external/round97'
    if not folder.exists():return dict(events=0,reason='no_native_session')
    rows=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
    assert not any(r['kind']=='failure' for r in rows),[r for r in rows if r['kind']=='failure']
    sessions=[r for r in rows if r['kind']=='session']
    assert len(sessions)==1
    session=sessions[0]
    assert session['mode']==launch['mode'] and session['operator']==launch['operator']
    assert session['eligibility']=='non_initial_seed_and_non_current_start_v2'
    assert session['initial_seed_hash']
    capacities=citi.parse_instance_mirror(ROOT/launch['panel']['input_path'])['Q']
    initial=read(folder.parent/'initial_witness.json')
    assert normalized_hash(initial['routes'],capacities)==session['initial_seed_hash']
    starts={}
    for setup_path in (folder.parent/'native_logs').glob('*.round97.setup.json'):
        setup=read(setup_path);assert setup['valid'] and setup['call'] not in starts
        start_path=Path(str(setup_path).replace('.round97.setup.json','.round68.start.json'))
        start=read(start_path) if start_path.exists() else None
        current_hash=None
        if start is not None:
            assert start['model_sha256']==setup['model_sha256']
            if start['submitted']:
                assert start['mapping_complete'] and start['rows_valid'] and start['readback_valid'] and start['objective_valid']
                witness=read(folder.parent/(start['source']+'_witness.json'))
                current_hash=normalized_hash(witness['routes'],capacities)
        starts[setup['call']]=(setup['model_sha256'],current_hash)
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
        assert e['matches_initial_seed_physical_state'] == (e['input_hash']==session['initial_seed_hash'])
        model_sha,current_hash=starts[e['call']]
        assert e['model_sha256']==model_sha
        expected_start=None if current_hash is None else e['input_hash']==current_hash
        assert e['matches_supplied_start_physical_state'] is expected_start
        if 'mapped_vector' in e:assert sha(folder/e['mapped_vector'])==e['mapped_vector_sha256']
        if launch['mode']!='feedback':assert 'submission_return_code' not in e
        excluded=(e['matches_initial_seed_physical_state'] is True or
                  e['matches_supplied_start_physical_state'] is True)
        if excluded:
            assert e['status']=='start_matching_state_observation_only'
            assert not any(k in e for k in ['closure_seconds','candidate_F','submission_return_code'])
        else:
            assert e['matches_initial_seed_physical_state'] is False
            if launch['mode']=='observe':
                assert e['status'] in ['observe_new_state','observe_duplicate_state']
                assert 'candidate_F' not in e
        if e.get('order_moves',0):assert launch['operator']=='r96'
    first={}
    for e in events:
        first.setdefault(e['input_hash'], e)
    for h,e in first.items():
        witness=read(folder/('input_'+h+'.json'))
        assert witness['sha256']==h==normalized_hash(witness['routes'],capacities)
        assert (folder/('vector_'+str(e['event'])+'.csv')).exists()
    if launch['mode']!='feedback':
        assert not any(e['kind']=='archive_handoff' for e in rows)
    counts=collections.Counter(e['status'] for e in events)
    checkpoint_F={}
    for row in rows:
        if row['kind']=='predeadline_verified_candidate':
            checkpoint_F[row['event']]=min(checkpoint_F.get(row['event'],float('inf')),row['F'])
    return dict(events=len(events),status_counts=dict(counts),physical_witnesses=checked,
        verified_candidates=sum(e['kind']=='predeadline_verified_candidate' for e in rows),
        strict_closure_improvements=sum(e.get('candidate_F',float('inf'))<e.get('input_F',0)-1e-9 for e in events),
        excluded_start_matching_events=sum(e['status']=='start_matching_state_observation_only' for e in events),
        eligible_physical_events=sum(e['matches_initial_seed_physical_state'] is False and
            e['matches_supplied_start_physical_state'] is not True for e in events),
        post_start_events=sum(e['matches_initial_seed_physical_state'] is False and
            e['matches_supplied_start_physical_state'] is not True and e.get('nodes',0)>0 for e in events),
        accepted_order_moves=sum(e.get('order_moves',0) for e in events),
        order_proposals=sum(e.get('order_proposals',0) for e in events),
        incremental_order_improvement_events=sum(e.get('initial_old_closure_complete',False) and
            e.get('initial_old_closure_F') is not None and
            min(e.get('candidate_F',float('inf')),checkpoint_F.get(e['event'],float('inf')))
                < e['initial_old_closure_F']-1e-9 for e in events),
        incremental_order_count_scope='Recorded fresh-closure joint R96/R83 increment; excludes cache reuse and interrupted improvements not retained by the best archive, so is a lower bound, not all discoveries.',
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
        expected='custom' if launch['arm']=='P-GRB' else 'research-round97-v2-ensc-native-'+launch['mode']+'-'+launch['operator']
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
    assert label=='qualification03','Only declared v2 qualification admitted'
    build=ready_build()
    # Development-only functional windows; no complete-performance conclusion.
    schedule=[('F5','SHADOW',900),('F5','FEEDBACK',900),('F2','FEEDBACK',240)]
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
        command=r90.command_for(prereg,panel,'ENS-C',dest)+['--round97-native-closure',mode,'--round97-native-operator','r96']
        launches.append(dict(number=len(launches)+1,id=role,arm=arm,mode=mode,operator='r96',panel=panel,
            destination=str(dest),stage='qualification',cap_seconds=cap,hard_stop_seconds=cap-2,command=command))
    dll=Path('D:/gurobi1302/win64/bin/gurobi130.dll');api=ctypes.CDLL(str(dll));version=[ctypes.c_int() for _ in range(3)]
    api.GRBversion(*[ctypes.byref(v) for v in version]);assert [v.value for v in version]==[13,0,2]
    identity=dict(schema='round97-v2-qualification-v1',source_ref=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_hashes=bindings(),candidate_binary_sha256=sha(binary),dll_sha256=sha(dll),
        gurobi_version=[v.value for v in version],cmake_cache_sha256=sha(BUILD/'CMakeCache.txt'),
        prereg_sha256=sha(OUT/'research_state.md'),runner_sha256=sha(__file__),
        revision_plan_sha256=sha(OUT/'revision02_plan.md'),
        build_identity_sha256=sha(OUT/'production_v2_identity.json'),
        helper_hashes=helper_bindings(),prereg=prereg,launches=launches,
        maximum_starts=len(launches),maximum_process_seconds=sum(x[2] for x in schedule),
        question='Real post-start MIPSOL decode, physical closure, full current-model mapping, legal feedback and continued native proof. Not final performance qualification.',
        audit_reference_scope='Unchanged R96 original compact reference exports only; no old solver times reused.')
    write(camp/'identity.json',identity);print(json.dumps(dict(prepared=label,starts=len(launches),seconds=sum(x[2] for x in schedule))))

def run(label,number):
    ext.ensure_idle();camp=OUT/label;identity=read(camp/'identity.json')
    assert identity['source_hashes']==bindings(),'source changed after batch freeze'
    assert identity['runner_sha256']==sha(__file__)
    assert identity['prereg_sha256']==sha(OUT/'research_state.md')
    assert identity['revision_plan_sha256']==sha(OUT/'revision02_plan.md')
    ready_build()
    for path,expected in identity['helper_hashes'].items():
        assert sha(ROOT/path)==expected, path
    assert identity['build_identity_sha256']==sha(OUT/'production_v2_identity.json')
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
