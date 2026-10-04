"""One specifically bounded, read-only recovery of confirmation arm 6.

Never repairs the killed process's CSV or summary. Native NEJ1 receipts remain
the evidence; typed logs and frozen source qualify the missing call-type rows.
Import launches nothing and uses no native solver.
"""
import json,re,time
import round101_campaign as campaign
from round101_common import *
from round100_idle import ensure_idle

RECOVERY=OUT/'recovery06'
CAMP=OUT/'confirmation01'

def frozen(q):
    assert q['runner_sha256']==sha(campaign.__file__)
    assert q['source_hashes']==bindings() and q['helpers']==campaign.helpers()
    assert sha(ROOT/q['prereg']['candidate_binary'])==q['candidate_binary_sha256']
    assert sha(q['input_manifest'])==q['prereg_sha256']
    assert sha('D:/gurobi1302/win64/bin/gurobi130.dll')==q['dll_sha256']
    assert sha(BUILD/'Round65ReferenceBuild.exe')==q['reference_binary_sha256']

def original_records():
    return [json.loads(x) for x in (CAMP/'summary.jsonl').read_text().splitlines()]

def verify_preserved():
    m=read(RECOVERY/'preserved_manifest.json')
    for p,h in m['files'].items():assert sha(ROOT/p)==h,p
    # Appending the three never-started rows must preserve the six raw rows.
    prefix=(CAMP/'summary.jsonl').read_bytes().splitlines(keepends=True)[:6]
    import hashlib
    assert hashlib.sha256(b''.join(prefix)).hexdigest()==m['original_summary_prefix_sha256']
    for p,h in read(RECOVERY/'identity.json')['derived_files'].items():assert sha(RECOVERY/p)==h

def records_view(camp):
    records=[json.loads(x) for x in (Path(camp)/'summary.jsonl').read_text().splitlines()]
    if Path(camp).resolve()==CAMP.resolve():
        verify_preserved();r=read(RECOVERY/'record_overlay.json')
        assert records[5]['audit_passed'] is False and records[5]['endpoint'] is None
        records[5]=r
    return records

def audit_view(destination):
    d=Path(destination)
    if d.resolve()==Path(read(CAMP/'identity.json')['launches'][5]['destination']).resolve():
        verify_preserved();return read(RECOVERY/'audit.json')
    return read(d/'audit.json')

