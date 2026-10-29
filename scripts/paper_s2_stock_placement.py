"""Expand an explicit Round139 stock placement research command; --run executes."""
from pathlib import Path
import json,sys
import paper_s2 as baseline

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_stock_placement_round139.json'

def main():
    baseline.CONFIG=PROFILE
    parser=baseline.parser();parser.description=__doc__
    parser.add_argument('--placement',choices=['base','both','lp-only','mip-only'],required=True)
    args=parser.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('registered R137 parent profile differs')
        if not args.out_dir.resolve().is_relative_to(Path('E:/codes/ExactEBRP-work').resolve()):
            raise ValueError('Round139 research output must be under E:/codes/ExactEBRP-work')
        config['argv'][-1]=args.placement
        launch=baseline.plan(args,config)
        launch.update(schema='round139-stock-placement-research-launch-v1',placement=args.placement,
            LP_stock=args.placement in ['both','lp-only'],MIP_stock=args.placement in ['both','mip-only'],
            research_profile=True,H_seed=20260626,parent_profile_SHA256=config['parent_profile_SHA256'])
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:
        parser.error(str(error).replace('Round137 PE','Round139 PE').replace('Round137 DLL','Round139 DLL'))

if __name__=='__main__':sys.exit(main())
