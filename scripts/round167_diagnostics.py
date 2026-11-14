"""Frozen serial diagnostics. C++ owns all modeling, optimization and oracles."""
from round167_common import *
import csv,os,math
Q=OUT/'qualification'
DRIVER=WORK/'build-cache/round167/Round167Research.exe'
ENV=dict(os.environ,PATH='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+os.environ['PATH'])
FRAMES=['R163-C20-S_root','R163-B20-B_root','R163-X20-S_root','R163-C35-U_root',
        'R163-B35-S_root','R163-X35-S_root','R163-C20-S_child','R163-B20-B_child']
REPS=['R_abs','C166','D167']
def calls(): return sum(p.read_text().count('"phase":"begin"') for p in Q.rglob('Optimize.jsonl'))
def run(label,args,solve=False):
    records=read(Q/'driver_calls.json') if (Q/'driver_calls.json').exists() else []
    old=[r for r in records if r['label']==label]
    if old:
        assert len(old)==1 and old[0].get('exit_code')==0,('failed/incomplete attempt: retain and explicitly repair',label)
        return
    consumed=sum(r.get('seconds',0) for r in records)
    assert consumed<3600 and calls()<96
    if solve:
        assert (OUT/'diagnostic_manifest.json').exists(), 'freeze before first Optimize'
        manifest=read(OUT/'diagnostic_manifest.json')
        assert sha(DRIVER)==manifest['executable']['SHA256']
        assert all(sha(ROOT/p)==digest for p,digest in manifest['CPP_sources'].items())
    rec=dict(label=label,command=[str(DRIVER),*[str(a) for a in args]],UTC=utc(),before_Optimize=calls(),PE_SHA256=sha(DRIVER))
    records.append(rec);write(Q/'driver_calls.json',records)
    log=Q/'logs'/f'{label}.log';log.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    with log.open('wb') as f:
        result=subprocess.run(rec['command'],cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=max(1,3600-consumed))
    rec.update(exit_code=result.returncode,seconds=time.perf_counter()-start,after_Optimize=calls(),log=bind(log))
    write(Q/'driver_calls.json',records)
    print(label,rec['exit_code'],round(rec['seconds'],3),'Optimize',rec['after_Optimize'],flush=True)
    assert result.returncode==0,log
def inherited_frames():
    old=read(ROOT/'results/unified_exact_round166/qualification/driver_calls.json')
    result=[]
    for frame in FRAMES:
        row=next(r for r in old if r['label']==frame+'_B');a=row['command']
        def current(p):
            p=Path(p);text=p.as_posix();oldroot='E:/codes/ExactEBRP-work/worktrees/round166/'
            assert text.startswith(oldroot),p
            return ROOT/text[len(oldroot):]
        inp,parent=current(a[2]),current(a[7]);assert inp.is_file() and parent.is_file()
        result.append(dict(id=frame,input=inp,T=a[3],lam=a[6],parent=parent,lo=a[12],hi=a[13],cutoff=a[14],
                           original_command=a,input_SHA256=sha(inp),parent_SHA256=sha(parent)))
    return result
def preflight():
    Q.mkdir(parents=True,exist_ok=True)
    run('algebra',['algebra',Q/'algebra.json'])
    run('tiny_oracle',['tiny-oracle',Q/'tiny_oracle.csv'])
    for frame in inherited_frames():
        for level in range(3):
            for rep in REPS:
                label=f"{frame['id']}_F{level}_{rep}";directory=Q/'canonical'/label
                run('prepare_'+label,['prepare',frame['input'],frame['T'],frame['lam'],frame['parent'],directory,rep,
                                     frame['lo'],frame['hi'],frame['cutoff'],level,0])
    for local in ['L1','L2','L3','L4']:
        for rep in REPS: run('prepare_'+local+'_'+rep,['local-prepare',local,rep,Q/'local'/(local+'_'+rep)])
    tiny=Q/'tiny';tiny.mkdir(exist_ok=True)
    for name,content in [('optimum.txt','1\n0 4 0 1 2 0\n2 -1\n'),('zero_stock.txt','1\n0 3 0 1 0\n3\n')]:
        target=tiny/name
        if not target.exists(): target.write_text(content,encoding='utf-8')
    inp=ROOT/'results/unified_exact_round166/qualification/tiny/initial3.txt'
    for case,lo,hi,cutoff,parent,s0 in [('nonzero',0,.5,.725,tiny/'optimum.txt',0),('S0',0,0,.3,tiny/'zero_stock.txt',1)]:
        for rep in ['R_abs','D167']:
            label=case+'_'+rep
            run('prepare_'+label,['prepare',inp,360,.15,parent,tiny/label,rep,lo,hi,cutoff,0,s0])
    # No solver export control. The B writer is byte-checked against R166's
    # actually used canonical file, without repeating an old complete run.
    frame=inherited_frames()[0]
    run('unchanged_B',['prepare',frame['input'],frame['T'],frame['lam'],frame['parent'],Q/'unchanged_B','B',frame['lo'],frame['hi'],frame['cutoff'],0,0])
    old=Path('E:/codes/ExactEBRP-work/worktrees/round166/results/unified_exact_round166/qualification/global/R163-C20-S_root_B/model.lp')
    new=Q/'unchanged_B/base.lp'
    write(Q/'B_unchanged.json',dict(PASS=sha(old)==sha(new),old=bind(old),new=bind(new),Optimize=0,
        core_source_unchanged=not git('diff',BASE,'--','src/CplexBaseline.cpp','src/GurobiBaseline.cpp','src/MipStartMapping.cpp','src/IntervalRowFactory.cpp')))
    assert sha(old)==sha(new),'B export bytes changed'
def freeze():
    assert calls()==0 and not (OUT/'diagnostic_manifest.json').exists()
    frames=inherited_frames();positions=[]
    for frame in frames:
        common=None
        for level in range(3):
            for rep in REPS:
                sid=f"{frame['id']}_F{level}_{rep}";folder=Q/'canonical'/sid;data=read(folder/'prepare.json')
                positions.append(dict(id=sid,kind='canonical',frame=frame['id'],representation=rep,level=level,
                    folder=folder.relative_to(ROOT).as_posix(),mask=data['mask'],conditional_stocks=data['conditional_stocks'],
                    selected_station=data['selected_station'],degenerate=data['degenerate'],model=bind(folder/'model.lp'),
                    common_SHA256=data['common_SHA256'],objective='original G + lambda sum omega e',Native_TimeLimit=20))
                if rep!='C166':
                    if common is None:common=data['common_SHA256']
                    assert common==data['common_SHA256'],'R_abs/D167 common block mismatch'
    for local in ['L1','L2','L3','L4']:
        for rep in REPS:
            folder=Q/'local'/(local+'_'+rep)
            positions.append(dict(id=local+'_'+rep,kind='local',representation=rep,folder=folder.relative_to(ROOT).as_posix(),model=bind(folder/'model.lp'),Native_TimeLimit=5))
    for case in ['nonzero','S0']:
        for rep in ['R_abs','D167']:
            folder=Q/'tiny'/(case+'_'+rep)
            positions.append(dict(id=case+'_'+rep,kind='tiny',representation=rep,folder=folder.relative_to(ROOT).as_posix(),model=bind(folder/'model.lp'),Native_TimeLimit=60))
    # Local checks run before the canonical matrix. No adaptive masks/objectives.
    positions=positions[72:84]+positions[:72]+positions[84:]
    sourcepaths=['src/round167_research.cpp','include/Round167ConditionalState.hpp']
    write(OUT/'diagnostic_manifest.json',dict(UTC=utc(),frozen_before_Optimize=True,Optimize_at_freeze=calls(),
        schema='round167-fixed-88-plus-8-repair-only-v1',max_Optimize=96,reserved_repair_calls=8,max_diagnostic_outer_seconds=3600,
        science_remaining_at_freeze_seconds=36000-(time.time()-read(OUT/'entry_state.json')['work_start_unix']),
        paper_and_review_reserved_seconds=10800,positions=positions,frames=[{k:str(v) if isinstance(v,Path) else v for k,v in r.items()} for r in frames],
        executable=bind(DRIVER),CPP_sources={p:sha(ROOT/p) for p in sourcepaths},
        DLL=bind(Path('D:/gurobi1302/win64/bin/gurobi130.dll')),
        parameters=dict(Threads=1,Seed=0,MIPGap=0,MIPGapAbs=0,NodeLimit='infinity',FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5,other_strategies='Native defaults'),
        type_policy='all integer columns relaxed for pure LP; original types restored; R_abs s/q continuous even in tiny MIP',
        no_history_time_speedup_claim=True,no_complete_method_runs=True))
    print('Frozen 72 canonical + 12 local + 4 tiny positions before Optimize.')
def boundaries():
    run('algebra_final',['algebra',Q/'algebra_final.json'])
    tiny=Q/'tiny';parent=tiny/'positive_loaded_return.txt'
    if not parent.exists():parent.write_text('1\n0 3 0 1 0\n1\n',encoding='utf-8')
    inp=ROOT/'results/unified_exact_round166/qualification/tiny/initial3.txt'
    for case,lo in [('fixed_positive',.5),('narrow_positive',.5-1e-12)]:
        for rep in ['R_abs','D167']:
            run('prepare_'+case+'_'+rep,['prepare',inp,360,.15,parent,tiny/(case+'_'+rep),rep,lo,.5,.725,0,0])
def execute():
    manifest=read(OUT/'diagnostic_manifest.json')
    for position in manifest['positions']:
        folder=ROOT/position['folder'];assert sha(folder/'model.lp')==position['model']['SHA256']
        run('solve_'+position['id'],['solve',folder,'MIP' if position['kind']=='tiny' else 'LP',position['Native_TimeLimit']],True)
        if position['kind']=='local':
            receipt=read(folder/'solve.json');assert receipt['qualified_optimum'],position['id']
            if position['representation']!='C166':assert abs(receipt['objective']-1)<=1e-7,position['id']
            if position['id']=='L4_D167':write(Q/'local_admission.json',dict(UTC=utc(),PASS=True,actual_Optimize=calls(),canonical_Optimize=0,scope='all 12 predeclared local LPs qualified before canonical solves'))
def summarize():
    manifest=read(OUT/'diagnostic_manifest.json');positions=[]
    for p in manifest['positions']:
        folder=ROOT/p['folder'];s=read(folder/'solve.json') if (folder/'solve.json').exists() else dict(native_status='UNEXECUTED')
        data=read(folder/'prepare.json');positions.append(dict(**p,prepare=data,solve=s))
    write(OUT/'positions.json',positions)
    fields=['id','kind','representation','frame','level','native_status','qualified_optimum','objective','lower','mask','conditional_stocks','common_SHA256','columns','binaries','rows','nonzeros','build_seconds','runtime','work','outer_seconds']
    with (OUT/'positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader()
        for p in positions:
            merged={**p,**p['prepare'],**p['solve']};merged['id']=p['id']
            w.writerow({key:json.dumps(merged.get(key,[])) if key=='mask' else merged.get(key,'') for key in fields})
    triples=[]
    for frame in FRAMES:
        for level in range(3):
            group={r:next(p for p in positions if p['id']==f'{frame}_F{level}_{r}') for r in REPS}
            values={r:group[r]['solve']['objective'] for r in REPS}
            allqualified=all(group[r]['solve'].get('qualified_optimum') for r in REPS)
            if allqualified:
                assert abs(values['D167']-values['R_abs'])<=1e-7,(frame,level,values)
                assert values['D167']>=values['C166']-1e-7,(frame,level,values)
                if level==0:assert max(values.values())-min(values.values())<=1e-7
            triples.append(dict(frame=frame,level=level,values=values,all_qualified=allqualified,
                                delta_D167_C166=values['D167']-values['C166'] if allqualified else None))
    local={p['id']:p['solve']['objective'] for p in positions if p['kind']=='local'}
    for label in ['L1','L2','L3','L4']:
        for rep in ['R_abs','D167']:assert abs(local[label+'_'+rep]-1)<=1e-7
    assert local['L1_C166']==0 and local['L2_C166']==0 and local['L4_C166']==0
    for case,value in [('nonzero',.15),('S0',.3)]:
        for rep in ['R_abs','D167']:
            p=next(p for p in positions if p['id']==case+'_'+rep);assert p['solve']['qualified_optimum'] and abs(p['solve']['objective']-value)<=1e-7
    records=read(Q/'driver_calls.json');fee=sum(r['seconds'] for r in records)
    write(OUT/'qualification.json',dict(UTC=utc(),PASS=True,actual_Optimize=calls(),positions=len(positions),canonical_positions=72,local_positions=12,tiny_positions=4,
        unexecuted=sum('UNEXECUTED'==p['solve']['native_status'] for p in positions),qualified=sum(bool(p['solve'].get('qualified_optimum')) for p in positions),
        diagnostic_outer_seconds=fee,Native_Runtime=sum(p['solve'].get('runtime',0) for p in positions),
        triples=triples,local=local,algebra=read(Q/'algebra.json'),B_unchanged=read(Q/'B_unchanged.json'),new_complete_GI_TBC_P_runs=0))
    assert calls()<=96 and fee<=3600
    print('Qualified',calls(),'Optimize, diagnostic outer',round(fee,3),'seconds.')
if __name__=='__main__':globals()[sys.argv[1]]()
