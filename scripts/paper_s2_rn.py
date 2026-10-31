"""Explicit Round143 reciprocal-normalization research entry; --run executes."""
import json,sys
import paper_s2 as baseline
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_rn_round143.json'

def main():
    baseline.CONFIG=PROFILE;p=baseline.parser();p.description=__doc__;p.add_argument('--rn',choices=['on','off'],default='on')
    args=p.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('the inherited stable R137 profile differs from the byte authority')
        config['argv'][-1]=args.rn
        launch=baseline.plan(args,config);launch.update(schema='round143-RN-launch-v1',RN=args.rn=='on',research_profile=True)
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:p.error(str(error))

if __name__=='__main__':sys.exit(main())
