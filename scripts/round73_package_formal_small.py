"""Full small-panel audit and lossless artifacts; zero new Optimize calls."""
import csv
import gzip
import json
import math
from pathlib import Path
import time
import round73_native_evidence as evidence
from round73_qualify import ROOT, OUT as STAGE, sha, write
OUT=STAGE/'formal_small'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    frozen=read(OUT/'identity.json');summary=read(OUT/'summary.json')
    assert summary['completed']==6 and all(r['audit']['passed'] for r in summary['records'])
    assert sha(ROOT/'scripts/round73_formal_small.py')==frozen['driver_sha256']
    assert sha(evidence.__file__)==frozen['reader_sha256']
    assert sha(evidence.physical_module.__file__)==frozen['physical_sha256']
    assert sha(ROOT/'build/round73/v6/ExactEBRP.exe')==frozen['binary_sha256']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    manifest=[];checks=[]
    def archive(source,relative):
        target=OUT/'evidence'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        raw=source.read_bytes()
        if target.exists():assert gzip.decompress(target.read_bytes())==raw
        else:target.write_bytes(gzip.compress(raw,mtime=0))
        assert gzip.decompress(target.read_bytes())==raw
        manifest.append(dict(source=str(source.relative_to(ROOT)),artifact=str(target.relative_to(OUT)),
            source_sha256=sha(source),artifact_sha256=sha(target),raw_bytes=len(raw),bytes=target.stat().st_size))
    calls=0;witnesses=0;full_bounds=0;rejection_tests=0
    for launch,done in zip(frozen['launches'],summary['records']):
        folder=ROOT/launch['destination'];p=launch['panel']
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        records=read(folder/'observations.json')
        for record in records:
            path=folder/'journal'/f'event_{record["sequence"]}.commit'
            checked=evidence.receipt(path,record['first_observed_seconds'],launch['cap'])
            assert checked==record
        replay=evidence.audit(ROOT,p,records,frozen['binary_sha256'])
        assert all(replay[k]==done['audit'][k] for k in replay)
        original_calls=[r['payload'] for r in records if r['payload']['kind']=='call']
        for c in original_calls:
            log=Path(c['native_log_path'])
            native_count=log.read_text(encoding='utf-8',errors='replace').count('Optimize a model')
            assert native_count==1,(log,native_count)
            calls+=native_count
            if launch['arm']=='P-GRB':
                ref=frozen['references'][p['id']]
                assert sha(Path(c['model_path']))==ref['canonical_sha256']
        uncommitted=[f.name for f in (folder/'journal').glob('*.json') if not f.with_suffix('.commit').exists()]
        observed={f'event_{r["sequence"]}.commit' for r in records}
        unseen=[f.name for f in (folder/'journal').glob('*.commit') if f.name not in observed]
        # Extra post-kill files are retained but never promoted or backdated.
        if done['stop_reason']=='normal_return':assert not uncommitted and not unseen
        bad=folder/'journal/event_1.commit'
        try:evidence.receipt(bad,301,300)
        except AssertionError:rejection_tests+=1
        else:raise AssertionError('postcutoff read accepted')
        full=next((c for c in original_calls if c['full_original']),None)
        if full:
            try:evidence.replay_bound(full,replay['UB']+1,replay['witnesses'])
            except AssertionError:rejection_tests+=1
            else:raise AssertionError('contradictory full native bound accepted')
        for c in original_calls:
            if c['native_preconditions'] and not c['full_original']:
                # A prospective child or foreign leaf cannot strengthen the
                # complete frozen cover merely because its bound is large.
                malformed=dict(c,leaf='not_in_this_live_frontier')
                try:evidence.replay_bound(malformed,.01,replay['witnesses'])
                except AssertionError:rejection_tests+=1
                else:raise AssertionError('foreign active leaf accepted')
        checks.append(dict(number=launch['number'],id=p['id'],arm=launch['arm'],
            forced=launch['forced'],UB=replay['UB'],LB=replay['LB'],gap=replay['gap'],
            uncommitted_data=uncommitted,unseen_receipts=unseen,
            physical_witnesses=replay['physical_witnesses'],native_calls=len(original_calls),
            global_native_bound_events=replay['global_native_bound_events'],
            normal_certificate=done['audit'].get('normal_result_certificate',False),
            recovered_certificate=False,wall_seconds=done['wall_seconds'],endpoint=done['audit']['endpoint']))
        witnesses+=replay['physical_witnesses'];full_bounds+=replay['global_native_bound_events']
        for source in sorted(folder.rglob('*')):
            if source.is_file():archive(source,Path('diagnoses')/str(launch['number'])/(str(source.relative_to(folder))+'.gz'))
    for source in sorted((OUT/'reference').rglob('*')):
        if source.is_file():archive(source,Path('reference')/(str(source.relative_to(OUT/'reference'))+'.gz'))
    pairs=[]
    def compare(a,b):
        ea,eb=a['endpoint'],b['endpoint'];ta,tb=a['wall_seconds'],b['wall_seconds']
        out=dict(reference=a['arm'],candidate=b['arm'],time_delta=tb-ta,UB_delta=eb['U']-ea['U'],LB_delta=eb['L']-ea['L'],gap_delta=eb['gap']-ea['gap'])
        if ea['certificate'] and eb['certificate']:
            small=ta<60 and tb<60
            ma,mr=(2,.2) if small else (10,.15);sa,sr=(5,.5) if small else (30,.5)
            out.update(material_improvement=ta-tb>ma and (ta-tb)/ta>mr,
                       severe_regression=tb-ta>sa and (tb-ta)/ta>sr,classification='both_certified')
        elif not ea['certificate'] and not eb['certificate']:
            ga,gb=ea['gap'],eb['gap']
            out.update(material_improvement=ga-gb>.001 and (ga-gb)/max(ga,1e-30)>.1,
                       severe_regression=gb-ga>.01 and (gb-ga)/max(ga,1e-30)>.5,classification='both_open')
        else:
            out.update(material_improvement=None,severe_regression=None,
                       classification='certificate_gain' if eb['certificate'] else 'certificate_loss')
        return out
    for role in ['D3','D4']:
        arms={r['arm']:r for r in checks if r['id']==role}
        for a,b in [('P-GRB','DS-X'),('P-GRB','JDS-X'),('DS-X','JDS-X')]:
            pairs.append(dict(id=role,**compare(arms[a],arms[b])))
    write(OUT/'pairs.json',pairs)
    refs=sum(read(p)['wall_seconds'] for p in (OUT/'reference').glob('*/completion.json'))
    write(OUT/'checks.json',checks);write(OUT/'evidence_manifest.json',manifest)
    audit=dict(formal_runs=6,actual_optimize_calls=calls,physical_witnesses=witnesses,
        full_domain_native_bound_events=full_bounds,negative_replay_checks=rejection_tests,
        artifacts=len(manifest),raw_bytes=sum(r['raw_bytes'] for r in manifest),
        compressed_bytes=sum(r['bytes'] for r in manifest),
        reference_builds=1,reference_optimizer_calls=0,reference_wall_seconds=refs,
        wall_seconds=time.perf_counter()-started,all_checks_passed=True,script_sha256=sha(__file__))
    write(OUT/'audit.json',audit)
    prior=read(STAGE/'runtime_resource_summary.json')
    write(STAGE/'formal_resource_summary.json',dict(runtime_checkpoint=prior,
        formal_performance_launches=6,formal_optimize_calls=calls,
        formal_wall_seconds=summary['total_wall_seconds'],formal_reference_builds=1,
        formal_reference_optimizer_calls=0,formal_reference_wall_seconds=refs,
        formal_offline_replay_seconds=summary['offline_replay_seconds'],formal_package_seconds=audit['wall_seconds'],
        stage_complete=False))
    print(json.dumps(dict(audit=audit,pairs=pairs,checks=checks),indent=2))


if __name__=='__main__':main()
