"""Round116 identities and finite, exit-observed fees; no launch on import."""
from round115_common import ROOT, PYTHON, DLL, DLL_SHA, SOURCE, PE_SHA, bindings, read, write, sha, env, process_origin
from pathlib import Path
import json, os, sys, time, types
import round115_common as inherited

OUT=ROOT/'results/unified_exact_round116'
BASE='7eef812efb1bd3046c48e76ff6ac968de276a9b0'
PE=ROOT/'build/research/round116-inherited/ExactEBRP.exe'
LAYER='R116_SIX_ROLES_FOUR_FROZEN_METHODS_EXTERNAL_SOURCE_MEASUREMENT_V2'

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    closed=[(read(p),read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(r['outer_seconds_upper'] for _,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=56-starts,remaining_outer_seconds=65000-seconds,
        qualification_starts=sum(read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def check_identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and len(bindings())==206
    assert p['measured_source_commit']==SOURCE
    return p

# Exactly the old actual-exit observation and pending/sealed receipt predicates.
close_fee=types.FunctionType(inherited.close_fee.__code__,dict(vars(inherited),OUT=OUT,budget=budget),'close_fee')
def clock_evidence(d,l):
    value=inherited.clock_evidence(d,l)
    value['total_exceeds_cap']=value['T_total']>l['cap_seconds']
    return value

if __name__=='__main__':
    assert sys.argv[1]=='close-fee';close_fee(sys.argv[2])
