"""Preserve the paid F5/ON run; repair only legacy readback arm dispatch.

The R94 parameter reader accepts ENS-C/LP-G labels. ORDER-ON uses that same
native backend contract, but must retain its separate preset and trace checks.
No changed solver command, binary, model, tolerance, cap, input or Start.
"""
import argparse
import json
import time
from pathlib import Path
import round96_primal as base
from round96_prepare import ROOT,OUT,read,write,sha,evidence

CAMP=OUT/'primal_v2'

def auditor():
    old=base.scope.audit_adapter(base.r90)
    def audit(launch,observations,completion,identity):
        if launch['arm']!='ORDER-ON':return old(launch,observations,completion,identity)
        checked=base.scope.scope_receipt(launch,observations)
        normal=completion['stop_reason']=='normal_return'
        result=read(Path(launch['destination'])/'result.json') if normal else None
        if normal:assert result['algorithm_preset']=='research-round96-ensc-route-order'
        audited=evidence.audit(ROOT,launch['panel'],observations,identity['candidate_binary_sha256'])
        evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,observations,result,completion['stop_reason'],{})
        if normal:
            # Label dispatch only. Same five readbacks and all return codes;
            # nine native settings and LP/MIP scope are checked above.
            audited['five_native_parameter_readback']=base.scope.v2.parameter_readback(
                result,require_call=checked['native_calls']>0,arm='ENS-C')
            audited['route_order']=base.order_trace(launch,observations,result)
        audited.update(native_scope_adapter=checked,passed=True,lp_g_split_evidence=None,
            readback_dispatch=dict(actual_arm='ORDER-ON',native_contract='ENS-C',
                actual_preset_checked=True if normal else None,adapter_sha256=sha(__file__)))
        return audited
    return audit

def records():
    return [json.loads(line) for line in (CAMP/'summary.jsonl').read_text().splitlines()]

def audited_record(row):
    return read(ROOT/row['audit_path']) if 'audit_path' in row else read(Path(row['destination'])/'audit.json')

def crosscheck(items,launch):
    same=[r for r in items if r['id']==launch['id']];lower=[];upper=[]
    for row in same:
        audit=audited_record(row);assert audit['passed']
        lower.append(max(audit['LB'],row['endpoint']['L']))
        upper.extend(w['F'] for w in audit['witnesses'])
        if audit.get('final_physical_verification'):upper.append(audit['final_physical_verification']['F'])
    offline=[];known=read(OUT/'fixed_route_cases.json');panel=launch['panel']
    for ref in known['offline_references']:
        original=next(c['panel'] for c in known['cases'] if c['role']==ref['role'])
        if all(original[key]==panel[key] for key in ['input_sha256','T_seconds','pickup_seconds','drop_seconds','lambda']):
            path=ROOT/ref['witness_path'];assert sha(path)==ref['witness_sha256']
            checked=evidence.physical_module.physical(panel,read(path));assert checked['original_T_feasible']
            offline.append(dict(path=ref['witness_path'],F=checked['F']));upper.append(checked['F'])
    assert not upper or max(lower)<=min(upper)+1e-7
    write(CAMP/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(passed=True,strongest_L=max(lower),
        best_physical_U=min(upper) if upper else None,offline_known_witnesses=offline,
        scope='Offline contradiction check only; never merged certificate or Start'))
    if len(same)==3:
        adapted=[dict(r,arm='LP-G' if r['arm']=='ORDER-ON' else r['arm']) for r in same]
        write(CAMP/f'decision_signals_{launch["id"]}.json',dict(candidate='ORDER-ON',
            signals=base.external.r94.severe_signals(adapted,launch['id']),
            action='Keep outcomes and planned tests; no algorithm-specific fallback'))

def recover():
    base.idle();base.build_identity();original=read(base.CAMP/'identity.json')
    assert original['bindings']==base.bindings() and not CAMP.exists()
    prefix=[json.loads(line) for line in (base.CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(prefix)==3 and [r['audit_passed'] for r in prefix]==[True,True,False]
    launch=original['launches'][2];dest=Path(launch['destination']);completion=read(dest/'completion.json')
    assert launch['arm']=='ORDER-ON' and completion['returncode']==0 and completion['within_cap']
    start=time.perf_counter()
    recovered=auditor()(launch,read(dest/'observations.json'),completion,original)
    recovered['offline_audit_seconds']=time.perf_counter()-start
    recovered['recovery_scope']='Offline replay of the original paid process. Legacy arm-label assertion corrected; no Optimize or changed numerical check.'
    write(dest/'audit_v2.json',recovered)
    CAMP.mkdir()
    identity=dict(original,runner_sha256=sha(__file__),base_runner_sha256=original['runner_sha256'],
        original_identity_sha256=sha(base.CAMP/'identity.json'),adapter_sha256=sha(__file__),
        preserved_failure={name:sha(dest/name) for name in ['audit.json','observations.json','completion.json','result.json','launch.json']})
    write(CAMP/'identity.json',identity)
    prefix[2]=dict(prefix[2],audit_passed=True,endpoint=recovered['endpoint'],audit_error=None,
        audit_path=(dest/'audit_v2.json').relative_to(ROOT).as_posix(),recovered_without_optimize=True,
        original_failed_audit_sha256=sha(dest/'audit.json'))
    with (CAMP/'summary.jsonl').open('x',encoding='utf-8') as stream:
        for row in prefix:stream.write(json.dumps(row)+'\n')
    crosscheck(prefix,launch)
    write(CAMP/'admission.json',dict(passed=True,identity_sha256=sha(CAMP/'identity.json'),
        recovered_audit_sha256=sha(dest/'audit_v2.json'),adapter_sha256=sha(__file__),
        optimizer_calls=0,paid_restarts=0,remaining_starts=9,
        scope='Only the next never-started primal number >=4 may run; original inputs, binary, commands, order and caps retained.'))
    print(json.dumps(dict(recovered=prefix[2],route_order=recovered['route_order'])))

def run(number):
    base.idle();base.build_identity();identity=read(CAMP/'identity.json');gate=read(CAMP/'admission.json')
    assert gate['passed'] and gate['identity_sha256']==sha(CAMP/'identity.json')
    assert identity['adapter_sha256']==gate['adapter_sha256']==sha(__file__)
    assert identity['bindings']==base.bindings()
    assert identity['original_identity_sha256']==sha(base.CAMP/'identity.json')
    prefix=records();assert number>=4 and len(prefix)==number-1 and all(r['audit_passed'] for r in prefix)
    launch=identity['launches'][number-1];assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    base.r90.CAMPAIGN=CAMP;base.r90.audit_launch=auditor()
    result=base.r90.run_one(launch,identity['prereg'],identity);prefix.append(result)
    crosscheck(prefix,launch)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['recover','run']);parser.add_argument('--number',type=int)
    args=parser.parse_args()
    if args.action=='recover':recover()
    else:
        assert args.number and 4<=args.number<=12;run(args.number)
