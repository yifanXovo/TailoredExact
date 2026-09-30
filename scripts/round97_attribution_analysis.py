"""Combine the original development and three added operator controls, without reruns.

The view preserves raw destinations, launch numbers, original audit failures and
source campaigns. It cannot launch an experiment and contains no command fields.
"""
import json
from pathlib import Path
import round97_analyze_batch_v4 as analyzer
import round97_operator_attribution as attribution
import round97_continue_after_v1_recovery as development
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext

LABEL='analysis_views/development_with_attribution'


def main():
    ext.ensure_idle()
    originals=read(development.CAMP/'identity.json')
    additions=read(attribution.CAMP/'identity.json')
    development.identity_check(originals)
    original_rows=development.prefix(originals,13)
    attribution.check(additions)
    added_rows=attribution.prefix(additions,3)
    assert originals['candidate_binary_sha256']==additions['candidate_binary_sha256']
    assert originals['source_hashes']==additions['source_hashes']
    launches=originals['launches']+additions['launches']
    rows=original_rows+added_rows
    assert len(launches)==len(rows)==16
    assert len({r['destination'] for r in launches})==16
    for role in ['F5','D7','V1','F2']:
        selected=[r for r in launches if r['id']==role]
        assert len(selected)==4 and {r['arm'] for r in selected}=={'OLD-FEEDBACK','FEEDBACK','OFF','P-GRB'}
        assert len({r['panel']['input_sha256'] for r in selected})==1
        assert len({r['panel']['T_seconds'] for r in selected})==1
        assert len({r['cap_seconds'] for r in selected})==1
    view=OUT/LABEL
    assert not view.exists() and not (OUT/(LABEL+'_analysis')).exists()
    bindings={}
    source_campaigns=[]
    for name,identity,completed in [('development02',originals,original_rows),('attribution01',additions,added_rows)]:
        camp=OUT/name
        for path in [camp/'identity.json',camp/'summary.jsonl']:
            bindings[path.relative_to(ROOT).as_posix()]=sha(path)
        source_campaigns.append(dict(batch=name,launches=[dict(number=r['number'],id=r['id'],arm=r['arm'],
            destination=r['destination']) for r in identity['launches']]))
        for launch,row in zip(identity['launches'],completed,strict=True):
            analyzer.outcomes.load(launch,row)
            raw=Path(launch['destination'])
            if launch['arm']!='P-GRB' and (raw/'external/round97/events.jsonl').exists():
                path=OUT/f"{name}_{launch['number']:02d}_vectors.json"
                assert read(path)['passed'] and read(path)['optimizer_calls']==0
                bindings[path.relative_to(ROOT).as_posix()]=sha(path)
    write(view/'identity.json',dict(schema='round97-two-batch-analysis-view-v1',analysis_only=True,
        launches=[{k:v for k,v in r.items() if k!='command'} for r in launches],
        source_campaigns=source_campaigns,source_bindings=bindings,
        candidate_binary_sha256=originals['candidate_binary_sha256'],
        maximum_new_solver_starts=0,optimizer_calls=0,
        interpretation='All four original development roles with both operators, OFF and P. Numbers belong to source campaigns; raw destinations uniquely identify runs. No result is copied into another arm.'))
    with (view/'summary.jsonl').open('x',encoding='utf-8') as stream:
        for row in rows:stream.write(json.dumps(row)+'\n')
    analyzer.main(LABEL)
    paths=[view/'identity.json',view/'summary.jsonl',OUT/(LABEL+'_analysis')/'identity.json',
           Path(__file__).resolve(),Path(analyzer.__file__).resolve()]
    write(view/'projection_receipt.json',dict(passed=True,optimizer_calls=0,new_solver_starts=0,
        source_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
        limitation='Additional old-operator controls were selected after original development. They remain development data, never independent confirmation. V1 feedback and D7 P interruptions retain their original limitations.'))


if __name__=='__main__':main()
