"""Same-run observed checkpoints and final P/K1 comparisons; no optimization."""
import json
import time
from pathlib import Path
from round78_qualify import ROOT, sha, write
import round73_native_evidence as evidence
OUT=ROOT/'results/unified_exact_round78/campaign'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def campaign_summary():
    return read(OUT/'summary.json')


def gap_fields(endpoint):
    upper=endpoint['U'];gap=endpoint['gap']
    return dict(endpoint,relative_gap=gap/abs(upper) if upper is not None and upper!=0 else None)


def checkpoint(records,done,t):
    if done['wall_seconds']<=t and done['stop_reason']=='normal_return':
        return gap_fields(dict(done['audit']['endpoint'],available=True,
            paid_completion_seconds=done['wall_seconds'],source='normal_final_endpoint_available_by_checkpoint'))
    visible=[r['payload'] for r in records if r['effective_available_seconds']<=t]
    witnesses=[r['objective'] for r in visible if r['kind']=='witness']
    lower=max([0]+[r['global_bound'] for r in visible if r['kind']=='bound' and r['global_available']])
    if not witnesses:
        return gap_fields(dict(available=False,U=None,L=lower,gap=None,certificate=False,
                    source='no_committed_physical_UB_observed_by_checkpoint'))
    upper=min(witnesses);assert lower<=upper+1e-7
    return gap_fields(dict(available=True,U=upper,L=lower,gap=upper-lower,certificate=False,
                source='committed_physical_and_full_domain_evidence_only'))


def compare(a,b):
    if not a['available'] or not b['available']:
        return dict(classification='unavailable_physical_endpoint',material_improvement=None,severe_regression=None)
    out=dict(UB_delta=b['U']-a['U'],LB_delta=b['L']-a['L'],gap_delta=b['gap']-a['gap'],
        mixed_UB_LB_directions=(b['U']-a['U'])*(b['L']-a['L'])>0)
    if a['certificate']!=b['certificate']:
        return dict(out,classification='certificate_gain' if b['certificate'] else 'certificate_loss',
                    material_improvement=None,severe_regression=None)
    if not a['certificate']:
        ga,gb=a['gap'],b['gap'];assert ga>=-1e-7 and gb>=-1e-7
        return dict(out,classification='both_open',material_improvement=ga-gb>.001 and (ga-gb)/max(ga,1e-30)>.1,
                    material_regression=gb-ga>.001 and (gb-ga)/max(ga,1e-30)>.1,
                    severe_regression=gb-ga>.01 and (gb-ga)/max(ga,1e-30)>.5)
    ta,tb=a['paid_completion_seconds'],b['paid_completion_seconds']
    return dict(out,classification='both_certified_V50',wall_delta=tb-ta,
                material_improvement=ta-tb>10 and (ta-tb)/ta>.15,
                material_regression=tb-ta>10 and (tb-ta)/ta>.15,
                severe_regression=tb-ta>30 and (tb-ta)/ta>.5)


