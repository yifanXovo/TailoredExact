"""Finite first-pair judgment; no new experiment."""
import time
_started=time.perf_counter()
from round151_common import *
def main():
    configure();full=read(OUT/'reports/full.json');assert not full['pending'] and len(full['formal_arms'])==2
    assert full['complete_Native_Optimize']==full['complete_Native_returned']==9
    c=full['comparisons'][0];assert c['role']=='N-B35-S' and not c['B_certificate'] and not c['C_certificate']
    assert c['delta_U']>0 and c['delta_L']>0 and c['delta_signed_gap']>0
    gap_change=100*c['delta_signed_gap']/c['B_signed_gap']
    reason=(f"On the same new PE with independent complete own H, C worsens N-B35 physical U {abs(c['U_improvement_percent']):.6f}%, "
        f"improves supported L only {c['L_improvement_percent']:.6f}%, and enlarges signed gap {gap_change:.6f}%; both remain open. "
        "The numerical root increment is real but the small terminal support gain does not compensate for the worse incumbent/gap "
        "in the complete prescribed window. This is insufficient complete enhancement value, rather than a mathematical invalidity "
        "or an all-cases-must-win rule. The severe double-open reference does not trigger and is not the adoption criterion.")
    stop=("The first-pair entry condition for the certificate-retention role is not met. No specific independent N-C20 question "
        "would reverse this finite positioning; a possible unmeasured easy-role gain alone is not a reason to search for a positive case. "
        "Its complete performance remains untested here. No P attribution, third role, seed, longer cap, GD/STOCK/Shared-S combination, "
        "iterative cutoff or more exact conditional oracle is entered. Close the current root-penalty propagation implementation chain "
        "and organize its validity, expression and cost results in the paper.")
    write(OUT/'certificate_pair_decision.json',dict(UTC=utc(),enter=False,decided_after_first_pair=True,
        first_pair_comparison=c,reason=reason,independent_question_requiring_NC20=False,no_NC20_complete_outcome_inferred=True,positions_not_entered=[3,4]))
    write(OUT/'clarification_decision.json',dict(UTC=utc(),enter=False,capacity_spent_seconds=0,
        reason='No substantive complete C benefit requiring uniform/conditional attribution or structural clarification; '+stop))
    write(OUT/'candidate_decision.json',dict(UTC=utc(),schema='round151-finite-root-penalty-closure-v1',study_complete=True,
        decision='EXPRESSION_AND_LP_VALUE_ONLY_CLOSE_COMPLETE_PROMOTION',reason=reason,stopping_reason=stop,
        paper_conclusion=("Standalone conditional resource-penalty propagation is valid and strengthens the saved pure-B LP. "
            f"The complete N-B35 test nevertheless loses {abs(c['U_improvement_percent']):.4f} percent in physical U, "
            f"gains only {c['L_improvement_percent']:.4f} percent in supported L and enlarges the signed gap {gap_change:.4f} percent, "
            "with both arms open. We retain the expression result and do not promote this root propagation as a complete enhancement. Stable GI-TBC remains primary."),
        A='C',GD=False,unique_candidate_frozen_before_complete_results=True,methods_uniform=True,stable_B_primary=True,
        automatic_default_change=False,recommend_complete_enhancement=False,root_penalty_chain_closed=True,
        mathematical_validity=True,actual_C_subset_P_subset_B=True,complete_scope=['N-B35-S'],known_exposed=True,
        blind_or_multiseed_robustness=False,LP_Optimize_new=2,baseline_Optimize_new=0,C20_LP_Optimize_new=0,complete_arms_new=2,
        severe_double_open_reference_triggered=c['serious_double_open_regression'],adoption_not_threshold_only=True,
        signed_gap_change_percent=gap_change,optional_clarification_entered=False,no_more_Optimize_queued=True,automatic_merge=False,
        production_source=read(OUT/'candidate_manifest.json')['source_commit'],PE_SHA=read(OUT/'candidate_manifest.json')['production_PE_SHA']))
    external=read(OUT/'infra/external_costs.json');elapsed=time.perf_counter()-_started
    external['processes'].append(dict(kind='diagnostic',label='finite_stage_decision',outer_seconds=elapsed,
        basis='Measured decision frame, no Native/Optimize/compile; final tiny write covered by disclosed allowance'))
    write(OUT/'infra/external_costs.json',external)
    print(json.dumps(dict(decision='EXPRESSION_AND_LP_VALUE_ONLY',signed_gap_change_percent=gap_change,seconds=elapsed)))
if __name__=='__main__':main()
