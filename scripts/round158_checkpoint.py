"""Metadata-only watcher; request normal return at a predeclared node checkpoint."""
import re
from round158_common import *

def run(label,nodes):
    folder=OUT/'level'/label;threshold=int(nodes);tick=time.perf_counter()
    while not (folder/'result.json').exists():
        log=folder/'native.log'
        if log.exists():
            with log.open('rb') as f:
                f.seek(0,2);f.seek(max(0,f.tell()-65536));tail=f.read().decode(errors='replace')
            observed=[int(m[1]) for m in re.finditer(r'(?m)^\s*(\d+)\s+\d+\s+(?:[-0-9.]|infeasible|cutoff)',tail)]
            if observed and max(observed)>=threshold:
                request=dict(UTC=utc(),reason='predeclared finite initial expression diagnosis; main research remains active',
                    requested_checkpoint_nodes=threshold,displayed_nodes_at_request=max(observed),
                    source='diagnostic_decision.md',normal_terminate_only=True)
                write(folder/'TERMINATE.json',request)
                write(folder/'checkpoint_request.json',dict(request,monitor_wall_seconds=time.perf_counter()-tick,
                    monitor_Optimize=0,metadata_only=True,nested_monitor_not_extra_scientific_fee=True))
                print(json.dumps(request),flush=True);return
        time.sleep(10)
    print(json.dumps(dict(UTC=utc(),normal_result_observed_before_checkpoint=True)),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
