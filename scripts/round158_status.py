"""Small metadata/PID-birth status; no optimizer, producer or experiment."""
import re
from round158_common import *

def status(label='level_rx35_raw_quarter_deep_v3'):
    configure();folder=OUT/'fees'/label;launch=read(folder/'launch.json')
    receipt=folder/'receipt.json';state=dict(UTC=utc(),fee=label,budget=budget(),metadata_only=True)
    if receipt.exists():state.update(state='EXIT_OBSERVED',receipt=read(receipt))
    else:
        identity=read(folder/'PID.json');child=meter.process_snapshot(identity)
        parent=meter.process_birth(launch['parent_pid'])
        parent_ok=bool(parent and parent['creation_filetime']==launch['parent_birth']['creation_filetime'])
        state.update(state='RUNNING' if child['same_process_alive'] and parent_ok else 'INSPECT_UNCLOSED_FEE',
            child=child,parent_same_birth_alive=parent_ok,open_fee_not_yet_charged=True)
    command=launch['command'];research=OUT/'level'/command[5];log=research/'native.log'
    if log.exists():
        with log.open('rb') as stream:
            stream.seek(0,2);stream.seek(max(0,stream.tell()-65536));tail=stream.read().decode(errors='replace')
        nodes=[line for line in tail.splitlines() if re.match(r'^\s*\d+\s+\d+\s+(?:[-0-9.]|infeasible|cutoff)',line)]
        state['last_displayed_node_line']=nodes[-1] if nodes else None
    result=research/'result.json'
    if result.exists():state['result']=read(result)
    else:state['final_result_available']=False
    write(OUT/'infra/live_status.json',state);print(json.dumps(state),flush=True)

if __name__=='__main__':status(*sys.argv[1:])
