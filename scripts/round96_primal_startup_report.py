"""Compare OFF handoff to the unchanged first R83 closure inside ON."""
import csv
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha
import round90_lp_g_g3 as r90
import round96_primal_recovery_v2 as campaign

def phase(path,name):
    with path.open(newline='',encoding='utf-8') as stream:
        rows=[r for r in csv.DictReader(stream) if r['event']==name]
    assert len(rows)==1
    return float(rows[0]['process_seconds'])

def main():
    records=campaign.records();assert len(records)==12 and all(r['audit_passed'] for r in records)
    rows=[]
    for role in ['F5','F2','V1','V2']:
        arms={r['arm']:r for r in records if r['id']==role};on=Path(arms['ORDER-ON']['destination']);off=Path(arms['ENS-C']['destination'])
        old=read(on/'hga.csv.route_order/old_0/final.json');handoff=read(off/'external/initial_witness.json')
        assert r90.route_hash(r90.normalize(old))==r90.route_hash(r90.normalize(handoff))
        audit=campaign.audited_record(arms['ORDER-ON'])['route_order'];assert audit['handoff_final']
        end={};closure={}
        for arm,path in [('ON',on),('OFF',off)]:
            stages=path/'phases.csv'
            end[arm]=phase(stages,'improving_gini_range_construction_complete')
            closure[arm]=end[arm]-phase(stages,'decoded_descent_complete')
        rows.append(dict(role=role,off_handoff_equals_on_first_original_closure=True,
            off_startup_F=handoff['objective'],on_startup_F=audit['final_F'],
            delta_startup_F=audit['final_F']-handoff['objective'],order_moves=audit['order_moves'],
            physical_snapshots=audit['physical_witnesses_replayed'],startup_end_seconds=end,
            post_seed_closure_and_publication_seconds=closure,
            difference_full_startup_seconds=end['ON']-end['OFF'],
            off_handoff_sha256=sha(off/'external/initial_witness.json'),
            on_first_closure_sha256=sha(on/'hga.csv.route_order/old_0/final.json')))
    write(OUT/'primal_startup_comparison.json',dict(passed=True,rows=rows,optimizer_calls=0,
        source_sha256=sha(__file__),summary_sha256=sha(campaign.CAMP/'summary.jsonl'),
        timing_scope='Observed phases include original/new closure, validation, snapshots and range publication. Differences are measured startup costs, not isolated pure reorder CPU or repeatable causal timing estimates. Full costs remain in the parent process and are not added twice.'))

if __name__=='__main__':main()
