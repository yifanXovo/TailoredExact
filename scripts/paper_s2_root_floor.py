"""Round153 research entry: GI-TBC with self-paid uniform own-root floor."""
import json,sys
from pathlib import Path
import paper_s2 as baseline
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_root_floor_round153.json'

def main():
    baseline.CONFIG=PROFILE;p=baseline.parser();p.description=__doc__
    p.add_argument('--floor',choices=['off','on'],default='on');args=p.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('stable profile differs from byte authority')
        config['argv'][config['argv'].index('--round153-root-floor')+1]=args.floor
        launch=baseline.plan(args,config);launch.update(schema='round153-own-root-floor-launch-v1',
            floor=args.floor,GD=False,STOCK=False,Shared_S=False,research_profile=True)
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:p.error(str(error))
if __name__=='__main__':sys.exit(main())