def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    assert not (OUT/'audit.json').exists(),'Do not replace a completed analysis'
    frozen=read(OUT/'identity.json');summary=campaign_summary()
    assert summary['completed']==3 and all(r['audit']['passed'] for r in summary['records'])
    assert sha(ROOT/'scripts/round78_research.py')==frozen['driver_sha256']
    assert sha(evidence.__file__)==frozen['reader_sha256']
    assert sha(evidence.physical_module.__file__)==frozen['physical_sha256']
    assert sha(ROOT/'build/round78/v1/ExactEBRP.exe')==frozen['binary_sha256']
    assert sha(ROOT/'results/unified_exact_round78/full_screen_plan.md')==frozen['plan_sha256']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    all_checkpoints=[];actual_calls=[];endpoint_checks=[];observation_coverage=[]
    for launch,done in zip(frozen['launches'],summary['records']):
        folder=ROOT/launch['destination'];records=read(folder/'observations.json')
        assert read(folder/'launch.json')==launch
        assert sha(ROOT/launch['panel']['instance_path'])==launch['panel']['input_sha256']
        for r in records:
            checked=evidence.receipt(folder/'journal'/f'event_{r["sequence"]}.commit',r['first_observed_seconds'],launch['cap'])
            assert checked==r
        if records:
            replay=evidence.audit(ROOT,launch['panel'],records,frozen['binary_sha256'])
            for k in ['UB','LB','native_calls_started','physical_witnesses']:assert replay[k]==done['audit'][k]
        else:
            assert done['audit']['endpoint']['source']=='normal_startup_deadline_physical_only'
            evidence.physical_module.ROOT=ROOT
            physical=evidence.physical_module.physical(launch['panel'],read(folder/'result.json'))
            assert physical['original_T_feasible'] and physical['F']==done['audit']['endpoint']['U']
        for r in records:
            c=r['payload']
            if c['kind']!='call':continue
            log=Path(c['native_log_path']);contents=log.read_text(encoding='utf-8',errors='replace')
            count=contents.count('Optimize a model')
            assert 'Gurobi Optimizer version 13.0.2' in contents
            assert count==1,(log,count)
            if launch['arm']=='P-GRB':
                assert sha(Path(c['model_path']))==frozen['references'][launch['panel']['id']]['canonical_sha256']
            actual_calls.append(dict(arm=launch['arm'],call=c['call'],model_sha256=c['model_sha256'],
                native_preconditions=c['native_preconditions'],log=str(log.relative_to(ROOT))))
        for t in [300,600,900,1200]:
            all_checkpoints.append(dict(arm=launch['arm'],seconds=t,**checkpoint(records,done,t)))
        endpoint=done['audit']['endpoint']
        if done['stop_reason']=='normal_return':
            physical=evidence.physical_module.physical(launch['panel'],read(folder/'result.json'))
            assert physical['original_T_feasible'] and abs(physical['F']-endpoint['U'])<1e-7
            assert done['audit']['LB']<=physical['F']+1e-7
            # Final extraction may obtain a witness beyond the last observed
            # callback. It can invalidate an older bound but cannot be backdated.
            if records:
                scopes={r['payload']['call']:r['payload'] for r in records if r['payload']['kind']=='call'}
                for r in records:
                    e=r['payload']
                    if e['kind']=='bound' and e['global_available']:
                        evidence.replay_bound(scopes[e['call']],e['native_bound'],replay['witnesses']+[physical])
        observed={f'event_{r["sequence"]}.commit' for r in records}
        observation_coverage.append(dict(arm=launch['arm'],
            uncommitted_data=[f.name for f in (folder/'journal').glob('*.json') if not f.with_suffix('.commit').exists()],
            unseen_receipts=[f.name for f in (folder/'journal').glob('*.commit') if f.name not in observed],
            policy='All raw files retained; unobserved or incomplete evidence never promoted or backdated.'))
        endpoint_checks.append(dict(arm=launch['arm'],wall_seconds=done['wall_seconds'],
            stop_reason=done['stop_reason'],**gap_fields(endpoint)))
    comparisons=[];protection=[]
    for t in [300,600,900,1200]:
        arms={r['arm']:r for r in all_checkpoints if r['seconds']==t}
        for a,b in [('P-GRB','BDS-C'),('P-GRB','K1-R'),('K1-R','BDS-C')]:
            comparisons.append(dict(seconds=t,reference=a,candidate=b,**compare(arms[a],arms[b])))
        p,k,j=arms['P-GRB'],arms['K1-R'],arms['BDS-C']
        fraction=None
        if all(v['available'] and not v['certificate'] for v in [p,k,j]):
            advantage=p['gap']-k['gap']
            if advantage>.001 and advantage/max(p['gap'],1e-30)>.1:
                fraction=(p['gap']-j['gap'])/advantage
        protection.append(dict(seconds=t,retained_K1_P_relative_gap_advantage=fraction,
            loss_of_most_advantage_at_this_checkpoint=fraction is not None and fraction<.5,
            scope='Descriptive exposed-role comparison, not a per-instance algorithm switch or historical-fastest veto'))
    write(OUT/'checkpoints.json',all_checkpoints);write(OUT/'comparisons.json',comparisons)
    write(OUT/'protection.json',protection);write(OUT/'actual_calls.json',actual_calls)
    write(OUT/'endpoint_checks.json',endpoint_checks)
    write(OUT/'observation_coverage.json',observation_coverage)
    audit=dict(all_checks_passed=True,completed=3,actual_optimize_calls=len(actual_calls),
        normal_returned_runs=sum(d['stop_reason']=='normal_return' for d in summary['records']),
        relative_gap_definition='(U-L)/abs(U) for an available nonzero U; otherwise null. Signed differences retained.',
        original_summary_sha256=sha(OUT/'summary.json'),
        wall_seconds=time.perf_counter()-started,optimizer_calls_in_this_audit=0,script_sha256=sha(__file__))
    write(OUT/'audit.json',audit)
    print(json.dumps(dict(audit=audit,endpoints=endpoint_checks,protection=protection),indent=2))


if __name__=='__main__':main()
