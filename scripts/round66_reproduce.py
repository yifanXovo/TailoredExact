"""Fresh, separately identified reproduction using a locally rebuilt solver."""
import argparse,shutil
from pathlib import Path
import round66_research as run

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True,help='New results directory inside this checkout')
    ap.add_argument('--ids',nargs='+',required=True,choices=list(run.panel()))
    ap.add_argument('--arms',nargs='+',default=['P-GRB','K1-R','ARC'],
                    choices=['P-GRB','K1-R','ARC','Q-PLUS','K1-AM'])
    ap.add_argument('--cap',type=int,required=True,choices=[20,120,300,600])
    a=ap.parse_args();original=run.OUT;destination=(run.ROOT/a.output).resolve()
    if len(set(a.ids))!=len(a.ids) or len(set(a.arms))!=len(a.arms):raise RuntimeError('Duplicate run request')
    if 'micro' in a.ids:
        if a.ids!=['micro'] or a.cap!=20 or len(a.arms)>2:raise RuntimeError('Use a separate at-most-two-arm micro batch at cap 20')
    elif a.cap==20:raise RuntimeError('Original performance instances require cap 120, 300 or 600')
    if not destination.is_relative_to(run.ROOT) or destination.exists():
        raise RuntimeError('Reproduction needs a new directory inside the checkout; no overwrite is allowed')
    if len(a.ids)*len(a.arms)>16:raise RuntimeError('Declare a smaller bounded reproduction batch')
    destination.mkdir(parents=True)
    for name in ['research_map.md','mathematics.md']:
        shutil.copyfile(original/name,destination/name)
    run.OUT=destination;run.RAW=destination/'local_raw'
    run.runner.OUT=destination;run.runner.RAW=run.RAW;run.runner.LEDGER=destination/'processes.jsonl'
    run.freeze()
    run.write(destination/'reproduction_plan.json',dict(ids=a.ids,arms=a.arms,cap_seconds=a.cap,
        maximum_launches=len(a.ids)*len(a.arms),original_build_manifest=str(original/'build_v1.json'),
        scope='fresh reproduction, new binary/source binding; never substitutes for original observations'))
    run.refbuild(a.ids)
    run.run(a.ids,a.arms,a.cap,'fresh_reproduction')
if __name__=='__main__':main()
