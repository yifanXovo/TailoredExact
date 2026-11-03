"""Preregister the one remaining K20 proof question after mixed hard-role results."""
import time
_started=time.perf_counter()
from round149_common import *
import round149_campaign as campaign


def main():
    configure();before=budget();assert not before['unclosed']
    full=read(OUT/'reports/full.json');assert not full['pending'] and len(full['comparisons'])==2
    assert not any(c['serious_double_open_regression'] for c in full['comparisons'])
    assert before['remaining_G1_seconds']>=2400+1800
    reason=('The two completed hard-role pairs are mixed: K35 physical U improves2.00348% and signed gap6.69% '
        'with L .87754% lower; RB35 physical U is3.08518% worse, L2.26970% higher and signed gap4.626% worse. '
        'Neither triggers the serious double-open reference rule, but RB35 loses D incumbent value. '
        'One remaining discriminating question can change adoption: does uniform PF repair standalone D\'s '
        'K20 certification shortfall under the original R134 proof policy? The positive K20 matched LP '
        'resource-shortage signal motivates this question; the short health arm is not a performance comparator. '
        'Use one same-new-PE D/PF cap1200 pair, each complete own H, T5400/lambda.15. '
        'A substantial proof advantage would add independent algorithm value relevant to accepting the '
        'observed hard-role tradeoffs; absent that, those mixed hard-role results alone do not warrant '
        'a uniform PF recommendation. No RX20, seed, longer cap, factor combination or further clarification '
        'will follow regardless of this outcome.')
    write(OUT/'reports/hard_roles_snapshot.json',full)
    campaign.freeze('k20',[dict(role='K-20-S',method=m,cap=1200) for m in ['D','D_PF']],reason)
    write(OUT/'stages/rb35_decision.json',dict(decision='ONE_FINAL_K20_PROOF_CLARIFICATION',reason=reason,
        hard_role_comparisons=full['comparisons'],budget_before=before,complete_cap_reserved=2400,
        verification_reserve=1800,matrix_SHA=sha(OUT/'k20_matrix.json'),
        independent_admission_required=True,no_further_experiment_after_this_pair=True,
        no_promotion_decided_yet=True,Optimize=0,Native_load=0,compile=0))
    elapsed=time.perf_counter()-_started;path=OUT/'infra/external_costs.json';value=read(path)
    value['processes'].append(dict(kind='diagnostic',outer_seconds=elapsed,
        label='final_K20_proof_stage_preparation',basis='One measured Python frame including imports and frozen metadata; no Optimize/Native/compile'))
    write(path,value);print(json.dumps(dict(frozen=True,seconds=elapsed,budget=budget())))


if __name__=='__main__':main()
