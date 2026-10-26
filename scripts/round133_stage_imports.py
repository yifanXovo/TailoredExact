"""Stage only missing tiny pinned metadata required by inherited pure readers."""
from round133_common import *
import ast

def main():
    manifest=OUT/'infra/import_dependencies.json'
    data=read(manifest) if manifest.exists() else dict(base=BASE,dependencies=[],attempts=[])
    command=[PYTHON,'-B','-c','import sys;sys.path.insert(0,"scripts");import round133_read;import round133_campaign;import round133_small_native;print("PURE_IMPORTS_READY")']
    for attempt in range(12):
        result=subprocess.run(list(map(str,command)),cwd=ROOT,env=environment(),capture_output=True,timeout=20)
        data['attempts'].append(dict(UTC=utc(),returncode=result.returncode,
            stderr=result.stderr.decode('utf-8',errors='replace')))
        if result.returncode==0:
            data.update(PASS=True,Optimize=0,no_campaign_restore=True)
            write(manifest,data);print('PURE_IMPORTS_READY');return
        last=result.stderr.decode('utf-8',errors='strict').strip().splitlines()[-1]
        assert last.startswith('FileNotFoundError:') and 'No such file or directory: ' in last,last
        name=ast.literal_eval(last.split('No such file or directory: ',1)[1])
        path=Path(name).resolve();relative=path.relative_to(ROOT.resolve())
        assert relative.parts[0]=='results' and relative.parts[1]!='unified_exact_round133'
        assert path.suffix=='.json' and not path.exists()
        content=git('show',BASE+':'+relative.as_posix())
        assert len(content)<=262144 and sum(q['bytes'] for q in data['dependencies'])+len(content)<=2097152
        json.loads(content)
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        data['dependencies'].append(dict(path=relative.as_posix(),commit=BASE,
            SHA=sha(path),bytes=len(content),purpose='Required top-level metadata import; no historical raw fallback'))
        write(manifest,data)
    raise RuntimeError('Bounded metadata staging exhausted; inspect imports without expanding history')

if __name__=='__main__':main()
