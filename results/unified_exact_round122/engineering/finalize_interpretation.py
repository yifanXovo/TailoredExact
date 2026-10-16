"""Complete the eight-group prose from frozen tables; no producer is touched."""
from pathlib import Path
import collections,json,re,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import round122_common as c
OUT=ROOT/'results/unified_exact_round122'

def main():
    target=OUT/'paper_result_interpretation.md'
    prior=OUT/'engineering/paper_interpretation_before_final.md'
    old_receipt=OUT/'engineering/sealed_interpretation_receipt_before_final.json'
    if not prior.exists():
        assert c.sha(target)=='4c31221192f06c449c5ee460acce6fd6241a1cf67b4f16e4331520c8ffcacf9e'
        prior.write_bytes(target.read_bytes())
        old_receipt.write_bytes((OUT/'engineering/sealed_interpretation_receipt.json').read_bytes())
    assert c.sha(prior)=='4c31221192f06c449c5ee460acce6fd6241a1cf67b4f16e4331520c8ffcacf9e'
    arms=c.read(OUT/'all32_arms.json');pairs=c.read(OUT/'all48_pairs.json');stage=c.read(OUT/'stage_decision.json')
    values=[c.read(OUT/f'reconstruction/group{n:02d}/current_core.json') for n in range(1,9)]
    assert len(arms)==32 and len(pairs)==48 and all(a['numbers_qualified'] and a['formal_protocol_qualified'] for a in arms)
    assert stage['execution_stage']=='COMPLETE' and stage['stage']=='BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION'
    assert stage['new_exposed_M_B_gains']==1 and stage['new_D1_exposed']==5
    assert not any(stage['veto'].values()) and not stage['conditions']['at_least_two_exposed_material_M_B_gains_or_new_certificates']
    assert not any(a['source_reduced'] for a in arms) and not any(p['severe_regression'] for p in pairs)
    actual_review=c.read(OUT/'review/post_formal_independent.json');assert actual_review['decision']=='ACCEPT'
    physical={(x['group_number'],x['arm']):x for x in c.read(OUT/'own_fleets_and_objective_parts.json')}
    text=prior.read_text(encoding='utf-8')
    start=text.index('## V20 certification')
    text=text[start:text.index('## Evidence and claim limits')]
    text=text.replace('This is a finite candidate-selection condition, not a significance\ntest. The complete stage rule still requires the remaining fixed Seed1\ngroup, including its possible higher-priority proof or severe-regression\noutcomes. No final stage or replacement paper reference is selected in\nthis partial-panel draft.',
        'This is a finite candidate-selection condition, not a significance\ntest. Both mandatory Seed1 groups are now complete. Neither the proof-risk\npriority nor either primary performance veto fires; the final stage and\none fixed existing paper reference are stated below.')
    text=text.replace('The final PB-C50-S\nSeed1 group remains necessary before any full-panel stage decision.',
        'The final PB-C50-S\nSeed1 group is retained separately below; neither repeat adds a new role.')
    head='''# Round122 frozen-method benchmark: complete result interpretation

The complete preregistered panel contains six new Seed0 problems and two
fixed Seed1 repeats:32 once-only arms and48 evaluable directed comparisons.
The single stage decision is **COMPLETE /
BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION**. Retain **frozen M-B as the
existing paper reference**; ENS-C remains the unchanged project default,
and MB-D1 remains a separately reported research candidate. This is no
default replacement or new algorithm selection. This batch ends here.

D1/P has5 WIN and1 MIXED on the six new problems. Both fixed Seed1 D1/P
comparisons are WIN. The decisive unmet positive-selection condition is
incremental breadth: only one exposed new role supplies a material D1/M-B
gain or new certificate, below the registered requirement of two. There
is no severe comparison or unresolved proof-source rejection in this batch.

The complete numerical tables are [all32 arms](all32_arms.csv) and
[all48 pairs](all48_pairs.csv); [the final report](final_report.md) includes
all three clocks. Values below are rounded for readability; the JSON/CSV
evidence retains full precision, signed gaps and original proof categories.
Every comparison uses its own physical U, qualified L and the original
certificate-first materiality rules. Case discussions use Seed0 unless
explicitly marked Seed1. No open cap is interpreted as a final proof time.

'''
    tail=['## Fixed PB-C50-S Seed1 repeat','',
        'All four methods remain open with qualified positive lower bounds. No source reduction, rejected proof source, damaged call or severe comparison occurs. The complete four-vehicle fleets remain physically feasible. This repeat adds no V50 nonzero certificate.','',
        '| Method | Own U | Qualified L | Signed gap |','|---|---:|---:|---:|']
    group=[a for a in arms if a['group_number']==8]
    for a in group:tail.append('| '+a['arm']+' | '+' | '.join(f'{a[k]:.10g}' for k in ['U','L','gap'])+' |')
    tail+=['',
        'D1/P, M-B/P and ENS-C/P are WIN. D1/M-B, D1/ENS-C and M-B/ENS-C are TIE. D1 and M-B have identical qualified endpoints; ENS-C has a higher L, but its0.0011534280 gap advantage is below the applicable0.0014180013 materiality threshold. All windows remain open, so no certification-time ratio applies.','',
        '| Pair | dU | dL | dgap | dG | d(lambda*P) |','|---|---:|---:|---:|---:|---:|']
    checked=[]
    for p in [p for p in pairs if p['group_number']==8]:
        a,b=physical[8,p['candidate']],physical[8,p['control']]
        dG=a['G']-b['G'];dP=a['lambda_P']-b['lambda_P']
        assert abs(dG+dP-p['dU'])<=1e-7 and abs(p['dgap']-(p['dU']-p['dL']))<=1e-12
        tail.append('| '+p['candidate']+'/'+p['control']+' | '+' | '.join(f'{x:+.10f}' for x in [p['dU'],p['dL'],p['dgap'],dG,dP])+' |')
        checked.append(dict(pair=p['candidate']+'/'+p['control'],dG=dG,d_lambda_P=dP,**{k:p[k] for k in ['dU','dL','dgap','classification']}))
    tail+=['',
        'The three integrated methods retain G=0.0501195842 and lambda*P=0.3222221913, identical to their Seed0 physical endpoints. Cold P-GRB has G=0.0760398198 and lambda*P=0.3157407388. Their improvement in G therefore outweighs a larger penalty term; this differs from Seed0, where both components favored the integrated endpoints. These are arithmetic endpoint decompositions and do not identify an internal search cause.','',
        'D1 is enabled but naturally unexposed again: one paid root proof is retained, the pair is incomplete, installation and expanded Optimize counts are zero. The original AM path records three atomic splits. The first two preserve infeasible right children, followed by adaptive_mass_score_reaches_tau. The not_exposed record occurs on L0.0.0.0 at177.8644658 process seconds. Neither a missing installation nor these original splits is an engineering failure. The full-method comparison retains this observation. A feasible own fleet outside a terminal leaf interval does not by itself establish that a Start was submitted, accepted or installed into that restricted model. Those stages require their own call/model/scope records.','',
        'Each integrated method makes seven returned LP calls and one returned MIP call. H takes34.2260–34.5153 seconds, the recorded LP partition26.0560–103.1310 seconds and the MIP partition3391.5920–3468.6970 seconds. This locates the dominant recorded work in the MIP request, alongside actual multi-model LP costs. It does not separate incumbent search from a proof tail or establish counterfactual D1 overhead.','',
        '| Method | T_produce | T_verify | T_total |','|---|---:|---:|---:|']
    for a in group:tail.append('| '+a['arm']+' | '+' | '.join(f'{a[k]:.10f}' for k in ['T_produce','T_verify','T_total'])+' |')
    tail+=['',
        'The final D1 producer includes its continuation wrapper birth and imports. Its necessary verification takes85.1722841 seconds; the subsequent175.4091488-second four-arm reconciliation is charged to group management and is not attached to D1 T_verify. The120-second management amount is a reference/reservation, not a hard group timeout. All actual fees remain below the unchanged100000-second total limit.','',
        'Cold P-GRB returned normally but the legacy R86 auditor asserted that the final physical U must not exceed the best earlier committed physical U. Independently verified sequence217 has F=0.391713327901773; the final returned fleet has F=0.39178055857928196. Both are feasible, and every one of64 native bounds remains below both. The assertion orders two valid upper bounds rather than detecting an erroneous lower bound. The frozen contract uses the final fleet, so recovery retains final U=0.39178055857928196, L=0.34945085964584033 and certificate=false. The stronger historical witness is not substituted.','',
        'A strictly hash-scoped, read-only adapter replaces only this ordering assertion in memory with explicit physical and bound checks. Every other finalizer statement remains identical, and the complete inherited source/model/Seed/return audit passes. Separate recovery sidecars preserve every original P byte, the original failed audit/traceback and formal08 exit1 fee. Actual T_verify=930.1450991000165 and T_total=4500.817390100012 include the failure, investigation and complete waiting interval; T_produce=3570.6722909999953 is unchanged. Independent admission preceded the fresh birth of the original never-started fourth D1 position. No already-produced arm was rerun. The recovery chain is disclosed in [the explanation](recovery/group08/recovery_explanation.md) and its bound closeout.','',
        'The Seed0 C50 comparisons were also WIN/WIN/WIN/TIE/TIE/TIE. Cold P-GRB improves its final physical U and L at Seed1 while the integrated physical U stays unchanged; this does not create a new role or justify choosing the better Seed. Both fixed Seed blocks remain beside their Seed0 results.','',
        '## Final candidate decision and fixed paper reference','',
        'The prioritized rule independently yields BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION. All32 positions and48 pairs are valid and evaluable; no proof-source rejection or severe regression is present. The six new D1/P comparisons give5 WIN/1 MIXED, five new roles actually expose D1 including V35/V50, D1 preserves the two M-B nonzero certificates, and both fixed Seed1 primary comparisons are WIN. Nevertheless, only PB-B50-U supplies an exposed new material D1/M-B WIN or new certificate. The required count is at least two. This alone prevents the positive freeze exit. The decision does not use ENS dominance as an additional hidden gate.','',
        'On the six new roles, D1/M-B is1 WIN/2 LOSS/1 MIXED/2 TIE. The PB-B35-B Seed1 WIN is a useful fixed-repeat observation but cannot replace a second new-role gain. Across all eight blocks, D1/P is7 WIN/1 MIXED; D1/M-B and D1/ENS-C are each2 WIN/2 LOSS/1 MIXED/3 TIE. These combined eight-block counts are descriptive and do not replace the registered six-problem denominator.','',
        'Retain frozen M-B as the one existing paper reference for the structured exact-method comparison. Its complete algorithm is already supported; it is WIN against cold P-GRB on all six new roles and both fixed repeats, obtains the same two new-role V20 nonzero certificates as D1, and captures the common gains without requiring the D1 breadth claim that failed here. ENS-C remains the implementation default and a full reported comparator. This reference recommendation is not an instance winner selector and does not claim M-B dominates ENS-C. M-B/ENS-C is1 WIN/1 LOSS/4 TIE on new roles and1 WIN/2 LOSS/5 TIE over all eight blocks. The PB-C35-U and PB-B35-B Seed1 losses remain explicit M-B limitations relative to ENS-C. Separately, historical R120 C2 Seed0 has severe D1/M-B LOSS (while M-B/P is WIN); its later Seed1 D1/M-B WIN does not erase the adverse Seed0 result.','',
        'The evidence supports completed finite benchmarking and open quality/bound improvements, with limited nonzero full-certification range. All new-role nonzero certificates occur at V20: P-GRB has one and each integrated method has two. No method obtains a new V35/V50 nonzero certificate, and no own-zero or source-reduced result is used to substitute for one. Both C50 D1-unexposed observations remain valid full-method results.','',
        'No new research problem is required to close this benchmark task. The batch ends without automatic extra inputs, Seeds, variants or algorithm changes. Any later mathematical research would need its own question and preregistration; these endpoint and cost observations do not establish a universal missing cut or an internal D1 branching mechanism. R121 remains COMPLETE / ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK as historical support, while this broader batch does not select a new primary. D0 remains an ablation and MB-PC remains stopped.','',
        '## Evidence, execution cost and claim limits','',
        'The canonical authorities are all eight current_core.json files, full32/all48 tables, proof_reliability, mechanism_account, own_fleets_and_objective_parts, Seed/source/scale layers, and the original call/model/epoch/cutoff/Seed/Start/return records. All32 physical objectives and three clocks,48 exact typed pair records and the prioritized stage were actually recomputed by a different executor. The independent review is ACCEPT, covering all nine negative/mixed pairs, a complete V50 fleet and the actual exposed PB-B50-U D1 model4 (103428 rows/24522 columns), its base objective/types, all three D1 rows, outward endpoints/ObjCon and full Start/scope checks. No native Optimize was used for this review. The performed numerical checks are not a guarantee against every possible floating-point error.','',
        'The complete physically feasible fleets satisfy inventory, service direction/integrality, assigned-Q prefix/return loads and original time constraints. The open outcomes are not attributed to missing vehicles or incomplete physical solutions. Native MIP costs dominate the recorded large-role partitions; the evidence does not establish inventory/route assignment as a causal bottleneck or distinguish all search effort from proof effort. LP, H, installation, callbacks, closeout and post-seal verification remain separately visible, with no nested-time double counting. Actual certified-time ratios are reported only when both methods certify.','',
        'Observed outer fees are75202.98446220002/100000 seconds, including every failed/recovery episode. Qualification uses448.3212315000128/6000 seconds, below the3000-second soft plan; no soft-plan extension was needed. There are50 fee-level observed/conservative starts plus5 distinct controllers,55 in total. Native component timers are nested. Read-only report/review/publication work has its own measured receipts and is not replaced by a human-time estimate.','',
        'The six problems are finite, non-IID and nonfactorial. The two station sources do not supply six cities; station overlaps remain recorded. Source, geography, stock, Q/T, weight totals and scale vary together, so their isolated causal effects are not estimated. Two Seeds do not estimate population probabilities. No best-of-Seed endpoint, across-instance winner dispatch or cross-round exact speedup is constructed. The algorithm/source identities, numerical policy, full denominators and adverse cases stay fixed. Workspace and storage measures support reliable execution and are not mathematical contributions.','']
    combined=head+text+'\n'.join(tail)
    combined=re.sub(r'\b(has|and|its|applicable|at|takes|partition|subsequent|The|unchanged|of|All|give|is|each|are|uses)(?=\d)',r'\1 ',combined)
    combined=combined.replace(':32',': 32').replace('full32/all48 tables','full 32/48 tables')
    combined=combined.replace('[all32 arms]','[32 arms]').replace('[all48 pairs]','[48 pairs]')
    target.write_text(combined,encoding='utf-8')
    final_text=target.read_text(encoding='utf-8')
    assert 'draft' not in final_text.lower() and 'remaining fixed' not in final_text.lower()
    receipt=dict(UTC=c.utc(),scope='COMPLETE_ALL_EIGHT_GROUPS32_ARMS48_PAIRS',document_SHA=c.sha(target),
        previous_document_SHA=c.sha(prior),previous_receipt_SHA=c.sha(old_receipt),
        core_SHAs={str(n):c.sha(OUT/f'reconstruction/group{n:02d}/current_core.json') for n in range(1,9)},
        all32_arms_SHA=c.sha(OUT/'all32_arms.json'),all48_pairs_SHA=c.sha(OUT/'all48_pairs.json'),
        stage_decision_SHA=c.sha(OUT/'stage_decision.json'),stage=stage['stage'],paper_reference='M-B',
        ENS_default_unchanged=True,all_fixed_Seed_layers_retained=True,no_instance_selection=True,
        group08_displayed_endpoint_clock_rows=group,group08_decomposition=checked,
        original_groups01_07_case_numbers_retained_from_prior_verified_prose=True,
        full_actual_independent_review_SHA=c.sha(OUT/'review/post_formal_independent.json'),
        pending='Separate final prose claims review and actual public delivery/recovery/cleanup',
        script_SHA=c.sha(__file__),Optimize=0,native_starts=0)
    c.write(OUT/'engineering/sealed_interpretation_receipt.json',receipt)
    c.write(OUT/'paper_reference_recommendation.json',dict(method='M-B',stage=stage['stage'],
        rationale='Existing complete reference; six new and both fixed-repeat M-B/P WIN, two V20 certificates retained, D1 incremental breadth condition unmet.',
        limitations=['No M-B dominance over ENS-C','New C35 LOSS','Fixed B35 Seed1 LOSS versus ENS-C','Historical R120 C2 Seed0 severe D1/M-B LOSS retained as D1 sensitivity','No new V35/V50 nonzero certificate'],
        project_default='ENS-C',default_changed=False,instance_or_Seed_dispatch=False,automatic_further_batch=False,
        all48_pairs_SHA=c.sha(OUT/'all48_pairs.json'),stage_decision_SHA=c.sha(OUT/'stage_decision.json')))
    print(json.dumps(dict(complete=True,stage=stage['stage'],paper_reference='M-B',document_SHA=c.sha(target))),flush=True)

if __name__=='__main__':main()
