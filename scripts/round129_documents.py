"""Local update of the existing reading source; execute after final evidence review."""
from round129_common import *
import types
import round128_documents as previous_export

def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def fmt(x):return 'open' if x is None else f'{x:.3f}'

def documents():
    obs=read(OUT/'observations.json');dec=read(OUT/'scientific_decision.json');summ=read(OUT/'stratified_summary.json')
    review=OUT/'review/final_independent_review.md';assert review.is_file()
    aa=obs['arms'];pp=obs['pairs'];dd=obs['differences'];costs=obs['costs'];lookup={(a['id'],a['seed'],a['method']):a for a in aa}
    roles=read(OUT/'input_manifest.json')['roles'];newids=[p['id'] for p in roles[:4]]
    def cell(a):
        if not all(a.get(k) for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) or a.get('source_reduced'):return 'U (unqualified)'
        return ('C '+fmt(a['T_cert'])) if a['certificate'] and a['T_cert'] is not None else ('O ('+fmt(a['T_produce'])+')')
    methods=table(['Role','Seed','P','MB','MS2'],[[p['id'],s,*[cell(lookup[p['id'],s,m]) for m in ['P','MB','MS2']]] for p in roles for s in [0,1]])
    support=table(['Role','Seed','MS2/MB status','Direction','MS2 saving (s)'],[
        [r['id'],r['seed'],r['classification'],r['direction'],fmt(r['MS2_saving_seconds']) if r['MS2_saving_seconds'] is not None else 'N/A'] for r in obs['support']])
    counts=table(['Seed','P certified','MB certified','MS2 certified'],[[s,*[dec['new_certificate_counts_by_Seed'][str(s)][m] for m in ['P','MB','MS2']]] for s in [0,1]])
    allarms=table(['Role','Seed','Method','Certified','T_produce','T_verify','T_total','T_cert','U','L'],[
        [a['id'],a['seed'],a['method'],a['certificate'],*[fmt(a[k]) for k in ['T_produce','T_verify','T_total','T_cert']],f"{a['U']:.12g}",f"{a['L']:.12g}"] for a in aa])
    allpairs=table(['Role','Seed','Comparison','Typed status','Direction'],[[p['id'],p['seed'],p['left']+'/'+p['right'],p['classification'],p['direction']] for p in pp])
    rule_table=table(['Fixed condition','Requirement','Satisfied'],[[k,dec['condition_descriptions'][k],v] for k,v in dec['conditions'].items()])
    exposure=table(['Role','Seed','Same complete H','Same initial U/root','Triple cover removed','Triple conditional removed'],[
        [d['id'],d['seed'],d['complete_H_actions_fleet_equal'],d['initial_root_scope_U_equal'],
         d['actual_root_difference']['families'].get('cover_3',0) if d['actual_root_difference'] else 'unexposed/unknown',
         d['actual_root_difference']['families'].get('conditional_3',0) if d['actual_root_difference'] else 'unexposed/unknown'] for d in dd])
    cost_lookup={(c['id'],c['seed'],c['method']):c for c in costs}
    actual_cost='All ten matched MB/MS2 observations have the same complete H actions and fleets, initial U, root scope and settings. After triple deletion, the remaining rows and all columns, types, bounds and objective match exactly. The actual triple cover/conditional counts removed at each Seed are 0/910 (UC-C15-S), 2204/76 (UC-B20-B), 0/2280 (UC-C20-U), 3969/8211 (UC-B30-S), and 0/2280 (PB-C20-B). '
    actual_cost+='UC-B20-B naturally has three splits in each MB and MS2 arm at both Seeds; every other MB/MS2 arm has zero splits. This new exposure coexists with the historical R128 no-split observations. Without a new D control it does not identify a net decomposition speed benefit. '
    for seed in [0,1]:
        a=cost_lookup['UC-C20-U',seed,'MB'];b=cost_lookup['UC-C20-U',seed,'MS2']
        actual_cost+=f"At UC-C20-U Seed{seed}, MB and MS2 respectively use {a['MIP_native_seconds']:.3f} and {b['MIP_native_seconds']:.3f} native MIP seconds, {a['MIP_native_work']:.3f} and {b['MIP_native_work']:.3f} work units, and {int(a['native_nodes'])} and {int(b['native_nodes'])} nodes. Model-generation plus native-read seconds are {a['model_generation_seconds']+a['native_model_read_seconds']:.3f} and {b['model_generation_seconds']+b['native_model_read_seconds']:.3f}. "
    assert all(abs(cost_lookup[p['id'],s,'MB']['root_LP_bound']-cost_lookup[p['id'],s,'MS2']['root_LP_bound'])<=1e-12 for p in roles for s in [0,1])
    actual_cost+='The C20 saving accompanies lower MIP time/work despite more MS2 nodes at both Seeds; fixed row-writing/read savings are about 0.3 seconds. All observed matched root LP bounds agree within 1e-12. This finite agreement does not prove global redundancy of triple rows. Native costs remain nested explanatory measurements rather than T_cert.'
    endpoint_limits='UC-C15-S and UC-B30-S remain open for all three methods at both Seeds. UC-B30-S has an open-endpoint reversal: MS2 and MB U are respectively 0.381251 and 0.429057 at Seed0 but 0.429057 and 0.365930 at Seed1. UC-C15-S Seed1 also has slightly worse MS2 U than MB. Both-open comparisons remain UNDETERMINED with no certification ratio or Win. The three tiny negative signed gaps and all fifteen Seed1 raw top-level LB=0/certificate=false records are preserved. Qualified final endpoints use the original source/return/coverage and numerical policy; no raw field, LB or gap is clipped or rewritten.'
    ratio_summary='In the new layer, MS2/P and MB/P each have two both-certified observations, two method-only certificates and four both-open observations. Their certification-time ratio geometric means (right/left) are 87.827903 and 81.425709 respectively, solely on UC-B20-B at the two Seeds. MS2/MB has four both-certified observations (UC-B20-B and UC-C20-U at both Seeds) and four both-open observations; its right/left geometric mean is 1.179515 on those four observations only. In protection, MS2/P and MB/P are method-only certified at both Seeds and have no ratio; MS2/MB is both-certified at both Seeds with a 1.224121 right/left geometric mean. These intersections do not represent the full panel.'
    zero=[f"{a['id']}/Seed{a['seed']}/{a['method']}" for a in aa if a['method']!='P' and a['native_Optimize']==0]
    tag=dec['tag'];recommend=tag=='RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE'
    outcome=('The five fixed conditions support recommending uniform MS2 as the single method candidate for the next paper revision. This is a recommendation awaiting the user\'s adoption; the current method identity and historical full-M-B tables remain unchanged.' if recommend else
             'Necessary qualified evidence is incomplete; the identified issue requires resolution before a scientific promotion. The current method identity and historical tables remain unchanged.' if dec['execution']!='COMPLETE' else
             'Retain full frozen M-B as the sole paper method. The fixed confirmation ends with these observations; it does not trigger new inputs, Seeds, thresholds or per-instance selection.')
    migration='If adopted, the main-method performance claims would require separately labelled MS2 measurements for Tables SC3-SC5, R127-S and R127-T, the full-MB entries and derived comparisons in Tables 3-6, and their Supplement S authorities. Tables R127-C through R127-E and R128.1-R128.2 remain historical full-MB diagnostic evidence; any renewed mechanism claim must identify its new MS2 reference explicitly. This is a table-migration scope, not authorization to execute another batch.'
    section='''### 6.9 Prospective confirmation of a uniform pair-support candidate (Round129)

Round128 supplied a bounded development signal on known K2/SC-B20-S, while retaining the K1 timing reversal and open K3. Round129 is a separately preregistered finite confirmation of a single already implemented candidate. MS2 omits three-station support on every input and retains the full frozen H, R, pair support, ordered supply, C_G, controller and numerical policy. No MD-R variant is run and no MD-R pseudo-row suppression is applied to MB/MS2. P remains the original independently paid cold compact Gurobi baseline. All thirty arms use the original same E2 PE and Gurobi 13.0.2 DLL; the only varied native parameter is the prespecified Seed0/1.

The method remains a tailored branch-and-cut framework with Gini-interval decomposition. Its project strengthening is generated statically for each actual scoped model; Gurobi performs the native branching, presolve and native cut generation. The framework name or abbreviation supplies no separate novelty claim.

The four new problems are UC-C15-S (CITI, compact/r1, shortage, V15/M2, Q=[30,30], T=3600, cap600), UC-B20-B (CABI, regional/r2, balanced, V20/M2, Q=[20,40], T=7200, cap1200), UC-C20-U (CITI, regional/r1, surplus, V20/M2, Q=[30,30], T=7200, cap1200), and UC-B30-S (CABI, compact/r2, shortage, V30/M3, Q=[25,25,25], T=7200, cap1200). The known PB-C20-B protection input (V20/M2, Q=[30,30], T=3600, cap900) is reported separately and cannot supply a prospective gain. These are draws from two existing source tables, not new cities, IID samples or a full factorial design. Seeds add observations of the same problems.

The recipe, dependencies, all ten method orders, caps and five candidate rules were committed before once-only offline generation. Original R126/R122/R109/R57 anchor, tie, target, inventory, weight, depot and travel-time rules are retained. No H/LP/MIP or difficulty/reachability filter selected the data. All lawful station overlap is retained. Shortage arithmetic supplies positive necessary objective floors of 12/275 and 464877/2500000 for UC-C15-S and UC-B30-S respectively, excluding the depot; these decimal-data checks are not injected into any model, Start or reported native lower bound. Balanced/surplus outcomes remain regardless of zero objectives or backend exposure.

Each method independently pays its complete H/admission/model/native/online-output workflow under the original complete deadline, shutdown reserve and numerical settings. No solution, U, Start, basis, tree or cache is shared. The opposite Seed reverses each role's method order. Thirty arms form ten matched groups and thirty typed shared-data comparisons (MS2/P, MS2/MB, MB/P), not thirty independent trials. The new layer contains 24 arms/eight groups/24 comparisons; protection contains six/two/six.

**Table R129.1. Every fixed complete-method observation (seconds).** C denotes a qualified certificate and its complete T_cert=T_produce. O denotes a qualified open result and observed T_produce in parentheses, with T_cert=null. U would identify unqualified evidence. The last two rows are the known protection role.

'''+methods+'''
**Table R129.2. New-input certification counts, keeping Seeds separate (denominator four per Seed).**

'''+counts+f'''
The numbers of new problems certified at both Seeds are P: {dec['new_both_Seed_certified_problem_counts']['P']}, MB: {dec['new_both_Seed_certified_problem_counts']['MB']}, MS2: {dec['new_both_Seed_certified_problem_counts']['MS2']}. At Seed0 the P-certified/method-open counts are MB: {dec['new_P_certified_method_open_by_Seed']['0']['MB']}, MS2: {dec['new_P_certified_method_open_by_Seed']['0']['MS2']}; at Seed1 they are MB: {dec['new_P_certified_method_open_by_Seed']['1']['MB']}, MS2: {dec['new_P_certified_method_open_by_Seed']['1']['MS2']}. Full per-observation U, qualified L, raw signed gap, all three clocks and every reverse comparison remain in the accompanying arms/pairs authorities and Supplement S. Open endpoints are not certification Wins, and open times are not replaced by caps.

**Table R129.3. All matched MS2/MB directions, including the separate protection role.** Savings are T_MB-T_MS2 only when both certify; N/A carries no unobserved speed ratio.

'''+support+'''
Component attribution is conditional on actual complete H/actions/fleet, initial U and root scope, native settings, and duplicate-preserving full matrix/column/type/bound/objective equality after the triple deletion. Every actual root is checked after its own H. Subsequent legitimate own-UB trajectories can differ. Missing roots, incomplete H or unmatched scopes restrict the observation to a complete-method comparison. The all-candidate counts (1120, 2660, 2660, 13485 and 2660) are below the original shared cap50000, so this panel does not reassign a binding enumeration budget. Actual cover/conditional counts and split/target, LP/MIP work/nodes, model/Start and witness-availability diagnostics are retained in the mechanism evidence. An absent split neither invalidates completeness nor demonstrates multi-leaf speedup. No new D control effect is measured.

'''+actual_cost+'\n\n'+endpoint_limits+'\n\n'+ratio_summary+'''

For a fixed valid scope with identical domains and objective, deleting valid triple rows preserves the physical integer optimum and can only weaken or preserve the mathematical optimal LP lower bound. No theorem makes deletion faster. Native Runtime, work, nodes, root LP time, fewer rows or a smaller open gap do not replace complete certification time. Ratios and their geometric means are restricted to explicitly labelled both-certified intersections.

The fixed research decision magnitude requires a certified MS2 saving of at least max(10 seconds,10% of MB time), or MS2-only certification. A material time cost uses the symmetric faster-method reference; these labels do not alter strict unrounded Win/Lose or claim statistical significance. Advancement also requires no additional per-Seed certification loss or P-only risk, protection of every current MB certificate, no two-Seed large protection slowdown, one newly exposed role supporting MS2/MB materially at both Seeds, and one new role giving direct MS2/P certification Wins at both Seeds. Development K2, protection, subsecond directions and open gaps cannot substitute for the new signal.

'''+rule_table+f'''
The finite scientific recommendation is `{tag}`. {outcome} The exact mode mapping is original E2 `--round127-mode mb` to original E2 `--round127-mode ms2`; only three-station cover/conditional support is omitted uniformly. No old MB number is relabelled MS2. {migration} This small prospective panel does not establish V50/V60 safety. The frozen paper method, P benchmark, historical ENS-C default, R127 PT negative findings and all R128 reverse/open/no-split facts remain identifiable. No extra confirmation is automatically appended.

'''
    inherited={}
    def fetch(path):
        data=git('show',BASE+':'+path);inherited[path]=hashlib.sha256(data).hexdigest();return data
    # Git returns bytes without universal-newline decoding. Canonicalize inherited
    # CRLF before writing on Windows so tables do not acquire CRCRLF blank rows.
    main=fetch('results/unified_exact_round128/manuscript.md').decode('utf-8-sig').replace('\r\n','\n')
    main=main.replace('Round128 inclusive-root and support reading draft, 22 October 2026.','Round129 uniform-support confirmation reading draft, 22 October 2026.',1)
    assert main.count('## 7. Extended endpoint evidence')==1
    main=main.replace('## 7. Extended endpoint evidence',section+'## 7. Extended endpoint evidence',1)
    note='\n\nRound129 separately evaluates four fixed new inputs and one known protection role, thirty complete arms and thirty shared-data comparisons in Section 6.9. Execution is '+summ['execution']+'; the finite recommendation is `'+tag+'`. '+outcome+'\n'
    main=main.replace('\n## 1. Introduction',note+'\n## 1. Introduction',1)
    main=main.replace('The current priority is substantive review of the single unexecuted uniform triple-support simplification design in Section 6.8. The frozen full M-B remains the sole paper method.',
        'That is the historical Round128 recommendation. Section 6.9 now reports the separately authorized finite confirmation and its candidate decision. '+outcome)
    main=main.replace('The sole next priority is substantive review of one unexecuted uniform simplification confirmation design:',
        'The historical Round128 next-priority recommendation, subsequently executed in Section 6.9, was substantive review of one then-unexecuted uniform simplification confirmation design:',1)
    main=main.replace('[research decision](research_decision.md)','[current candidate decision](candidate_decision.md)')
    main=main.replace('[Supplement S](tables/complete_results.md) is inherited unchanged from R124’s published arithmetic derivation;',
        '[Supplement S](tables/complete_results.md) retains the historical published arithmetic tables and adds the separately labelled Round129 clocks;')
    (OUT/'manuscript.md').write_text(main,encoding='utf-8',newline='\n')
    for name in ['model_appendix.md','algorithm_appendix.md','references.bib','tables/historical_display.md']:
        p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(fetch('results/unified_exact_round128/'+name))
    for name in ['literature_evidence.csv','literature_scope.md','historical_attribution.md','method_spec_matrix.csv','paper_method_config.json']:(OUT/name).write_bytes(fetch('results/unified_exact_round126/'+name))
    appendix='''

## B.13 Uniform support candidate confirmation (Round129)

Round129 changes no production source, H, model generator, numerical policy or controller. It reuses original E2 modes mb/ms2/p. The sole candidate MS2 suppresses triple support for every input while retaining pairs, ordered supply and the shared enumeration order/cap. The five fixed candidate rules and thirty complete paid observations are in Section 6.9. The distinction between a proposed candidate, the current frozen full-M-B method identity and its historical tables is retained. The independent finite review and public recovery are evidence checks, not new native solves or rational proofs of all matrices.
'''
    with (OUT/'algorithm_appendix.md').open('a',encoding='utf-8') as f:f.write(appendix)
    history=fetch('results/unified_exact_round126/tables/complete_results.md').decode('utf-8-sig').replace('\r\n','\n')
    (OUT/'tables/complete_results.md').write_text(history+'\n\n# Separately labelled Round129 complete clocks\n\n'+allarms+'\n'+allpairs,encoding='utf-8',newline='\n')
    (OUT/'reproducibility.md').write_text('# Round129 reproducibility\n\nUse RESUME.md, source_recipe.json, input_manifest.json, E2_identity.json and argv_freeze.json for the frozen protocol and original runtime identity. The physical/Start/source/return/coverage contract is inherited from R127/R128. Candidate rules and exact denominator limitations are in candidate_decision.md. Public restoration uses only the science-commit export manifest and current finite carriers, with no Optimize, native start, compilation, local-raw fallback or full historical campaign. The PE/DLL/license remain external and are not published.\n',encoding='utf-8')
    report='# Round129 final report\n\nExecution: **'+summ['execution']+'**. Scientific recommendation: **`'+tag+'`**.\n\n'+outcome+'\n\n'
    report+='Four new problems, one existing protection role, thirty complete independently paid arms, ten serial groups and thirty typed shared-data comparisons were frozen before once-only generation. No tuning, redraw, additional role/Seed, extended cap or performance retry was used. Two Seeds are not two new problems.\n\n'
    report+='## Candidate conditions and certification risk\n\n'+rule_table+'\n'+counts+'\nBoth-Seed-certified new problems: `'+json.dumps(dec['new_both_Seed_certified_problem_counts'])+'`; P-certified/method-open new risks: `'+json.dumps(dec['new_P_certified_method_open_by_Seed'])+'`.\n\n'
    report+='New roles satisfying condition4: `'+json.dumps(dec['rule4_supporting_new_inputs'])+'`; condition5: `'+json.dumps(dec['rule5_supporting_new_inputs'])+'`. Protection retention and both-Seed slowdown checks are retained verbatim in scientific_decision.json.\n\n'+methods+'\n'+support
    report+='\n## Actual exposure and costs\n\n'+exposure+'\n'+actual_cost+'\n\nNo-native MB/MS2 observations: `'+json.dumps(zero)+'`. Unexposed observations are retained and do not satisfy the new triple-removal signal. All actual split/target, LP/MIP seconds/work/nodes, modeling/Start and first retained own witness matching final U are in mechanism_costs.csv; native seconds remain nested explanatory costs, not certification time. Fixed-scope LP deletion monotonicity is a mathematical statement, not a speed claim or a claim of global redundancy. Missing diagnostics remain unknown.\n\n'+endpoint_limits+'\n\n'+ratio_summary+'\n\n'
    report+='## Complete arms and typed comparisons\n\n'+allarms+'\n'+allpairs+'\n'
    report+='## Identity, review and limits\n\nAll formal arms use original E2 PE `'+E2_SHA+'` and Gurobi DLL `'+DLL_SHA+'`. No production program or exporter was compiled. Preformal review accepted the frozen panel after correcting only two equal legacy P identity declarations from E0 to actual E2; the original argv/binding and missing-sparse-import failure remain preserved. The source and H/controller/model bytes remain frozen.\n\n'
    report+='The separate final executor\'s actual finite recomputation and representative matrix/physical/certificate-chain checks are documented in review/final_independent_review.md. These are finite internal evidence checks, not external replication, statistical evidence from IID problems or a rational audit of every matrix. Current paper defaults and all historical labels remain unchanged. R127 PT 0/3 versus P1/3, K1 timing reversal, K3 open outcomes and the R128 absence of actual MB splits remain in the maintained manuscript.\n\n'
    report+=migration+'\n\nResource accounting is recorded in resource_accounting.json. Actual publication, one public recovery and safe owned duplicate cleanup are added only after execution, with retained failures and receipts. PDF export and visual verification are separate from the scientific decision. No further experiment is executed by this confirmation.\n'
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    (OUT/'review_actions.md').write_text('# Round129 review actions\n\nThe separate preformal review accepted all frozen roles, method orders, modes, fixed rules and budget. It requested truthful E2 values for two legacy P executable declarations; both were corrected before production without changing their equality gate or solver behavior. The failed missing-R94 sparse import occurred before native production and remains in fees.\n\nThe final separate-executor record supplies its exact recomputed comparison/decision scope and representative physical, matrix and certificate-source observations. The author retains all contrary, open and unexposed outcomes. One saved-small-selection addendum covers the two pathless R127 tiny manifest roles without regenerating data.\n\nPDF page review, publication scan, one empty-root recovery and guarded cleanup are evidenced by the actual later receipts. No item is declared passed before its receipt exists.\n',encoding='utf-8')
    write(OUT/'manuscript_lineage.json',dict(UTC=utc(),parent_commit=BASE,inherited_exact_blob_hashes=inherited,
        maintained_source='manuscript.md + retained model/algorithm appendices + references + historical tables',
        new_section='6.9 Round129 finite uniform pair-support confirmation',R125_formula_and_H_controller_appendices_preserved=True,
        old_MB_tables_not_relabelled=True,PDF_pending=True))
    print(json.dumps(dict(documents_written=True,execution=summ['execution'],decision=tag)))

def pdf():
    # Reuse the maintained exporter and existing portrait handling for R128;
    # the new five-column R129 tables use the same default portrait flow.
    call=types.FunctionType(previous_export.pdf.__code__,dict(vars(previous_export),OUT=OUT,TEMP=TEMP))
    call()

if __name__=='__main__':{'documents':documents,'pdf':pdf}[sys.argv[1]]()
