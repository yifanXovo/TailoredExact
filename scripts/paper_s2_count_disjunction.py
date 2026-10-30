"""Expand Round141 root count-disjunction research command; --run executes."""
from pathlib import Path
import json,sys
import paper_s2 as baseline

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_count_disjunction_round141.json'

def main():
    baseline.CONFIG=PROFILE
    parser=baseline.parser();parser.description=__doc__
    parser.add_argument('--mode',choices=['d0','d1'],default='d1')
    args=parser.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('registered stable parent profile differs')
        if not args.out_dir.resolve().is_relative_to(Path('E:/codes/ExactEBRP-work').resolve()):
            raise ValueError('Round141 output must be under E:/codes/ExactEBRP-work')
        config['argv'][-1]=args.mode
        launch=baseline.plan(args,config)
        launch.update(schema='round141-count-disjunction-research-launch-v1',proof_mode=args.mode,
            counts='tc2',stock=True,placement='both',root_once=True,H_seed=20260626,research_only=True)
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:parser.error(str(error))

if __name__=='__main__':sys.exit(main())
