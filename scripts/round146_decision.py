"""Retrospective scientific decision from the seven completed formal positions."""
import csv
from round146_common import *

def main():
    configure();assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');assert len(full['new_arms'])==7 and not full['pending']
    assert len(full['pairs'])==3 and len(full['same_PE_BASE_bridges'])==1
    k=next(p for p in full['pairs'] if p['role']=='K-20-S')
    x=next(p for p in full['pairs'] if p['role']=='R-X20-S-T1')
    r=next(p for p in full['pairs'] if p['role']=='R-B35-S-T2')
    b=full['same_PE_BASE_bridges'][0]
    assert all(a['native_proof_qualified'] and a['performance_eligible'] and a['H_complete'] for a in full['new_arms'])
    assert k['GD_certificate'] and x['GD_certificate'] and k['GD_U']==k['STOCK_U'] and x['GD_U']==x['STOCK_U']
    assert r['GD_U']<r['STOCK_U'] and r['GD_L']>r['STOCK_L']
    assert b['GD_U']>b['BASE_U'] and b['GD_relative_gap']>b['BASE_relative_gap']
    k_gain=100*(k['STOCK_T_cert']-k['GD_T_cert'])/k['STOCK_T_cert']
    r_gain=100*(r['STOCK_U']-r['GD_U'])/r['STOCK_U']
    base_loss=100*(b['GD_U']-b['BASE_U'])/b['BASE_U']
    with (OUT/'reports/verified_U_trajectories.csv').open(newline='',encoding='utf-8') as stream:tr=list(csv.DictReader(stream))
    base_tr=[a for a in tr if a['role']=='R-B35-S-T2' and a['method']=='BASE']
    early=next(a for a in base_tr if float(a['U'])<=.362136826573)
    gd_final=next(a for a in tr if a['role']=='R-B35-S-T2' and a['method']=='STOCK_GD' and abs(float(a['U'])-r['GD_U'])<1e-12)
    complete=(f'Three complete same-PE STOCK/STOCK+GD pairs retain the uniform candidate. '
        f'K20 certifies the same U=.7168065462777502 in {k["STOCK_T_cert"]:.6f} versus {k["GD_T_cert"]:.6f}s '
        f'({k_gain:.4f}% earlier); total times are {k["STOCK_T_total"]:.6f}/{k["GD_T_total"]:.6f}s. '
        f'RX20 retains U=.6453250303858205 and certification, with a small absolute certificate-clock gain '
        f'of {-x["delta_T_produce"]:.6f}s and total gain of {-x["delta_T_total"]:.6f}s; '
        f'its extra {x["delta_T_verify"]:.6f}s verification is included. '
        f'RB35 improves U from {r["STOCK_U"]:.12f} to {r["GD_U"]:.12f} ({r_gain:.4f}%), '
        f'L from {r["STOCK_L"]:.12f} to {r["GD_L"]:.12f}, and gap by {-100*r["delta_relative_gap"]:.4f} percentage points. '
        f'Both RB35 arms remain open after full cap2400 windows; GD verification costs {r["delta_T_verify"]:.6f}s more. '
        f'The necessary same-PE stable BASE bridge returns U/L={b["BASE_U"]:.12f}/{b["BASE_L"]:.12f}. '
        f'The combination raises L by {b["delta_L"]:.12f} but worsens U by {base_loss:.4f}% '
        f'and gap by {100*b["delta_relative_gap"]:.4f} percentage points versus BASE.')
    historical=(f'The stable BASE pressure comparison above is newly measured on the same PE; its matching historical '
        f'R145 endpoints are not reused as a free new experiment. BASE already has U={float(early["U"]):.12f} '
        f'at producer time {float(early["producer_seconds"]):.3f}s, better than the combination\'s final U. '
        f'BASE improves again to its final U at {float(base_tr[-1]["producer_seconds"]):.3f}s; '
        f'the combination reaches its final U at {float(gd_final["producer_seconds"]):.3f}s. '
        f'Both early and late observations are retained; a near-cap explanation does not erase the observed regression. '
        f'K20/RX20 have strong same-PE STOCK references but no new same-PE BASE arms. Earlier STOCK certificate gains '
        f'and the old RN-P K35 gains remain useful historical results with their original identities. '
        f'K35 is tested here only in the finite LP stage; no complete STOCK+GD K35 or new RN-P bridge was run, '
        f'so this study makes no claim to replace or improve RN-P\'s complete K35 performance.')
    discussion=('Retain STOCK+GD as a research candidate and retain stable R137 GI-TBC as the default. '
        'Direct GD provides real original-variable optimized information and useful incremental complete-search '
        'benefits over STOCK on all three measured roles. The combination alleviates, but does not eliminate, '
        'the important RB35 incumbent/gap regression versus stable BASE. That is a limitation of the selected '
        'combination; it is not evidence that adding GD caused the older STOCK regression or that GD alone is useless. '
        'The material same-PE pressure regression, rather than tiny certified-bound differences or a small mixed endpoint, '
        'prevents stable promotion. Stop this finite full-method expansion after the BASE bridge. '
        'No K35 rescue panel, RN-P bridge, extra seed, K15/RX35 boundary run, BASE+GD second full candidate, '
        'state-Hoover branch or tuning grid is opened. These additional runs are unnecessary for this adoption decision; '
        'unused budget is not an invitation to extend the panel. The evidence is from known configurations and Seed0, '
        'so no general dominance, out-of-sample performance or multi-seed robustness is claimed.')
    d=dict(UTC=utc(),decision='RESEARCH_ONLY',study_complete=True,new_candidate_promoted_to_stable=False,
        uniform_candidate='STOCK+GD-state',primary_reference='STOCK',stable_pressure_bridge='BASE on RB35-T2 only',
        incremental_GD_value_confirmed_on_measured_roles=True,complete_discussion=complete,
        historical_discussion=historical,decision_discussion=discussion,
        navigation_discussion=('K20 certifies about 20.52% sooner than same-PE STOCK, RX20 retains certification, and '
            'RB35 improves both endpoints over STOCK. A necessary same-PE BASE bridge still shows a 9.63% U '
            'regression and 1.74 percentage-point gap increase on RB35. Retain the positive incremental GD '
            'results as research-only; stable R137 remains unchanged and no further panel is entered.'),
        observations=dict(K20_certificate_time_improvement_percent=k_gain,RB35_U_improvement_vs_STOCK_percent=r_gain,
            RB35_U_regression_vs_BASE_percent=base_loss,RB35_gap_regression_vs_BASE_percentage_points=100*b['delta_relative_gap']),
        same_PE_pairs=full['pairs'],same_PE_BASE_bridge=b,
        new_standalone_LP_Optimize=5,formal_positions=7,short_health_qualifications=1,
        all_entered_Native_Optimize=full['all_entered_observed_Native_Optimize'],
        total_new_experiment_seconds=budget()['G1_seconds'],ceiling_seconds=28800,
        unentered=['K35 complete pair','K35 RN-P bridge','K15','RX35-T2','additional Seeds',
            'BASE+GD second full candidate','state-level Hoover extension','global/state coefficient grid'],
        independent_final_review_record='review/final_scientific_review.json',delivery_record='RESUME.md',Optimize=0,Native_load=0)
    write(OUT/'candidate_decision.json',d)
    write(OUT/'stage_base_bridge.json',dict(UTC=utc(),decision='STOP_FULL_EXPANSION_RETAIN_RESEARCH',
        bridge=b,reason=discussion,charged_seconds=budget()['G1_seconds'],all_entered_windows_retained=True,Optimize=0,Native_load=0))
    print(json.dumps(dict(decision=d['decision'],observations=d['observations'],experimental_seconds=d['total_new_experiment_seconds'])))

if __name__=='__main__':main()
