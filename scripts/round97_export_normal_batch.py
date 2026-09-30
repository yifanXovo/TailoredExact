"""Compact evidence for completed normal attribution/confirmation arms; no Optimize.

The input batch and optional role select existing registered runs, never launch
or relabel experiments. Original files are retained and archives are byte-tested.
"""
import argparse
import json
import tarfile
from pathlib import Path
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext


def main(batch,role):
    ext.ensure_idle()
    assert batch in ('attribution01','confirmation01')
    assert role is None or role in ('C1','C2','C3')
    assert role is None or batch=='confirmation01'
    camp=OUT/batch;identity=read(camp/'identity.json')
    launches=[r for r in identity['launches'] if role is None or r['id']==role]
    assert len(launches)==(9 if batch=='confirmation01' and role is None else 3)
    rows=[json.loads(s) for s in (camp/'summary.jsonl').read_text(encoding='utf-8').splitlines()]
    completed={r['number']:r for r in rows}
    index=camp/('evidence_'+(role or 'complete')+'.json')
    assert not index.exists()
    bundles=[];files={camp/'identity.json',camp/'summary.jsonl'}
    for launch in launches:
        raw=Path(launch['destination']);audit=read(raw/'audit.json');receipt=read(raw/'completion.json')
        row=completed[launch['number']]
        assert (row['id'],row['arm'])==(launch['id'],launch['arm'])
        assert row['audit_passed'] and audit['passed'] and row['endpoint']==audit['endpoint']
        assert row['completion']==receipt and receipt['stop_reason']=='normal_return' and receipt['returncode']==0
        result=read(raw/'result.json')
        endpoint=camp/'endpoint_witnesses'/(launch['id']+'_'+launch['arm']+'.json')
        assert not endpoint.exists()
        write(endpoint,dict(role=launch['id'],arm=launch['arm'],panel=launch['panel'],endpoint=audit['endpoint'],
            witness=result,verified=audit['final_physical_verification'],optimizer_calls=0))
        archive=camp/'compact_evidence'/f"{launch['number']:02d}_{launch['id']}_{launch['arm']}_evidence.tar.gz"
        assert not archive.exists();archive.parent.mkdir(parents=True,exist_ok=True)
        journal=sorted(p for p in (raw/'journal').iterdir() if p.is_file())
        assert len(journal)==2*audit['committed_events']
        packed=journal+[raw/'observations.json']
        with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
            for path in packed:tar.add(path,arcname=path.relative_to(ROOT).as_posix(),recursive=False)
        with tarfile.open(archive,'r:gz') as tar:
            members=tar.getmembers();assert len(members)==len(packed)
            for member,path in zip(members,packed,strict=True):
                assert member.name==path.relative_to(ROOT).as_posix()
                assert tar.extractfile(member).read()==path.read_bytes()
        bundles.append(dict(path=archive.relative_to(ROOT).as_posix(),sha256=sha(archive),
            bytes=archive.stat().st_size,committed_events=audit['committed_events'],
            verified_exact_members=len(packed)))
        files.update(p for p in raw.rglob('*') if p.is_file() and 'journal' not in p.relative_to(raw).parts)
        files.add(endpoint)
    write(index,dict(optimizer_calls=0,new_solver_starts=0,role=role,batch=batch,
        journal_and_observation_archives=bundles,source_sha256=sha(__file__),
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)],
        scope='Byte-verified original journal and observations archives; raw files retained. Large models, vectors and CSVs remain local with hashes.'))
    print(json.dumps(dict(passed=True,batch=batch,role=role,arms=len(launches),optimizer_calls=0,archives=bundles)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('batch');parser.add_argument('--role')
    args=parser.parse_args();main(args.batch,args.role)
