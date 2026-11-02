"""Separate Round147 standalone GD entry; --gd off selects stable BASE."""
import json
import sys
from pathlib import Path
import paper_s2 as baseline

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'config/gi_tbc_gd_round147.json'


def main():
    baseline.CONFIG = PROFILE
    parser = baseline.parser()
    parser.description = __doc__
    parser.add_argument('--gd', choices=['on', 'off'], default='on')
    args = parser.parse_args()
    try:
        config = baseline.read(PROFILE)
        if baseline.sha(ROOT / 'config/gi_tbc_round137.json') != config['parent_profile_SHA256']:
            raise ValueError('stable R137 profile differs from byte authority')
        assert '--round138-stock-rlt' not in config['argv']
        config['argv'][config['argv'].index('--round146-gd') + 1] = args.gd
        launch = baseline.plan(args, config)
        launch.update(schema='round147-standalone-GD-launch-v1',
                      GD=args.gd == 'on', STOCK=False, research_profile=True)
        print(json.dumps(launch, indent=2) if args.json else launch['windows_command'], flush=True)
        return baseline.execute(launch) if args.run else 0
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
