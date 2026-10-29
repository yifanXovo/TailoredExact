"""Expand the uniform Round140 inventory-count research command; --run executes."""
from pathlib import Path
import json,sys
import paper_s2 as baseline

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_tc2_round140.json'

def main():
    baseline.CONFIG=PROFILE
    parser=baseline.parser();parser.description=__doc__
    parser.add_argument('--counts',choices=['tc','tc2'],default=None,
        help='uniform count mode; omitted uses the separate research profile')
    args=parser.parse_args()
    try:
        config=baseline.read(PROFILE)
        args.counts=config.get('default_counts','tc2') if args.counts is None else args.counts
        if args.counts not in ['tc','tc2']:
            raise ValueError('research profile has an invalid uniform default_counts')
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('registered R137 parent profile differs')
        if not args.out_dir.resolve().is_relative_to(Path('E:/codes/ExactEBRP-work').resolve()):
            raise ValueError('Round140 research output must be under E:/codes/ExactEBRP-work')
        config['argv'][-1]=args.counts
        launch=baseline.plan(args,config)
        launch.update(schema='round140-inventory-count-stock-research-launch-v1',counts=args.counts,
            stock=True,placement='both',research_profile=True,H_seed=20260626,
            parent_profile_SHA256=config['parent_profile_SHA256'])
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:
        parser.error(str(error).replace('Round137 PE','Round140 PE').replace('Round137 DLL','Round140 DLL'))

if __name__=='__main__':sys.exit(main())
