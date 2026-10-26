"""Fresh bounded reproduction; never overwrites the measured evidence."""
import argparse, os, re, shutil, subprocess, time
import round68_research as run

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
    ap.add_argument('--ids',nargs='+',required=True,choices=list(run.panel()))
    ap.add_argument('--arms',nargs='+',default=['P-GRB','K1-R','VD-P','VD-S'],choices=['P-GRB','K1-R','VD-P','VD-S'])
    ap.add_argument('--ctest',default='D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe')
    ap.add_argument('--cap',type=int,required=True,choices=[20,300,600]);a=ap.parse_args()
    destination=(run.ROOT/a.output).resolve();original=run.OUT
    if (original/'active_run.lock').exists():raise RuntimeError('Wait for the measured serial queue before reproduction qualification')
    if destination.exists() or not destination.is_relative_to(run.ROOT):raise RuntimeError('Need a new output directory inside this checkout')
    if len(set(a.ids))!=len(a.ids) or len(set(a.arms))!=len(a.arms):raise RuntimeError('Duplicate launch request')
    protocol=run.read(original/'protocol.json')
    assert all(protocol['caps'][i]==a.cap for i in a.ids),'Use separate batches for distinct whole-run deadlines'
    maximum=len(a.ids)*len(a.arms)
    assert maximum<=(4 if a.cap==20 else 16),'Bounded reproduction plan exceeded'
    destination.mkdir(parents=True)
    for name in ['plan.md','mathematics.md']:
        shutil.copyfile(original/name,destination/name)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    started=time.monotonic()
    test=subprocess.run([a.ctest,'--test-dir',str(run.BUILD),'--output-on-failure'],cwd=run.ROOT,env=env,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    test_wall=time.monotonic()-started
    (destination/'qualification_tests.log').write_bytes(test.stdout)
    if test.returncode:raise RuntimeError('Fresh build qualification failed; no experiment launched')
    match=re.search(rb'100% tests passed, 0 tests failed out of (\d+)',test.stdout)
    if not match or int(match[1])!=45:raise RuntimeError('Unexpected qualification test count')
    bound_build=destination/'bound_build';bound_build.mkdir()
    for name in ['ExactEBRP.exe','Round65ReferenceBuild.exe']:
        shutil.copyfile(run.BUILD/name,bound_build/name)
    shutil.copyfile(destination/'qualification_tests.log',bound_build/'tests.log')
    run.BUILD=bound_build;run.runner.BUILD=bound_build
    run.write(destination/'qualification.json',dict(final_ctest_passed_tests=int(match[1]),final_ctest_batches=1,
        ctest_wall_seconds=test_wall,new_native_qualification_optimize_calls=3,
        ctest_note='Fresh reproduction qualification, not copied historical results; other native unit-test calls not claimed counted',
        final_binary_sha256=run.sha(run.BUILD/'ExactEBRP.exe'),tests_sha256=run.sha(run.BUILD/'tests.log')))
    run.OUT=destination;run.RAW=destination/'local_raw'
    run.runner.OUT=destination;run.runner.RAW=run.RAW;run.runner.LEDGER=destination/'processes.jsonl'
    run.freeze()
    run.write(destination/'reproduction_plan.json',dict(ids=a.ids,arms=a.arms,cap=a.cap,maximum_launches=maximum,
        scope='Fresh separate build/source binding; not a substitute for historical measured timings',
        original_build_manifest=str(original/'build_v1.json')))
    run.refbuild(a.ids);run.run(a.ids,a.arms,a.cap,'fresh_reproduction')
    # Import only after rebinding: the reused audit modules share this driver.
    import package_round68
    assert package_round68.run.OUT==destination and package_round68.run.BUILD==bound_build
    package_round68.main()
