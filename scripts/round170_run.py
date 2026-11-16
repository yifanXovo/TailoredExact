"""Frozen 22-position serial C++ production. No Python optimization/model building."""
from round170_common import *
import ctypes

OFF={'--round146-gd':'off','--round148-shared-s':'off','--round149-penalty-feedback':'off',
     '--round151-penalty-propagation':'off','--round153-root-floor':'off','--round154-proof-floor':'off',
     '--round156-rn-refinement':'off','--round143-rn':'off','--round144-projection':'off',
     '--round145-projection':'off','--round140-counts':'off','--round141-count-proof':'off',
     '--round142-count-products':'off','--round160-physical-neighborhood':'off','--round162-physical-completion':'off'}
def tokens(argv):
    d={};i=1
    while i<len(argv):
        key=argv[i];assert key.startswith('--') and key not in d,key
        if key=='--plain-baseline':d[key]=True;i+=1
        else:d[key]=argv[i+1];i+=2
    return d
def command(p,d,arm,seed):
    freeze=read(ROOT/'results/unified_exact_round163/method_freeze.json')
    template=freeze['P_template'] if arm=='P' else freeze['B']['argv']
    values=dict(exe=str(PE),input=str(ROOT/p['input_path']),T=str(p['T_seconds']),
        **{'lambda':format(p['lambda'],'.17g')},pickup_time='60',drop_time='60',native_limit='594',
        cap='600',seed=str(seed),result=str(d/'result.json'),log=str(d/'native.log'),phases=str(d/'phases.csv'),
        external=str(d/'external'),hga=str(d/'hga.csv'),progress=str(d/'progress.csv'),journal=str(d/'journal'),
        destination=str(d),fingerprint=str(p['compact_reference']['metadata']['fingerprint']),PE_SHA=PE_SHA)
    cmd=[]
    for token in template:
        for key,value in values.items():token=token.replace('${'+key+'}',value)
        assert '${' not in token,token
        cmd.append(token)
    cmd[cmd.index('--process-shutdown-margin')+1]='6'
    cmd[cmd.index('--gurobi-seed')+1]=str(seed)
    cmd+=['--round166-breakpoint','off','--round169-primal-mode',dict(B='off',M='multistart',C='reweight',P='off')[arm],
          '--export-incumbent',str(d/'fleet.json')]
    if arm=='P':
        cmd+=['--algorithm-preset','custom']
        for key,value in OFF.items():cmd.extend([key,value])
    else:cmd+=['--round169-trace',str(d/'primal')]
    t=tokens(cmd)
    assert t['--threads']==t['--mip-threads']=='1' and t['--gurobi-seed']==str(seed)
    assert t['--process-wall-time-limit']=='600' and t['--time-limit']=='594'
    assert t['--algorithm-preset']==('custom' if arm=='P' else 'research-round83-vds-equal-net-exchange')
    assert t['--method']==('gurobi' if arm=='P' else 'gcap-frontier')
    assert t['--round127-mode']==('p' if arm=='P' else 'ms2')
    assert ('--plain-baseline' in t)==(arm=='P')
    assert '--round112-ens-start-compact' not in t and '--round169-h-panel' not in t
    return cmd
def freeze():
    assert not (OUT/'matrix_frozen.json').exists()
    roles={p['id']:p for p in read(OUT/'inputs_frozen.json')['roles']};positions=[]
    blocks=[('R163-C20-S',1,['B','C']),('R163-C35-U',1,['M','P','C','B']),
            ('R163-B35-S',1,['C','B','P','M']),('R163-X35-S',1,['P','M','B','C']),
            ('R163-C20-S',2,['C','B']),('R163-C35-U',2,['B','C']),
            ('R163-B35-S',2,['C','B']),('R163-X35-S',2,['B','C'])]
    for block,(role,seed,arms) in enumerate(blocks,1):
        for arm in arms:
            n=len(positions)+1;d=OUT/'complete_raw'/f'{n:02}_{role}_S{seed}_{arm}'
            positions.append(dict(position=n,block=block,role=role,arm=arm,Native_Seed=seed,Threads=1,
                cap=600,native_time_limit=594,shutdown_margin=6,directory=str(d),argv=command(roles[role],d,arm,seed),
                PE_SHA256=PE_SHA,source_commit=MEASURED,delivery_base=BASE))
    assert len(positions)==22 and sum(p['cap'] for p in positions)==13200
    assert {k:sum(p['arm']==k for p in positions) for k in 'BCMP'}==dict(B=8,C=8,M=3,P=3)
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),positions=positions,nominal_process_cap_sum=13200,
        required_analysis_reserve_seconds=5400,serial=True,H_seeds=[20260626,20260627,20260628],
        expected_H_calls=41,material_change_delta='max(1e-6,0.001*max(abs(U_reference),1e-12))',
        delta_reference=dict(CB='B',CM='M',BP='P',CP='P'),no_statistical_significance_claim=True,
        no_adverse_result_early_stop=True,no_extra_screen=True,inputs_SHA256=sha(OUT/'inputs_frozen.json'),
        candidate_manifest_SHA256=sha(OUT/'candidate_manifest.json'),runner_SHA256=sha(__file__)))
    print('FROZEN all 22 positions, 13200s cap sum, expected 41 own-H calls',flush=True)
