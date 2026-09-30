"""Analyze all frozen arms of one completed role while other roles remain.

Uses the versioned null-preserving whole-batch analyzer on an explicitly nonlaunchable
snapshot view. No raw results are copied or relabelled; original destinations
and launch numbers are preserved. Views never represent extra solver starts.
"""
import argparse
import json
from pathlib import Path
import round97_analyze_batch_v3 as analyzer
from round97_analyze_batch_v3 import ROOT, OUT, read, write, sha, ext


def main(batch, role):
    ext.ensure_idle()
    assert all(part and all(c.isalnum() or c in '_-' for c in part) for part in [batch,role])
    source=OUT/batch
    identity=read(source/'identity.json')
    launches=[r for r in identity['launches'] if r['id']==role]
    assert launches and {'P-GRB','OFF','FEEDBACK'} <= {r['arm'] for r in launches}
    all_completed=[json.loads(s) for s in (source/'summary.jsonl').read_text().splitlines()]
    completed=[r for r in all_completed if r['id']==role]
    assert [(r['number'],r['id'],r['arm']) for r in completed]==[
        (r['number'],r['id'],r['arm']) for r in launches], 'Every registered arm of this role must be completed'
    assert all(r['audit_passed'] for r in completed)
    for launch,row in zip(launches,completed):
        raw=Path(launch['destination'])
        analyzer.interrupted.validate_outcome(launch,read(raw/'audit.json'),row['completion'])
    assert len({r['panel']['input_sha256'] for r in launches})==1
    assert len({r['panel']['T_seconds'] for r in launches})==1
    assert len({r['cap_seconds'] for r in launches})==1
    for launch in launches:
        if launch['arm']=='P-GRB':continue
        events=Path(launch['destination'])/'external/round97/events.jsonl'
        if events.exists():
            audit=read(OUT/f"{batch}_{launch['number']:02d}_vectors.json")
            assert audit['passed'] and audit['optimizer_calls']==0
    label=f'analysis_views/{batch}_{role}_v3'
    view=OUT/label
    assert not view.exists() and not (OUT/(label+'_analysis')).exists()
    # Drop commands and all launcher authentication fields. This cannot serve
    # as a campaign identity for either version of the guarded runner.
    selected=[{k:v for k,v in r.items() if k!='command'} for r in launches]
    write(view/'identity.json',dict(schema='round97-analysis-view-only-v1',analysis_only=True,
        source_batch=batch,source_role=role,source_identity_path=(source/'identity.json').relative_to(ROOT).as_posix(),
        source_identity_sha256=sha(source/'identity.json'),launches=selected,
        maximum_new_solver_starts=0,optimizer_calls=0))
    with (view/'summary.jsonl').open('x',encoding='utf-8') as stream:
        for row in completed:stream.write(json.dumps(row)+'\n')
    analyzer.main(label)
    paths=[source/'identity.json',view/'identity.json',view/'summary.jsonl',
           OUT/(label+'_analysis')/'identity.json',Path(analyzer.__file__).resolve(),Path(__file__).resolve()]
    paths += [OUT/f"{batch}_{r['number']:02d}_vectors.json" for r in launches
              if (OUT/f"{batch}_{r['number']:02d}_vectors.json").exists()]
    write(view/'projection_receipt.json',dict(passed=True,optimizer_calls=0,new_solver_starts=0,
        source_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
        interpretation='All registered arms of one role, retaining original raw destinations/numbers. Included solver costs refer to existing runs and must not be counted again. Mutable campaign summary is copied as a fixed selected snapshot, never bound as if it could not grow.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('batch');parser.add_argument('role')
    args=parser.parse_args()
    main(args.batch,args.role)