def recover():
    ensure_idle();start=time.perf_counter();q=read(CAMP/'identity.json');frozen(q)
    rows=original_records();assert len(rows)==6 and all(r['audit_passed'] for r in rows[:5])
    old=rows[5];launch=q['launches'][5];d=Path(launch['destination'])
    assert (launch['number'],launch['id'],launch['arm'])==(6,'C101-V30','ENS-C')
    assert old['audit_passed'] is False and old['endpoint'] is None
    failed=read(d/'audit.json')
    assert failed['error']=="AssertionError('call has no same-position optimize ledger row')"
    completion=read(d/'completion.json')
    assert completion==old['completion'] and completion['stop_reason']=='whole_run_hard_stop'
    assert completion['within_cap'] and completion['committed_events']==368
    assert completion['end_to_end_seconds']<=launch['cap_seconds'] and not (d/'result.json').exists()
    actual=read(d/'launch.json');assert all(actual[k]==v for k,v in launch.items())
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    observations=read(d/'observations.json')
    assert len(observations)==368
    for row in observations:
        checked=campaign.r90.evidence.receipt(d/'journal'/f'event_{row["sequence"]}.commit',
            row['first_observed_seconds'],launch['cap_seconds'])
        assert checked==row,'durable receipt/observation mismatch'
    calls=[r['payload'] for r in observations if r['payload']['kind']=='call']
    returned=[r['payload']['call'] for r in observations if r['payload']['kind']=='returned']
    global_ids=sorted({r['payload']['call'] for r in observations
        if r['payload']['kind']=='bound' and campaign.scope.flag(r['payload']['global_available'])})
    assert len(calls)==5 and returned==[1,2,3,4] and global_ids==[4,5]
    ledger_path,ledger=campaign.scope.ledger_rows(d);assert ledger==[]
    kinds=['LP','LP','LP','CHILD_BOUND_TARGET_MIP','MIP'];details=[]
    for number,(call,kind) in enumerate(zip(calls,kinds),1):
        assert call['call']==number and call['settings']==campaign.scope.SETTINGS
        assert not campaign.scope.flag(call['full_original'])
        assert campaign.scope.flag(call['native_preconditions'])==(number>=4)
        assert call['model_scope']=='complete_original_compact_milp_intersected_with_static_gini_interval'
        model=Path(call['model_path']);log=Path(call['native_log_path'])
        assert model.parent.resolve()==(d/'external/models').resolve()
        assert log.parent.resolve()==(d/'external/native_logs').resolve()
        assert sha(model)==call['model_sha256']
        lp=model.read_text();sections=lp.split('\nGenerals\n');assert len(sections)==2
        generals,tail=sections[1].split('\nBinaries\n');binaries,end=tail.split('\nEnd\n')
        g=generals.split();b=binaries.split();assert len(g)==300 and len(b)==4000 and not end.strip()
        native=log.read_text();assert 'Gurobi Optimizer version 13.0.2' in native
        dims=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',native)
        assert dims;matrix=tuple(map(int,dims.groups()))
        fp=re.search(r'Model fingerprint: (0x[0-9a-f]+)',native).group(1)
        if number<=3:
            assert 'Variable types:' not in native and 'Optimal objective' in native
            assert re.search(r'Solved in \d+ iterations',native) and 'Root relaxation:' not in native
            assert number not in global_ids
        else:
            assert matrix==(30949,8739,192326) and fp=='0x0ebb8401'
            assert 'Variable types: 4439 continuous, 4300 integer (4000 binary)' in native
            assert call['model_sha256']==calls[0]['model_sha256']
        details.append(dict(call=number,qualified_solve_kind=kind,returned=number in returned,
            call_sequence=call['sequence'],model_sha256=sha(model),native_log_sha256=sha(log),
            native_log_path=log.relative_to(ROOT).as_posix(),matrix=matrix,fingerprint=fp,
            exported_general_count=len(g),exported_binary_count=len(b)))
    # These are frozen source dispatch sites, not retrospective solver statuses.
    source=(ROOT/'src/GurobiBaseline.cpp').read_text()
    for fragment in ['!out.lp_relaxation','request.variable_bound_overrides.empty()',
        'request.round60_fixed_inventory.empty()','request.additional_linear_rows.empty()',
        'options_.round63_time_mode=="off"','options_.round65_projection=="off"']:
        assert fragment in source,fragment
    source=(ROOT/'src/PaperExternalGiniTree.cpp').read_text()
    assert 'CHILD_BOUND_TARGET_MIP' in source and 'L0_terminal_mip' not in source
    assert '_terminal_mip.gurobi.log' in source
    audited=campaign.r90.evidence.audit(ROOT,launch['panel'],observations,q['candidate_binary_sha256'])
    campaign.r90.evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,
        observations,None,completion['stop_reason'],launch['panel']['reference'])
    scope=dict(schema='round101-specific-poststop-scope-recovery-v1',arm=launch['arm'],
        native_calls=5,lp_calls=[1,2,3],mip_calls=[4,5],global_bound_call_ids=global_ids,
        ledger_sha256=sha(ledger_path),settings=campaign.scope.SETTINGS,all_flags_strictly_decoded=True,
        qualification='NEJ1 call identity + actual typed model SHA + native log type + frozen source dispatch',
        calls=details,missing_csv_rows_not_recreated=True)
    audited.update(native_scope_adapter=scope,passed=True,offline_audit_seconds=time.perf_counter()-start,
        recovery_limitation='Committed interrupted endpoint only; no native final result, work, nodes or certificate reconstructed.')
    assert not audited['endpoint']['certificate']
    lower=max([audited['endpoint']['L']]+[r['endpoint']['L'] for r in rows[3:5]])
    upper=min([audited['endpoint']['U']]+[r['endpoint']['U'] for r in rows[3:5]])
    assert lower<=upper+1e-7
    RECOVERY.mkdir(exist_ok=False)
    manifest={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(d.rglob('*')) if p.is_file()}
    write(RECOVERY/'preserved_manifest.json',dict(files=manifest,original_summary_prefix_sha256=sha(CAMP/'summary.jsonl'),
        immutable_failed_record=old,original_identity_sha256=sha(CAMP/'identity.json')))
    write(RECOVERY/'audit.json',audited)
    write(RECOVERY/'record_overlay.json',dict(old,audit_passed=True,endpoint=audited['endpoint'],audit_error=None,
        recovery_audit_path=(RECOVERY/'audit.json').relative_to(ROOT).as_posix(),
        original_audit_failed=True,original_record_preserved=True))
    write(RECOVERY/'identity.json',dict(schema='round101-read-only-recovery06-v1',optimizer_calls=0,
        new_native_processes=0,original_identity_sha256=sha(CAMP/'identity.json'),
        reader_sha256=sha(__file__),source_bindings=q['source_hashes'],
        derived_files={n:sha(RECOVERY/n) for n in ['audit.json','record_overlay.json','preserved_manifest.json']},
        original_failure_preserved=True,cross_arm_lower=lower,cross_arm_upper=upper,passed=True))
    print(json.dumps(dict(passed=True,Optimize=0,endpoint=audited['endpoint'],native_calls=5,returned=4)))

if __name__=='__main__':recover()
