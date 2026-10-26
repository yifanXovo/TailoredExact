"""Compact immutable F2 journal archives and physical endpoint witnesses; zero Optimize."""
import json
import tarfile
from pathlib import Path
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext


def main():
    ext.ensure_idle();camp=OUT/'development02';identity=read(camp/'identity.json')
    launches=[r for r in identity['launches'] if r['id']=='F2']
    assert len(launches)==3
    bundles=[];files=[]
    for launch in launches:
        raw=Path(launch['destination']);audit=read(raw/'audit.json')
        assert audit['passed'] and read(raw/'completion.json')['stop_reason']=='normal_return'
        result=read(raw/'result.json')
        endpoint=camp/'endpoint_witnesses'/('F2_'+launch['arm']+'.json')
        write(endpoint,dict(role='F2',arm=launch['arm'],panel=launch['panel'],endpoint=audit['endpoint'],
            witness=result,verified=audit['final_physical_verification'],optimizer_calls=0))
        archive=camp/'compact_evidence'/f"{launch['number']:02d}_F2_{launch['arm']}_journal.tar.gz"
        assert not archive.exists();archive.parent.mkdir(parents=True,exist_ok=True)
        journal=sorted(p for p in (raw/'journal').iterdir() if p.is_file())
        assert len(journal)==2*audit['committed_events']
        with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
            for path in journal:tar.add(path,arcname=path.relative_to(ROOT).as_posix(),recursive=False)
        # Verify byte-exact contents once, while the solver machine is idle.
        with tarfile.open(archive,'r:gz') as tar:
            members=tar.getmembers();assert len(members)==len(journal)
            for member,path in zip(members,journal,strict=True):
                assert member.name==path.relative_to(ROOT).as_posix()
                assert tar.extractfile(member).read()==path.read_bytes()
        bundles.append(dict(path=archive.relative_to(ROOT).as_posix(),sha256=sha(archive),
                            bytes=archive.stat().st_size,committed_events=audit['committed_events'],
                            verified_exact_members=len(journal)))
        files.extend(p for p in raw.rglob('*') if p.is_file() and 'journal' not in p.relative_to(raw).parts)
        files.append(endpoint)
    write(camp/'evidence_f2.json',dict(optimizer_calls=0,new_solver_starts=0,
        journal_archives=bundles,source_sha256=sha(__file__),
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)],
        scope='Journals stored in byte-verified compact archives; models/full CSVs and large raw logs remain local with hashes. Original raw artifacts remain unchanged.'))
    print(json.dumps(dict(passed=True,roles=1,arms=3,optimizer_calls=0,journal_archives=bundles)))


if __name__=='__main__':main()