def admission():
    m=read(OUT/'matrix_frozen.json')
    assert json.loads(git('show','HEAD:results/unified_exact_round170/matrix_frozen.json'))==m
    assert sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    assert sha(OUT/'candidate_manifest.json')==m['candidate_manifest_SHA256']
    assert sha(OUT/'inputs_frozen.json')==m['inputs_SHA256'] and sha(__file__)==m['runner_SHA256']
    roles={p['id']:p for p in read(OUT/'inputs_frozen.json')['roles']}
    for p in m['positions']:
        assert sha(ROOT/roles[p['role']]['input_path'])==roles[p['role']]['input_sha256']
        assert p['argv']==command(roles[p['role']],Path(p['directory']),p['arm'],p['Native_Seed'])
    return m
def launch(p):
    d=Path(p['directory']);d.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();started=time.time()
    write(d/'invocation.json',dict(UTC=utc(),argv=p['argv'],PE=bind(PE),DLL=bind(DLL),
        source=git('rev-parse','HEAD'),measured_core_source=MEASURED,deadline_seconds=602,H_free_reuse=False))
    with (d/'console.log').open('wb') as f:
        proc=subprocess.Popen(p['argv'],cwd=ROOT,env=env(),stdout=f,stderr=subprocess.STDOUT)
        ok=ctypes.windll.kernel32.SetProcessAffinityMask(int(proc._handle),4)
        affinity=dict(mask=4,set_success=bool(ok))
        write(OUT/'active_position.json',dict(UTC=utc(),position=p['position'],role=p['role'],arm=p['arm'],
            Native_Seed=p['Native_Seed'],pid=proc.pid,started_epoch=started,deadline_epoch=started+602))
        try:rc=proc.wait(timeout=602)
        except subprocess.TimeoutExpired:
            proc.kill();rc=proc.wait();affinity['wrapper_killed']=True
    receipt=dict(UTC=utc(),started_epoch=started,ended_epoch=time.time(),process_outer_seconds=time.perf_counter()-tick,
        rc=rc,affinity=affinity,result=bind(d/'result.json') if (d/'result.json').is_file() else None)
    write(d/'completion.json',receipt)
    assert rc==0 and not affinity.get('wrapper_killed'),('preserve technical failure; no automatic rerun',d,receipt)
    return receipt
def complete():
    matrix=admission();elapsed=time.time()-SCIENCE_START
    assert elapsed+13200+5400<SCIENCE_CAP,('preserve 90min analysis reserve',elapsed)
    records=[]
    for p in matrix['positions']:
        d=Path(p['directory'])
        if d.exists():
            assert (d/'completion.json').is_file(),'incomplete producer; inspect instead of rerun'
            receipt=read(d/'completion.json');assert receipt['rc']==0
        else:
            # No concurrent optimizer may compete with this serial panel.
            other=subprocess.run(['tasklist','/FI','IMAGENAME eq ExactEBRP.exe','/FO','CSV','/NH'],capture_output=True,text=True)
            assert 'ExactEBRP.exe' not in other.stdout,other.stdout
            print('START',p['position'],p['role'],p['arm'],'Seed',p['Native_Seed'],utc(),flush=True)
            receipt=launch(p)
        r=result(d/'result.json')
        record=dict(position=p['position'],role=p['role'],arm=p['arm'],Native_Seed=p['Native_Seed'],status='returned',receipt=receipt,
            raw_endpoint={k:r.get(k) for k in ['status','objective','upper_bound','lower_bound','gap',
                'initial_heuristic_UB','strict_certified_original_problem','final_process_wall_time_seconds']})
        records.append(record)
        write(OUT/'complete_status.json',dict(UTC=utc(),records=records,positions_finished=len(records),
            process_outer_seconds=sum(x['receipt']['process_outer_seconds'] for x in records)))
        print('END',json.dumps(record,ensure_ascii=False),flush=True)
    write(OUT/'panel_complete.json',dict(UTC=utc(),positions=22,actual_status='all returned',no_automatic_reruns=True))

if __name__=='__main__':globals()[sys.argv[1]]()
