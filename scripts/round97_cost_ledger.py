"""Receipt-based R97 costs, including failures and zero-Optimize work.

Run idle into a fresh snapshot. Solver budget uses outer process wall only;
nested optimizer/callback costs, diagnostic children and queue waits are never
added to their parent wall a second time. Analysis views are not experiments.
"""
import argparse
import csv
import json
from pathlib import Path
from round97_analyze_batch import ROOT, OUT, read, write, sha, ext


def table(path,rows):
    if not rows:return
    with path.open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main(label):
    ext.ensure_idle()
    assert label and all(c.isalnum() or c in '_-' for c in label)
    target=OUT/'costs'/label;assert not target.exists()
    bindings={};solvers=[];unstarted=[];engineering=[];diagnostics=[];audits=[];queues=[];seen=set()
    def bind(path):bindings[Path(path).resolve().relative_to(ROOT).as_posix()]=sha(path)
    bind(Path(__file__))
    campaigns=[]
    for folder in sorted(OUT.iterdir()):
        identity_path=folder/'identity.json'
        if not folder.is_dir() or not identity_path.exists():continue
        identity=read(identity_path)
        if not identity.get('launches') or identity.get('analysis_only'):continue
        campaigns.append(folder);bind(identity_path)
        for launch in identity['launches']:
            raw=Path(launch['destination']).resolve()
            assert raw.is_relative_to(folder.resolve()) and raw not in seen
            seen.add(raw)
            completion=raw/'completion.json'
            if not completion.exists():
                assert not (raw/'process_start_marker.json').exists(), ('Started run without completion receipt',raw)
                unstarted.append(dict(batch=folder.name,number=launch['number'],id=launch['id'],arm=launch['arm'],
                    cap_seconds=launch['cap_seconds'],paid_seconds=0,
                    disposition='superseded_never_run' if folder.name=='qualification01' else 'registered_not_started'))
                continue
            done=read(completion);bind(completion)
            records=read(raw/'observations.json');bind(raw/'observations.json')
            audit=read(raw/'audit.json');bind(raw/'audit.json')
            calls=[r['payload']['call'] for r in records if r['payload']['kind']=='call']
            returned=[r['payload']['call'] for r in records if r['payload']['kind']=='returned']
            assert len(calls)==len(set(calls)) and set(returned)<=set(calls)
            count_complete=audit['passed'] and done['stop_reason']=='normal_return' and (raw/'result.json').exists()
            if audit['passed']:
                assert audit['native_calls_started']==len(calls) and audit['native_calls_returned']==len(returned)
            if count_complete:
                result=read(raw/'result.json');bind(raw/'result.json')
                count=result['gurobi_optimize_count'] if launch['arm']=='P-GRB' else result['external_gini_tree_optimize_count']
                assert count==len(calls)==len(returned)
            solvers.append(dict(batch=folder.name,number=launch['number'],id=launch['id'],arm=launch['arm'],
                operator=launch.get('operator','r83'),cap_seconds=launch['cap_seconds'],
                process_wall_seconds=done['process_wall_seconds'],
                supervised_end_to_end_seconds=done['fully_observed_end_to_end_seconds'],
                prelaunch_seconds=done['prelaunch_seconds'],postexit_drain_seconds=done['postexit_drain_and_restore_seconds'],
                returncode=done['returncode'],stop_reason=done['stop_reason'],audit_passed=audit['passed'],
                observed_native_call_scopes=len(calls),native_calls_returned=len(returned),
                optimize_count_complete=count_complete,
                verified_optimize_count=len(calls) if count_complete else None,
                offline_audit_seconds=audit['offline_audit_seconds'],
                administrative_annotation='Stopped for no-op feedback confound; actual OS stop reason retained.' if folder.name=='qualification01' else '',
                destination=raw.relative_to(ROOT).as_posix()))
    wrappers={}
    for folder in campaigns:
        for events_path in sorted(folder.glob('*queue*/events.jsonl')):
            events=[json.loads(s) for s in events_path.read_text().splitlines()]
            bind(events_path)
            for event in events:
                if event['phase']=='actual_model_vectors_passed':
                    path=OUT/event['audit_path'];assert sha(path)==event['audit_sha256']
                    assert path.name not in wrappers
                    wrappers[path.name]=event['wrapper_seconds']
            queues.append(dict(path=events_path.parent.relative_to(ROOT).as_posix(),
                final_phase=events[-1]['phase'],first_unix=events[0]['unix'],last_unix=events[-1]['unix'],
                wall_span_seconds=events[-1]['unix']-events[0]['unix'],
                added_to_totals=False,reason='Encloses already counted solvers/audits or waiting on an existing solver.'))
    for path in sorted((OUT/'engineering').glob('*/receipt.json')):
        receipt=read(path);bind(path);bind(path.parent/'launch.json')
        assert receipt['optimizer_calls']==0
        engineering.append(dict(label=path.parent.name,exit_code=receipt['exit_code'],
            wall_seconds=receipt['wall_seconds'],optimizer_calls=0,
            is_micro_process=path.parent.name.startswith('micro') or path.parent.name.startswith('revision02_micro_')))
    for path in sorted((OUT/'native_order_replay').glob('*.completion.json')):
        receipt=read(path);audit_path=path.with_name(path.name.replace('.completion.json','.audit.json'))
        audit=read(audit_path);bind(path);bind(audit_path)
        assert receipt['optimizer_calls']==0 and audit['receipt']==receipt
        diagnostics.append(dict(id=receipt['id'],exit_code=receipt['exit_code'],stop_reason=receipt['stop_reason'],
            child_process_seconds=receipt['wall_seconds'],wrapper_seconds=audit['wrapper_seconds_before_write'],
            optimizer_calls=0,passed=audit['passed'],child_cost_nested=True))
    for path in sorted(OUT.glob('*vectors*.json')):
        receipt=read(path)
        if 'vectors' not in receipt or 'wall_seconds' not in receipt:continue
        bind(path);assert receipt['optimizer_calls']==0
        amount=wrappers.get(path.name,receipt['wall_seconds'])
        assert amount>=receipt['wall_seconds']
        audits.append(dict(path=path.relative_to(ROOT).as_posix(),passed=receipt['passed'],
            vectors=len(receipt['vectors']),optimizer_calls=0,body_seconds=receipt['wall_seconds'],
            counted_seconds=amount,measured_scope='queue_wrapper' if path.name in wrappers else 'audit_body_only'))
    # The old failed queue never reached another solver. Its repair check is
    # a separately measured, zero-Optimize command, not its overlapping wait.
    failure_path=OUT/'development01/continuation_queue/failure_receipt.json'
    failures=[];repair_seconds=0.
    if failure_path.exists():
        failure=read(failure_path);bind(failure_path)
        assert failure['additional_solver_starts']==failure['optimizer_calls']==0
        repair_seconds=failure['repair_status_test']['command_wall_seconds']
        failures.append(dict(path=failure_path.relative_to(ROOT).as_posix(),receipt=failure))
    total_process=sum(r['process_wall_seconds'] for r in solvers)
    total_supervised=sum(r['supervised_end_to_end_seconds'] for r in solvers)
    non_solver=(sum(r['offline_audit_seconds'] for r in solvers)+sum(r['wall_seconds'] for r in engineering)+
                sum(r['wrapper_seconds'] for r in diagnostics)+sum(r['counted_seconds'] for r in audits)+repair_seconds)
    target.mkdir(parents=True)
    for name,rows in [('solver_arms',solvers),('unstarted',unstarted),('engineering',engineering),
                      ('offline_diagnostics',diagnostics),('vector_audits',audits),('queues',queues)]:table(target/(name+'.csv'),rows)
    write(target/'identity.json',dict(schema='round97-receipted-cost-ledger-v1',source_bindings=bindings,
        solver_starts=len(solvers),solver_process_seconds=total_process,
        solver_supervised_end_to_end_seconds=total_supervised,
        observed_native_call_scopes=sum(r['observed_native_call_scopes'] for r in solvers),
        verified_completed_native_optimize_calls=sum(r['verified_optimize_count'] or 0 for r in solvers),
        failed_arm_observed_native_call_scopes=sum(r['observed_native_call_scopes'] for r in solvers if not r['optimize_count_complete']),
        all_optimize_counts_complete=all(r['optimize_count_complete'] for r in solvers),
        native_calls_returned=sum(r['native_calls_returned'] for r in solvers),
        zero_optimize_diagnostic_starts=len(diagnostics),zero_optimize_micro_starts=sum(r['is_micro_process'] for r in engineering),
        experimental_starts_including_micro_and_diagnostics=len(solvers)+len(diagnostics)+sum(r['is_micro_process'] for r in engineering),
        engineering_command_count=len(engineering),non_solver_receipted_seconds=non_solver,
        measured_disjoint_seconds=total_supervised+non_solver,failures=failures,
        accounting=['80000s solver budget uses outer solver process seconds, including every failed arm.',
                    'Native Optimize counts and callback/closure/map times are nested, not extra wall.',
                    'Failed-arm journal call scopes are observed counts only; a failed audit does not establish exact complete Optimize accounting.',
                    'Diagnostic child wall is nested inside its measured per-case wrapper.',
                    'Queue spans overlap counted solvers/audits/waits and are not added.',
                    'Analysis projections and inherited R96 times are not new experiments.',
                    'Audit-body-only receipts omit unrecorded launcher overhead; measured_disjoint_seconds is not a claim of complete host wall accounting.',
                    'Builds and preparation commands are listed separately from experimental solver/micro/diagnostic starts.']))
    print(json.dumps(dict(solver_starts=len(solvers),solver_process_seconds=total_process,
                         observed_native_call_scopes=sum(r['observed_native_call_scopes'] for r in solvers),destination=str(target))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('label');main(parser.parse_args().label)
