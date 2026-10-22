"""Maintain the full reading draft with an explicit version/evidence migration."""
from round130_common import *
import re,types
import round128_documents as previous_export

def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n'
def time_cell(a):
    if not a['formal_protocol_qualified']:return 'U'
    return f"C {a['T_cert']:.3f}" if a['certificate'] else f"O ({a['T_produce']:.3f})"

def documents():
    o=read(OUT/'observations.json');d=read(OUT/'scientific_decision.json');summary=read(OUT/'stratified_summary.json')
    # The completed independent receipt gates authoring; its prose report is
    # required separately before final-report generation and publication.
    assert read(OUT/'review/final_independent_evidence.json')['status']=='PASS'
    by={(a['id'],a['seed'],a['method']):a for a in o['arms']}
    roles=[p['id'] for p in read(OUT/'input_manifest.json')['roles']]
    times=table(['Known role / Seed','P','PS','S2','S2R'],[
        [f'{id} / {seed}',*[time_cell(by[id,seed,m]) for m in ['P','PS','S2','S2R']]] for id in roles for seed in [0,1]])
    pp={(q['id'],q['seed'],q['left'],q['right']):q for q in o['pairs']}
    directions=table(['Known role / Seed','S2/P','S2/PS','S2/S2R'],[
        [f'{id} / {seed}',*[pp[id,seed,a,b]['direction'] for a,b in [('S2','P'),('S2','PS'),('S2','S2R')]]] for id in roles for seed in [0,1]])
    sameH=summary['all_actual_same_H'];sameRoot=summary['all_actual_same_effective_root']
    axes=d['axes'];axis_text=[]
    for axis in ['same_H_backend','outer_control']:
        for r in axes[axis]['records']:axis_text.append(f"{r['id']} ({axis.replace('_',' ')}): {r['status']}.")
    axis_text=' '.join(axis_text)
    costs={(x['id'],x['seed'],x['method']):x for x in o['costs']}
    b20=''
    for seed in [0,1]:
        a,b,c=by['UC-B20-B',seed,'S2'],by['UC-B20-B',seed,'S2R'],by['UC-B20-B',seed,'PS']
        b20+=f"At B20 Seed{seed}, S2/PS/S2R complete certification costs are {a['T_cert']:.3f}/{c['T_cert']:.3f}/{b['T_cert']:.3f} seconds; S2 produces {costs['UC-B20-B',seed,'S2']['split_count']} natural splits and S2R none. "
    contribution=table(['Comparison','Actual question','Scope boundary'],[
        ['S2/P','complete adopted method versus cold compact','all integrated differences; primary benchmark'],
        ['PS/P','net independently paid H and full Start integration','neither a free solution nor guaranteed improvement'],
        ['S2/PS','same-H complete backend/representation/control increment','does not isolate an individual cut or threshold'],
        ['S2/S2R','same effective root, exposed outer package','probing, targets, domain-dependent rows, scheduling and splits together'],
        ['S2R/PS','same-H single-root strengthened representation versus original compact','representation, LP preprocessing and cutoff domain remain coupled']])
    section=r'''### 6.10 Fixed-version same-start and outer-control attribution (Round130)

Round129's five conditions passed before this study. The user now adopts **GI-TBC (uniform pair-support implementation, MS2)** as the sole proposed method, short ID **S2**. Its algorithm identity is the original E2 `--round127-mode ms2`: pair support is enabled uniformly and triple support is never emitted. H, representation, ordered supply, C_G, A/B, Gini control, numerical tolerances and default native parameters are unchanged. Historical full M-B measurements retain their three-station identity; ENS-C remains the repository default and is not the paper reproduction entry. This is a version adoption, not a third algorithm or another candidate-selection round.

The fixed panel contains UC-B20-B, UC-C20-U and UC-B30-S from R129, with their original input bytes, Q vectors and physical T=7200 seconds. These are deliberately known attribution roles: a previously splitting nonzero-certified role, a further nonzero-certified risk role, and an open shortage role. They are not unseen prospective validation inputs, independent replications of R129 or a difficulty-blind sample. Balanced, surplus and shortage refer to total inventory scenarios, not identical local station regimes. No input, Seed, parameter, tuning file or cap was added after outcomes.

Each method independently pays its complete workflow under the same 1200-second cap, original 30-second shutdown reserve, six-second native offset and two-second hard-stop offset. Threads=MIPThreads=1, affinity mask4, H_seed=20260626, per-group Gurobi Seed0/1, PresolveAuto, MIPFocus=0, Cuts=-1 and requested zero relative/absolute MIP gaps are retained. Each native call receives only the remaining complete deadline. Three problems, two Seeds and four methods give 24 serial arms in six matched groups. The five prespecified comparisons in each group yield 30 typed shared-data entries, not 30 independent trials. No arm uses another arm's fleet, upper bound, Start, basis, tree or cache.

For each role, the Seed1 method order reverses Seed0. This limited counterbalancing does not remove all host-load noise or turn two paths into a statistical robustness study.

PS uses the existing independently paid H-to-original-compact entry, not P-tuned. Its complete Start mapper checks every actual column/type/bound/row and the original objective, submits and reads back the full vector, and leaves the mathematical model unchanged. P stays cold. A Start that does not create a new native incumbent is not automatically invalid: native heuristics can already have an equally good or better solution. Actual submission/readback and native adoption are reported separately. H and mapping costs are included in PS production time.

The inherited verified-zero startup scope is retained for PS/S2/S2R. Such a qualified startup-zero outcome has no backend exposure and is not same-H backend attribution; no new zero shortcut is introduced. The normal nonzero PS path has one original-compact MIP. Every formal role here has nonzero own H.

S2R uses the off-by-default unique `s2-root` mode, retaining pair support and all valid root strengthening. Its own H defines the inclusive root

\[
 I_0=[0,\min\{U_0,(n-1)/n\}],\qquad F_{\rm model}\le U_0.
\]

It suppresses only the semantically identified interval-no-improver proof-closure row, validates its own full Start against actual original integer types before LP relaxation, pays one complete root LP, restores the integer types, and pays one root MIP with one submitted own Start. No child LP, NEXT/AM target, split, epoch or restart follows. Nonzero chains cannot skip a call merely through a relevance tolerance. Native TIME_LIMIT/INTERRUPTED remains open; a near-equal numerical bound does not replace the required complete native optimal-root return. An infeasible root despite its legal own witness is a consistency issue, not a shortcut certificate. All costs share the deadline.

For a physical solution, nonnegative penalties give G<=F and nonnegative ratios give G<=(n-1)/n. Thus every physical F<=U0 solution lies in the root; the cutoff complement cannot improve the own verified U0. A qualified root bound L combines with that complement as min(L,U0) by domain coverage. This identity does not excuse a bound contradicting its own legal witness. Equality of an analytic regional floor and cutoff excludes strict improvement only; a floor slightly below the cutoff retains its own value under the original numerical policy. The ordinary S2 proof shortcut is unchanged.

**Table R130.1. Every complete-method observation (seconds).** C is qualified T_cert=T_produce; O gives observed T_produce with T_cert=null. Open times are never replaced by caps.

'''+times+'''
**Table R130.2. All primary, same-start and outer-control directions.** Win/Lose uses unrounded certificate time or a one-sided qualified certificate. Both open is UNDETERMINED. The remaining two fixed comparison types and all exact differences are retained in Supplement S and pairs.csv.

'''+directions+f'''
Actual complete-H/action/capacity-assigned fleet equality across all same-H comparisons is {sameH}. Actual effective-root identity for S2/S2R is {sameRoot}. The matrix checks retain duplicate rows and compare complete objectives, column order/types/bounds, settings and all remaining rows. If a normal S2 root contains the omitted semantic shortcut or its H/scope differs, that result is retained as a complete-method comparison with restricted attribution. Complete per-role facts are in actual_method_differences.json and same_H.csv.

{b20}The H witness already attains the eventual B20 objective, 0.5773330699702928, before proof. It is not itself an optimality certificate. The original R129 coverage example is kept separately and is never injected into a formal run. The new actual observations therefore separate a large backend/representation increment from any net contribution of the outer package; split counts alone cannot establish speedup.

{axis_text}

The symmetric descriptive materiality rule is slower-faster >= max(10 seconds,0.10*faster), separate from strict Win/Lose and from one-sided certificates. It is not a statistical test or algorithm switch. Native LP/MIP seconds, Work, nodes, model/Start costs, target/split exposure, closure sources and first retained own final-U witnesses are explanatory measurements. Missing subclocks remain unknown; Work is not used as a stopping budget. Ratios and geometric means use only explicit both-certified intersections.

Both C20 Seed1 S2 and S2R retain the qualified signed gap U-L=-1.4988010832439613e-15, with L unchanged under the original signed 1e-7 numerical window. Original raw top-level claims remain distinct from qualified source/return/coverage endpoints. No bound clipping, new tolerance or rational-exactness claim is introduced. Cross-arm physical witnesses are checked only for contradictions and never transferred as free bounds or certificates.

**Table R130.3. Contribution interpretation matrix.**

'''+contribution+f'''
Execution is **{summary['execution']}**. The finite claim decision is **`{d['tag']}`**. {d['claim_scope_assessment']['reason']} This does not reconsider R129's passed selection or combine per-instance winners. PS remains a useful reference without needing to dominate P. This panel supplies no new single-cut C_G or C_R ablation for final S2, no V50/V60 validation, and no population robustness claim. R127's adverse selected P-tuned result, R128's timing reversal/no-split facts, R129's open C15/B30 results and its Seed-dependent endpoint reversals remain visible. The fixed attribution study ends without additional experiments.

'''
    parent=ROOT/'results/unified_exact_round129';lineage={}
    def fetch(name):
        raw=git('show',BASE+':results/unified_exact_round129/'+name)
        lineage[name]=hashlib.sha256(raw).hexdigest()
        return raw.decode('utf-8-sig').replace('\r\n','\n')
    main=fetch('manuscript.md')
    begin=main.index('## Abstract');end=main.index('## 1. Introduction')
    abstract='''## Abstract

Static bicycle redistribution couples attainable station inventories with capacity- and time-feasible vehicle routes. We minimize inventory-to-target ratio Gini dispersion plus weighted two-sided target deviation under empty departure and unique nonzero one-way service. The sole proposed method is GI-TBC in its uniformly fixed pair-support implementation, MS2 (S2). It integrates independently paid full H, inventory-state products with implicit service integrality, valid static strengthening and complete scoped Gini-interval coverage around native LP/MIP calls. Triple support is disabled on every input. Certificates follow a declared floating-point evidence policy, distinct from ideal mathematical validity.

In R129's four new problems, P/S2 certify 1/2 problems per Seed, with the same both-Seed problem counts; the separate protection certificate is retained at both Seeds. C15 and B30 stay open, and B30 reverses its open-endpoint direction across Seeds. R130 then fixes S2 as the only paper method and runs 24 independently paid arms on three already-known roles against cold P, paid-H original compact PS and a comparable pair-only inclusive-root control S2R. These are attribution diagnostics, not another unseen validation set. '''+d['claim_scope_assessment']['abstract_result']+'''

Historical full M-B/ENS performance keeps its original algorithm identity. Open outcomes, reverse directions, the adverse selected P-tuned holdout result and limitations at larger station counts remain in the evidence. Ratios use only both-certified intersections and complete production costs. The integration is not claimed to introduce general cut theory, universally improve runtime or prove that every exposed component adds speed.

**Keywords:** bicycle redistribution; inventory-to-target ratio; Gini dispersion; mixed-integer programming; numerical optimality certificate; same-start attribution.

'''
    main=main[:begin]+abstract+main[end:]
    main=main.replace('Round129 uniform-support confirmation reading draft, 22 October 2026.','Round130 uniform pair-support paper reading draft, 22 October 2026.')
    main=main.replace('whose frozen implementation identity is M-B','whose fixed paper implementation identity is uniform pair-support MS2 (S2)')
    main=main.replace('M-B is fixed before outcomes; ENS-C is a historical predecessor/representation comparator','S2 is adopted from the passed R129 prospective selection; full M-B and ENS-C are historical predecessor/representation comparators')
    main=main.replace('The fixed small-instance panel provides the direct evaluation.','The actual MS2 observations in Section 6.9 and the known-role attribution in Section 6.10 provide current-version evidence. Earlier small-instance panels retain their full-M-B predecessor identity.')
    main=main.replace("from M-B's representation and complete-method comparison","from the tailored representation and complete-method comparison")
    main=main.replace('3. It reports a preregistered six-problem, twelve-arm small-instance optimality-certification comparison against cold P-GRB. Separate historical tables retain the six R122 problems, two fixed Seed repeats, 32 arms/48 directed pairs, all unfavorable outcomes, and the known V50 long-window proof limit. They are not pooled into one certification speedup or a larger new independent sample.',
        '3. It reports actual MS2 evidence from the passed R129 prospective selection and a fixed 24-arm, same-start and outer-control attribution study on three already-known roles. P-GRB remains the main cold benchmark; PS and S2R answer distinct matched questions. The earlier R126 six-problem certification panel and R122 endpoint/long-window tables remain predecessor evidence, including all unfavorable and open outcomes. These layers are not pooled into a larger independent sample.')
    a=main.index('## 4.');b=main.index('## 6.')
    method=main[a:b].replace('M-B','S2')
    method=method.replace('For a two- or three-station support W, the smallest explicit depot-cycle travel \\(\\tau(W)\\) is the minimum of two or six orders.',
        'For an active two-station support W, the smallest explicit depot-cycle travel \\(\\tau(W)\\) is the minimum of its two orders. The general three-station validity proof is retained in Appendix A for the full-M-B predecessor, but no three-station support row is emitted by S2.')
    main=main[:a]+method+main[b:]
    main=main.replace('## 6. Direct certification evidence on six fixed small problems','''## 6. Versioned certification and attribution evidence

The current sole method is S2/MS2. Its direct performance evidence is the actual MS2 layer in Section 6.9; Section 6.10 gives fixed known-role attribution. Sections 6.1-6.8 retain predecessor/development evidence, with their original full-M-B/ENS names and numerical authorities. Their V15/V20/V35/V50 results are not relabelled as final S2 measurements or pooled with its observations.''')
    main=main.replace('### 6.1 Prospective design and the one-method question','### 6.1 Historical R126 predecessor design and one-method question')
    main=main.replace('M-B is the sole proposed method throughout this paper.','At execution of the historical R126 panel, full three-station M-B was the sole proposed method; the current paper method is S2/MS2.')
    main=main.replace('Frozen M-B / GI-TBC remains the sole proposed method;',
        'At the Round128 stage, frozen full M-B / GI-TBC was the sole proposed method;')
    main=main.replace('Current MB/P remains two Wins and one BOTH_OPEN comparison',
        'That stage retains two MB/P Wins and one BOTH_OPEN comparison')
    main=main.replace('The K2 support signal warrants only a single future uniform confirmation design, while the frozen full M-B remains the sole paper method.',
        'At that stage, the K2 support signal warranted one future uniform confirmation design and full M-B remained the paper method. Section 6.9 records that completed R129 selection; Section 6.10 adopts S2 and gives the distinct current attribution study.')
    main=main.replace('This is a recommendation awaiting the user\'s adoption; the current method identity and historical full-M-B tables remain unchanged.',
        'This was the recommendation at the R129 stage. R130 now adopts uniform MS2 as the sole method; historical full-M-B numbers retain their original labels.')
    main=main.replace('No new D control effect is measured.','No new D control effect was measured in R129; the final pair-only outer-control comparison is reported separately in Section 6.10.')
    main=main.replace('### 6.9 Prospective confirmation of a uniform pair-support candidate (Round129)\n',
        '### 6.9 Prospective confirmation of a uniform pair-support candidate (Round129)\n\nThis section preserves the R129 selection-time record: the four inputs were new at that stage, MS2 was a candidate, and the five conditions passed. Section 6.10 adopts that version and treats the reused roles as known attribution diagnostics. The E2 numbers, raw-field meanings and original selection criteria below retain their historical identities.\n')
    main=main.replace('Without a new D control it does not identify a net decomposition speed benefit.',
        'Without its own D control, R129 did not identify a net decomposition speed benefit; the distinct final-version control is in Section 6.10.')
    main=re.sub(r'If adopted, the main-method performance claims would require separately labelled MS2 measurements for .*?This is a table-migration scope, not authorization to execute another batch\.',
        'R130 resolves this version map by labelling earlier full-M-B tables as predecessor evidence and restricting current main-method performance to qualified actual MS2 observations. It does not relabel old results or rerun the larger historical panels. The exact evidence layers and input/Seed/program/clock identities are listed in paper_version_manifest.json and evidence_migration.csv.',main,flags=re.S)
    main=main.replace('## 7. Extended endpoint evidence',section+'## 7. Extended endpoint evidence',1)
    main=main.replace('The direct empirical statement is the exact six-pair certification distribution and conditional both-certified time ratios in Section 6.',
        'The current direct statements concern the actual MS2 R129 observations and the complete fixed R130 attribution panel, with conditional both-certified time ratios. The six-pair R126 certification distribution remains evidence for the full-M-B predecessor.')
    main=main.replace('R124��s',"R124's")
    main=main.replace('The next step is the one evidence-based priority stated in the final report; this manuscript does not authorize further solving.',
        'The Round130 fixed attribution study ends here. Its final report narrows claims to the observed method/version/domain; no further solving, tuning, input or Seed is authorized.')
    main=main.replace('to the observed method/version/domain;', 'to the observed method, version and domain;')
    main=main.replace('unique one-way service explains why M-B can relax quantity declarations.',
        'unique one-way service explains why the adopted S2 representation can relax quantity declarations.')
    main=main.replace("M-B is the paper's single proposed method. On the historical Round126 Seed0 V15/V20 panel it certifies 5/6 problems against cold P-GRB's 3/6; all six paired outcomes and complete certification times are reported, including the time-close and open cases. That historical cohort's bounded scientific judgment is `LIMITED_DIRECT_CERTIFICATION_SUPPORT`. This empirical statement is separate from the ideal representation/coverage propositions and their floating-point implementation policy.",
        'GI-TBC in its uniform pair-support implementation, MS2 (S2), is the sole proposed method. Its R129 selection passed and is adopted here. The complete Round130 panel fixes the method and reports every same-start and pair-root control observation, with the claim scope in Section 6.10. '+d['claim_scope_assessment']['discussion_result']+' The historical R126 full-M-B Seed0 result, 5/6 certified versus cold P-GRB 3/6, retains its predecessor identity and is not relabelled as S2. Empirical observations remain separate from ideal representation/coverage propositions and their floating-point implementation policy.')
    main=main.replace('[current candidate decision](candidate_decision.md)', '[current claim decision](claim_decision.md)')
    main=main.replace('adds the separately labelled Round129 clocks', 'adds the separately labelled Round129 and Round130 clocks')
    (OUT/'manuscript.md').write_text(main,encoding='utf-8',newline='\n')
    for name in ['model_appendix.md','algorithm_appendix.md','references.bib','literature_evidence.csv','literature_scope.md']:
        value=fetch(name)
        if name=='model_appendix.md':
            value=value.split('\n',1)[0]+'\n\n**Current-version map (Round130).** The sole method is S2/MS2. All R125 equations, physical embeddings and valid-cut derivations below are retained. Only two-station support is active in S2; the general three-station proof describes the historical full-M-B option and is not an active-row claim. Numerical proof-shortcut and inclusive-root qualifications retain their stated domains.\n\n'+value.split('\n',1)[1]
        elif name=='algorithm_appendix.md':
            value=value.split('\n',1)[0]+'\n\n**Current-version map (Round130).** S2/MS2 uses the unchanged H and controller specified below with uniform pair-only support. Historical full-M-B traces and development variants retain their named identity. S2R is a diagnostic deletion control, not a second proposed method.\n\n'+value.split('\n',1)[1]
            value=value.replace('This supplement defines the frozen M-B controller and its finite feasible startup H.',
                'This supplement defines the controller and finite feasible startup H shared by the adopted S2/MS2 method and its full-M-B predecessor. The current S2 row policy is uniformly pair-only; the underlying H and controller definitions are unchanged.')
            value=value.replace('The saved R123 M-B command selects',
                'The inherited settings below originate in the saved R123 full-M-B command. The current S2 command additionally selects `--round127-mode ms2`, so every three-station support predicate is false. Both versions select')
            value=value.replace('the exact six native M-B argument vectors and their independent cold controls',
                'the exact six current S2 argument vectors, six independent cold controls and twelve diagnostic control vectors')
            value=value.replace('B_MINUS_6 take exactly their fixed table values',
                'B_MINUS_6 and SEED take exactly their fixed group-table values')
            value=value.replace('--gurobi-seed 0 --gurobi-presolve -1', '--gurobi-seed SEED --gurobi-presolve -1')
            value=value.replace('   --round98-state-service m-binary\n~~~',
                '   --round98-state-service m-binary --round127-mode ms2\n~~~')
            value=value.replace('| Row generation | Static physical plus shared interval factory;',
                '| Row generation | Uniform two-station support, no three-station support; static physical plus shared interval factory;')
            value=value.replace('The distinction between a proposed candidate, the current frozen full-M-B method identity and its historical tables is retained.',
                'At the R129 selection stage, MS2 was the proposed candidate and full M-B was the then-current frozen method. That historical distinction and all tables remain; R130 now adopts S2/MS2 as the sole paper method.')
            value+='''
## B.14 Current pair-support version and fixed attribution controls

The sole paper method is original E2 `ms2`, called S2. E3 retains its source behavior and adds the off-by-default unique `s2-root` identity plus PS parameter evidence readback. E2 is retained unchanged. PS reuses the full original-compact mapper/validator; S2R reuses R128 inclusive-root semantics with triple emission disabled. Section 6.10 states the paid workflows, exact cutoff complement, nonzero LP/MIP obligations, source/return/coverage requirements, actual exposure and attribution limits. No individual cut, H, threshold or native parameter is optimized here. The passed R129 candidate selection is not rerun.
'''
        (OUT/name).write_text(value,encoding='utf-8',newline='\n')
    target=OUT/'tables';target.mkdir(exist_ok=True)
    for name in ['historical_display.md','complete_results.md']:
        value=fetch('tables/'+name)
        if name=='complete_results.md':
            value+='\n\n# Round130 complete fixed clocks and comparisons\n\n'+times+'\n'+table(['Role / Seed','Comparison','Class','Direction','Unrounded time difference'],[
                [f"{q['id']} / {q['seed']}",q['left']+'/'+q['right'],q['classification'],q['direction'],q['left_minus_right_seconds'] if q['left_minus_right_seconds'] is not None else 'N/A'] for q in o['pairs']])
        (target/name).write_text(value,encoding='utf-8',newline='\n')
    write(OUT/'manuscript_lineage.json',dict(UTC=utc(),parent_commit=BASE,inherited_exact_blob_hashes=lineage,
        maintained_sources=['manuscript.md','model_appendix.md','algorithm_appendix.md','references.bib','tables/historical_display.md'],
        local_changes='sole method map; abstract/introduction and current pair support; labelled historical scope; 6.10 attribution; contribution table; B.14',
        R125_formulas_and_H_controller_derivations_retained=True,predecessor_values_relabelled=False,PDF_pending=True))
    (OUT/'reproducibility.md').write_text('''# Round130 reproduction

Use paper_method_config.json, paper_version_manifest.json, E3_frozen.json, input_manifest.json and argv_freeze.json for the unique paper method and actual 24 paid workflows. The repository default is unchanged; explicitly select ms2. Historical manifests identify their own full-M-B/ENS variants, clocks and evidence roles in evidence_migration.csv.

The same sealed E3 and original Gurobi 13.0.2 DLL are used for all formal arms. PE/DLL, licenses, credentials and fonts are excluded from publication. Source/build identities are retained. Qualification includes full E2/E3 small/medium models, renamed input, shared/fallback pair-root differences, existing Start/boundary contracts, and actual independent paid PS and S2R chains. Failed postseal reader attempts are preserved and did not rerun native PS.

One public empty-root recovery restores only this round and its exact dependencies, then replays published physical/model/Start/source/return/coverage and all 30 typed comparisons without Optimize, H, compilation or local raw fallback. Actual scope and receipts are supplied after execution. The independent internal reviews are finite evidence checks, not external replication or a global rational certificate.
''',encoding='utf-8')
    print('MAINTAINED_R130_READING_SOURCE_WRITTEN')

def pdf():
    os.environ['ROUND128_PDF_DEST']=str(OUT/'manuscript.pdf')
    os.environ['ROUND128_PDF_RECEIPT']=str(OUT/'pdf_export.json')
    os.environ['ROUND128_PDF_TEMP']=str(TEMP/'pdf')
    call=types.FunctionType(previous_export.pdf.__code__,dict(vars(previous_export),OUT=OUT,TEMP=TEMP))
    call()
if __name__=='__main__':{'documents':documents,'pdf':pdf}[sys.argv[1]]()
