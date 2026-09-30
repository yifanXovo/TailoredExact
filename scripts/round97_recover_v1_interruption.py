"""Exact arm9 read-only evidence recovery; never repairs its failed raw audit.

Only complete root MIP bounds are admitted. Inherited LP/cover lower bounds
are not used. No Optimize, new solution, final result or certificate is made.
"""
import csv
import json
import math
import re
import time
from pathlib import Path
import round97_development_v2 as development
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext, scope, evidence, event_audit

CAMP = OUT/'development02'
RECOVERY = CAMP/'hard_stop09_recovery.json'


def recover():
    ext.ensure_idle()
    assert not RECOVERY.exists()
    started = time.perf_counter()
    development.qualified()
    identity = read(CAMP/'identity.json')
    launch = identity['launches'][8]
    assert (launch['number'], launch['id'], launch['arm']) == (9, 'V1', 'FEEDBACK')
    raw = Path(launch['destination'])
    assert raw.resolve() == (CAMP/'raw/09_V1_FEEDBACK').resolve()
    original = read(raw/'audit.json')
    assert original['passed'] is False and original['endpoint'] is None
    assert original['error'] == "AssertionError('call has no same-position optimize ledger row')"
    completion = read(raw/'completion.json')
    assert completion['stop_reason'] == 'whole_run_hard_stop'
    assert completion['within_cap'] and completion['returncode'] != 0
    assert not (raw/'result.json').exists()
    records = read(raw/'observations.json')
    assert len(records) == completion['committed_events'] == 108
    for r in records:
        assert evidence.receipt(raw/'journal'/f"event_{r['sequence']}.commit",
                                r['first_observed_seconds'], launch['cap_seconds']) == r
    with (raw/'external/paper_optimize_ledger.csv').open(newline='') as stream:
        assert list(csv.DictReader(stream)) == []

    # Matched OFF supplies only an independently audited *model identity*;
    # no OFF objective, time, bound, incumbent or final result is transplanted.
    off_launch = identity['launches'][7]
    off = Path(off_launch['destination'])
    assert read(off/'audit.json')['passed']
    assert read(off/'completion.json')['stop_reason'] == 'normal_return'
    off_records = read(off/'observations.json')
    scope.scope_receipt(off_launch, off_records)
    calls = [r['payload'] for r in records if r['payload']['kind'] == 'call']
    off_calls = [r['payload'] for r in off_records if r['payload']['kind'] == 'call']
    assert [c['call'] for c in calls] == [1, 2, 3, 4, 5]
    assert [c['native_preconditions'] for c in calls] == [0, 0, 0, 1, 1]
    expected_settings = dict(read_return_code=0, Threads=1, Seed=0, Presolve=-1,
        MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
    correspondence = []
    for c, o in zip(calls, off_calls, strict=True):
        for key in ('call','leaf','model_sha256','model_scope','lower_g','upper_g',
                    'cutoff','gmax','full_original','native_preconditions','settings'):
            assert c[key] == o[key], key
        assert c['settings'] == expected_settings
        assert c['full_original'] == 0
        assert c['model_scope'] == 'complete_original_compact_milp_intersected_with_static_gini_interval'
        assert sha(c['model_path']) == c['model_sha256'] == sha(o['model_path'])
        log = Path(c['native_log_path']).read_text(encoding='utf-8')
        assert 'Gurobi Optimizer version 13.0.2' in log
        shape = re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros', log)
        off_shape = re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',
                             Path(o['native_log_path']).read_text(encoding='utf-8'))
        assert shape and off_shape and shape.groups() == off_shape.groups()
        kind = 'LP_observed_only' if c['call'] <= 3 else 'complete_root_MIP'
        if c['call'] <= 3:
            assert 'Solved in ' in log and 'Optimal objective' in log
            assert 'integer (' not in log
        else:
            assert shape.groups() == ('30999','8787','192624')
            assert c['leaf'] == 'L0' and c['lower_g'] == 0 and c['upper_g'] == c['cutoff']
            assert '4463 continuous, 4324 integer (4024 binary)' in log
            setup = read(c['native_log_path']+'.round97.setup.json')
            assert setup['valid'] and setup['model_sha256'] == c['model_sha256']
            assert (setup['variables'], setup['rows'], setup['epoch']) == (8787,30999,0)
            # Different counters: journal counts LP+MIP; R97 setup counts MIP.
            assert setup['call'] == c['call']-3
        correspondence.append(dict(journal_call=c['call'],classification=kind,
            model_sha256=c['model_sha256'],native_log=c['native_log_path']))

    audited = evidence.audit(ROOT,launch['panel'],records,identity['candidate_binary_sha256'])
    assert (audited['native_calls_started'],audited['native_calls_returned']) == (5,4)
    root_calls = {c['call']:c for c in calls if c['call'] in (4,5)}
    startup = next(w for w in audited['witnesses'] if w['source']=='same_run_verified_startup')
    lower = 0.0
    independent_bounds = []
    for r in records:
        b = r['payload']
        if b['kind'] != 'bound':
            continue
        assert b['call'] in root_calls and b['global_available'] == 1 and b['inconsistent'] == 0
        c = root_calls[b['call']]
        assert startup['sequence'] < b['sequence'] and abs(startup['F']-c['cutoff']) < 1e-12
        assert math.isfinite(b['native_bound'])
        # F >= G: points outside G<=cutoff have F>=cutoff. Inside, the
        # unmodified complete root MILP supplies its own numerical native LB.
        value = min(c['cutoff'], max(0.0,b['native_bound']))
        assert value <= audited['UB']+1e-7
        lower = max(lower,value)
        independent_bounds.append(dict(sequence=b['sequence'],call=b['call'],
            available=r['effective_available_seconds'],native_bound=b['native_bound'],global_bound=value))
    assert len(independent_bounds) == 89 and abs(lower-audited['LB']) < 1e-12
    audited['LB'] = lower
    audited['gap'] = audited['UB']-lower
    evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,records,None,
                               completion['stop_reason'],launch['panel']['reference'])
    audited['round97'] = event_audit(launch)
    vectors = OUT/'development02_09_vectors.json'
    assert read(vectors)['passed'] and read(vectors)['optimizer_calls'] == 0
    rows = [json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(rows) == 9 and rows[-1]['audit_passed'] is False and rows[-1]['endpoint'] is None
    files = [p for p in raw.rglob('*') if p.is_file()]
    files += [CAMP/'identity.json',off/'audit.json',off/'completion.json',off/'observations.json',
              off/'external/paper_optimize_ledger.csv',vectors,Path(__file__).resolve(),
              CAMP/'queue_v1_after_d7/status.json',CAMP/'queue_v1_after_d7/events.jsonl']
    files += [ROOT/p for p in identity['source_hashes']]
    files += [ROOT/p for p in identity['helper_hashes']]
    files += [Path(c['model_path']) for c in off_calls]
    files += [Path(c['native_log_path']) for c in off_calls]
    files += [OUT/'production_v2_identity.json',ROOT/identity['prereg']['candidate_binary']]
    bindings = {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))}
    write(RECOVERY,dict(schema='round97-exact-arm9-root-bound-recovery-v1',number=9,
        passed=True,optimizer_calls=0,original_audit_preserved=True,
        original_summary_prefix=rows,source_bindings=bindings,completion=completion,
        audited=audited,endpoint=audited['endpoint'],scope_correspondence=correspondence,
        independent_root_bounds=independent_bounds,verified_complete_optimize_count=None,
        certificate_status='unobserved_interrupted',wall_seconds=time.perf_counter()-started,
        limitation='Separate independently recovered observational endpoint. Raw audit remains failed. No finalized result, certificate, complete Optimize count, total callback cost, or certification ordering is inferred. LP and inherited cover lower bounds excluded from recovered LB.'))
    print(json.dumps(dict(passed=True,endpoint=audited['endpoint'],vectors=len(read(vectors)['vectors']),optimizer_calls=0)))


def validate():
    recovery = read(RECOVERY)
    assert recovery['passed'] and recovery['original_audit_preserved'] and recovery['optimizer_calls']==0
    assert recovery['number']==9 and recovery['verified_complete_optimize_count'] is None
    for path, expected in recovery['source_bindings'].items():
        assert sha(ROOT/path)==expected,path
    rows=[json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert rows[:9]==recovery['original_summary_prefix']
    assert not (CAMP/'raw/09_V1_FEEDBACK/result.json').exists()
    return recovery


if __name__=='__main__':
    recover()
