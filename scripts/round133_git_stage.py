"""Stage exactly the finite export paths, never the raw directory tree."""
from round133_common import *


def main():
    manifest=OUT/'export_manifest.json';value=read(manifest)
    assert value['schema']=='round133-finite-current-public-export-v1'
    branch=git('branch','--show-current').decode().strip()
    assert branch=='codex/round133-native-reliability-and-objective-gap'
    assert not git('diff','--cached','--name-only','-z'),'inspect pre-existing staged changes first'
    paths=[]
    for row in value['files']:
        path=ROOT/row['path'];assert path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['SHA256']
        paths.append(row['path'])
    paths.append(manifest.relative_to(ROOT).as_posix());assert len(set(paths))==len(paths)
    target=TEMP/'staging';target.mkdir(parents=True,exist_ok=False)
    pathspec=target/'science_paths.nul';pathspec.write_bytes(b''.join(name.encode('utf-8')+b'\0' for name in sorted(paths)))
    git('add','--sparse','--force','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
    staged=git('diff','--cached','--name-only','-z').decode().split('\0');staged=[name for name in staged if name]
    assert staged and set(staged).issubset(paths)
    assert all('/campaign/' not in name and '/fees/' not in name and '/diagnostics/' not in name for name in staged)
    write(target/'stage_receipt.json',dict(UTC=utc(),export_manifest_SHA=sha(manifest),
        explicit_allowed_paths=len(paths),staged_paths=len(staged),pathspec_SHA=sha(pathspec),
        branch=branch,raw_directories_never_staged=True,Optimize=0,compile=0))
    print(json.dumps(dict(allowed_paths=len(paths),staged_paths=len(staged),manifest_SHA=sha(manifest))))


if __name__=='__main__':main()
