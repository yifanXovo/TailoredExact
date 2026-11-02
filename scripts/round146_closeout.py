"""Assemble final evidence and navigation after the result-dependent decision."""
from round146_common import *
from round146_documents import SHORT,LABEL,table

def assemble():
    assert not budget()['unclosed']
    decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    full=read(OUT/'reports/full.json');cost=read(OUT/'cost_report.json');manifest=read(OUT/'candidate_manifest.json')
    assert not full['pending'] and full['all_entered_preserved']
    rows=full['new_arms']
    report='# Round146 scientific closeout: direct Gini deviation rows\n\n'
    report+=f'Decision: **{decision["decision"]}**. '+decision['decision_discussion']+'\n\n'
    report+='## Construction and finite optimized information\n\n'
    report+='The classical Gini–Hoover relation supplies at most two original-selector rows. State-conditioned continuous stock-box extrema are computed by exact dyadic water filling, with directed coefficient transport and root-once compatible sub-support inheritance. There are no new variables, source LPs, callbacks or controller changes. The original g + lambda P objective and R134 proof policy remain. The bare executable switch defaults off. The [mathematical note](mathematical_analysis.md) proves the bounds, zero-denominator scope and local half/half binary-family closure; the [LP report](LP_report.md) separates numerical optimized gains from saved-point separation.\n\n'
    report+='Five new matched LPs reuse sealed baseline optima and points. K20 gains on BASE, joint and STOCK; K35 and RX20 gain on BASE. The saved K35/RX20 joint optima satisfy GD and therefore provide unchanged-value witnesses on those particular strong carriers; those two LPs were not repeated. K20 joint is separated even with no zero-stock selector mass. The optional state-level Hoover branch and a global/state coefficient grid were not entered. These facts establish useful original-variable information; they do not establish complete performance.\n\n'
    report+='## One uniform complete candidate\n\n'
    report+='The frozen candidate is STOCK+GD-state, with STOCK as the same-PE reference. Every entered arm pays for its own full H and necessary verification. Seed0, Threads1, H seed20260626, original physical horizon/lambda and full registered caps are retained. The K20 strong-reference pair was admitted first; its result justified RX20, then the RB35 pressure question. All roles are known research configurations, not an independent validation set.\n\n'
    report+=decision['complete_discussion']+'\n\n'
    report+=table(['Role','Method','U','Supported L','Gap %','T cert','T verify','T total'],[
        [SHORT[r['role']],LABEL[r['method']],f'{r["U"]:.12g}',f'{r["L"]:.12g}',f'{100*r["relative_gap"]:.6f}',
         f'{r["T_cert"]:.6f}' if r['T_cert'] is not None else 'open',f'{r["T_verify"]:.6f}',f'{r["T_total"]:.6f}'] for r in rows])
    report+='Open T_cert values remain null in the machine data. [Full JSON](reports/full.json) and [CSV](reports/new_arms.csv) retain signed gaps, T_produce, Native return bounds separately from external supported L, initial LP, printed root-after-cuts, simplex, Work, nodes, splits, row/NZ counts and all call counts. [Physical incumbent trajectories](reports/verified_U_trajectories.csv) use committed producer availability clocks, separately from Native time. Root strength, density and trajectory differences are observations, not unique causal explanations.\n\n'
    report+=decision['historical_discussion']+'\n\n'
    report+='## Actual qualification, identity and cost\n\n'
    report+='Eight exact small-domain cases, inventory-unit invariance, actual canonical writer and Native readback, full physical and nonminimal-g Starts, strict sub-support inheritance, scope rejection and default-off matrix equivalence pass. The C++ writer driver has 14 total checks, including four scope rejection categories. One short complete health qualification is retained separately from formal performance. Its offline root-reader selection was amended before formal admission; original helper bytes and unused matrix are preserved, with no reoptimization or production change. Independent admissions bind the actual matrix/helper/PE identities.\n\n'
    report+=f'All {full["all_entered_observed_Native_Optimize"]} entered complete/qualification Native Optimize calls returned. The five standalone LPs are separate. New experimental outer cost is **{cost["charged_new_experiment_seconds"]:.9f} seconds** ({cost["charged_new_experiment_seconds"]/3600:.9f} hours), below 28800. H, all solver calls, qualification and necessary verification are counted once; nested runtimes/Work are not added again. Build cost is {cost["build_seconds_separate"]:.9f} seconds separately. Pure exact checks, authoring and public I/O are separate; unmetered authoring/probes are not presented as invented measured time. Unused budget is not unfinished work.\n\n'
    report+=f'Production source: `{manifest["source_commit"]}`. PE SHA256: `{manifest["production_PE_SHA"]}`. Three affected translation units were rebuilt; unchanged objects, compiler and DLL hashes are bound in the [manifest](candidate_manifest.json). Actual compiler bytes and Git EOL normalization have separate hashes. Stable R137 and every previous launcher/profile are unchanged. The only intentional R145 result amendment resolves the requested stage-index future tense. Original user modifications remain protected.\n\n'
    report+='## Delivery and scope\n\n'
    report+='The supplied preliminary ZIP/review attachment was unavailable locally. Four decision-relevant points were reconstructed from verified existing carriers with exact rational arithmetic and zero Optimize. This does not claim to rerun the supplied 11-point/47-configuration checks. The [goal](goal.md), [stage account](stage_evidence.md), [paper section](manuscript.pdf), [independent final review](review/final_scientific_review.json) and [continuation record](RESUME.md) preserve the scientific and delivery scope. Fixed science, production source and later publication metadata have distinct identities. Public recovery is a finite byte/member check, with no Optimize, compilation or commercial Native load. An English Draft PR is a required delivery step; its actual creation/readback is recorded separately in RESUME.\n'
    (OUT/'final_report.md').write_text(report,encoding='utf-8',newline='\n')
    stage='''# Stage evidence: shared resources, normalized products and direct deviations

R137 remains the stable GI-TBC algorithm and paper base. R138 STOCK retains
K15 certificate improvement about 112.77 to 33.82s and K20 certificates about
101.64/90.23s on two tested seeds, whose BASE references remained open at
cap1200. The second seed retains its disclosed V2 transport-repair identity;
it is not a pure seed-only intervention. R139–R142 answered finite placement,
two-sided count, conditional count-proof and CP questions without reopening
those grids. R143–R145 show complementary normalization/count/stock
information, while accurate root compression does not imply better search.

## R145 answers retained

R145 completed 11 new standalone LPs, four same-PE OFF/RN-JP Seed0 pairs
and one K35 old RN-P bridge. All formal positions and the short healthy
qualification passed. New experimental outer cost was 14485.720243101s;
its unused budget did not represent unfinished work.

| Role | OFF U / supported L | RN-JP U / supported L | Complete observation |
|---|---|---|---|
| K20 | .716806546278 / .705360087787 | .716806546278 / .702889298895 | Same U, weaker L, no certificate |
| K35 | .692854358631 / .558286661549 | .679684412741 / .541069698488 | U improves1.9008%; gap worsens.9718 percentage points |
| RX20-T1 | .645325030386 / same | .645325030386 / same | Same certificate, no material clock gain |
| RB35-T2 | .344642625592 / .218985949603 | .383702514966 / .220374791101 | U worsens11.3334%; gap worsens6.1062 percentage points |

K35 same-PE old RN-P U/L=.660923637174/.550645816146 is better at both
endpoints than RN-JP. RN-P reaches its final U around479.063s; RN-JP reaches
its worse final U around2175.578s. RB35 OFF already has .362136826572 around
849.266s, better than RN-JP's final .383702514966. R144's no-PC near-cap
prefix observation cannot explain away this R145 active-PC regression.

K35 RN-P/RN-JP printed root-after-cuts values are .44959/.44875;
K20 OFF/RN-JP .55666/.55620; RX20 .52281/.52165. K35 PC NZ33/384 and
root simplex3794/8435 differ; all formal outer splits are zero. These do not
identify row density as the sole cause or prove theoretical redundancy.
Joint K35 LP=.234508197894 exceeds strong RN+STOCK+TC+TC2=.229222197461;
O+joint does not raise it. Compact losses about2.75e-14/1.73e-14 are retained
as numerical observations, without a new repair-to-zero experiment.

## R146 answers

The zero-stock inequality ng >= sum_i s_i0 closes R145's half/half binary
family at g >=1/2 using one universal original-variable row. The strict
R145 complementarity theorem remains; its remaining gap alone does not
require a complex joint integer hull. This is a local epigraph statement,
not the complete routing hull and not a new general inequality theorem.

Five finite LPs establish direct optimized information, including K20 beyond
joint and beyond STOCK. K35/RX20 joint saved same-value feasible witnesses
are used without reoptimization. One uniform STOCK+GD candidate, complete
own H and same-PE STOCK comparisons answer incremental complete value.

'''
    stage+=decision['complete_discussion']+'\n\n'+decision['historical_discussion']+'\n\n'+decision['decision_discussion']+'\n'
    (OUT/'stage_evidence.md').write_text(stage,encoding='utf-8',newline='\n')
    guide='''# Round146: direct state-conditioned Gini deviation rows

The [scientific report](../results/unified_exact_round146/final_report.md),
[stage account](../results/unified_exact_round146/stage_evidence.md),
[mathematics](../results/unified_exact_round146/mathematical_analysis.md),
[finite LP results](../results/unified_exact_round146/LP_report.md) and
[paper section](../results/unified_exact_round146/manuscript.pdf) distinguish
the classical inequality, project-specific safe state coefficients, actual
optimized information and complete-method value.

'''+decision['decision_discussion']+'''

The separate research entry is `scripts/paper_s2_gd.py` and profile
`config/gi_tbc_gd_round146.json`. Required arguments are `--input`, `--out-dir`
(new directory), `--T`, `--cap` and `--seed`; physical lambda defaults to 0.15
and must match the intended objective. It prints a plan unless `--run` is
explicit. `--gd off` selects STOCK. The executable's `--round146-gd` switch
defaults off. All new output stays under `E:/codes/ExactEBRP-work`.

The frozen campaign matrices bind exact input, original lambda/T, caps,
Seed0/Threads1/H seed20260626, actual PE/DLL/source, helper bytes and full own-H
verification. See [entry equivalence](../results/unified_exact_round146/entry_check.json),
[same-PE results](../results/unified_exact_round146/reports/full.json),
[cost](../results/unified_exact_round146/cost_report.json),
[decision](../results/unified_exact_round146/candidate_decision.json) and
[continuation/delivery](../results/unified_exact_round146/RESUME.md).
Stable GI-TBC and all historical research launchers/profiles keep their identity.
'''
    (ROOT/'docs/round146_research.md').write_text(guide,encoding='utf-8',newline='\n')
    addition='\n\n<!-- Round146 evidence -->\n\nThe [Round146 direct Gini-deviation study](round146_research.md) adds at most two\noriginal-selector rows using the classical Gini–Hoover relation and exact\nstate-conditioned stock-box bounds. Five matched LPs establish useful information;\nexisting K35/RX20 joint witnesses avoid two unnecessary optimizations.\n'+decision['navigation_discussion']+'\nThe [decision](../results/unified_exact_round146/candidate_decision.json) and\n[delivery record](../results/unified_exact_round146/RESUME.md) retain all actual\npositive/negative evidence, source/PE identities and the separate publication checks.\n'
    for name in ['current_mainline.md','unified_exact_research_index.md']:
        path=ROOT/'docs'/name;text=path.read_text(encoding='utf-8');text=text.split('\n\n<!-- Round146 evidence -->')[0]
        path.write_text(text.rstrip()+addition,encoding='utf-8',newline='\n')
    print('Final scientific report, stage account and navigation assembled from frozen actual evidence')

if __name__=='__main__':assemble()
