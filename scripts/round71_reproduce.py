"""Fresh bounded replay from identical qualified bytes; never replace evidence.

This helper is not launched by the original campaign. Different source/binary
requires a separately identified build and qualification instead of replay.
"""
import argparse,shutil
import package_round71 as package
run=package.run

def main():
    package.bind()
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--ids',nargs='+',required=True,choices=list(run.panel()))
    parser.add_argument('--arms',nargs='+',required=True,choices=['P-GRB','DS','DS-X','K1-R'])
    parser.add_argument('--cap',type=int,required=True,choices=[30,120,300,600,1200])
    args=parser.parse_args();original=run.OUT;old_build=run.BUILD
    assert not (original/'active_run.lock').exists()
    destination=(run.ROOT/args.output).resolve()
    assert destination.is_relative_to(run.ROOT) and not destination.exists()
    assert len(set(args.ids))==len(args.ids) and len(set(args.arms))==len(args.arms)
    freeze,protocol=run.assert_frozen();panel=run.panel()
    assert all(protocol['caps'][i]==args.cap for i in args.ids)
    stages={panel[i]['stage'] for i in args.ids};assert len(stages)==1
    assert all(arm in protocol['allowed_arms'][i] for i in args.ids for arm in args.arms)
    maximum=len(args.ids)*len(args.arms)
    assert maximum<=25
    assert run.sha(old_build/'Round65ReferenceBuild.exe')==freeze['reference_binary']
    assert run.sha(old_build/'tests.log')==freeze['tests']
    destination.mkdir(parents=True);bound=destination/'bound_build';bound.mkdir()
    for name in ['plan.md','mathematics.md','affinity_qualification.json']:
        shutil.copyfile(original/name,destination/name)
    for name in ['ExactEBRP.exe','Round65ReferenceBuild.exe','tests.log']:
        shutil.copyfile(old_build/name,bound/name)
    qualification=run.read(original/'qualification.json')
    qualification.update(fresh_reproduction_note='Identical qualified bytes; no new build/CTest batch',
        inherited_ctest_tests=49,newly_executed_ctest_tests=0,
        inherited_qualification_path=str(original/'qualification.json'),
        configure_build_test_attempts=[],preflight_total_wall_seconds=0,
        inherited_native_test_calls=qualification['total_qualification_native_optimizer_calls'],
        total_qualification_native_optimizer_calls=0)
    run.write(destination/'qualification.json',qualification)
    run.OUT=destination;run.RAW=destination/'local_raw';run.BUILD=bound
    package.bind();run.freeze()
    new_protocol=run.read(destination/'protocol.json')
    new_protocol.update(maximum_performance=maximum if next(iter(stages))=='development' else 0,
        maximum_micro=maximum if next(iter(stages))=='correctness' else 0,
        maximum_reference_exports=len(args.ids),worst_case_seconds=maximum*args.cap)
    run.write(destination/'protocol.json',new_protocol)
    run.write(destination/'reproduction_plan.json',dict(ids=args.ids,arms=args.arms,cap=args.cap,
        maximum_launches=maximum,original_build_manifest=str(original/'build_v1.json'),
        scope='Fresh separate outputs; historical exposed roles are not independent confirmation. Every arm inherits mask4.'))
    run.refbuild(args.ids);run.run(args.ids,args.arms,args.cap,next(iter(stages)));package.main()

if __name__=='__main__':main()
