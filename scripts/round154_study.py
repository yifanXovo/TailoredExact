"""Finite serial study queues; no background continuation is implicit."""
from round154_common import *

def screen():
    for label in ['K35_saved','NC20_fresh']:
        for implementation in ['RN','residual']:
            run(f'{label}_{implementation}_screen_v1',240,'round154_targets.py',
                ['compare',label,implementation,'60','screen'])

if __name__=='__main__':globals()[sys.argv[1]]()
