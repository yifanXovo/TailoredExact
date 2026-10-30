"""Assemble compact source and final reports from qualified fixed authorities."""
from round142_common import *
from round142_analyze import require_idle
from round142_documents import table,SHORT,LABEL
configure()

def LP():
    require_idle();data=read(OUT/'reports/LP.json')
    body='# Round142 matched conditional source LPs\n\n'
    body+='The fixed R141 diagnostic ZIP is bound by SHA256 8552f9cbc2927e16b9f1e77f470a31651e4764c9034daa0e1fb0f04ee7a10d31. Six LP-floor conditional sources retain their actual MPS matrix, complete objective and ObjCon, physical input/support, g endpoints, cutoff, stock, old TC, parent TC2, selected count side and conditional child TC2. The inherited member comparison is in inherited_dependencies.json.\n\n'
    body+='C explicitly completes the selected or propagated linear ranges. Every saved original optimum satisfies these new ranges. Each new build reads the original MPS fingerprint, checks the full saved point against its rows and variable bounds, and confirms its identical objective. This yields twelve range-control equality witnesses with zero C Optimize, under the inherited numerical policy. It does not say the linear rows are globally redundant or provide a rational optimum certificate.\n\n'
    body+='S adds the missing opposite selected linear range and four CP facets. ALL adds all propagated linear ranges and CP. Both keep the original full matrix; their serialized MPS fingerprints, objective coefficients/constant, new row coefficients, senses and RHS are read back exactly before Optimize. Every new solve is continuous, explicit Gurobi Seed0 / Threads1 / Presolve -1 on affinity4, serial, with unchanged FeasibilityTol and OptimalityTol 1e-6 and cap90. No diagnostic result is installed into the online method.\n\n'
    by={(r['role'],r['side'],r['mode']):r for r in data['positions']}
    body+=table(['Role / side','Original L','S L','ALL L','S floor'],[
        [SHORT[role]+'/'+side,by[role,side,'selected']['old_L'],by[role,side,'selected']['L'],by[role,side,'all']['L'],by[role,side,'selected']['floor']]
        for role in ['K-35-U','R-B35-S-T2','K-20-S'] for side in ['low','high']])
    body+=table(['Role','Original min cover','S min cover','Gain','ALL - S'],[
        [SHORT[r['role']],r['old_cover'],r['selected_cover'],r['selected_gain'],r['ALL_minus_selected']] for r in data['covers']])
    body+='The same gains apply to the conservative min-floor, because the same 1e-7 downward policy and unchanged cutoff are used and the weaker side does not change. Tiny negative deltas on the two unchanged strong sides (about 1e-15) are numerical equality, not a loss from retaining and adding valid rows. S raises all three genuinely weaker sources, rather than only the nonbinding strong side. ALL gives no further optimized gain.\n\n'
    body+=table(['Role / side / mode','Range + CP rows','Added NZ','Build s','Solve s','Work'],[
        [SHORT[r['role']]+'/'+r['side']+'/'+r['mode'],str(r['range_rows'])+' + '+str(r['CP_rows']),
         r['nonzeros_after']-r['nonzeros_before'],r['construction_seconds'],r['solve_seconds'],r['Work']] for r in data['positions']])
    body+='K/W and endpoint counts are in reports/LP.csv. The newly constrained endpoints become active: K35 low beta-endpoint 8, K35 high alpha-endpoint 9, RB low beta-endpoint 5 and K20 low beta-endpoint 7. The old corresponding endpoints were 10.4765, 8.39817, 12.0380 and 10, while the average selectors already respected the conditional counts. Endpoints explain the missing freedom; no-division mass residuals establish row feasibility near g endpoints.\n\n'
    body+='All twelve new LPs pass their inherited quality gates. Every result binds canonical/solution SHA, actual DLL identity, measured helper SHA and source revision. The initial pure-Python tiny fixture constructor failed before any Optimize; the retained corrected run passes. Its two helper versions are preserved at delivery instead of retagging earlier S results. This fixture-only repair leaves product generation unchanged.\n\n'
    body+='The candidate is frozen uniformly to S. Selected uses four CP facets per source; ALL uses 384--548, without extra objective value on these domains. The mathematical explanation is other parent-family products plus selected conditional propagation, not a separate new propagation principle. The new rows enter the two scoped proof sources only, with one canonical append retaining count, child TC2 and all CP/range expected rows under the same SHA. The parent and original Native MIP keep their prior structure; only newly paid source floors change.\n\n'
    body+='This finite LP study establishes strict missing product freedom and small positive optimized source/cover increments. It is not a complete BRP hull, gap-closure or Native speed theorem. The full-method report retains all entered positive/adverse results and complete clocks separately.\n'
    (OUT/'LP_report.md').write_text(body,encoding='utf-8',newline='\n')

