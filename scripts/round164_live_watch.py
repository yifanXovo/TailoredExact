"""Read-only live OS binding; observer uses CPU mask1, production mask4."""
from pathlib import Path
import json,os,time
import round163_live_watch as inherited

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round164'

def main():
    matrix=inherited.read(OUT/'matrix_frozen.json');start=time.time();seen=set()
    while time.time()-start<57600:
        if (OUT/'panel_complete.json').exists():break
        try:
            active=inherited.read(OUT/'active_position.json');group=matrix['groups'][active['position']-1]
            path=OUT/group['group']/'runtime_os_binding.json'
            if path.exists():seen.add(group['position'])
            else:
                origin=Path(group['launch']['destination'])/'child_process_origin.json'
                if origin.exists():
                    value=inherited.binding(inherited.read(origin))
                    if value:
                        assert Path(value['PE'])==Path(group['launch']['command'][0])
                        value.update(gurobi_seed=group['arm']['gurobi_seed'],method=group['arm']['method'])
                        inherited.write(path,value);seen.add(group['position'])
                        print(json.dumps(dict(bound=group['position'],**group['arm'])),flush=True)
        except FileNotFoundError:pass
        time.sleep(.25)
    inherited.write(OUT/'live_watch_closeout.json',dict(started_unix=start,ended_unix=time.time(),
        bound_positions=sorted(seen),observer_affinity=1,production_affinity=4,Optimize=0,metadata_only=True))

if __name__=='__main__':main()
