"""Finite zero-Optimize fixtures for new wiring; no new native grid."""
from round121_common import *
import copy,tempfile
from round108_decisions import pair
from round121_evidence import extension,event_chain,_parameters
from round113_audit import event_lifecycle
from round118_call_logs import segments,build
from round114_claims import reconcile
from round121_decision import decide
import round109_seed_scope as computed
OLD_ROOT=Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP')
def preflight():
    tick=time.perf_counter();pairs=[];history=[]
    for n in [1,2,3]:
        path=OLD_ROOT/f'results/unified_exact_round120/reconstruction/group{n:02d}/current_core.json';v=read(path)
        by={a['arm']:a for a in v['arms']}
        for p in v['pairs']:
            r=pair(by[p['candidate']],by[p['control']]);assert all(r[k]==p[k] for k in r)
            pairs.append(dict(id=v['group']['id'],**r))
        history.append(dict(group=n,current_core_SHA=sha(path),source=str(path),arms=v['arms'],pairs=v['pairs']))
    assert len(pairs)==18
    write(OUT/'preflight_R120_pair_replay.json',dict(saved_groups=history,all18_unchanged_comparisons=pairs,Optimize=0,native_starts=0,
        old_Seed0_separate=True,engineering_seconds=time.perf_counter()-tick))
    print('R120 all18 frozen comparisons replayed without native or full historical recovery')
def run():
    tick=time.perf_counter();checks=[]
    def life(events):return event_lifecycle([dict(payload=dict(sequence=i,**e)) for i,e in enumerate(events,1)])
    value=life([dict(kind='identity'),dict(kind='call',call=1),dict(kind='not_started',call=1,actual_Optimize=False,reason='no_remaining_original_work_window')])
    assert value['started']==0 and value['not_started']==1 and not value['pending_declaration_ids'];checks.append('explicit_not_started_is_zero_Optimize')
    value=life([dict(kind='identity'),dict(kind='call',call=1),dict(kind='returned',call=1,return_code=0)])
    assert value['started']==value['returned']==1;checks.append('normal_return_including_time_limit_is_an_actual_call')
    value=life([dict(kind='identity'),dict(kind='call',call=1)])
    assert value['pending_declaration_ids']=={1} and value['unreturned_ids']=={1};checks.append('unknown_disposition_never_promoted_to_not_started')
    for seed in [0,1]:assert computed.expected(seed)['Seed']==seed
    raw=[dict(payload=dict(kind='call',call=1,settings=computed.expected(1),native_preconditions=False))]
    before=copy.deepcopy(raw);proof=dict(recovered_calls=[dict(call=1)])
    projected=computed.projected_records(raw,proof,legacy_seed=True)
    assert raw==before and projected[0]['payload']['native_preconditions'] and projected[0]['payload']['settings']['Seed']==0
    assert raw[0]['payload']['settings']['Seed']==1 and raw[0]['payload']['native_preconditions'] is False
    checks.append('different_Seed_metadata_projection_preserves_raw_and_actual_Seed')
    source=OLD_ROOT/'results/unified_exact_round120/qualification/h100/raw/01_H100_S0_P-GRB/result.json';r=read(source)
    for suffix in ['requested','effective']:r['gurobi_seed_'+suffix]=1
    assert _parameters(r,seed=1,require_call=True,arm='P-GRB')['seed']['effective']==1
    wrong=copy.deepcopy(r);wrong['gurobi_seed_effective']=0
    try:_parameters(wrong,seed=1,require_call=True,arm='P-GRB')
    except AssertionError:pass
    else:raise AssertionError('wrong actual Seed accepted')
    checks.append('actual_Seed_readback_checked_before_legacy_projection')
    log=b'Gurobi Optimizer version 13.0.2\nOptimize a model with 1 rows, 1 columns\nExplored 0 nodes\nBest objective 1, best bound 0, gap 100%\n'
    assert len(segments(log+log))==2
    try:segments(log+log.replace(b'Gurobi Optimizer version 13.0.2\n',b''))
    except AssertionError:pass
    else:raise AssertionError('unbound reused call log accepted')
    checks.append('same_log_multiple_calls_separate_spans_and_missing_preamble_rejected')
    claim=dict(arm='MB-D1',call=1,sequence=2,model_SHA='NONREAL',input_SHA='NONREAL',scope=dict(full_original=False,lower_g=0.,upper_g=.5,cutoff=1.),
        value=.4,source='NONREAL',available=2.,domain_verified=True,dependencies=[1])
    witness=dict(arm='M-B',call=0,sequence=1,G=.2,F=.3,input_SHA='NONREAL',physical_verified=True,source='NONREAL',available=1.)
    rejected=reconcile([claim],[witness]);assert rejected['rejections'] and rejected['damaged_calls']
    outside=dict(witness,G=.7);assert not reconcile([claim],[outside])['rejections'];checks.append('bad_same_domain_source_rejected_and_outside_scope_not_transferred')
    with tempfile.TemporaryDirectory(prefix='r121-finite-') as temporary:
        root=Path(temporary);d=root/'raw';(d/'external').mkdir(parents=True)
        l=dict(arm='MB-D1',command=['--round120-native-proof-d1'])
        for reason,extra in [('root_not_installed',dict(leaf='L0',pair_complete=False,deadline_remaining=0)),('original_AM_direct_split',dict(leaf='L0.0',pair_complete=False,deadline_remaining=10))]:
            write(d/'external/round120_events.jsonl',{})
            (d/'external/round120_events.jsonl').write_text(json.dumps(dict(sequence=1,kind='not_exposed',**extra))+'\n')
            value=event_chain(root,l,d,dict(calls={},returned_ids=set(),witnesses=[]))
            assert value['installed']==0 and value['actual_extended_Optimize']==0;checks.append(reason)
        (d/'external/round120_events.jsonl').unlink()
        (root/'zero.txt').write_text('1 1 [1]\ncapacities = [10, 2]\ninitial = [0, 1]\ntarget = [0, 1]\nweights = [0, 1]\nmin_ratio = [0, 0]\npoints = [(0, 0), (0, 0)]\n')
        p=dict(input_path='zero.txt',V=1,M=1,Q_vector=[1],T_seconds=120,pickup_seconds=60,drop_seconds=60,**{'lambda':.15})
        write(d/'result.json',dict(routes=[]));l['panel']=p
        value=event_chain(root,l,d,dict(started=0));assert value['not_exposed_original_verified_zero_H'];checks.append('zero_certificate_without_native_exposure')
        j=dict(calls={1:dict(native_log_path=str(d/'missing.log'))},not_started_ids={1},actual_started_ids=set())
        view=build(root,dict(arm='MB-D1'),d,j,{})
        assert not view['actual'] and not view['bindings'];checks.append('not_started_log_view_has_no_actual_Optimize')
    write(OUT/'qualification/finite_fixtures.json',dict(checks=checks,fixture_count=len(checks),Optimize=0,native_starts=0,
        source_seed0_readback_SHA=sha(source),no_artificial_proof_H_or_flag_in_formal=True,
        reused_R120_full_native_matrix_lifecycle_qualification=True,new_wiring_only=True,seconds=time.perf_counter()-tick))
    return checks
if __name__=='__main__':preflight() if sys.argv[1]=='preflight' else run()
