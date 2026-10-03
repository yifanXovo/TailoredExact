"""One pre-N2 resource decision after completed CF panel; never changes algorithm."""
from round100_common import *
from round100_idle import ensure_idle
def main():
    ensure_idle();cf=OUT/'certification_CF01'
    complete=[json.loads(s) for s in (cf/'summary.jsonl').read_text().splitlines()]
    assert len(complete)==6 and all(r['audit_passed'] for r in complete)
    assert not (OUT/'certification_N201').exists()
    costs=read(OUT/'certification_CF_results01/summary.json');spent=costs['conservative_outer_solver_seconds']
    assert costs['unknown_actual_outer_processes']==[]
    # Keep both future fresh-reference child allowances and the full holdout.
    extended=spent+21600+5400+120<=80000
    long=read(OUT/'long_protocol.json');n2=dict(long['roles'][2]);assert n2['id']=='R99-N2' and n2['cap_seconds']==3600
    n2['cap_seconds']=7200 if extended else 3600
    write(OUT/'N2_resource_decision.json',dict(prior_cost_summary_sha256=sha(OUT/'certification_CF_results01/summary.json'),
        prior_measured_seconds=spent,default_common_cap=3600,chosen_common_cap=n2['cap_seconds'],extension=extended,
        future_holdout_reserved_seconds=5400,future_fresh_reference_allowance_seconds=120,
        maximum_projected_total_seconds=spent+3*n2['cap_seconds']+5400+120,
        scope='experiment resource arrangement before any N2 arm; same cap for all three; no algorithm switch or tuning'))
    write(OUT/'certification_N2_protocol01.json',dict(roles=[n2],phase='certification extension',reference_billing='one_finite_batch',
        candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),optimizer_calls=0,resource_decision_sha256=sha(OUT/'N2_resource_decision.json')))
    print(json.dumps(dict(chosen_N2_common_cap=n2['cap_seconds'],extended=extended,prior_charged_seconds=spent)))
if __name__=='__main__':main()