def final():
    require_idle();decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    full=read(OUT/'reports/full.json');lp=read(OUT/'reports/LP.json');cost=read(OUT/'cost_report.json')
    body='# Round142 complete scientific report\n\n'
    body+='Task dated 30 October 2026; scientific closeout on 31 October 2026 (Asia/Shanghai).\n\n'
    body+=decision['decision_paragraph']+'\n\n'
    body+='## Source information and mathematical scope\n\n'
    body+='Conditional count CP does fill a real relaxation freedom: the exact Fraction witness violates the child CP by 9/40 while satisfying local VD-P, stock products, parent CP and TC/TC2. In the actual saved points, all new linear ranges already hold, so the source gains are product information. The weak-side and min-cover increments are:\n\n'
    body+=table(['Role','Old raw cover','Selected raw cover','Gain'],[[SHORT[r['role']],r['old_cover'],r['selected_cover'],r['selected_gain']] for r in lp['covers']])
    body+='ALL adds no optimized information beyond S; twelve explicit new continuous LPs and twelve zero-Optimize C equality witnesses are retained. Conservative floors use the original cutoff and downward 1e-7 policy. LP_report.md and reports/LP.csv give both sides, floors, rows/NZ, costs and K/W/endpoint diagnostics.\n\n'
    body+='The mathematical note proves the attainable-source-optimum sandwich for scalar injection, including the necessary integer-b extension premise; it explains R141 root equality without demanding an impossible D1-over-D0 gain. Reverse linear inventory bounds are implied by continuous selectors plus count bounds, and all 24 old plain/conditional checks leave physical intervals unchanged. Network integrality and the R138 endpoint theorem apply to the declared count-selector block only, not weighted inventory/routes or the full BRP hull. Fixed-g linear ranges are explicitly retained.\n\n'
    body+='## Complete entered results\n\n'
    body+=decision['complete_discussion']+'\n\n'
    body+=table(['Role','Method','U','L','T produce s','T cert s'],[
        [SHORT[r['role']],r['method'],r['U'],r['L'],r['T_produce'],r['T_cert']] for r in full['new_arms']])
    body+=table(['Role / method','Signed gap','Relative gap','Verify s','Total s'],[
        [SHORT[r['role']]+'/'+r['method'],r['signed_gap'],r['relative_gap'],r['T_verify'],r['T_total']] for r in full['new_arms']])
    body+='Open T_cert is null. Every complete method pays its own H, normal root/lookahead, both online count proofs, construction, validation and Native search. Source LPs, returned Native ObjVal/ObjBoundC, external merged L, nodes and Work remain separately observable; nested costs are not charged twice. Every formal run uses Seed0, Threads1, serial timing and affinity4, with separate H seed20260626 and inherited physical/objective parameters.\n\n'
    body+='## Matching, benefits and adverse outcomes\n\n'+decision['attribution_discussion']+'\n\n'
    body+=table(['Role','Same-PE CP - D1 U','CP - D1 L','Produce delta s','Total delta s'],[
        [SHORT[r['role']],r['delta_U'],r['delta_L'],r['delta_T_produce'],r['delta_T_total']] for r in full['same_PE_bridges']])
    body+='The matching checks root, support, input, own H, selection/pivot, links and first integer matrix equality after removing only the floor row. Online source floors bind actual new calls and canonical SHAs; diagnostic floors are not imported. CP is absent from the parent and integer MIP. Historical GI-TBC/stock/TC/TC2 positions retain their original source, PE and full clocks, and are cross-version references. No claim that Native actually branches on b follows.\n\n'
    body+=decision['conditional_work_discussion']+'\n\n'
    body+='## Cost, qualification and delivery\n\n'
    b=cost['experiment'];charged=cost['charged_new_experiment_seconds'];body+=f'Conservative new experimental charge, including every measured method outer and mandatory pure postverification: **{charged:.6f} s ({charged/3600:.6f} h)** of 28800 s. The inherited online G1 submeter is {b["G1_seconds"]:.6f} s and separately excludes explicit pure postverification segments; these are alternative views, not additive fees. Qualification, the tiny construction failure and all entered arms are counted. Builds, offline analysis, documents and public I/O are separate. See cost_report.json and durable fee receipts; no exact timing is invented for interactive work.\n\n'
    body+='Independent mathematics/writer review preceded expensive runs. Targeted qualification covers low/high constants, current positive/fixed/tiny g domains, exact Native added-row reads, full expected-row coverage, source-floor binding, source-only placement and old default-off behavior. R141 scope, Start, VType restoration and source revocation policy are reused. Stable R137 and old research entries/profiles remain unchanged.\n\n'
    body+='The goal, manifests, exact source/PE/DLL/build lineage, frozen matrices, unique raw/failures, compact reports, incremental reading PDF, independent final review and continuation entry form the scientific delivery. English Draft PR/public-byte recovery/current-round cleanup are recorded additively in RESUME.md and their receipts; they do not relabel fixed science or trigger new Optimize. Both WORKSPACE_POLICY conventions remain explicit. No automatic merge, force push, old-round deletion or message to others follows.\n'
    (OUT/'final_report.md').write_text(body,encoding='utf-8',newline='\n')

if __name__=='__main__':globals()[sys.argv[1]]()
