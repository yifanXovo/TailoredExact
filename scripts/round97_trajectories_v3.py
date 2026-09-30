"""Conservative, audited evidence-availability trajectories for complete roles.

These curves show original physical witnesses and complete-domain native
bounds available to the observer. They do not backdate outer U updates,
feedback acceptance or final certificates. SHADOW-only candidates never enter.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import round86_native_evidence as evidence
import round97_outcome_evidence as outcomes
from round97_analyze_batch import ROOT, OUT, read, write, sha, ext


def table(path, rows):
    with path.open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def collect(launch, completed):
    raw=Path(launch['destination'])
    audit,receipt,result,extra_paths,recovered_bounds=outcomes.load(launch,completed)
    records=read(raw/'observations.json')
    assert len(records)==audit['committed_events']
    witnesses={w['sequence']:w for w in audit['witnesses']}
    calls={r['payload']['call']:r['payload'] for r in records if r['payload']['kind']=='call'}
    journal_paths=[]
    upper=None;lower=0.;previous_time=0.
    rows=[dict(process_seconds=0.,sequence=None,kind='analytical_nonnegative_objective_only',
               available_physical_U=None,available_global_native_L=0.,available_gap=None)]
    for sequence, record in enumerate(records,1):
        event=record['payload'];assert event['sequence']==sequence==record['sequence']
        commit=raw/'journal'/f'event_{sequence}.commit'
        assert evidence.receipt(commit,record['first_observed_seconds'],launch['cap_seconds'])==record
        journal_paths.extend([commit,commit.with_suffix('.json')])
        available=record['effective_available_seconds']
        assert available>=max(record['data_close_seconds'],record['first_observed_seconds'])
        assert available>=previous_time
        previous_time=available
        change=False
        if event['kind']=='witness':
            verified=witnesses[sequence]
            assert verified['original_T_feasible'] and verified['available']==available
            assert abs(verified['F']-event['objective'])<1e-7
            if upper is None or verified['F']<upper:
                upper=verified['F'];change=True
        elif event['kind']=='bound':
            assert not event['inconsistent']
            assert type(event['global_available']) in (int,bool)
            if event['global_available']:
                if recovered_bounds is not None:
                    verified=recovered_bounds[sequence]
                    assert verified['available']==available and verified['call']==event['call']
                    assert verified['native_bound']==event['native_bound']
                    bound=verified['global_bound']
                    assert bound==min(calls[event['call']]['cutoff'],max(0.,event['native_bound']))
                else:
                    bound=event['global_bound']
                    assert abs(evidence.replay_bound(calls[event['call']],event['native_bound'],audit['witnesses'])-bound)<1e-10
                assert math.isfinite(bound)
                if bound>lower:lower=bound;change=True
        if upper is not None:assert lower<=upper+1e-7
        if change:
            rows.append(dict(process_seconds=available,sequence=sequence,kind=event['kind'],
                available_physical_U=upper,available_global_native_L=lower,
                available_gap=None if upper is None else upper-lower))
    assert upper==audit['UB'] and lower==audit['LB']
    # The launcher did not record when it first read the finalized result.
    # Keep that endpoint outside the time series; process wall is cost, not
    # an invented first-observation/certificate timestamp.
    endpoint=audit['endpoint']
    common=[]
    cap=launch['cap_seconds']
    # Descriptive output checkpoints only; not algorithm triggers or budgets.
    for t in sorted({0,cap,*[s for s in [30,60,120,240,300,600,900,1200,1800,2400,3000,3600,5400,7200] if s<=cap]}):
        known=[r for r in rows if r['process_seconds']<=t]
        last=known[-1] if known else None
        common.append(dict(number=launch['number'],id=launch['id'],arm=launch['arm'],process_seconds=t,
            available_physical_U=None if last is None else last['available_physical_U'],
            available_global_native_L=0 if last is None else last['available_global_native_L'],
            available_gap=None if last is None else last['available_gap']))
    return rows,common,dict(process_wall_seconds=receipt['process_wall_seconds'],
        final_result_first_observed_seconds=None,committed_events=len(records),
        stop_reason=receipt['stop_reason'],normal_return=result is not None,
        original_raw_audit_passed=completed['audit_passed'],
        recovered_root_bounds_only=recovered_bounds is not None,
        certificate_status=outcomes.certificate_status(audit['endpoint'],result),
        changing_evidence_records=len(rows)-1,
        observer_delay_max_seconds=max((r['effective_available_seconds']-r['data_close_seconds'] for r in records),default=0),
        certificate_observed_in_audit=endpoint['certificate'],
        endpoint=dict(endpoint,certificate=endpoint['certificate'] if result is not None else None),
        endpoint_timing=('Untimed finalized result; process wall is cost, not first certificate availability.' if result is not None else 'Interrupted committed evidence already represented by journal records; no finalized result or certificate time.')),[raw/p for p in ['audit.json','completion.json','observations.json']]+([raw/'result.json'] if result is not None else [])+journal_paths+extra_paths


def main(batch,role,label):
    ext.ensure_idle()
    assert all(p and all(c.isalnum() or c in '_-' for c in p) for p in [batch,role,label])
    campaign=OUT/batch;identity=read(campaign/'identity.json')
    launches=[r for r in identity['launches'] if r['id']==role]
    completed=[json.loads(s) for s in (campaign/'summary.jsonl').read_text().splitlines()]
    selected=[r for r in completed if r['id']==role]
    assert launches and [(r['number'],r['id'],r['arm']) for r in launches]==[
        (r['number'],r['id'],r['arm']) for r in selected]
    assert len({r['cap_seconds'] for r in launches})==1
    destination=OUT/'trajectories'/label
    assert not destination.exists()
    data=[];checkpoints=[];facts=[]
    paths=[campaign/'identity.json',Path(__file__).resolve(),Path(outcomes.__file__).resolve(),ROOT/'scripts/round86_native_evidence.py']
    for launch,done in zip(launches,selected):
        rows,points,fact,bound_paths=collect(launch,done)
        data.append((launch,rows));checkpoints.extend(points)
        facts.append(dict(number=launch['number'],id=role,arm=launch['arm'],**fact));paths.extend(bound_paths)
    destination.mkdir(parents=True)
    for launch,rows in data:table(destination/f"{launch['number']:02d}_{launch['arm']}.csv",rows)
    table(destination/'common_checkpoints.csv',checkpoints)
    write(destination/'identity.json',dict(batch=batch,role=role,optimizer_calls=0,new_solver_starts=0,
        source_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in paths},facts=facts,
        scope='Audited evidence availability, not an outer-control-state reconstruction. Final reported endpoints remain separate.',
        caveats=['No SHADOW archive/checkpoint candidate contributes to these U curves.',
                 'Early LP/tree global bounds not in committed native evidence are omitted, so L can be conservative.',
                 'Native physical witnesses may be known before the outer algorithm updates its U.',
                 'No interpolation, retroactive candidate acceptance, invented certificate time, bound clipping or endpoint splicing.',
                 'Final results have no recorded first-observation timestamp and are excluded from the timed curves/checkpoints.',
                 'Exact acknowledged arm5 and independently recovered arm9 have no result; arm9 uses only separately validated root-MIP bounds, excluding inherited LP/cover bounds. Original failed audit is preserved and no certificate completion is inferred.',
                 'Post-return checkpoint fields retain evidence already available; they imply no further solver work.']))
    print(json.dumps(dict(batch=batch,role=role,arms=len(launches),destination=str(destination),optimizer_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('batch');parser.add_argument('role');parser.add_argument('label')
    args=parser.parse_args();main(args.batch,args.role,args.label)
