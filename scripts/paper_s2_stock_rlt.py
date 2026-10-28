"""Expand the explicit Round138 inventory-RLT research profile; --run executes."""
from pathlib import Path
import json,sys
import paper_s2 as baseline

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'config/gi_tbc_stock_rlt_round138.json'

def main():
    baseline.CONFIG=PROFILE
    p=baseline.parser();p.description=__doc__
    p._option_string_actions['--exe'].help='local compatible executable; default is the verified Round138 candidate PE'
    args=p.parse_args()
    try:
        config=baseline.read(PROFILE)
        if baseline.sha(ROOT/'config/gi_tbc_round137.json')!=config['parent_profile_SHA256']:
            raise ValueError('the inherited R137 profile differs from the registered byte authority')
        launch=baseline.plan(args,config)
        launch.update(schema='round138-stock-rlt-research-launch-v1',stock_rlt=True,
            research_profile=True,parent_profile_SHA256=config['parent_profile_SHA256'])
        print(json.dumps(launch,indent=2) if args.json else launch['windows_command'],flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError,ValueError) as error:
        p.error(str(error).replace('Round137 PE','Round138 candidate PE').replace('Round137 DLL','Round138 DLL'))

if __name__=='__main__':sys.exit(main())
