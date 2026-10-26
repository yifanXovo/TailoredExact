"""Retain every replication and distinguish D7 cross-cap consistency; zero optimization."""
import json
import time
from pathlib import Path
from round81_analyze import ROOT, OUT, read, compare, gap_fields, sha, write, cross_run_consistency

PRIOR_HASHES={'78': {'identity.json': 'e6f5cadb69c66415a252bf659e012b52b46824cdf1d2d0e911710e8827aed9db', 'summary.json': '4e33fec175f4dd761051c7a5aa83d15b4aa95d0e5200948e89eb02983cc95bdf', 'audit.json': 'f1356ef606f6faf9fb4ce8577714a9fbc5d6c62cccc215ede04991028063cc5e', 'checkpoints.json': '6a3ea8fc728c5b80461db7594dad934e08140a09faa199a274484bb7c41339fa'}, '79': {'identity.json': 'd8caccb4f0b609e2de764803a8dc2747a8087ee566a32b528df05aa67392cd39', 'summary.json': '48d55aeac1be0ea68a4d491224a41fd48dac3fd9bbe5d8691a17ce06a24bbb27', 'audit.json': '5ee7ed35da11bc38935b71d07959f1b5f5e0e54c33f06c79c497b9b6735d4297', 'checkpoints.json': 'c6587388a8cb37eed0b18e306b19f4d5e3e48b7930d016ddeeb3863f593cc9d7'}, '80': {'identity.json': 'cf0f15e2e2741714e5f606c987b3cc3e37ade54cc7635cffd08fdd8f8d014841', 'summary.json': 'd60cfd881a9816ec110d467d46d1a91bc023aeab0e0e033a4f996372908c5bf3', 'audit.json': '722f7a023224a254b87a89eff4ecac52e6cab0043e7164cf6a4ee057fb9a40b2', 'checkpoints.json': '56bb4ecfb3c7298312aa82f99e6d1894e08319d5829d646aab1094f9f17fdcd7'}}


def option(command,name):
    if name not in command:return None
    i=command.index(name)
    return True if i+1==len(command) or command[i+1].startswith('--') else command[i+1]


def endpoint(done):
    assert done['audit']['passed']
    return gap_fields(dict(done['audit']['endpoint'],available=True,paid_completion_seconds=done['wall_seconds']))


def validate_pair(current,previous,new_identity,old_identity,identical_cap):
    assert new_identity['binary_sha256']==old_identity['binary_sha256']
    assert new_identity['source_commit']==old_identity['source_commit']
    assert current['arm']==previous['arm']
    for key in ['instance_path','input_sha256']:
        assert current['panel'][key]==previous['panel'][key],key
    for key in ['V','M','Q','T_seconds','pickup_seconds','drop_seconds','lambda']:
        assert float(current['panel'][key])==float(previous['panel'][key]),key
    flags=['--method','--threads','--mip-threads','--gurobi-seed','--gurobi-presolve',
        '--round61-candidate-mode','--algorithm-preset','--round65-witness-audit','--round65-hga-zero-stop','--plain-baseline']
    if identical_cap:
        assert current['cap']==previous['cap']
        flags+=['--time-limit','--process-wall-time-limit','--process-shutdown-margin']
    for flag in flags:assert option(current['command'],flag)==option(previous['command'],flag),flag


