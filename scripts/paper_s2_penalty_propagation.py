"""Independent Round151 research entry; default-off production control; GD stays off."""
import json,sys
from pathlib import Path
import paper_s2 as baseline
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_penalty_propagation_round151.json'
def main():
    baseline.CONFIG=PROFILE;p=baseline.parser();p.description=__doc__
    p.add_argument('--propagation',choices=['off','uniform','conditional'],default='conditional');args=p.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('stable profile differs from byte authority')
        config['argv'][config['argv'].index('--round151-penalty-propagation')+1]=args.propagation
        launch=baseline.plan(args,config);launch.update(schema='round151-standalone-penalty-launch-v1',
            propagation=args.propagation,GD=False,STOCK=False,Shared_S=False,research_profile=True)
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:p.error(str(error))
if __name__=='__main__':sys.exit(main())
