"""Capture actual current-core dependencies during the one final local rebuild."""
from pathlib import Path
import argparse,csv,os,sys,time
import round123_common as c

def run(root):
    tick=time.perf_counter();root=Path(root).resolve();assert root==c.ROOT
    out=root/'results/unified_exact_round123';receipt=c.read(out/'controller/formal01/receipt.json')
    assert receipt['exit_code']==0 and not c.budget()['unclosed']
    runtime=Path(sys.base_prefix).resolve();reads=set();writes=set()
    def boundary(event,args):
        if event in ['subprocess.Popen','socket.connect','os.system','os.posix_spawn']:
            raise AssertionError(('No process/network in local post-seal rebuild',event))
        if event=='ctypes.dlopen' and args and any(n in str(args[0]).lower() for n in ['gurobi','cplex']):
            raise AssertionError('No solver library in local post-seal rebuild')
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve()
        assert p.is_relative_to(root) or p.is_relative_to(runtime),('External dependency',str(p))
        if p.is_relative_to(root):
            mode=args[1];flags=args[2]
            mask=getattr(os,'O_ACCMODE',os.O_WRONLY|os.O_RDWR)
            reading=bool('r' in mode or '+' in mode) if isinstance(mode,str) else flags&mask in [os.O_RDONLY,os.O_RDWR]
            (reads if reading else writes).add(p.relative_to(root).as_posix())
    sys.addaudithook(boundary);csv.field_size_limit(64*1024*1024)
    import read_round123 as reader
    dest=out/'reconstruction/final';value=reader.rebuild(root,dest)
    modules=[]
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        p=Path(filename).resolve()
        assert p.is_relative_to(root) or p.is_relative_to(runtime),('External imported module',name,str(p))
        if p.is_relative_to(root):modules.append(dict(module=name,path=p.relative_to(root).as_posix()))
    dependencies=sorted(reads|{m['path'] for m in modules})
    assert all((root/p).is_file() for p in dependencies)
    c.write(dest/'dependency_reads.json',dict(paths=dependencies,actual_opened_for_read=sorted(reads),
        actual_local_modules=modules,write_paths=sorted(writes),current_core_SHA=c.sha(dest/'current_core.json'),
        scope='Actual Python read/process/network/library audit during local final rebuild; standard runtime allowed, not an OS sandbox',
        no_old_root_or_runtime_binary_fallback=True,native_starts=0,Optimize=0,UTC=c.utc(),seconds=time.perf_counter()-tick))
    print('Actual final local rebuild dependency capture complete: '+value['decision']['research_disposition'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(c.ROOT));args=parser.parse_args();run(args.root)
