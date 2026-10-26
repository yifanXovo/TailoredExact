"""R100 clock rules with explicit Round101 poststop recovery and censoring."""
import csv,sys,math
from round101_common import *
from round101_recover_scope import records_view,audit_view
import round86_native_evidence as evidence
CHECKPOINTS=[300,600,900,1200,1800,3600,5400,7200]
def save(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main(label,campaigns):
    target=OUT/label;target.mkdir(exist_ok=False);runs=[];known={};checkpoint_rows=[];timings=[]
    for name in campaigns:
        q=read(OUT/name/'identity.json')
        done=records_view(OUT/name)
        assert len(done)==len(q['launches']) and all(r['audit_passed'] for r in done)
        for r in done:
            a=q['launches'][r['number']-1];d=Path(a['destination']);audit=audit_view(d)
            result=read(d/'result.json') if r['completion']['stop_reason']=='normal_return' else {}
            obs=read(d/'observations.json');c=r['completion'];ep=r['endpoint']
            assert audit['passed'] and c['stop_reason'] in ['normal_return','whole_run_hard_stop']
            if not result:assert not ep['certificate'] and not (d/'result.json').exists()
            runs.append((name,q,a,d,audit,result,obs,c,ep))
            if ep['certificate']:
                h=a['panel']['input_sha256']
                if h in known:assert abs(known[h]-ep['U'])<=1e-7
                known[h]=ep['U']
    for name,q,a,d,audit,result,obs,c,ep in runs:
        base=dict(campaign=name,number=a['number'],role=a['id'],arm=a['arm'])
        pre=c['prelaunch_seconds'];end=c['end_to_end_seconds'];process_end=c['process_wall_seconds']
        for cp in CHECKPOINTS:
            if cp>a['cap_seconds']:continue
            if end<=cp:
                if ep['certificate']:point={k:ep[k] for k in ['U','L','gap','certificate']};covered=True;source='same_run_certificate_completed_before_checkpoint'
                else:point=dict(U=None,L=None,gap=None,certificate=False);covered=False;source='unproved_censored_exit_before_checkpoint; endpoint retained separately, no interpolation'
            else:
                prefix=[v for v in obs if v['effective_available_seconds']+pre<=cp]
                verified=evidence.audit(ROOT,a['panel'],prefix,q['candidate_binary_sha256'])
                point=dict(U=verified['UB'],L=verified['LB'],gap=verified['gap'],certificate=False)
                covered=True;source='same_run_committed_scope_verified_prefix_only'
            checkpoint_rows.append(dict(base,checkpoint_full_seconds=cp,covered=covered,**point,
                relative_gap=point['gap']/max(abs(point['U']),1e-12) if point['U'] is not None and point['gap'] is not None else None,
                actual_full_exit_seconds=end,source=source,observations_sha256=sha(d/'observations.json')))
        star=known.get(a['panel']['input_sha256']);qualified=[w for w in audit.get('witnesses',[]) if star is not None and abs(w['F']-star)<=1e-7]
        # These bound journal publication/receipt milestones, not the earlier
        # engine discovery or physical verification instant. Application zero
        # follows process launch by an unknown nonnegative offset.
        by_sequence={v['sequence']:v for v in obs}
        find_lower=min((by_sequence[w['sequence']]['data_close_seconds']+pre for w in qualified),default=None)
        find_upper=min((w['available']+pre for w in qualified),default=None)
        if find_lower is not None:assert find_lower<=find_upper<=end+1e-7
        safe_find_lower=pre if find_upper is not None else None
        cert_upper=end if ep['certificate'] else None
        app_snapshot=result.get('final_process_wall_time_seconds')
        cert_lower=pre+app_snapshot if ep['certificate'] and app_snapshot is not None else None
        if cert_lower is not None:assert cert_lower<=cert_upper+1e-6
        phases=[]
        if (d/'phases.csv').exists():
            with (d/'phases.csv').open(newline='',encoding='utf-8') as f:phases=list(csv.DictReader(f))
        phase_key='process_seconds' if phases and 'process_seconds' in phases[0] else None
        def phase_time(phase):
            matches=[p for p in phases if p.get('event')==phase]
            return float(matches[-1][phase_key]) if matches and phase_key else None
        serialize_start=phase_time('final_result_serialization_start');serialize_end=phase_time('final_result_serialization_complete')
        app_exit=phase_time('process_exit')
        timings.append(dict(base,certificate=ep['certificate'],reliable_numerical_Fstar=star,
            t_find_full_safe_lower_seconds=safe_find_lower,t_find_full_observation_upper_seconds=find_upper,
            journal_publication_full_conservative_lower_seconds=find_lower,
            journal_receipt_full_observation_upper_seconds=find_upper,
            t_cert_full_completion_conservative_lower_seconds=cert_lower,t_cert_full_completion_observation_upper_seconds=cert_upper,
            complete_certification_time_seconds=cert_upper,observed_full_exit_seconds=end,observed_process_exit_seconds=process_end,
            stop_reason=c['stop_reason'],normal_result_available=bool(result),
            application_clock_final_snapshot_seconds=app_snapshot,
            t_tail_safe_lower_seconds=max(0.,cert_lower-find_upper) if cert_lower is not None and find_upper is not None else None,
            t_tail_safe_upper_seconds=cert_upper-safe_find_lower if cert_upper is not None and safe_find_lower is not None else None,
            post_publication_to_full_completion_lower_seconds=max(0.,cert_lower-find_upper) if cert_lower is not None and find_upper is not None else None,
            post_publication_to_full_completion_upper_seconds=cert_upper-find_lower if cert_upper is not None and find_lower is not None else None,
            unproved_observed_post_find_seconds=end-find_upper if not ep['certificate'] and find_upper is not None else None,
            serialization_seconds=serialize_end-serialize_start if serialize_start is not None and serialize_end is not None else None,
            recorded_app_closing_seconds=app_exit-serialize_start if app_exit is not None and serialize_start is not None else None,
            wrapper_postexit_seconds=c['postexit_drain_and_restore_seconds'],
            offline_validation_seconds=audit.get('offline_audit_seconds'),
            exact_engine_certificate_instant=None,exact_engine_find_instant=None,
            scope='full completion includes admission, launch/input/model/search/native verification/normal close; t_find safe interval only process launch to first qualified observation; journal publication/receipt and app final snapshot bound milestones, not earlier native discovery/certificate; narrow post-publication window is not engine proof tail; exact engine instants unknown; offline independent audit separately engineering'))
    save(target/'checkpoints.csv',checkpoint_rows);save(target/'discovery_certification.csv',timings)
    write(target/'summary.json',dict(optimizer_calls=0,runs=len(runs),checkpoint_records=len(checkpoint_rows),
        covered_scope_verified_checkpoints=sum(r['covered'] for r in checkpoint_rows),
        uncovered_checkpoint_records=sum(not r['covered'] for r in checkpoint_rows),
        scripts_sha256=sha(__file__),clock_contract='original R99 full-completion boundary retained; no interpolation or native Runtime substitution'))
    print(json.dumps(dict(passed=True,runs=len(runs),checkpoints=len(checkpoint_rows),Optimize=0)))
if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
