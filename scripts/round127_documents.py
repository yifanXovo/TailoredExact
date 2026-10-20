"""Maintain one complete reading source and concise four-axis study report."""
from round127_common import *
import csv,collections
def csvrows(name):
    with (OUT/(name+'.csv')).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def fmt(value,missing='open'):return missing if value in [None,''] else f'{float(value):.3f}'
def mdtable(head,values):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in values)+'\n'
def counts(p):return ', '.join(f'{k}: {v}' for k,v in p['classes'].items())
def documents():
    summary=read(OUT/'stratified_summary.json');selection=read(OUT/'tuning_selection.json');q=selection['selected']
    assert summary['all_observed_arms_qualified'],'resolve or explicitly report any additional qualification fault before generating this complete-position text'
    main,tiny,core=map(csvrows,['main_pairs','tiny_pairs','core_pairs']);seed=csvrows('seed_transitions');mechanisms=csvrows('mechanism_costs')
    old=ROOT/'results/unified_exact_round126'
    for name in ['model_appendix.md','algorithm_appendix.md','references.bib']:
        (OUT/name).write_bytes((old/name).read_bytes())
    (OUT/'tables').mkdir(exist_ok=True)
    for p in (old/'tables').glob('*'):
        if p.is_file():(OUT/'tables'/p.name).write_bytes(p.read_bytes())
    seed_section='''### 6.4 Seed confirmation with the original executable

Round127 v3 retains the six problems and original complete caps, changes Gurobi Seed from 0 to 1, and independently pays both original executable E0 arms. These are six problems under two Seeds, with no best-of-Seed selection. The new symmetric direction uses strict unrounded complete certification cost on both-certified pairs, or a qualified certificate against a valid open comparator. Both-open is undetermined. The historical materiality labels in Section 6.3 remain historical; Table R127-S reports the additional symmetric direction.

'''
    seed_section+='**Table R127-S. E0 Seed1 certification and transition from the same six Seed0 problems.** Times are complete production seconds, present only for qualified certificates.\n\n'
    seed_section+=mdtable(['Problem','Seed0 status / direction','Seed1 status / direction','MB cert s','P cert s'],[[r['id'],f"{t['Seed0_category']} / {t['Seed0_direction_new_symmetric_rule']}",f"{r['classification']} / {r['direction']}",fmt(r['left_T_cert']),fmt(r['right_T_cert'])] for r,t in zip(main,seed)])
    seed_section+=f"\nSeed1 gives {counts(summary['main'])}. Directions are {summary['main']['directions']}. The conditional geometric mean P/MB ratio is {fmt(summary['main']['conditional_geometric_mean'])} over {summary['main']['both_certified_intersection_n']} both-certified problems; this intersection does not represent the open runs.\n\n"
    tiny_section='''### 6.5 Tiny cases, repeated Seeds and absolute delay risk

Two once-generated geographic cases, SM-C8-S (V8/M1, shortage, Q=20, T=2400) and SM-B10-B (V10/M2, balanced, Q=15/25, T=3600), use E0 and a 90-second complete cap. Each uses Seeds 0,1,2 and two independent repetitions with reversed method order. No warmup or cross-run fleet, bound, Start or basis is shared. Twelve matched observations still concern two problems. The 10-second axis is an absolute observed-delay warning, not an internal method switch or statistical significance threshold. A smaller positive delay is still a direction Lose.

'''
    tiny_section+='**Table R127-T. All tiny observations.** Delta is MB minus P, only when both certify.\n\n'
    tiny_section+=mdtable(['Problem','Seed / repeat','Status','MB cert s','P cert s','Delta s','Delta >=10 s'],[[r['id'],r['seed']+'/'+r['repeat'],r['classification'],fmt(r['left_T_cert']),fmt(r['right_T_cert']),fmt(r['left_minus_right_seconds'],'N/A'),r['dt_ge_10_warning'] or 'unknown'] for r in tiny])
    for t in summary['tiny_risks']:
        tiny_section+=f"\n{t['id']}: {t['both_certified_pairs']}/6 both-certified, {t['P_only_count']} P-only, {t['dt_ge10_count']} observed delays at least 10 seconds. Median delta {fmt(t['median_dt'])} seconds ({t['median_scope']}); repeated warning={t['repeated_ge10']}, all-six median warning={t['typical_median_ge10']}. Per-Seed paired differences are {t['by_seed']}. No cap is substituted for a missing certification time.\n"
    core_section='''### 6.6 Grouped mechanism diagnostics on three known roles

All core methods use the same frozen E1 executable and DLL, fresh Seed1 runs and own complete H. K1 is SC-C15-S (600 seconds), K2 SC-B20-S (1200), and K3 PB-B35-B (1200). E1 pays its own P and MB comparators; the same-named E0 observations are not reused. MR deletes only support cover/conditional handling and ordered compatible-supply rows C_R. MG deletes only explicit H-spread, variable-S/fixed centering, objective estimators and the dedicated W_SP block C_G. Existing derived inventory domains, exact Gini/state products, cap/floor, penalty-LB closure and required movement remain. MS2 deletes only three-station support, retaining pairs and ordered compatibility. Native Gurobi Cuts retain their original settings in all MB-type arms. These are deletion diagnostics around the same H and representation, not alternative proposed algorithms.

The required MD specification did not pass mathematical qualification. The retained numerical closure can emit an impossible row when gamma_L + lambda P_LB >= U0 - 1e-9. As already explained in Appendix A.5.6/A.7, that closure establishes no strict improver under the declared numerical policy; it need not retain an equal-U0 physical solution or its Start. A legal V2, zero-stock, T=60, handling-unit=120 boundary has forced Y=0, P_LB=2 and U0=0.3. Its equal-U0 empty fleet violates only the impossible row. Thus the requested inclusive root embedding and retained own-U0 Start cannot both be guaranteed while preserving that closure. Three MD arms were blocked before formal evaluation. This is a specification incompatibility, not evidence that interval control is beneficial or harmful, and does not by itself revoke the existing no-strict-improver proof policy. No replacement experiment was added.

'''
    core_section+='**Table R127-C. All predeclared core comparisons.** Left is the evaluated method; ratios use the both-certified intersection only. PT aliases, when applicable, are marked and not counted independently.\n\n'
    core_section+=mdtable(['Role','Left / right','Status','Direction','Left cert s','Right cert s','Right / left'],[[r['id'],r['left']+'/'+r['right']+(' (alias)' if r['alias']=='True' else ''),r['classification'],r['direction'],fmt(r['left_T_cert']),fmt(r['right_T_cert'],'not run' if r['right']=='MD' else 'open'),fmt(r['right_over_left_certification_ratio'],'N/A')] for r in core])
    core_section+='\n**Table R127-M. Original root exposure and cost.** Native seconds are diagnostics within the complete production clock. Unknown means unavailable from the original run; no extra Optimize was used.\n\n'
    core_section+=mdtable(['Role / mode','H complete','Root rows / cols','Root LP L','LP native s','MIP native s','Splits / target hits'],[[r['id']+'/'+r['method'],r['H_complete'] or 'N/A',r['root_rows']+'/'+r['root_columns'],fmt(r['root_LP_bound'],'unknown'),fmt(r['LP_native_seconds'],'unknown'),fmt(r['MIP_native_seconds'],'unknown'),(r['split_count'] or 'N/A')+'/'+(r['target_reached_events'] or 'N/A')] for r in mechanisms])
    core_section+='\nActual family counts, nonzeros, H/fleet identities, native calls/nodes and first logged own-witness availability are in mechanism_costs.csv. Saved original root-LP points are tested against actual deleted rows without a new solve. For MG, W is eliminated using its serialized bounds and every W-containing inequality; an empty interval identifies only non-extendibility of that saved point. A nonempty interval or equal LP objective does not establish global redundancy. These root diagnostics do not establish certification-time causality. Full H/scope matching and actual row/column differences are recorded per role. Pair/triple totals 1120,2660,21420 are below the shared 50000 cap, so MS2 does not redistribute a binding truncation budget.\n\n'
    tuning='''### 6.7 A bounded, separately trained compact baseline

The six fixed configurations vary only MIPFocus (0/1/2/3) and native Cuts (-1/2). S12, PB-B20-S and R98-C2 each use Seeds 2 and 3, totaling 36 E1 cold-P runs in a precommitted cyclic order. None is a core, main or tiny evaluation input. Actual model environments read back the settings after presets, with zero Starts. Selection maximizes qualified certifications N, then the minimum per-Seed count, then the declared censored penalty score and tie-breakers. A nondefault requires no loss in N or its per-Seed minimum, and either more certifications or at least a 10% score improvement when N ties above zero. The score's open-run value 1 is an artificial training penalty; it is never a certification time or speedup. Complete training clocks use the uniformly recorded parent admission marker; original sealed receipts and the initial import-prefix correction are preserved separately.

'''
    tuning+='**Table R127-Q. All six predeclared configurations.** Each denominator is six training positions; the two per-Seed counts each have denominator three.\n\n'
    tuning+=mdtable(['Config','Focus / Cuts','N Seed2','N Seed3','N / N_min','Score'],[[r['id'],str(r['MIPFocus'])+'/'+str(r['Cuts']),r['N_by_seed']['2'],r['N_by_seed']['3'],str(r['N'])+'/'+str(r['N_min']),fmt(r['S_q'])] for r in selection['scores']])
    tuning+=f"\nThe committed selection is {q['id']} (MIPFocus={q['MIPFocus']}, Cuts={q['Cuts']}). "+('No stable increment was identified within this finite screen. PT therefore points to P in each core role: three aliases, no duplicate observations or zero-time speedups. ' if q['id']=='q0' else 'This one parameter file is used unchanged in all three held-out known roles, including adverse outcomes. ')
    tuning+='This is parameter holdout confirmation on known instances, not an independently sampled benchmark or an optimally tuned general solver. The main comparison MB/P changes the whole integrated method and cannot identify one component. Shared MB arms across seven core comparisons are not independent replications.\n\n'
    manuscript=(old/'manuscript.md').read_text(encoding='utf-8-sig')
    manuscript=manuscript.replace('Round126 complete certification-focused reading draft, 19 October 2026.','Round127 v3 complete integrated-diagnostics reading draft, 21 October 2026. R126 results below retain their historical scope.')
    manuscript=manuscript.replace('## 7. Extended endpoint evidence',seed_section+tiny_section+'\n'+core_section+tuning+'## 7. Extended endpoint evidence',1)
    cert=summary['per_layer_certifications'];tiny_warn=sum(t['dt_ge10_count'] for t in summary['tiny_risks']);tiny_both=sum(t['both_certified_pairs'] for t in summary['tiny_risks']);tiny_ponly=sum(t['P_only_count'] for t in summary['tiny_risks'])
    abstract_add=f" Round127 v3 adds six Seed1 confirmations: MB certifies {cert['E0_main']['MB']}/6 and P {cert['E0_main']['P']}/6. Its twelve tiny matched repeats give {tiny_both} both-certified pairs, {tiny_ponly} P-only pairs and {tiny_warn} observed MB delays of at least 10 seconds. The same E1 build supplies {summary['core_observed']} core arms and 36 separately trained compact runs selecting {q['id']}; on the three known core roles, MB certifies {cert['E1_core']['MB']}/3 and P {cert['E1_core']['P']}/3. The three mandatory MD arms remain blocked by the inclusive-root/equality-closure incompatibility; the diagnostic study is partial. All unfavorable and open results are retained in Sections 6.4-6.7."
    manuscript=manuscript.replace('**Keywords:**',abstract_add.strip()+'\n\n**Keywords:**',1)
    manuscript=manuscript.replace('We evaluate a complete tailored exact method, denoted M-B,','We evaluate a complete tailored exact method, a tailored branch-and-cut framework with Gini-interval decomposition (GI-TBC), whose frozen implementation identity is M-B,',1)
    manuscript=manuscript.replace('## 9. Conclusion','The Round127 diagnostic cohort comprises nine distinct evaluation inputs and three separate training inputs. E0/E1 layers and shared-arm comparisons remain distinct. Its execution status is PARTIAL because MD failed its mandatory inclusive-root qualification. The four evidence axes are reported separately; the remaining specification decision must not be hidden by wins elsewhere. The unchanged mathematical appendices retain the complete R125 derivations and declared numerical-closure distinction.\n\n## 9. Conclusion',1)
    manuscript=manuscript.replace('## References and supporting material','Round127 adds bounded Seed, tiny, grouped-row and compact-parameter evidence to this conclusion. It does not establish universal component necessity, an absence of tiny regressions or superiority to the best possible Gurobi tuning. The single next priority is substantive review of the MD inclusive-root/retained-closure specification; no follow-up algorithm or enlarged experiment is executed here.\n\n## References and supporting material',1)
    (OUT/'manuscript.md').write_text(manuscript,encoding='utf-8')
    write(OUT/'manuscript_lineage.json',dict(parent='Round126 full reading source',parent_SHA=sha(old/'manuscript.md'),appendices={n:dict(parent_SHA=sha(old/n),active_SHA=sha(OUT/n),byte_identical=True) for n in ['model_appendix.md','algorithm_appendix.md','references.bib']},historical_tables_preserved=True,no_R125_derivation_removed=True))
    report=f'''# Round127 v3 final study report

Execution: **PARTIAL**. Scientific judgment: **{summary['scientific_judgment']}**.
The issue is confined to the requested MD inclusive-root/own-U0-Start specification and retained documented no-strict-improver closure. Three MD arms were unstarted; no D-effect result is claimed. This finding does not itself revoke frozen MB's existing numerical proof policy.

The sole paper algorithm remains frozen M-B / GI-TBC. E0 main/tiny and E1 training/core are separate performance layers. All unaffected prescribed positions completed, with no outcome-driven retries, replacement roles, cap extensions or parameter changes.

## Four evidence axes

1. Seed confirmation: {counts(summary['main'])}; directions {summary['main']['directions']}. The Seed0/Seed1 transition table still concerns six problems.
2. Tiny risk: {counts(summary['tiny'])}; directions {summary['tiny']['directions']}. Two problems, six observations each; absolute 10-second flags, P-only counts and per-Seed differences are in tiny_statistics.csv. Missing certification times stay null.
3. Mechanisms: MD blocked before formal; C_R, C_G and three-station support comparisons are listed below. They fix H/representation and test only named deleted groups. A faster weakened arm remains a diagnostic and does not replace MB.
4. Bounded compact tuning: selected {q['id']}, Focus={q['MIPFocus']}, Cuts={q['Cuts']}, from all 36 predeclared training positions, before E1 evaluation. {'q0 makes PT a P alias, not a stronger independent baseline.' if q['id']=='q0' else 'One unchanged selected file was applied to all three known held-out roles.'} Open training penalties are not times to certification.

'''
    report+=mdtable(['Comparison','Nonalias typed statuses','Evaluable / unevaluable / alias','Directions'],[[k,counts(v),f"{v['evaluable_nonalias_entries']} / {v['unevaluable_nonalias_entries']} / {v['alias_entries']}",str(v['directions'])] for k,v in summary['core_by_comparison'].items()])
    report+='\nMechanism dispositions: '+str(summary['mechanism_axis'])+'\n'
    report+=f'''
## Evidence and denominator limits

There are {summary['observed_formal_arms']} actual formal arms: 12 E0 main, 24 E0 tiny and {summary['core_observed']} E1 core. Three MD positions are blocked; {summary['PT_aliases']} PT aliases are separately identified. Evaluation has nine distinct inputs; training has three inputs and 36 runs. Six main pairs, twelve tiny pairs and 21 typed core entries share inputs and arms, so they cannot be pooled as 39 independent trials. Both-open remains UNDETERMINED, invalid/blocked UNEVALUABLE. Ratios and geometric means use only explicit both-certified intersections.

E0 PE SHA256: {E0_SHA}. E1 PE SHA256: {summary['tuning_selected'] and selection['E1_SHA']}. DLL SHA256: {DLL_SHA}. Exact source/build/family/parameter bindings are in E0_identity.json, E1_build.json, E1_frozen.json and method_matrix.md. No executable, DLL, license, font or full external paper is published.

The initial nine singleton training clocks omitted the wrapper import prefix from their raw production clock. No run was repeated. The fixed complete clock for all36 is recovered from each real parent admission marker and the sealed producer end, with raw receipts untouched; the parent prefix is not added twice to machine fees. The timing-only independent review covered the first eight positions. Later formal clocks include wrapper creation/imports from the actual OS process origin. A 60-second conservative allowance records the brief unmetered read-only clock closeout; it is not native solver time.

Native qualification and all formal outputs retain original physical, model/type/Start, actual Seed, cutoff/cover and normal-return checks. Numerical certificates retain the declared tolerances; finite checks are not universal rational matrix proofs. Root-point deletion checks add no Optimize and cannot predict eventual certification time. All missing or unexposed diagnostics remain unknown.

The complete maintained manuscript and byte-identical R125/R126 mathematical appendices preserve earlier R122/R123/R126 negative evidence. Manuscript/PDF validation and independent review are documented separately. Finite carriers retain all normal, failed and qualification records; public recovery uses one science commit without native software or historical campaign restoration.

Prepublication machine-accounting snapshot: {summary['fees']['paid_outer_seconds']:.3f} seconds paid; {summary['fees']['remaining_outer_seconds']:.3f} seconds remaining of 54000. Final resource_accounting.json includes subsequent packaging/review/recovery costs and explicitly labeled conservative administrative allowances. Nested H/LP/MIP runtime is never added again.

Next sole priority: resolve the MD inclusive-root/retained equality-closure specification through substantive user review. This round executes no new algorithm, instance, Seed panel, tuning configuration or longer window.
'''
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    print(json.dumps(dict(manuscript_bytes=(OUT/'manuscript.md').stat().st_size,appendices_preserved=True,report=True)))
if __name__=='__main__':documents()
