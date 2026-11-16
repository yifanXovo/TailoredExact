"""Serial subprocess orchestration only. H/selection/verification/exact solving are C++."""
from round169_common import *
import argparse, ctypes, re

def result(p):
    d=read(p);return d[0] if isinstance(d,list) else d['results'][0] if 'results' in d else d

def command(p,d,arm='B',panel=False,direct=False):
    cap=300 if p['V']==20 else 600
    template=read(ROOT/'results/unified_exact_round163/method_freeze.json')['B']['argv']
    values=dict(exe=str(PE),input=str(ROOT/p['input_path']),T=str(p['T_seconds']),
        **{'lambda':format(p['lambda'],'.17g')},pickup_time='60',drop_time='60',native_limit=str(cap-6),
        cap=str(cap),seed='0',result=str(d/'result.json'),log=str(d/'native.log'),phases=str(d/'phases.csv'),
        external=str(d/'external'),hga=str(d/'hga.csv'),progress=str(d/'progress.csv'),journal=str(d/'journal'))
    cmd=[]
    for t in template:
        for k,v in values.items():t=t.replace('${'+k+'}',v)
        assert '${' not in t,t
        cmd.append(t)
    cmd[cmd.index('--process-shutdown-margin')+1]='6'
    cmd+=['--round166-joint-breakpoint','off','--round169-primal-mode',dict(B='off',M='multistart',C='reweight')[arm],
        '--round169-trace',str(d/'primal'),'--export-incumbent',str(d/'fleet.json')]
    if panel:cmd+=['--round169-h-panel']
    elif direct:cmd+=['--round169-h-base-direct']
    return cmd,cap

def launch(cmd,d,timeout):
    d.mkdir(parents=True,exist_ok=False)
    t=time.perf_counter();started=time.time()
    write(d/'invocation.json',dict(UTC=utc(),argv=cmd,PE=bind(PE),DLL=bind(DLL),source=git('rev-parse','HEAD'),
        deadline_seconds=timeout,H_free_reuse=False))
    with (d/'console.log').open('wb') as f:
        p=subprocess.Popen(cmd,cwd=ROOT,env=env(),stdout=f,stderr=subprocess.STDOUT)
        try:
            ok=ctypes.windll.kernel32.SetProcessAffinityMask(int(p._handle),4)
            affinity=dict(mask=4,set_success=bool(ok))
        except Exception as e:affinity=dict(error=str(e))
        try:rc=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill();rc=p.wait();affinity['wrapper_killed']=True
    receipt=dict(UTC=utc(),started_epoch=started,ended_epoch=time.time(),process_outer_seconds=time.perf_counter()-t,
        rc=rc,affinity=affinity,result=bind(d/'result.json') if (d/'result.json').is_file() else None)
    write(d/'completion.json',receipt)
    if rc:raise RuntimeError(f'failed process {d}: rc={rc}; preserve and inspect console')
    return receipt

def candidate():
    sources={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file()}
    sources['CMakeLists.txt']=sha(ROOT/'CMakeLists.txt')
    data=dict(UTC=utc(),source_commit=git('rev-parse','HEAD'),source_hashes=sources,PE=bind(PE),DLL=bind(DLL),
        compiler=bind('D:/msys64/ucrt64/bin/g++.exe'),
        compiler_version=subprocess.check_output(['D:/msys64/ucrt64/bin/g++.exe','--version'],env=env()).decode(),
        build_cache=bind(WORK/'build-cache/round169/CMakeCache.txt'),build_ninja=bind(WORK/'build-cache/round169/build.ninja'),
        build_commands=['cmake -S <R169 ROOT> -B <WORK>/build-cache/round169 -G Ninja -DCMAKE_MAKE_PROGRAM=<VS Ninja> -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64',
            'cmake --build <WORK>/build-cache/round169 --target ExactEBRP -j 4'],
        flags='Release -O3 -DNDEBUG; C++17; no fast-math',B_M_C_common_PE=True,default_off=True,
        historical_R168_PE_not_used_for_performance=True)
    write(OUT/'candidate_manifest.json',data)
    write(OUT/'environment_manifest.json',dict(UTC=utc(),Python=sys.version,PATH_prefix=env()['PATH'].split(';')[:2],
        compiler=data['compiler'],DLL=data['DLL'],PE=data['PE'],Threads=1,Native_Seed=0,H_seeds=[20260626,20260627,20260628]))
    print('Candidate',data['source_commit'],data['PE']['SHA256'],flush=True)

