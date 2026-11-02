"""Separate Round148 D+shared-S entry; --shared-s off selects same-PE D."""
import json
import sys
from pathlib import Path
import paper_s2 as baseline

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_shared_s_round148.json'


def main():
    baseline.CONFIG=PROFILE
    parser=baseline.parser();parser.description=__doc__
    parser.add_argument('--shared-s',choices=['on','off'],default='on')
    args=parser.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('stable R137 profile differs from byte authority')
        config['argv'][config['argv'].index('--round148-shared-s')+1]=args.shared_s
        launch=baseline.plan(args,config)
        launch.update(schema='round148-shared-S-launch-v1',GD=True,STOCK=False,
            shared_S=args.shared_s=='on',research_profile=True)
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:parser.error(str(error))


if __name__=='__main__':sys.exit(main())
