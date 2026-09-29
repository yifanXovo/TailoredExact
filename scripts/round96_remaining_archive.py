"""Incremental formal evidence archive by unarchived completed arm numbers."""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha
import round96_external as external

def main():
    parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('--external-after',type=int,required=True)
    parser.add_argument('--primal-after',type=int,required=True);args=parser.parse_args()
    assert args.label.replace('_','').isalnum();external.ensure_idle();start=time.perf_counter();files=set();arms=[]
    for name,threshold in [('external',args.external_after),('primal_v2',args.primal_after)]:
        camp=OUT/name
        records=[json.loads(line) for line in (camp/'summary.jsonl').read_text().splitlines()]
        assert all(r['audit_passed'] for r in records)
        for row in records:
            if row['number']<=threshold:continue
            folder=Path(row['destination']);files.update(p for p in folder.rglob('*') if p.is_file())
            arms.append(dict(campaign=name,number=row['number'],id=row['id'],arm=row['arm']))
        files.update(p for p in camp.glob('*') if p.is_file())
    assert arms
    for folder in OUT.iterdir():
        if folder.is_dir() and (folder.name.startswith(('external_report_','external_trajectory_','primal_report_',
            'primal_v2_trajectory_','cost_report_'))):
            files.update(p for p in folder.rglob('*') if p.is_file())
    files.update(p for p in OUT.glob('*') if p.is_file() and p.suffix in {'.md','.json'}
        and not p.name.startswith(('stage','formal_archive_')))
    files.update((ROOT/'scripts').glob('round96*.py'))
    records=[];archive=OUT/f'formal_archive_{args.label}.zip';assert not archive.exists()
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as stream:
        for path in sorted(files):
            relative=path.relative_to(ROOT).as_posix();digest=sha(path)
            stream.write(path,relative);records.append(dict(path=relative,bytes=path.stat().st_size,sha256=digest))
    with zipfile.ZipFile(archive) as stream:
        assert len(stream.infolist())==len(records)
        for row in records:assert hashlib.sha256(stream.read(row['path'])).hexdigest()==row['sha256']
    write(OUT/f'formal_archive_{args.label}.json',dict(files=records,arms=arms,archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,verified_members=len(records),wall_seconds=time.perf_counter()-start,
        optimizer_calls=0,paid_starts=0,source_sha256=sha(__file__),
        scope='Complete raw files for selected completed arms and current analysis/harness snapshot. Earlier source/binary identities and raw prefixes remain in stage1–3; archived state is not automatically the latest report state.'))
    print(json.dumps(dict(arms=len(arms),members=len(records),bytes=archive.stat().st_size,seconds=time.perf_counter()-start)))

if __name__=='__main__':main()
