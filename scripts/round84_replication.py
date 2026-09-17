"""One same-build U6 repetition, preserving both realizations; no optimization."""
import json
import time
from round84_analyze import ROOT, OUT, read, compare, sha, write, cross_run_consistency
from round81_replication import validate_pair, endpoint


def main():
    started=time.perf_counter()
    assert not (OUT/'active_run.lock').exists()
    assert not (OUT/'replication_audit.json').exists(), 'Never replace completed evidence'
    for name in ['audit.json','mechanism_audit.json']:
        assert read(OUT/name)['all_checks_passed']
    protocol=read(OUT.parent/'protocol.json')
    prior=ROOT/'results/unified_exact_round83/campaign'
    assert sha(prior/'identity.json')==protocol['prior_U6_campaign_identity_sha256']
    assert sha(prior/'endpoint_checks.json')==protocol['prior_U6_endpoints_sha256']
    assert read(prior/'audit.json')['all_checks_passed']
    assert read(prior/'mechanism_audit.json')['all_checks_passed']
    current=read(OUT/'identity.json');previous=read(prior/'identity.json')
    assert current['source']==previous['source']
    for field in ['qualification_sha256','reader_sha256','physical_sha256','exchange_replay_sha256']:
        assert current[field]==previous[field],field
    summary=read(OUT/'summary.json');old_summary=read(prior/'summary.json')
    assert summary['completed']==9 and old_summary['completed']==13
    fresh_points=read(OUT/'checkpoints.json');old_points=read(prior/'checkpoints.json')
    repeated=[];points=[];paired=[];consistency_records=[];old_ends={};new_ends={}
    arms=['P-GRB','ENS-C','K1-R']
    for arm in arms:
        launch=next(l for l in current['launches'] if l['panel']['id']=='U6' and l['arm']==arm)
        old_launch=next(l for l in previous['launches'] if l['panel']['id']=='U6' and l['arm']==arm)
        validate_pair(launch,old_launch,current,previous,True)
        assert launch['cap']==3600 and launch['hard_stop_seconds']==old_launch['hard_stop_seconds']
        assert launch['forced']==old_launch['forced']==False
        for launch_row in [launch,old_launch]:
            affinity=read(ROOT/launch_row['destination']/'affinity.json')
            assert affinity['child']['process_mask']==4
        done=next(r for r in summary['records'] if r['id']=='U6' and r['arm']==arm)
        old_done=next(r for r in old_summary['records'] if r['id']=='U6' and r['arm']==arm)
        old_end=endpoint(old_done);new_end=endpoint(done)
        old_ends[arm]=old_end;new_ends[arm]=new_end
        repeated.append(dict(id='U6',arm=arm,prior_stage=83,current_stage=84,cap=3600,
            prior=old_end,current=new_end,change_between_realizations=compare(old_end,new_end,50),
            identical_source_binary_input_cap_flags=True,
            scope='One fresh repeat; both original outcomes retained. No best-repeat selection or statistical-equivalence claim.'))
        for stage,row in [(83,old_end),(84,new_end)]:
            consistency_records.append(dict(id='U6',arm=arm,origin=stage,**row))
        for t in [300,600,1200,1800,2400,3600]:
            old=next(r for r in old_points if r['id']=='U6' and r['arm']==arm and r['seconds']==t)
            new=next(r for r in fresh_points if r['id']=='U6' and r['arm']==arm and r['seconds']==t)
            points.append(dict(id='U6',arm=arm,seconds=t,prior=old,current=new,
                descriptive_change=compare(old,new,50)))
            consistency_records.extend([dict(old,origin=83),dict(new,origin=84)])
    for a,b in [('P-GRB','ENS-C'),('P-GRB','K1-R'),('K1-R','ENS-C')]:
        paired.append(dict(id='U6',seconds=3600,reference=a,candidate=b,
            prior_comparison=compare(old_ends[a],old_ends[b],50),
            current_comparison=compare(new_ends[a],new_ends[b],50)))
        for t in [300,600,1200,1800,2400]:
            pair={arm:next(r for r in points if r['arm']==arm and r['seconds']==t) for arm in [a,b]}
            paired.append(dict(id='U6',seconds=t,reference=a,candidate=b,
                prior_comparison=compare(pair[a]['prior'],pair[b]['prior'],50),
                current_comparison=compare(pair[a]['current'],pair[b]['current'],50)))
    assert len(repeated)==3 and len(points)==18 and len(paired)==18
    consistency=cross_run_consistency(consistency_records)
    write(OUT/'replication.json',dict(realizations=repeated,checkpoints=points,matched_pair_comparisons=paired,
        scope='Every pair uses controls from its own realization. D6/D7 earlier R78-build long results are historical background, not this same-build repeat.'))
    write(OUT/'repeat_bound_consistency.json',consistency)
    audit=dict(all_checks_passed=True,identical_cap_repeated_arms=3,matched_checkpoint_rows=18,
        matched_pair_comparisons=18,cross_run_consistency_roles=len(consistency),
        prior_bound_hashes={name:sha(prior/name) for name in ['identity.json','endpoint_checks.json','summary.json','checkpoints.json','audit.json']},
        optimizer_calls=0,wall_seconds=time.perf_counter()-started,script_sha256=sha(__file__),
        helper_sha256=sha(ROOT/'scripts/round81_replication.py'),
        scope='Descriptive finite replication only, without backdating missing U, time interpolation or choosing a preferred realization.')
    write(OUT/'replication_audit.json',audit)
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
