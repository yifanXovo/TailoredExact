"""Read-only frozen old-raw replay. A fresh process per finite observation."""
from round111_common import *
import cProfile, collections, inspect, pstats
import round109_seed_audit as old
import round108_reader as core
import round100_campaign as campaign
import round90_lp_g_g3 as supervisor

def sample(number,qualification=False):
    plan=read(OUT/'replay_plan.json')
    return next(s for s in plan['samples'] if s['number']==number and (s['campaign']!='campaign')==qualification)

def profile_contract(measure):
    source=inspect.getsource(core.model_contract)
    source=source.replace('    m=lp_model(path);t=m[\'types\'];names=m[\'order\'];quantities=[n for n in names if n.startswith((\'p_\',\'d_\'))]',
        "    _t=time.perf_counter();m=lp_model(path);measure['model_read_parse']+=time.perf_counter()-_t\n    _t=time.perf_counter();t=m['types'];names=m['order'];quantities=[n for n in names if n.startswith(('p_','d_'))]")
    source=source.replace("    counter=collections.Counter(m['rows']);a=evidence.instance(root,p);link_count=0",
        "    measure['column_type_classification']+=time.perf_counter()-_t\n    _t=time.perf_counter();counter=collections.Counter(m['rows']);measure['duplicate_row_Counter']+=time.perf_counter()-_t\n    _t=time.perf_counter();a=evidence.instance(root,p);measure['input_read_parse']+=time.perf_counter()-_t;link_count=0")
    source=source.replace("            terms={n:1. for n in quantities if n.endswith('_'+str(i))}",
        "            _t=time.perf_counter();terms={n:1. for n in quantities if n.endswith('_'+str(i))}")
    source=source.replace("            assert selectors", "            measure['per_station_column_classification']+=time.perf_counter()-_t\n            _t=time.perf_counter();assert selectors")
    source=source.replace('            link_count+=2',"            link_count+=2;measure['frozen_A_B_checks']+=time.perf_counter()-_t")
    namespace=dict(vars(core),time=time,measure=measure)
    exec(compile(source,__file__+'::instrumented_unchanged_contract','exec'),namespace)
    return namespace['model_contract'],source

def replay(kind,number,label,qualification=False):
    s=sample(number,qualification);launch=s['launch'];d=Path(launch['destination'])
    out=OUT/'qualification/replays'/label;out.mkdir(parents=True,exist_ok=False)
    entry=time.perf_counter();check_identity();entry_seconds=time.perf_counter()-entry
    postexit_tick=time.perf_counter()
    identity=read(OLD_ROOT/s['identity_path']);records=read(d/'observations.json');completion=read(d/'completion.json')
    # Only necessary adapter output is redirected; frozen input bytes are read-only.
    old.ROOT=campaign.ROOT=supervisor.ROOT=OLD_ROOT
    saved_write=old.write
    old.write=lambda path,value:write(out/'computed_seed_scope.json',value)
    measure=collections.defaultdict(float);saved_contract=core.model_contract;saved_scope=core.model_scope_contract
    profiler=cProfile.Profile() if kind=='old-profile' else None
    if profiler:
        core.model_contract,source=profile_contract(measure)
        (out/'instrumented_contract.py').write_text(source,encoding='utf-8')
        def scope(*args):
            t=time.perf_counter()
            try:return saved_scope(*args)
            finally:measure['scope_check_including_Counter']+=time.perf_counter()-t
        core.model_scope_contract=scope
    error=None;result=None;tick=time.perf_counter()
    try:
        if profiler:profiler.enable()
        if kind=='new':
            import round111_seed_audit as new
            result=new.adapter(launch,records,completion,identity)
        else:result=old.adapter(launch,records,completion,identity)
    except Exception as exc:error=repr(exc)
    finally:
        if profiler:profiler.disable()
        adapter_seconds=time.perf_counter()-tick
        old.write=saved_write;core.model_contract=saved_contract;core.model_scope_contract=saved_scope
    post=time.perf_counter()
    if result is not None:write(out/'audit.json',result)
    else:write(out/'rejection.json',dict(error=error))
    # Required same-group crosscheck, receipt write and own audit-output writes
    # are included in this engineering envelope, never used to requalify R110.
    if result is not None:
        assert result['passed'] and result['endpoint']['L']<=result['endpoint']['U']+1e-7
    write(out/'postexit_output_receipt.json',dict(adapter_seconds=adapter_seconds,audit_passed=error is None,
        historical_native_clocks_unchanged=True))
    postexit_seconds=time.perf_counter()-postexit_tick
    compare=None
    if result is not None:
        baseline=read(d/'audit.json');baseline.pop('offline_audit_seconds',None)
        current=read(out/'audit.json')
        if 'neutral_exchange' in baseline:
            baseline['neutral_exchange'].pop('offline_seconds')
            current['neutral_exchange'].pop('offline_seconds')
        equal=current==baseline
        compare=dict(exact_recursive_equal=equal,excluded=read(OUT/'replay_plan.json')['equivalence_whitelist'],
            baseline_SHA=sha(d/'audit.json'),current_SHA=sha(out/'audit.json'))
    if profiler:
        profiler.dump_stats(str(out/'profile.pstats'))
        with (out/'profile.txt').open('w',encoding='utf-8') as f:pstats.Stats(profiler,stream=f).sort_stats('cumulative').print_stats(70)
    write(out/'receipt.json',dict(kind=kind,number=number,qualification_fixture=qualification,
        necessary_admission_identity_seconds=entry_seconds,adapter_seconds=adapter_seconds,
        necessary_postexit_seconds=postexit_seconds,phases=dict(measure),
        phases_are_nested_do_not_sum=True,error=error,comparison=compare,
        output_metadata_cost_included=True,old_raw_read_only=True,Optimize=0,
        engineer_replay_does_not_change_old_whole_clock_or_eligibility=True,
        optimized_phase_metrics=(new.last_metrics if kind=='new' else None)))
    print(json.dumps(read(out/'receipt.json')),flush=True)
    assert error is None,error
    assert equal,'decisive or unknown audit output changed'

if __name__=='__main__':replay(sys.argv[1],int(sys.argv[2]),sys.argv[3],'--qualification' in sys.argv[4:])