def main():
    started=time.perf_counter()
    assert not (OUT/'active_run.lock').exists()
    assert not (OUT/'replication_audit.json').exists(), 'Never overwrite a completed comparison'
    assert read(OUT/'audit.json')['all_checks_passed'] and read(OUT/'mechanism_audit.json')['all_checks_passed']
    current=read(OUT/'identity.json');summary=read(OUT/'summary.json')
    assert summary['completed']==14
    prior={}
    for stage,hashes in PRIOR_HASHES.items():
        folder=ROOT/f'results/unified_exact_round{stage}/campaign'
        for name,digest in hashes.items():assert sha(folder/name)==digest,(stage,name)
        assert read(folder/'audit.json')['all_checks_passed']
        prior[int(stage)]={name:read(folder/name) for name in ['identity.json','summary.json','checkpoints.json']}
    repeated=[];paired=[];consistency_records=[]
    for identity in ['S12','C2','D4','D6']:
        stage=80 if identity=='D6' else 79
        old=prior[stage];old_id=old['identity.json'];old_s=old['summary.json']
        fresh={};earlier={};V=None
        for launch in [l for l in current['launches'] if l['panel']['id']==identity]:
            arm=launch['arm'];V=int(launch['panel']['V'])
            previous=next(l for l in old_id['launches'] if l['panel']['id']==identity and l['arm']==arm)
            validate_pair(launch,previous,current,old_id,True)
            done=next(r for r in summary['records'] if r['id']==identity and r['arm']==arm)
            old_done=next(r for r in old_s['records'] if r['id']==identity and r['arm']==arm)
            fresh[arm]=endpoint(done);earlier[arm]=endpoint(old_done)
            consistency_records.extend([dict(id=identity,arm=arm,origin=stage,**earlier[arm]),
                dict(id=identity,arm=arm,origin=81,**fresh[arm])])
            repeated.append(dict(id=identity,arm=arm,prior_stage=stage,cap=launch['cap'],prior=earlier[arm],current=fresh[arm],
                change_between_realizations=compare(earlier[arm],fresh[arm],V),
                identical_source_binary_input_cap_flags=True,
                scope='Both original and one fresh repeat retained. Frozen practical comparisons are descriptive, not statistical equivalence.'))
        pairs=[('P-GRB','BDS-C')]
        if 'K1-R' in fresh:pairs += [('P-GRB','K1-R'),('K1-R','BDS-C')]
        for a,b in pairs:
            old_c=compare(earlier[a],earlier[b],V);new_c=compare(fresh[a],fresh[b],V)
            paired.append(dict(id=identity,reference=a,candidate=b,prior_stage=stage,prior_comparison=old_c,current_comparison=new_c,
                scope='Each comparison uses its own matched fresh controls; no historical K1 row is imported into the R81 D6 pair.'))
    assert len(repeated)==11
    old=prior[78];old_id=old['identity.json']
    assert all(l['panel']['id']=='D7' and l['cap']==1200 for l in old_id['launches'])
    now_points=read(OUT/'checkpoints.json');cross=[]
    for launch in [l for l in current['launches'] if l['panel']['id']=='D7']:
        previous=next(l for l in old_id['launches'] if l['arm']==launch['arm'])
        assert launch['cap']==3600
        validate_pair(launch,previous,current,old_id,False)
        for stage,source in [(78,old['summary.json']),(81,summary)]:
            done=next(r for r in source['records'] if r['arm']==launch['arm'] and r.get('id','D7')=='D7')
            consistency_records.append(dict(id='D7',arm=launch['arm'],origin=stage,**endpoint(done)))
        for t in [300,600,1200]:
            old_point=next(r for r in old['checkpoints.json'] if r['arm']==launch['arm'] and r['seconds']==t)
            new_point=next(r for r in now_points if r['id']=='D7' and r['arm']==launch['arm'] and r['seconds']==t)
            cross.append(dict(id='D7',arm=launch['arm'],seconds=t,prior_cap=1200,current_cap=3600,
                prior=old_point,current=new_point,descriptive_change=compare(old_point,new_point,50),
                scope='Fresh longer-cap consistency only. Native defaults may respond to the different global deadline; not identical-cap or independent-checkpoint replication.'))
    consistency=cross_run_consistency(consistency_records)
    write(OUT/'replication.json',dict(realizations=repeated,matched_pair_comparisons=paired))
    write(OUT/'long_window_consistency.json',cross)
    write(OUT/'repeat_bound_consistency.json',consistency)
    audit=dict(all_checks_passed=True,identical_cap_repeated_arms=len(repeated),cross_cap_checkpoint_rows=len(cross),
        cross_run_consistency_roles=len(consistency),
        prior_hashes=PRIOR_HASHES,optimizer_calls=0,wall_seconds=time.perf_counter()-started,script_sha256=sha(__file__),
        scope='Preserve every original/repeated endpoint and all signs; no best-repeat selection, added seed, historical control import or statistical-equivalence claim.')
    write(OUT/'replication_audit.json',audit);print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
