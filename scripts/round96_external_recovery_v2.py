"""Offline hard-stop recovery and only the two untouched H6 commands.

Never fabricate flushed optimize rows or a normal finalization. The frozen
NEJ1 journal is the primary receipt for an interrupted call; all normal runs
still use the original strict CSV-backed auditor.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path
import round96_external as base
from round96_prepare import ROOT, OUT, read, write, sha, evidence

CAMP = OUT/'external_v2'
ORIGINAL_AUDITOR = base.scope.audit_adapter(base.r90)

def interrupted(launch, observations, completion, identity):
    dest = Path(launch['destination'])
    assert completion['stop_reason'] == 'whole_run_hard_stop'
    assert completion['within_cap'] and not (dest/'result.json').exists()
    assert launch['arm'] in {'ENS-C', 'LP-G'} and launch['id'] == 'H6'
    assert completion['process_wall_seconds'] >= launch['hard_stop_seconds']
    assert sha(ROOT/base.BIN) == identity['candidate_binary_sha256'] == base.SHA
    # Confirm what a true native_preconditions flag means in the exact source
    # bound to the executable. Do not infer MIP scope from filenames alone.
    frozen = subprocess.check_output(['git','show',identity['source_ref']+':src/GurobiBaseline.cpp'],cwd=ROOT)
    assert b'out.model_fingerprint_matches_request && !out.lp_relaxation' in frozen
    assert b'request.variable_bound_overrides.empty() && request.round60_fixed_inventory.empty()' in frozen
    assert b'request.additional_linear_rows.empty()' in frozen
    calls=[]; lp=[]; mip=[]; logs=[]
    global_ids={r['payload']['call'] for r in observations
                if r['payload']['kind']=='bound' and base.scope.flag(r['payload']['global_available'])}
    returned={r['payload']['call'] for r in observations if r['payload']['kind']=='returned'}
    for position,row in enumerate(observations,1):
        checked=evidence.receipt(dest/'journal'/f'event_{position}.commit',
                                 row['first_observed_seconds'],launch['cap_seconds'])
        assert checked==row, 'Saved observation differs from hashed committed bytes'
        event=row['payload']
        if event['kind']!='call': continue
        calls.append(event)
        assert event['call']==len(calls) and event['settings']==base.scope.SETTINGS
        assert not base.scope.flag(event['full_original'])
        pre=base.scope.flag(event['native_preconditions'])
        path=Path(event['native_log_path']); text=path.read_text()
        assert path.is_relative_to(dest/'external/native_logs')
        assert 'Gurobi Optimizer version 13.0.2' in text and 'using up to 1 threads' in text
        if pre:
            assert ' integer (' in text
            mip.append(event['call'])
        else:
            assert path.name.endswith('_lp.gurobi.log') and 'Optimal objective' in text
            assert event['call'] in returned and event['call'] not in global_ids
            lp.append(event['call'])
        logs.append(dict(call=event['call'],path=path.relative_to(ROOT).as_posix(),sha256=sha(path)))
    assert calls and set(global_ids)<=set(mip)
    # This recovery is only for an interrupted final MIP with all prior calls
    # returned. Lost CSV is retained, never rewritten or treated as complete.
    assert returned==set(range(1,len(calls))) and calls[-1]['call'] in mip
    ledger_path,rows=base.scope.ledger_rows(dest)
    assert len(rows)<=len(calls)
    for i,row in enumerate(rows):
        assert row['leaf_id']==calls[i]['leaf'] and row['model_sha256']==calls[i]['model_sha256']
        assert (row['solve_kind']=='LP') == (i+1 in lp)
    audited=evidence.audit(ROOT,launch['panel'],observations,identity['candidate_binary_sha256'])
    evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,observations,None,
                               completion['stop_reason'],{})
    audited['native_scope_adapter']=dict(native_calls=len(calls),lp_calls=lp,mip_calls=mip,
        global_bound_call_ids=sorted(global_ids),settings=base.scope.SETTINGS,
        provenance='hashed NEJ1 calls, exact-source precondition contract, native logs and model SHA replay',
        ledger_sha256=sha(ledger_path),flushed_optimize_rows=len(rows),native_logs=logs,
        frozen_source_ref=identity['source_ref'])
    audited['lp_g_split_evidence']=base.r90.lp_g_split_evidence(launch,None,completion['stop_reason'])
    audited.update(passed=True,administrative_hard_stop=True,
        recovery_scope='Committed observational endpoint only. No finalization, full ledger, certificate or normal return inferred.')
    return audited

def auditor(launch,observations,completion,identity):
    if completion['stop_reason']=='whole_run_hard_stop' and launch['arm']!='P-GRB':
        return interrupted(launch,observations,completion,identity)
    return ORIGINAL_AUDITOR(launch,observations,completion,identity)

def records():
    return [json.loads(line) for line in (CAMP/'summary.jsonl').read_text().splitlines()]

def audit_record(row):
    return read(ROOT/row['audit_path'] if 'audit_path' in row else Path(row['destination'])/'audit.json')

def crosscheck(items,launch):
    same=[r for r in items if r['id']==launch['id']]; lowers=[]; uppers=[]
    for row in same:
        a=audit_record(row); assert a['passed']
        lowers.extend([a['LB'],row['endpoint']['L']]); uppers.extend(w['F'] for w in a['witnesses'])
        if a.get('final_physical_verification'): uppers.append(a['final_physical_verification']['F'])
    assert not uppers or max(lowers)<=min(uppers)+1e-7
    write(CAMP/f'cross_arm_H6_{len(same)}.json',dict(passed=True,strongest_L=max(lowers),
        best_physical_U=min(uppers) if uppers else None,scope='Offline consistency only, never merged certificate'))
    if len(same)==3:
        write(CAMP/'decision_signals_H6.json',dict(signals=base.r94.severe_signals(items,'H6'),
            action='Retain hard stop separately; no rerun or extension'))

def recover():
    base.ensure_idle(); identity=read(base.CAMP/'identity.json')
    assert identity['bindings']==base.source_bindings() and not CAMP.exists()
    prefix=base.completed(); assert len(prefix)==16
    assert all(r['audit_passed'] for r in prefix[:15]) and not prefix[-1]['audit_passed']
    launch=identity['launches'][15]; dest=Path(launch['destination']); tick=time.perf_counter()
    result=interrupted(launch,read(dest/'observations.json'),read(dest/'completion.json'),identity)
    result['offline_audit_seconds']=time.perf_counter()-tick
    write(dest/'audit_v2.json',result); CAMP.mkdir()
    new=dict(identity,original_identity_sha256=sha(base.CAMP/'identity.json'),adapter_sha256=sha(__file__),
        preserved_failed_summary_sha256=sha(base.CAMP/'summary.jsonl'))
    write(CAMP/'identity.json',new)
    prefix[-1]=dict(prefix[-1],audit_passed=True,audit_error=None,endpoint=result['endpoint'],
        split_evidence=result['lp_g_split_evidence'],audit_path=(dest/'audit_v2.json').relative_to(ROOT).as_posix(),
        recovered_without_optimize=True,administrative_hard_stop=True,original_failed_audit_sha256=sha(dest/'audit.json'))
    with (CAMP/'summary.jsonl').open('x',encoding='utf-8') as stream:
        for row in prefix: stream.write(json.dumps(row)+'\n')
    crosscheck(prefix,launch)
    write(CAMP/'admission.json',dict(passed=True,identity_sha256=sha(CAMP/'identity.json'),
        adapter_sha256=sha(__file__),optimizer_calls=0,paid_restarts=0,remaining_numbers=[17,18],
        scope='Original two untouched H6 commands, identities, order and caps; no paid prefix restart'))
    print(json.dumps(dict(endpoint=result['endpoint'],calls=result['native_scope_adapter']['native_calls'],
                          witnesses=result['physical_witnesses'],returned=result['native_calls_returned'])))

def run(number):
    base.ensure_idle(); identity=read(CAMP/'identity.json'); gate=read(CAMP/'admission.json')
    assert gate['passed'] and gate['identity_sha256']==sha(CAMP/'identity.json')
    assert gate['adapter_sha256']==identity['adapter_sha256']==sha(__file__)
    assert identity['bindings']==base.source_bindings()
    assert identity['original_identity_sha256']==sha(base.CAMP/'identity.json')
    assert sha(ROOT/base.BIN)==base.SHA
    prefix=records(); assert number in [17,18] and len(prefix)==number-1 and all(r['audit_passed'] for r in prefix)
    launch=identity['launches'][number-1]; assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    base.r90.CAMPAIGN=CAMP; base.r90.audit_launch=auditor
    prereg=dict(common=base.COMMON,candidate_binary=base.BIN,candidate_binary_sha256=base.SHA)
    row=base.r90.run_one(launch,prereg,identity); prefix.append(row); crosscheck(prefix,launch)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['recover','run']);p.add_argument('--number',type=int)
    a=p.parse_args(); recover() if a.action=='recover' else run(a.number)
