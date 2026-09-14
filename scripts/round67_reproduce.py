"""Fresh bounded reproduction; never overwrites the measured evidence."""
import argparse, shutil
import round67_research as run

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
    ap.add_argument('--ids',nargs='+',required=True,choices=list(run.panel()))
    ap.add_argument('--arms',nargs='+',default=['P-GRB','K1-R','VD-P','LOG'],choices=['P-GRB','K1-R','VD-P','LOG'])
    ap.add_argument('--cap',type=int,required=True,choices=[20,300,600]);a=ap.parse_args()
    destination=(run.ROOT/a.output).resolve();original=run.OUT
    if destination.exists() or not destination.is_relative_to(run.ROOT):raise RuntimeError('Need a new output directory inside this checkout')
    if len(set(a.ids))!=len(a.ids) or len(set(a.arms))!=len(a.arms):raise RuntimeError('Duplicate launch request')
    protocol=run.read(original/'protocol.json')
    assert all(protocol['caps'][i]==a.cap for i in a.ids),'Use separate batches for distinct whole-run deadlines'
    maximum=len(a.ids)*len(a.arms)
    assert maximum<=(6 if a.cap==20 else 16),'Bounded reproduction plan exceeded'
    destination.mkdir(parents=True)
    for name in ['plan.md','mathematics.md','resource_plan_update_1.json']:
        shutil.copyfile(original/name,destination/name)
    run.OUT=destination;run.RAW=destination/'local_raw'
    run.runner.OUT=destination;run.runner.RAW=run.RAW;run.runner.LEDGER=destination/'processes.jsonl'
    run.freeze()
    run.write(destination/'reproduction_plan.json',dict(ids=a.ids,arms=a.arms,cap=a.cap,maximum_launches=maximum,
        scope='Fresh separate build/source binding; not a substitute for historical measured timings',
        original_build_manifest=str(original/'build_v1.json')))
    run.refbuild(a.ids);run.run(a.ids,a.arms,a.cap,'fresh_reproduction')
