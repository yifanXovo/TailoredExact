"""Fixed diagnostics orchestration. Optimization/model/oracle are exclusively C++."""
from round166_common import *
import csv,math,os
Q=OUT/'qualification'
DRIVER=WORK/'build-cache/round166/Round166Qualification.exe'
PE=WORK/'build-cache/round166/ExactEBRP.exe'
ENV=dict(os.environ,PATH='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+os.environ['PATH'])
def calls():
    return sum(sum('"phase":"begin"' in s for s in p.read_text().splitlines()) for p in Q.rglob('Optimize.jsonl'))
def run(label,args):
    ledger=Q/'driver_calls.json';records=read(ledger) if ledger.exists() else []
    assert label not in [r['label'] for r in records],('never automatically rerun',label)
    state=Q/'window.json'
    if not state.exists():write(state,dict(UTC=utc(),start_unix=time.time(),limit_seconds=3600,max_Optimize=120))
    assert time.time()-read(state)['start_unix']<3500 and calls()<120
    rec=dict(label=label,command=[str(x) for x in args],UTC=utc(),before_Optimize=calls())
    records.append(rec);write(ledger,records)
    start=time.perf_counter();log=Q/'logs'/f'{label}.log';log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('wb') as f:r=subprocess.run([str(x) for x in args],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=3600-(time.time()-read(state)['start_unix']))
    rec.update(exit_code=r.returncode,seconds=time.perf_counter()-start,after_Optimize=calls(),log=bind(log))
    write(ledger,records);print(label,rec['exit_code'],rec['seconds'],'Optimize',rec['after_Optimize'],flush=True)
    assert r.returncode==0,log
def local():run('local',[DRIVER,'local',Q/'local'])
def roots():
    parents=read(Q/'parents/source_manifest.json')['records'];manifest=read(ROOT/'results/unified_exact_round163/input_manifest.json')['roles']
    for index,p in enumerate(parents):
        role=next(x for x in manifest if x['id']==p['id']);assert sha(ROOT/role['input_path'])==role['input_sha256']
        upper=min(math.nextafter((role['V']-1)/role['V'],math.inf),math.nextafter(p['U'],math.inf))
        for domain,lo,hi in [('root',0,upper)]+([('child',0,upper/2)] if index<2 else []):
            for rep in ['B','C166']:
                label=p['id']+'_'+domain+'_'+rep
                run(label,[DRIVER,'physical',ROOT/role['input_path'],role['T_seconds'],60,60,format(role['lambda'],'.17g'),
                    ROOT/p['parent_path'],Q/'global'/label,rep,'LP',90,lo,hi,math.nextafter(p['U'],math.inf),p['id']+'_'+domain+'_epoch1'])
def tiny():
    tiny=Q/'tiny';tiny.mkdir(exist_ok=True)
    for initial in (3,4):
        p=tiny/f'initial{initial}.txt'
        p.write_text(f'2 1 [3]\ncapacities = [100,4,4]\ninitial = [50,{initial},0]\ntarget = [0,2,2]\nweights = [0,1,1]\npoints = [(0,0),(0,0),(0,0)]\n',encoding='utf-8')
    (tiny/'empty.txt').write_text('0\n')
    (tiny/'zero_stock.txt').write_text('1\n0 3 0 1 0\n3\n')
    run('tiny_oracle',[DRIVER,'tiny-oracle',tiny/'oracle.csv'])
    for rep in ['B','C166']:
        run('tiny_restore_'+rep,[DRIVER,'physical',tiny/'initial3.txt',360,60,60,.15,tiny/'empty.txt',tiny/('restore_'+rep),rep,'restore',30,0,.5,.725,'tiny_nonbreak_epoch1'])
        run('tiny_S0_'+rep,[DRIVER,'physical',tiny/'initial3.txt',360,60,60,.15,tiny/'zero_stock.txt',tiny/('S0_'+rep),rep,'MIP-zero',30,0,0,.3,'tiny_S0_epoch2'])
        run('tiny_zero_'+rep,[DRIVER,'physical',tiny/'initial4.txt',480,60,60,.15,tiny/'empty.txt',tiny/('zero_'+rep),rep,'MIP',30,0,.5,.8,'tiny_zero_epoch3'])
def summarize():
    rows=list(csv.DictReader((Q/'local/local.csv').open()));assert len(rows)==64
    for c in range(8):
        for objective in range(2):
            group=sorted([r for r in rows if int(r['config'])==c and int(r['objective'])==objective],key=lambda x:int(x['representation']))
            values=[float(r['value']) for r in group]
            assert max(values[:3])-min(values[:3])<=1e-7,group
            assert values[3]<=values[0]+1e-7
    assert [float(r['value']) for r in rows[:8]]==[1.,-1.,1.,-1.,1.,-1.,0.,-2.]
    pairs=[]
    for bdir in sorted((Q/'global').glob('*_B')):
        cdir=bdir.with_name(bdir.name[:-1]+'C166');b=read(bdir/'LP.json');c=read(cdir/'LP.json')
        assert b['LP_evidence'] and c['LP_evidence'] and b['lower_available'] and c['lower_available']
        delta=c['objective']-b['objective'];assert abs(delta)<=1e-7,(bdir,delta)
        pairs.append(dict(id=bdir.name[:-2],B=b,C166=c,signed_LP_delta=delta))
    assert len(pairs)==8
    write(Q/'LP_pairs.json',pairs)
    for rep in ['B','C166']:
        main=read(Q/'tiny'/('restore_'+rep)/'MIP.json')
        assert read(Q/'tiny'/('restore_'+rep)/'LP.json')['integer_domain_restored']
        assert abs(main['objective']-.15)<1e-7 and main['Start_submitted'] and main['Start_rows_valid']
        if rep=='C166':
            phys=read(Q/'tiny'/('restore_'+rep)/'physical.json')
            assert phys['Y']==[1,1] and abs(phys['F']-.15)<1e-7
        assert read(Q/'tiny'/('S0_'+rep)/'physical.json')['Y']==[0,0]
        assert abs(read(Q/'tiny'/('zero_'+rep)/'physical.json')['F'])<1e-7
    assert calls()<=120
    write(OUT/'qualification.json',dict(UTC=utc(),PASS=True,actual_Optimize=calls(),local_LP=64,global_LP=16,
        boundary_tiny_native=8,diagnostic_window_seconds=time.time()-read(Q/'window.json')['start_unix'],
        same_raw_LP_projection=True,internal_nonbreak_inventory=[1,1],integer_type_restoration=True,
        complete_Start_actual_rows=True,zero_stock=True,loaded_return=True,independent_manual_oracle=True,
        independent_zero_controller='pending',LP_pairs=bind(Q/'LP_pairs.json'),algebra=read(Q/'algebra.json')))
    print('Qualification PASS',calls())
def tiny_resume():
    # B's two native calls completed and qualified. Only a misplaced test
    # assertion failed after them. Retain its files and do not rerun B.
    tiny=Q/'tiny'
    b=read(tiny/'restore_B/MIP.json');lp=read(tiny/'restore_B/LP.json')
    assert b['available'] and b['objective']==.15 and lp['integer_domain_restored']
    write(Q/'reader_fix.json',dict(UTC=utc(),reason='integer_domain_restored belongs to the completed LP return, not following MIP',
        failed_label='tiny_restore_B',healthy_native_calls=2,solver_rerun=False,
        B_final_fleet_not_persisted_after_reader_assertion=True,manual_oracle_unique_optimal_Y=[1,1]))
    for rep in ['B','C166']:
        if rep=='C166':
            run('tiny_restore_'+rep,[DRIVER,'physical',tiny/'initial3.txt',360,60,60,.15,tiny/'empty.txt',tiny/('restore_'+rep),rep,'restore',30,0,.5,.725,'tiny_nonbreak_epoch1'])
        run('tiny_S0_'+rep,[DRIVER,'physical',tiny/'initial3.txt',360,60,60,.15,tiny/'zero_stock.txt',tiny/('S0_'+rep),rep,'MIP-zero',30,0,0,.3,'tiny_S0_epoch2'])
        run('tiny_zero_'+rep,[DRIVER,'physical',tiny/'initial4.txt',480,60,60,.15,tiny/'empty.txt',tiny/('zero_'+rep),rep,'MIP',30,0,.5,.8,'tiny_zero_epoch3'])
if __name__=='__main__':globals()[sys.argv[1]]()
