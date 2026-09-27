"""Two charged observational runs, reusing the measured v5 static core unchanged."""
import argparse,subprocess,csv,hashlib,json,shutil
from pathlib import Path
import round65_research as r

DIRECTORY=r.BUILD.parent/(r.BUILD.name+'-hga-timing')
EXE=DIRECTORY/'Round65HgaTiming.exe'
SOURCE=r.ROOT/'scripts/round65_hga_timing.cpp'
LIBRARY=r.BUILD/'libexact_ebrp_core.a'
FREEZE=r.OUT/'hga_timing_build.json'
ENABLE_DECODER_COUNTER=False

def build():
    if (r.OUT/'active_run.lock').exists():raise RuntimeError('no compilation during performance')
    if FREEZE.exists():raise RuntimeError('timing build already frozen')
    if EXE.exists():raise RuntimeError('preserve retained timing binary; choose a separate EBRP_ROUND65_BUILD for reproduction')
    active=r.read(r.OUT/r.read(r.OUT/'active_build.json')['file'])
    for path,value in active['source_files'].items():assert r.sha(r.ROOT/path)==value
    references={}
    for identity in ['C5','C7']:
        eligible=[e for e in r.runner.entries() if e['id']==identity and e['arm'] in ['candidate','reliable']
                  and (r.ROOT/e['destination']/'completion.json').exists()]
        if not eligible:raise RuntimeError('run a reliability control for '+identity+' before timing')
        chosen=max(eligible,key=lambda e:(e['arm']=='candidate',e['charged_number']))
        path=r.ROOT/chosen['destination']/'hga.csv'
        # Do not import older campaign verifiers here: their legacy runner
        # module has mutable global paths. Keep this build-only binding local.
        with path.open(encoding='utf-8-sig',newline='') as trajectory:
            logical=[{key:row[key] for key in ['generation','best_fitness','strict_improvement']}
                     for row in csv.DictReader(trajectory)]
        logical_sha=hashlib.sha256(json.dumps(logical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        references[identity]=dict(path=str(path.relative_to(r.ROOT)),sha256=r.sha(path),
                                  logical_sha256=logical_sha,launch_number=chosen['charged_number'])
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    compiler=['D:/msys64/ucrt64/bin/c++.exe','-O3','-DNDEBUG','-std=c++17','-Wall','-Wextra','-Wpedantic',
              '-DEXACT_EBRP_ENABLE_GUROBI=1']
    instrumentation={};objects=[]
    if ENABLE_DECODER_COUNTER:
        copied=DIRECTORY/'counter-include/hga_tgbc'
        shutil.copytree(r.ROOT/'include/hga_tgbc',copied)
        original=r.ROOT/'include/hga_tgbc/HybridGA.h';changed=copied/'HybridGA.h'
        content=original.read_text(encoding='utf-8')
        before='const auto decode_started = fixed_generations >= 0 ? steady_clock::now()\n                                                       : steady_clock::time_point{};'
        after='const auto decode_started = steady_clock::now();'
        guard='if (fixed_generations >= 0)\n        decoder_seconds += duration<double>(steady_clock::now() - decode_started).count();'
        assert content.count(before)==content.count(guard)==1
        changed.write_text(content.replace(before,after).replace(guard,
            'decoder_seconds += duration<double>(steady_clock::now() - decode_started).count();'),encoding='utf-8')
        adapter=r.ROOT/'src/HgaTgbcRunner.cpp';obj=DIRECTORY/'timed_hga_adapter.o'
        compile_command=compiler+['-I'+str(copied.parent),'-I'+str(r.ROOT/'include'),'-c',str(adapter),'-o',str(obj)]
        with (DIRECTORY/'adapter_build.log').open('w') as log:
            subprocess.run(compile_command,cwd=r.ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        objects=[str(obj)]
        instrumentation=dict(source=str(original.relative_to(r.ROOT)),original_sha256=r.sha(original),
            transformed_header=str(changed.relative_to(r.ROOT)),transformed_header_sha256=r.sha(changed),
            runner_source=str(adapter.relative_to(r.ROOT)),runner_source_sha256=r.sha(adapter),
            runner_object=str(obj.relative_to(r.ROOT)),runner_object_sha256=r.sha(obj),compile_command=compile_command,
            change='enable only the two decoder timing guards; no genetic or stopping change')
    command=compiler+['-I'+str(r.ROOT/'include'),str(SOURCE)]+objects+[str(LIBRARY),'-o',str(EXE)]
    library_hash=r.sha(LIBRARY)
    with (DIRECTORY/'build.log').open('w') as log:subprocess.run(command,cwd=r.ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert r.sha(LIBRARY)==library_hash
    r.write(FREEZE,dict(solver_build=r.read(r.OUT/'active_build.json'),source=str(SOURCE.relative_to(r.ROOT)),
        source_sha256=r.sha(SOURCE),core_archive=str(LIBRARY.relative_to(r.ROOT)),core_archive_sha256=library_hash,
        executable=str(EXE.relative_to(r.ROOT)),executable_sha256=r.sha(EXE),command=command,
        changes_to_measured_solver=False,optimizer_calls=0,reference_trajectories=references,
        decoder_counter_enabled=ENABLE_DECODER_COUNTER,instrumentation=instrumentation,
        planned_roles=['C5','C7'],planned_charged_launches=2,cap_seconds=120,
        reliability_category_extension=dict(previous_plan=8,with_timing=12 if ENABLE_DECODER_COUNTER else 10,hard_total_limit=72),
        scope='aggregate HGA timing only, no performance qualification'))

def run():
    frozen=r.read(FREEZE)
    for path,value in [(SOURCE,frozen['source_sha256']),(LIBRARY,frozen['core_archive_sha256']),(EXE,frozen['executable_sha256'])]:
        assert r.sha(path)==value
    for identity in ['C5','C7']:
        p=r.panel()[identity];assert r.sha(r.ROOT/p['instance_path'])==p['input_sha256']
        stage='timing_decoder_v5' if ENABLE_DECODER_COUNTER else 'timing_v5'
        arm='timing-decoder' if ENABLE_DECODER_COUNTER else 'timing-reliable'
        folder=r.RAW/stage/identity/arm
        command=[EXE,p['instance_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],folder]
        r.runner.execute(command,folder,dict(id=identity,arm=arm,stage=stage,
            build_freeze=FREEZE.name),120,'hga-timing-diagnostic',0)
        assert r.read(folder/'hga_timing.json')['optimizer_calls']==0
        if ENABLE_DECODER_COUNTER:assert r.read(folder/'hga_timing.json')['decoder_seconds']>0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','run','decoder-build','decoder-run'])
    action=parser.parse_args().action
    if action.startswith('decoder-'):
        ENABLE_DECODER_COUNTER=True
        DIRECTORY=r.BUILD.parent/(r.BUILD.name+'-hga-decoder-timing')
        EXE=DIRECTORY/'Round65HgaTiming.exe'
        FREEZE=r.OUT/'hga_decoder_timing_build.json'
    build() if action.endswith('build') else run()
