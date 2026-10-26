"""Frozen small batch qualification: direct wrapper and original native children."""
from round110_common import *
import csv, re, shutil, struct, traceback

def pe_header(path):
    data=Path(path).read_bytes();offset=struct.unpack_from('<I',data,0x3c)[0]
    assert data[offset:offset+4]==b'PE\0\0'
    optional=offset+24;assert struct.unpack_from('<H',data,optional)[0]==0x20b
    reserve,commit=struct.unpack_from('<QQ',data,optional+72)
    return dict(machine=hex(struct.unpack_from('<H',data,offset+4)[0]),stack_reserve_bytes=reserve,stack_commit_bytes=commit,
        PE_SHA=sha(path),PE_bytes=len(data))

def prepare():
    old=Path('E:/codes/ExactEBRP-round109')
    identity=read(old/'results/unified_exact_round109/candidate_identity.json')
    old_bindings=identity['source_bindings'];current=bindings()
    changes={k:dict(old_SHA=v,new_SHA=current.get(k)) for k,v in old_bindings.items() if current.get(k)!=v}
    assert set(changes)=={'src/Parser.cpp'}
    old_build=OUT/'engineering/initialization01/inherited_build.ninja'
    new_build=BUILD/'build.ninja'
    def flags(path):
        # SOURCE_DIR is used by separate test targets and necessarily tracks
        # checkout location; it is not a production optimization/link setting.
        return sorted(set(line.strip() for line in path.read_text().splitlines()
            if line.strip().startswith(('FLAGS =','LINK_FLAGS =','DEFINES =')) and 'EXACT_EBRP_SOURCE_DIR' not in line))
    assert flags(old_build)==flags(new_build),(flags(old_build),flags(new_build))
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    toolchain={p:sha(Path('D:/msys64/ucrt64/bin')/p) for p in ['g++.exe','libstdc++-6.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll']}
    production=dict(production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL_SHA=sha(DLL),source_bindings=current,
        base=BASE,changes=changes,PE_header=pe_header(BUILD/'ExactEBRP.exe'),old_PE_header=pe_header(old/'build/research/round109-inherited-mb-v1/ExactEBRP.exe'),
        build_flag_set=flags(new_build),inherited_build_flag_set=flags(old_build),build_type='',CXX_flags='',link_flags='',
        compiler=str(compiler),toolchain=toolchain,
        configure_launch_SHA=sha(OUT/'engineering/configure01/launch.json'),configure_receipt_SHA=sha(OUT/'engineering/configure01/receipt.json'),
        build_launch_SHA=sha(OUT/'engineering/build01/launch.json'),build_receipt_SHA=sha(OUT/'engineering/build01/receipt.json'))
    assert production['production_PE_SHA']!=OLD_PE_SHA and production['DLL_SHA']==DLL_SHA
    assert production['PE_header']['stack_reserve_bytes']==production['old_PE_header']['stack_reserve_bytes']==2097152
    write(OUT/'production_identity.json',production)
    q=OUT/'qualification'
    manifest=read(OUT/'input_manifest.json');lines=[];mapping=[];groups={}
    for p in manifest['roles']:
        lines.append(p['input_path']+'\t'+str(p['T_seconds']))
        T=p['T_seconds'];directory=q/'main_inputs'/str(T);directory.mkdir(parents=True,exist_ok=True)
        target=directory/Path(p['input_path']).name;shutil.copyfile(ROOT/p['input_path'],target)
        assert sha(target)==p['input_sha256']
        mapping.append(dict(id=p['id'],source=p['input_path'],mapped=target.relative_to(ROOT).as_posix(),SHA=sha(target),T=T))
        groups[T]=directory
        source=old/'results/unified_exact_round109/qualification/reference'/p['id']
        dest=q/'reference'/p['id'];dest.mkdir(parents=True)
        for name in ['original.lp','build.json']:shutil.copyfile(source/name,dest/name)
        assert read(dest/'build.json')['canonical_sha256']==sha(dest/'original.lp')
    source=old/'results/unified_exact_round109/qualification/reference/H100';dest=q/'reference/H100';dest.mkdir(parents=True)
    for name in ['original.lp','build.json']:shutil.copyfile(source/name,dest/name)
    (q/'parser_batch.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    wrappers=[]
    for variant,parser in [('old',OUT/'engineering/initialization01/old_Parser.cpp'),('new',ROOT/'src/Parser.cpp')]:
        source=BUILD/f'parser_{variant}.cpp'
        source.write_text('#include "'+parser.as_posix()+'"\n#include "'+(ROOT/'scripts/round110_parser_batch.inc').as_posix()+'"\n',encoding='utf-8',newline='\n')
        wrappers.append(dict(variant=variant,source=str(source),source_SHA=sha(source),Parser_source_SHA=sha(parser),
            compiler_command=[str(compiler),'-std=c++17','-Wall','-Wextra','-Wpedantic','-I'+str(ROOT/'include'),str(source),'-o',str(BUILD/f'Round110Parser_{variant}.exe')]))
    write(q/'parser_build_plan.json',dict(wrappers=wrappers,toolchain=toolchain,flags=['-std=c++17','-Wall','-Wextra','-Wpedantic'],Optimize=0))
    entries=[]
    for T,directory in sorted(groups.items()):
        d=q/'main_entry'/str(T)
        command=[str(BUILD/'ExactEBRP.exe'),'--method','option-consistency-test','--input',str(directory),
            '--lambda','0.15','--T',str(T),'--pickup-time','60','--drop-time','60','--time-limit','120',
            '--process-wall-time-limit','120','--threads','1','--mip-threads','1','--gurobi-seed','0',
            '--algorithm-preset','custom','--frontier-execution-mode','external-gini-tree',
            '--auto-interval-oracle','false','--auto-interval-bpc-fallback','false','--primal-heuristic','none',
            '--out',str(d/'result.json'),'--log',str(d/'native.log'),'--process-phase-ledger',str(d/'phases.csv')]
        entries.append(dict(T=T,destination=str(d),command=command,expected_names=sorted(x['id']+'.txt' for x in mapping if x['T']==T)))
    write(q/'main_entry_plan.json',dict(entries=entries,path_mapping=mapping,production_PE_SHA=production['production_PE_SHA'],
        diagnostic='option-consistency-test',Optimize=0,heuristic=False,oracle=False,extra_native_child=False,
        source_path_proof=dict(parseArgs='src/main.cpp',common_main='src/main.cpp',diagnostic='solveOptionConsistencyDiagnostic',
            postprocess='external-gini-tree branch bypasses runAutoIntervalOracleClosure; serialization and phase exit only')))
    print('new PE and exact inherited flags bound; parser/main plans and exact cold references frozen')

def billed_zero(kind):
    from round100_idle import ensure_idle
    tick,creation=process_origin();ensure_idle();identity=check_identity();q=OUT/'qualification'
    if kind=='parser':
        specs=[dict(destination=str(q/'parser_equivalence'/v),command=[str(BUILD/f'Round110Parser_{v}.exe'),str(q/'parser_batch.tsv')]) for v in ['old','new']]
        label='parser_equivalence01'
    else:
        specs=read(q/'main_entry_plan.json')['entries'];label='main_entry01'
        if kind=='main-resume':
            assert read(OUT/'fees/main_entry01/receipt.json')['exit_code']==1
            specs=[spec for spec in specs if not Path(spec['destination']).exists()]
            assert len(specs)==2, 'only the two never-started T groups'
            label='main_entry02'
            write(q/'main_entry_resumption_plan.json',dict(original_fee_retained=True,original_declared_starts=4,
                original_actual_children=1,new_starts=3,new_native_children=2,no_rerun=True,
                reason='offline audit expected phase column; actual ledger schema uses event; native3600 returned normally'))
    b=budget();starts=1+len(specs)
    assert not b['unclosed'] and b['qualification_starts']+starts<=20
    assert b['remaining_starts']>=starts+57 and b['remaining_outer_seconds']>=88200+1800+2000-b['qualification_seconds']
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[sys.executable,__file__,'billed-zero',kind],cwd=str(ROOT),qualification=True,
        conservative_process_starts=starts,declared_native_children=len(specs),actual_wrapper_processes=1,
        children=specs,production_PE_SHA=identity['production_PE_SHA'],DLL_SHA=DLL_SHA,wrapper_creation_unix=creation,budget_before=b,
        zero_Optimize=True,cap_seconds=480))
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0;actual=0;completed=[]
    try:
        for spec in specs:
            dest=Path(spec['destination']);dest.mkdir(parents=True,exist_ok=False)
            command=spec['command'];binary=Path(command[0]);start=time.perf_counter()
            write(dest/'launch.json',dict(command=command,cwd=str(ROOT),PE_SHA=sha(binary),DLL_SHA=DLL_SHA,
                source_bindings=identity['source_bindings'],started_unix=time.time(),Optimize=0))
            with (dest/'stdout.log').open('xb') as so,(dest/'stderr.log').open('xb') as se:
                child=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se);actual+=1
                write(dest/'process.json',dict(pid=child.pid,parent_pid=os.getpid()))
                rc=child.wait(timeout=120)
            receipt=dict(exit_code=rc,process_seconds=time.perf_counter()-start,PE_SHA=sha(binary),stdout_SHA=sha(dest/'stdout.log'),stderr_SHA=sha(dest/'stderr.log'),Optimize=0)
            write(dest/'raw_exit_receipt.json',receipt);assert rc==0,receipt
            if kind=='parser': assert 'batch_complete\t12\tOptimize=0' in (dest/'stderr.log').read_text()
            else:
                with (dest/'phases.csv').open(newline='') as f: phases=list(csv.DictReader(f))
                done=[r for r in phases if r['event']=='instance_parsing_complete']
                assert sorted(r['detail'].split('instance=',1)[1] for r in done)==spec['expected_names'],done
                results=read(dest/'result.json');assert len(results)==len(spec['expected_names'])
                for r in results:
                    assert r['method']=='option-consistency-test' and r['status']=='diagnostic_complete' and r['option_audit_consistent']
                    assert r['route_time_limit_seconds']==spec['T'] and r['pickup_time_seconds']==r['drop_time_seconds']==60
                    assert all(value==0 for key,value in r.items() if key.endswith('optimize_count'))
                    assert r['primal_heuristic']=='none' and all(not route.get('operations') for route in r['routes'])
                assert phases[-1]['event']=='process_exit' and phases[-1]['detail']=='rc=0'
            completed.append(dict(destination=dest.relative_to(ROOT).as_posix(),raw_exit_receipt_SHA=sha(dest/'raw_exit_receipt.json'),PE_SHA=sha(binary)))
        if kind=='parser':
            old=q/'parser_equivalence/old/stdout.log';new=q/'parser_equivalence/new/stdout.log'
            assert old.read_bytes()==new.read_bytes(),'C++ mathematical/extraction bitwise mismatch'
            write(q/'parser_equivalence_receipt.json',dict(passed=True,instances=12,finite_extraction_cases=16,
                binary64_bitwise_equal=True,integer_fields_exact=True,old_dump=old.relative_to(ROOT).as_posix(),new_dump=new.relative_to(ROOT).as_posix(),
                dump_SHA=sha(new),parser_plan_SHA=sha(q/'parser_build_plan.json'),metadata_separate=True,Optimize=0,completed=completed))
        else:
            all_completed=[]
            for spec in read(q/'main_entry_plan.json')['entries']:
                dest=Path(spec['destination']);exit_record=read(dest/'raw_exit_receipt.json')
                assert exit_record['exit_code']==0 and exit_record['PE_SHA']==identity['production_PE_SHA']
                with (dest/'phases.csv').open(newline='') as f: phases=list(csv.DictReader(f))
                assert sorted(r['detail'].split('instance=',1)[1] for r in phases if r['event']=='instance_parsing_complete')==spec['expected_names']
                assert phases[-1]['event']=='process_exit' and phases[-1]['detail']=='rc=0'
                results=read(dest/'result.json');assert len(results)==len(spec['expected_names'])
                for r in results:
                    assert r['method']=='option-consistency-test' and r['status']=='diagnostic_complete' and r['option_audit_consistent']
                    assert r['route_time_limit_seconds']==spec['T'] and r['pickup_time_seconds']==r['drop_time_seconds']==60
                    assert all(value==0 for key,value in r.items() if key.endswith('optimize_count'))
                    assert r['primal_heuristic']=='none' and all(not route.get('operations') for route in r['routes'])
                all_completed.append(dict(destination=dest.relative_to(ROOT).as_posix(),raw_exit_receipt_SHA=sha(dest/'raw_exit_receipt.json'),PE_SHA=identity['production_PE_SHA']))
            write(q/'main_entry_receipt.json',dict(passed=True,instances=12,processes=3,production_PE_SHA=identity['production_PE_SHA'],
                all_instance_parsing_complete=True,all_normal_return=True,Optimize=0,heuristic=False,oracle=False,completed=all_completed,
                plan_SHA=sha(q/'main_entry_plan.json'),old_failed_offline_wrapper_preserved=kind=='main-resume'))
    except BaseException:
        code=1;(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,conservative_process_starts=starts,
            actual_native_children_with_launch=actual,stop_reason='normal_return' if code==0 else 'actual_exception',qualification=True,nested_seconds_added=False))
        print(json.dumps(read(d/'receipt.json')),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='compile-parser':
        for x in read(OUT/'qualification/parser_build_plan.json')['wrappers']: engineering('compile_parser_'+x['variant']+'01',x['compiler_command'])
    elif sys.argv[1]=='billed-zero':billed_zero(sys.argv[2])
    else:raise ValueError(sys.argv[1])
