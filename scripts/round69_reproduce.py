"""Fresh, bounded runs of the identical previously qualified executable.

This helper is not executed as part of the original validation. It refuses to
overwrite outputs or silently bind a newly built/different executable.
"""
import argparse,shutil
import package_round69 as package
run=package.run

def main():
    package.bind()
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True)
    ap.add_argument('--ids',nargs='+',required=True,choices=list(run.panel()))
    ap.add_argument('--arms',nargs='+',required=True,choices=['P-GRB','K1-R','VD-S'])
    ap.add_argument('--cap',type=int,required=True,choices=[120,300,1200,3600])
    args=ap.parse_args();original=run.OUT;old_build=run.BUILD
    assert not (original/'active_run.lock').exists(),'Wait for the original serial queue'
    destination=(run.ROOT/args.output).resolve()
    assert destination.is_relative_to(run.ROOT) and not destination.exists(),'Use a new local output directory'
    assert len(set(args.ids))==len(args.ids) and len(set(args.arms))==len(args.arms)
    protocol=run.read(original/'protocol.json');freeze=run.read(original/'build_v1.json')
    assert all(protocol['caps'][i]==args.cap for i in args.ids)
    stages={protocol['stages'][i] for i in args.ids};assert len(stages)==1
    assert 'D3' not in args.ids or args.arms==['VD-S']
    assert len(args.ids)*len(args.arms)<=16
    assert run.sha(old_build/'ExactEBRP.exe')==freeze['binary']
    assert run.sha(old_build/'Round65ReferenceBuild.exe')==freeze['reference_binary']
    assert run.sha(old_build/'tests.log')==freeze['tests']
    for name,value in freeze['source'].items():assert run.sha(run.ROOT/name)==value,name
    destination.mkdir(parents=True);bound=destination/'bound_build';bound.mkdir()
    for name in ['plan.md','mathematics.md']:shutil.copyfile(original/name,destination/name)
    for name in ['ExactEBRP.exe','Round65ReferenceBuild.exe','tests.log']:shutil.copyfile(old_build/name,bound/name)
    qualification=run.read(original/'qualification.json')
    qualification['fresh_reproduction_note']='Exact same qualified bytes; inherited tests, zero new qualification batches'
    run.write(destination/'qualification.json',qualification)
    run.OUT=destination;run.RAW=destination/'local_raw';run.BUILD=bound
    package.bind();run.freeze()
    run.write(destination/'reproduction_plan.json',dict(ids=args.ids,arms=args.arms,cap=args.cap,
        maximum_launches=len(args.ids)*len(args.arms),original_build_manifest=str(original/'build_v1.json'),
        scope='Fresh separate output; historical stage labels describe roles, not independent confirmation. No original result overwritten.'))
    run.refbuild(args.ids);run.run(args.ids,args.arms,args.cap,next(iter(stages)))
    package.main()
    if any(i in ['D6','D7'] for i in args.ids):
        import round69_checkpoints
        round69_checkpoints.main()

if __name__=='__main__':main()
