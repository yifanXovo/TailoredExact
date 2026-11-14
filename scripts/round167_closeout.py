"""Read-only verification and explicit research/receipt bookkeeping."""
from round167_common import *
import csv,shutil,zipfile
Q=OUT/'qualification';PAPER=ROOT/'results/unified_exact_round137'
def evidence():
    start=time.perf_counter();positions=read(OUT/'positions.json');manifest=read(OUT/'diagnostic_manifest.json')
    assert len(positions)==88
    with (OUT/'positions.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==88 and len({r['id'] for r in rows})==88
    assert [r['id'] for r in rows]==[p['id'] for p in positions]
    for p in positions:
        folder=ROOT/p['folder'];assert sha(folder/'model.lp')==p['model']['SHA256']==p['solve']['fingerprint']
        assert p['solve']['qualified_optimum'] and p['solve']['original_types_restored']
        params=read(folder/'parameters.json');assert params['Threads']==1 and params['Seed']==0 and params['MIPGap']==params['MIPGapAbs']==0
        assert params['NodeLimit']>=1e99 and params['TimeLimit']==p['Native_TimeLimit']
    count=sum(p.read_text().count('"phase":"begin"') for p in Q.rglob('Optimize.jsonl'));assert count==88
    oldroot=WORK/'worktrees/round166/results/unified_exact_round166/qualification/global'
    historical=[]
    for p in positions:
        if p.get('kind')=='canonical' and p['level']==0 and p['representation'] in ['R_abs','C166']:
            arm='B' if p['representation']=='R_abs' else 'C166'
            path=oldroot/(p['frame']+'_'+arm)/'model.lp';new=ROOT/p['folder']/'base.lp'
            assert sha(path)==sha(new),(p['id'],'historical canonical base changed')
            historical.append(dict(id=p['id'],old_SHA256=sha(path),current_base_SHA256=sha(new)))
    write(OUT/'evidence_checks.json',dict(UTC=utc(),PASS=True,Optimize=0,actual_calls=count,unique_position_ids=88,
        complete_models_fingerprints=True,actual_parameters=True,types_restored=True,historical_canonical_byte_controls=historical,
        core_default_sources_unchanged=not git('diff',BASE,'--','src/CplexBaseline.cpp','src/GurobiBaseline.cpp','src/MipStartMapping.cpp','src/IntervalRowFactory.cpp'),
        parameter_resource_authorities_unchanged=not git('diff',BASE,'--','results/unified_exact_round166/analysis'),seconds=time.perf_counter()-start))
    print('Evidence identities, parameters, unique position IDs and 16 historical model-byte controls PASS.')
def build_manifest():
    directory=WORK/'build-cache/round167';dest=OUT/'build';dest.mkdir(exist_ok=True)
    for name in ['CMakeCache.txt','.ninja_log']:
        target=dest/(name.lstrip('.'));shutil.copyfile(directory/name,target)
    exe=directory/'Round167Research.exe'
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    cpp=['src/round167_research.cpp','include/Round167ConditionalState.hpp']
    core=['src/CplexBaseline.cpp','src/GurobiBaseline.cpp','src/MipStartMapping.cpp','src/IntervalRowFactory.cpp','include/Round166Research.hpp']
    cmake='D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
    configure=[cmake,'-S',str(ROOT),'-B',str(directory),'-G','Ninja','-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
        '-DCMAKE_MAKE_PROGRAM=D:/PROGRA~1/MICROS~1/2022/PROFES~1/Common7/IDE/COMMON~1/MICROS~1/CMake/Ninja/ninja.exe',
        '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DEXACT_EBRP_BUILD_ROUND167_RESEARCH=ON','-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE=','-DCMAKE_CXX_FLAGS=']
    write(OUT/'candidate_manifest.json',dict(UTC=utc(),scope='offline representation diagnostics only',base_source=BASE,
        sources={p:sha(ROOT/p) for p in cpp},frozen_core_sources={p:sha(ROOT/p) for p in core},
        executable=bind(exe),DLL=bind(Path('D:/gurobi1302/win64/bin/gurobi130.dll')),compiler=bind(compiler),
        compiler_version=subprocess.check_output([str(compiler),'--version']).decode('utf-8',errors='replace'),
        configure_command=configure,build_command=[cmake,'--build',str(directory),'--target','Round167Research','-j','4'],
        CMake_cache=bind(dest/'CMakeCache.txt'),full_rebuild_core=True,production_default_changed=False,
        prepare_v1='build/preparation_v1.json',v1_repair='guard receiver construction when b=u to avoid INT_MAX b+1; add parameter/dual evidence; no prepared mathematical matrix changed',
        final_PE_all_88_solves=True,prepared_models_individually_fingerprinted=True,commercial_DLL_published=False))
    print('Actual new source/compiler/PE/DLL identity and build recorded.')
def costs():
    records=read(Q/'driver_calls.json');producer=sum(r['seconds'] for r in records)
    # A conservative enclosing window includes interleaved derivation/build,
    # wrapper management and both summary-reader fixes, avoiding an understated
    # subprocess-only outer fee. Review calculations are separately included.
    first=min(datetime.fromisoformat(r['UTC']).timestamp() for r in records)
    reader=read(Q/'reader_repair.json')
    csv_repair=read(Q/'CSV_id_repair.json')
    evidence_end=read(OUT/'evidence_checks.json')['UTC']
    last=max([datetime.fromisoformat(r['UTC']).timestamp()+r['seconds'] for r in records]+
             [datetime.fromisoformat(reader['UTC']).timestamp(),datetime.fromisoformat(csv_repair['UTC']).timestamp(),datetime.fromisoformat(evidence_end).timestamp()])
    review=[]
    for name in ['math_final.json','data_final.json']:
        p=OUT/'review'/name
        if p.exists():
            report=read(p)
            if name=='math_final.json':value=report.get('first_reader_attempt_seconds_conservative',0)+report.get('independent_offline_seconds_success',0)
            else:value=report.get('independent_offline_seconds_total_conservative',0)
            review.append(dict(report=bind(p),seconds=value))
    manuscript=OUT/'review/manuscript_checks.json'
    if manuscript.exists():
        value=read(manuscript)
        review.append(dict(report=bind(manuscript),seconds=value.get('seconds',value.get('offline_seconds',.18))))
    conservative=last-first+sum(v['seconds'] for v in review)
    assert conservative<3600
    entry=read(OUT/'entry_state.json');elapsed=time.time()-entry['work_start_unix']
    write(OUT/'cost_report.json',dict(UTC=utc(),actual_Optimize=88,unused_reserved_Optimize=8,max_Optimize=96,
        recorded_CPP_subprocess_outer_seconds=producer,Native_Runtime_seconds=read(OUT/'qualification.json')['Native_Runtime'],
        diagnostic_enclosing_window_begin_UTC=datetime.fromtimestamp(first,timezone.utc).isoformat(),
        diagnostic_enclosing_window_end_UTC=datetime.fromtimestamp(last,timezone.utc).isoformat(),
        conservative_diagnostic_window_seconds=last-first,includes_interleaved_build_derivation_management_reader_repair=True,
        independent_offline_review_computation=review,conservative_diagnostic_total_seconds=conservative,
        no_double_addition_of_nested_CPP_Runtime=True,max_diagnostic_outer_seconds=3600,
        conservative_science_elapsed_seconds=elapsed,max_science_window_seconds=36000,
        paper_and_review_reservation_at_freeze_seconds=10800,
        science_remaining_at_freeze=read(OUT/'diagnostic_manifest.json')['science_remaining_at_freeze_seconds'],
        ordinary_git_public_transfer_IO='recorded separately in delivery receipt; not reported as Optimize/scientific calculation',
        work_completed_early_allowed=True))
    qual=read(OUT/'qualification.json');qual['diagnostic_CPP_subprocess_seconds']=qual.pop('diagnostic_outer_seconds',producer)
    qual.update(conservative_diagnostic_total_seconds=conservative,diagnostic_cost_authority='cost_report.json')
    write(OUT/'qualification.json',qual)
    print('Diagnostic conservative total',round(conservative,3),'s; recorded subprocesses',round(producer,3),'s.')
def protect():
    before=read(OUT/'entry_state.json')['protected'];after=protected();assert before==after,'protected tracked files changed'
    write(OUT/'protected_tree_check.json',dict(UTC=utc(),PASS=True,protected=after,tracked_status_and_dirty_file_bytes_equal=True,zero_delete=True))
if __name__=='__main__':globals()[sys.argv[1]]()