def qualify():
    start=time.perf_counter();roles=read(OUT/'h_panel_frozen.json')['roles'];receipts=[]
    d=OUT/'qualification/base_direct';cmd,_=command(roles[0],d,direct=True);receipts.append(launch(cmd,d,60))
    raw=(ROOT/'tests/data/round59_tiny.txt').read_text();print(raw,flush=True)
    # Tiny fixture already in the test suite; only two degenerate objective copies.
    for name,lam,zero_w in [('lambda0',0,False),('weights0',.15,True),('zero',.15,False)]:
        p=OUT/f'qualification/inputs/{name}.txt';p.parent.mkdir(parents=True,exist_ok=True)
        text=re.sub(r'weights\s*=\s*\[[^\n]*\]',lambda m:'weights = ['+','.join('0' for _ in m[0].split('[')[1].split(']')[0].split(','))+']',raw) if zero_w else raw
        p.write_text(text,encoding='utf-8')
        q=dict(id=name,V=2,input_path=p.relative_to(ROOT).as_posix(),T_seconds=3600,**{'lambda':lam})
        d=OUT/f'qualification/{name}';cmd,_=command(q,d,arm='C');cmd+=['--round169-h-only']
        receipts.append(launch(cmd,d,60));s=read(d/'primal/selection.json');assert s['calls']==1 and s['skip_reason'],s
    total=sum(r['process_outer_seconds'] for r in receipts);assert total<300
    write(OUT/'qualification/receipt.json',dict(UTC=utc(),processes=receipts,process_outer_seconds=total,cap=300,
        original_base_comparison='pending first real H-panel base',Optimize=0))
    print('qualification processes',total,flush=True)

def h_panel():
    assert (OUT/'candidate_manifest.json').is_file()
    start=time.perf_counter();panel=read(OUT/'h_panel_frozen.json');receipts=[];rows=[]
    write(OUT/'h_window.json',dict(start_epoch=time.time(),outer_cap=1200))
    for p in panel['roles']:
        d=OUT/'h_raw'/p['id'];cmd,_=command(p,d,panel=True)
        remaining=1200-(time.perf_counter()-start)
        assert remaining>0
        receipts.append(launch(cmd,d,remaining))
        s=read(d/'primal/selection.json');s['role']=p['id'];s['can_trigger_E5']=p['can_trigger_E5'];rows.append(s)
        print(p['id'],json.dumps(s),flush=True)
    elapsed=time.perf_counter()-start;assert elapsed<=1200
    actual=sum(r['calls'] for r in rows);assert actual<=35
    direct=result(OUT/'qualification/base_direct/result.json')
    first=result(OUT/'h_raw'/panel['roles'][0]['id']/'result.json')
    assert direct['routes']==first['routes']
    assert all(abs(direct[k]-first[k])<1e-13 for k in ['G','P','objective'])
    for p in panel['roles']:
        d=OUT/'h_raw'/p['id']/'primal'
        for j in [1,2]:
            if (d/f'M_s{j}/path.json').exists() and (d/f'C_s{j}/path.json').exists():
                assert read(d/f'M_s{j}/path.json')['initial_random_orders_SHA256']==read(d/f'C_s{j}/path.json')['initial_random_orders_SHA256']
    native=list((OUT/'h_raw').rglob('*.begin.json'));assert not native,native
    triggered=any(r['E4_role_gate'] and r['can_trigger_E5'] for r in rows)
    write(OUT/'h_results.json',dict(UTC=utc(),rows=rows,H_calls=actual,Optimize=0,E4_triggered=triggered,
        process_receipts=receipts,shared_outer_seconds=elapsed,base_direct_same_fleet_G_P_F=True,matched_random_orders=True))
    with (OUT/'h_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    m=read(OUT/'matrix_frozen.json');m['status']='E4_triggered' if triggered else 'not-triggered'
    for p in m['positions']:p['status']='authorized_pending' if triggered else 'not-triggered'
    m['E4_evidence_SHA256']=sha(OUT/'h_results.json');write(OUT/'matrix_frozen.json',m)
    print('H PANEL COMPLETE',actual,'calls',elapsed,'seconds; E4',triggered,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['candidate','qualify','h_panel']);a=ap.parse_args();globals()[a.action]()
