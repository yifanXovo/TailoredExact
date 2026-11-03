"""Separate Round149 D+PF research entry; --pf off selects same-new-PE D."""
import json
import sys
from pathlib import Path
import paper_s2 as baseline
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_penalty_feedback_round149.json'


def main():
    baseline.CONFIG=PROFILE;parser=baseline.parser();parser.description=__doc__
    parser.add_argument('--pf',choices=['on','off'],default='on');args=parser.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('stable R137 profile differs from byte authority')
        config['argv'][config['argv'].index('--round149-penalty-feedback')+1]=args.pf
        launch=baseline.plan(args,config)
        launch.update(schema='round149-penalty-product-feedback-launch-v1',
            PF=args.pf=='on',GD=True,STOCK=False,Shared_S=False,research_profile=True)
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:parser.error(str(error))


if __name__=='__main__':sys.exit(main())
