def billed(name,first,last,label,qualification=False):
    tick,creation=process_origin();ensure_idle();production=check_identity();camp=OUT/name;identity=read(camp/'identity.json');b=budget()
    assert identity['source_hashes']==bindings() and identity['helpers']==helpers() and identity['runner_sha256']==sha(__file__)
    assert identity['prereg_sha256']==sha(identity['protocol_path']) and not b['unclosed']
    previous=records(camp);assert len(previous)==first-1 and all(r.get('qualified_offline_audit_passed',r['audit_passed']) for r in previous)
    children=last-first+1;nominal=sum(x['cap_seconds'] for x in identity['launches'][first-1:last]);remaining=full_remaining_reserve()
    assert b['remaining_starts']>=(children+1+remaining['starts'] if qualification else remaining['starts'])
    assert b['remaining_outer_seconds']>=remaining['nominal_seconds']+remaining['overhead_seconds']+(nominal+120 if qualification else 0)
    if qualification:assert b['qualification_starts']+children+1<=20 and b['qualification_seconds']+nominal+120<=2000
    else:
        gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
        assert gate['production_PE_SHA']==production['production_PE_SHA'] and gate['DLL_SHA']==DLL_SHA
        assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['campaign_identity_SHA']==sha(camp/'identity.json')
        assert gate['qualification_identity_SHA']==sha(OUT/'qualification/identity.json')
        assert len({x['group_number'] for x in identity['launches'][first-1:last]})==1
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[sys.executable,*sys.argv],
        cwd=str(ROOT),conservative_process_starts=children+1,declared_native_children=children,actual_wrapper_processes=1,
        cap_seconds=nominal+120,budget_before=b,all_remaining_fixed_reserve=remaining,wrapper_creation_unix=creation,
        qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,offline_projection=_projection_meta))
    for path in helpers():
        target=d/'source_snapshot'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
    (d/'source_snapshot/scripts/round110_cold26_resumed_campaign.py').write_bytes(_resume_source.read_bytes())
    (d/'source_snapshot/scripts/round110_cold_runtime.py').write_bytes(_cold_source.read_bytes())
    (d/'source_snapshot/scripts/round110_scoped_resumed_campaign.py').write_bytes(_scoped_prior_source.read_bytes())
    (d/'source_snapshot/scripts/round110_scoped_evidence.py').write_bytes(_scoped_source.read_bytes())
    (d/'source_snapshot/scripts/round110_resumed_campaign.py').write_bytes(_prior_source.read_bytes())
    (d/'source_snapshot/derived_billed.py').write_text(_derived_source,encoding='utf-8')
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0
    try:
        for number in range(first,last+1):
            arm_tick=(_resumed_admission_tick if number==first else time.perf_counter());check_identity();launch=identity['launches'][number-1]
            assert not Path(launch['destination']).exists() and sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            write(d/f'{number:02d}_before.json',dict(number=number,id=launch['id'],arm=launch['arm'],seed=launch['seed'],started_unix=time.time()))
            rec=supervised_run(launch,identity,arm_tick)
            same=[r for r in records(camp) if r['id']==launch['id'] and identity['launches'][r['number']-1]['seed']==launch['seed']]
            lower=[r['endpoint']['L'] for r in same];upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
            assert not upper or max(lower)<=min(upper)+1e-7,'offline contradictory cross-arm physical/native evidence'
            dest=Path(launch['destination']);seconds=time.perf_counter()-arm_tick
            write(dest/'whole_arm_receipt.json',dict(number=number,id=rec['id'],arm=rec['arm'],seed=launch['seed'],complete_seconds=seconds,
                completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
                includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True))
            write(d/f'{number:02d}_after.json',dict(completed_and_audited=True,whole_arm_receipt_SHA=sha(dest/'whole_arm_receipt.json')))
            assert seconds<=launch['cap_seconds'],'full arm exceeded frozen cap'
    except BaseException:
        code=1;(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,stop_reason='normal_return' if code==0 else 'actual_exception',
            conservative_process_starts=children+1,qualification=qualification,
            actual_native_children_with_launch=sum((Path(x['destination'])/'launch.json').exists() for x in identity['launches'][first-1:last]),
            nested_seconds_added=False,earlier_failure_slots_refunded=False))
        print(json.dumps(read(d/'receipt.json')),flush=True)
    if qualification:
        all_records=records(camp);assert len(all_records)==5;LP=[];MIP=[];starts=[]
        for record in all_records:
            dest=Path(record['destination']);observations=read(dest/'observations.json')
            assert all(r['payload']['settings']==seed_audit.expected(identity['launches'][record['number']-1]['seed']) for r in observations if r['payload']['kind']=='call')
            if record['arm']!='P-GRB':
                with (dest/'external/paper_optimize_ledger.csv').open(newline='') as f: rows=list(csv.DictReader(f))
                LP.append(any(x['solve_kind']=='LP' for x in rows));MIP.append(any(x['solve_kind']!='LP' for x in rows))
                starts.extend(str(p.relative_to(ROOT)) for p in (dest/'external/native_logs').glob('*.round68.start.json') if read(p).get('submitted'))
        assert all(LP) and all(MIP) and starts and any(r['endpoint']['certificate'] for r in all_records)
        write(OUT/'qualification/identity.json',dict(passed=True,production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,source_bindings=bindings(),
            current_CLI_records=all_records,qualified_argv=[x['command'] for x in identity['launches']],actual_seeds=[x['seed'] for x in identity['launches']],
            LP_reached=LP,MIP_reached=MIP,submitted_Starts=starts,legal_terminations=5,not_performance=True,
            parser_equivalence_receipt_SHA=sha(OUT/'qualification/parser_equivalence_receipt.json'),main_entry_receipt_SHA=sha(OUT/'qualification/main_entry_receipt.json'),
            qualification_campaign_identity_SHA=sha(camp/'identity.json')))
