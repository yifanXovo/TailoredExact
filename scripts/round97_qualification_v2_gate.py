"""Create an evidence-bound real v2 gate, only after all three arms/audits.

Zero Optimize. This is functional qualification, never complete-performance
acceptance. Missing evidence fails closed without retrying any paid arm.
"""
import json
from pathlib import Path
import round97_campaign_v2 as campaign
from round97_campaign_v2 import ROOT, OUT, read, write, sha

CAMP=OUT/'qualification03'


def main():
    campaign.ext.ensure_idle()
    assert not (CAMP/'gate.json').exists()
    identity=read(CAMP/'identity.json')
    assert identity['source_hashes']==campaign.bindings()
    assert identity['runner_sha256']==sha(campaign.__file__)
    assert identity['build_identity_sha256']==sha(OUT/'production_v2_identity.json')
    for path,expected in identity['helper_hashes'].items():
        assert sha(ROOT/path)==expected,path
    campaign.ready_build()
    summary=[json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(summary)==len(identity['launches'])==3
    assert [(r['id'],r['arm']) for r in identity['launches']]==[
        ('F5','SHADOW'),('F5','FEEDBACK'),('F2','FEEDBACK')]
    bindings={}
    def bind(path):
        path=Path(path)
        bindings[path.relative_to(ROOT).as_posix()]=sha(path)
    for path in [CAMP/'identity.json',CAMP/'summary.jsonl',
                 OUT/'production_v2_identity.json',Path(__file__).resolve(),
                 ROOT/'scripts/round97_vector_audit.py']:bind(path)
    evidence=[]
    for launch,completed in zip(identity['launches'],summary):
        assert [launch[k] for k in ['number','id','arm']]==[completed[k] for k in ['number','id','arm']]
        assert completed['audit_passed'] and completed['completion']['returncode']==0
        assert completed['completion']['stop_reason']=='normal_return'
        raw=Path(launch['destination']);audit=read(raw/'audit.json')
        assert audit['passed'] and audit['endpoint']==completed['endpoint']
        assert read(raw/'completion.json')==completed['completion']
        vector_path=OUT/f"qualification03_{launch['number']:02d}_vectors.json"
        vector=read(vector_path)
        assert vector['passed'] and vector['optimizer_calls']==0 and vector['vectors']
        assert vector['source_sha256']==sha(ROOT/'scripts/round97_vector_audit.py')
        for item in vector['vectors']:
            assert sha(ROOT/item['path'])==item['sha256']
            bind(ROOT/item['path'])
        stats=audit['round97']
        assert campaign.event_audit(launch)==stats
        if launch['id']=='F5':
            assert stats['post_start_events']>0 and stats['excluded_start_matching_events']>0
        path=raw/'external/round97/events.jsonl'
        events=[json.loads(s) for s in path.read_text().splitlines()]
        solutions=[e for e in events if e['kind']=='solution']
        expected_vectors={}
        for event in solutions:
            source=path.parent/f"vector_{event['event']}.csv"
            if source.exists():
                expected_vectors[source.relative_to(ROOT).as_posix()]=(event['event'],'input',event['model_sha256'])
            if event.get('mapped_vector'):
                mapped_path=path.parent/event['mapped_vector']
                expected_vectors[mapped_path.relative_to(ROOT).as_posix()]=(event['event'],'mapped',event['model_sha256'])
        assert len(vector['vectors'])==len(expected_vectors)
        assert {v['path']:(v['event'],v['kind'],v['model_sha256']) for v in vector['vectors']}==expected_vectors
        actual_models={sha(p):p for p in (raw/'external/models').glob('*.lp')}
        assert all(v['model_sha256'] in actual_models for v in vector['vectors'])
        submitted=[e for e in solutions if e.get('submission_return_code')==0]
        continued=[dict(submission_event=s['event'],later_event=e['event'],call=s['call'],
                        submitted_nodes=s['nodes'],later_nodes=e['nodes'])
                   for s in submitted for e in solutions
                   if e['call']==s['call'] and e['event']>s['event'] and e['nodes']>s['nodes']]
        mapped={e['event'] for e in solutions if e.get('model_feasible') and e.get('mapping_complete')}
        assert all(s['event'] in mapped and s['candidate_F']<s['input_F']-1e-9 for s in submitted)
        if launch['mode']=='shadow':
            assert not submitted and stats['vector_observations']==stats['archive_handoffs']==0
            assert stats['incremental_order_improvement_events']>0
        elif launch['id']=='F5':
            assert submitted and continued and stats['vector_observations']>0
        # F2 is a protection/no-increment role, not a requirement that every
        # short window must submit. Report its actual behavior separately.
        for witness in stats['physical_witnesses']:
            witness_path=path.parent/witness['path']
            assert sha(witness_path)==witness['sha256'];bind(witness_path)
        # Bind actual immutable matrices and receipts, not only vector metadata.
        for model in (raw/'external/models').glob('*.lp'):bind(model)
        bind(raw/'external/initial_witness.json')
        for setup in (raw/'external/native_logs').glob('*.round97.setup.json'):
            bind(setup)
            start_path=Path(str(setup).replace('.round97.setup.json','.round68.start.json'))
            if start_path.exists():
                bind(start_path)
                start=read(start_path)
                if start['submitted']:bind(raw/'external'/(start['source']+'_witness.json'))
        for source in [raw/'audit.json',raw/'completion.json',raw/'result.json',path,vector_path]:bind(source)
        evidence.append(dict(number=launch['number'],id=launch['id'],arm=launch['arm'],
            endpoint=completed['endpoint'],process_wall_seconds=completed['completion']['process_wall_seconds'],
            stats={k:v for k,v in stats.items() if k!='physical_witnesses'},
            submissions=len(submitted),independent_vectors=len(vector['vectors']),
            independent_vector_audit_seconds=vector['wall_seconds'],
            continued_same_call_node_progress=continued,
            native_optimize_calls=audit['native_scope_adapter']['native_calls']))
    write(CAMP/'gate.json',dict(schema='round97-v2-real-native-qualification-v1',passed=True,
        real_post_start_native_qualified=True,independent_actual_model_vectors_passed=True,
        combined_increment_observed=True,feedback_continued_proof_observed=True,
        qualification_only=True,complete_performance_accepted=False,
        source_ref=identity['source_ref'],candidate_binary_sha256=identity['candidate_binary_sha256'],
        bindings=bindings,evidence=evidence,solver_starts=3,
        paid_process_seconds=sum(e['process_wall_seconds'] for e in evidence),
        optimizer_calls=sum(e['native_optimize_calls'] for e in evidence),
        caveats=['No final certification-time conclusion from functional windows.',
                 'Vector observation does not prove unique candidate source.',
                 'Increment counts are recorded fresh-closure joint R96/R83 lower bounds.',
                 'Callback/closure/mapping expenses are nested within paid process wall.']))
    print(json.dumps(dict(passed=True,qualification_only=True,
        paid_process_seconds=sum(e['process_wall_seconds'] for e in evidence))))


if __name__=='__main__':main()
