"""Offline reader qualification on completed development traces, no solver.

Synthetic handoff records exercise only the reader; they are never formal
journal evidence and supply no performance endpoint or bound.
"""
import time
from round96_prepare import ROOT,OUT,read,write,sha
from round96_primal import order_trace

def main():
    started=time.perf_counter();cases=read(OUT/'fixed_route_cases.json')['cases'];records=[]
    for case in cases:
        folder=OUT/'route_order'/case['id']/'order';final=read(folder/'final.json')
        handoff=dict(final,kind='witness',call=0)
        result=order_trace(dict(panel=case['panel'],destination='unused_fixture'),
            [dict(payload=handoff)],dict(external_gini_tree_root_coverage_valid=True),fixture_root=folder)
        assert result['triggered'] and result['handoff_final']
        records.append(dict(id=case['id'],result=result))
    write(OUT/'primal_auditor_fixture.json',dict(passed=True,records=records,optimizer_calls=0,
        reader_sha256=sha(ROOT/'scripts/round96_primal.py'),fixture_sha256=sha(__file__),
        completed_sha256=sha(OUT/'route_order/completed.json'),
        elapsed_seconds=time.perf_counter()-started,
        scope='Offline synthetic handoff fixture only; no formal native evidence or optimization.'))

if __name__=='__main__':main()
