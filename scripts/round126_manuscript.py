"""Generate R126's full reading draft from the R125 method text and sealed tables.

Maintained sources are manuscript.md, the two adjacent appendices, references.bib
and generated CSV authorities. TeX/combined Markdown are export intermediates.
"""
from pathlib import Path
import csv, json, math, shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round126'
PRIOR=ROOT/'results/unified_exact_round125'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def fmt(x,d=6):return 'unknown' if x is None else f'{x:.{d}g}' if isinstance(x,float) else str(x)
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows])+'\n'

def historical_display():
    def rows(name):
        with (OUT/'tables'/name).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
    def number(value):
        if value in ['',None]:return 'unknown'
        try:return f'{float(value):.12g}'
        except ValueError:return value
    arms=rows('r122_arms.csv');pairs=rows('r122_pairs.csv');long=rows('r123_arms.csv');lp=rows('r123_pairs.csv')
    text='# Complete historical-result display supplement\n\n'
    text+='This display is generated one way from the six unchanged R125 table authorities. Numeric display uses twelve significant figures; the adjacent original CSV/Markdown files retain their exact published bytes and full precision. N is a nonzero numerical certificate; O is a qualified open endpoint. Historical WIN labels retain their old endpoint rule and are not new certification wins.\n\n'
    text+='## Table S1a. All 32 R122 physical/bound endpoints\n\n'+table(['Role','Seed','Method','U','L','Signed gap','Tier'],[
        [a['id'],a['seed'],a['arm'],number(a['U']),number(a['L']),number(a['gap']),'N' if a['certificate']=='True' else 'O'] for a in arms])+'\n'
    text+='## Table S1b. All 32 R122 complete clocks\n\n'+table(['Role','Seed','Method','Cap','T_produce','T_verify','T_total'],[
        [a['id'],a['seed'],a['arm'],a['cap_seconds'],number(a['T_produce']),number(a['T_verify']),number(a['T_total'])] for a in arms])+'\n'
    text+='## Table S2. All 48 R122 directed comparisons\n\n'+table(['Role','Seed','Candidate','Control','Class','Severe'],[
        [a['id'],a['seed'],a['candidate'],a['control'],a['classification'],a['severe_regression']] for a in pairs])+'\n'
    text+='## Table S3a. All three known R123 endpoints\n\n'+table(['Method','U','L','Signed gap','Tier'],[
        [a['arm'],number(a['U']),number(a['L']),number(a['gap']),'O'] for a in long])+'\n'
    text+='## Table S3b. All three R123 complete clocks\n\n'+table(['Method','Cap','T_produce','T_verify','T_total'],[
        [a['arm'],a['cap_seconds'],number(a['T_produce']),number(a['T_verify']),number(a['T_total'])] for a in long])+'\n'
    text+='## Table S4. All three R123 directed comparisons\n\n'+table(['Candidate','Control','Class','Severe'],[
        [a['candidate'],a['control'],a['classification'],a['severe_regression']] for a in lp])+'\n'
    original=(OUT/'tables/complete_results.md').read_text(encoding='utf-8-sig')
    text+=original[original.index('## Table S5'):]
    (OUT/'tables/historical_display.md').write_text(text,encoding='utf-8')

def direct_study(summary,arms,pairs):
    manifest=read(OUT/'input_manifest.json');positive=read(OUT/'shortage_positive_objective.json')['roles']
    by={(a['id'],a['arm']):a for a in arms}
    design=table(['Problem','Source','n/m','Geometry / stock','Q','Physical T (s)','Production cap (s)','Order'],[
        [p['id'],p['source'],f"{p['V']}/{p['M']}",p['geometry']+' / '+p['inventory'],str(p['Q_vector']),p['T_seconds'],p['cap_seconds'],'P, M-B' if p['method_order'][0]=='P-GRB' else 'M-B, P'] for p in manifest['roles']])
    totals=table(['Problem','sum initial','sum target','sum weights','lambda sum weights'],[
        [p['id'],p['total_initial'],p['total_target'],fmt(p['sum_weights'],12),fmt(p['lambda_sum_weights'],12)] for p in manifest['roles']])
    endpoints=table(['Problem','Method','Own U','Qualified L','Raw signed U-L','Certificate / evidence'],[
        [a['id'],a['arm'],fmt(a['U'],12),fmt(a['L'],12),fmt(a['gap'],12),('yes / ' if a['certificate'] else 'no / ')+a['proof_evidence']] for a in arms])
    clocks=table(['Problem','Method','Cap','T_produce','T_verify','T_total','T_cert'],[
        [a['id'],a['arm'],a['cap_seconds'],fmt(a['T_produce'],9),fmt(a['T_verify'],9),fmt(a['T_total'],9),fmt(a['T_cert'],9)] for a in arms])
    comparison=table(['Problem','Main category','P minus M-B (s)','T_cert P/M-B','Time description','T_total P/M-B'],[
        [p['id'],p['classification'],fmt(p['observed_P_minus_MB_seconds'],9),fmt(p['speedup'],9),p['time_description'] or 'censored / no time ratio',fmt(p['total_time_speedup'],9)] for p in pairs])
    floors=table(['Shortage problem','sum b','sum D','s','Exact-decimal positive floor'],[
        [p['id'],p['sum_initial'],p['sum_target'],p['shortage'],fmt(p['positive_floor_decimal'],12)] for p in positive if p['positive_objective_proved']])
    pm=summary['per_method'];cs=summary['categories'];intersection=summary['both_certified_subset']
    positives=', '.join(summary['supporting_nonzero_problems']) or 'none'
    negatives=', '.join(summary['adverse_problems']) or 'none'
    subset=', '.join(intersection['ids']) or 'empty'
    flips=[p for p in pairs if p['P_T_produce'] is not None and p['MB_T_produce'] is not None and
        (p['P_T_produce']-p['MB_T_produce']>0)!=(p['P_T_total']-p['MB_T_total']>0)]
    total_view=('T_total reverses the observed production-cost ordering on '+', '.join(p['id'] for p in flips)+
        '. Both cost views are retained. On an open pair this is an output-cost observation, with no certification-time ordering or speedup inference; T_produce remains the main certification clock where qualified.') if flips else 'T_total preserves the observed production-cost ordering on every observed pair. Both clocks remain visible; the main certification metric is still T_produce where qualified.'
    if summary['scientific_judgment']=='LIMITED_DIRECT_CERTIFICATION_SUPPORT':
        empirical=f"The evidence provides limited direct certification support on {positives}. No problem meets the predeclared opposite material-time or P-only category. This does not turn the remaining problems into wins or establish a population runtime claim."
    elif summary['scientific_judgment']=='MIXED_DIRECT_CERTIFICATION_EVIDENCE':
        empirical=f"The direct certification evidence is mixed: the supporting nonzero problems are {positives}; the opposite certification/time cases are {negatives}. A smaller open gap cannot offset the latter risk."
    elif summary['scientific_judgment']=='NONZERO_CERTIFICATION_EVIDENCE_LIMITED':
        empirical="The panel supplies limited evidence of a nonzero certification advantage under the predeclared material-time convention. Any smaller observed ratio differences remain visible; this classification is not a claim that measured times are identical or that historical method benefits vanish."
    else:
        empirical=f"The scientific priority is {summary['scientific_judgment']}. Qualified physical outcomes remain reportable, but incomplete or rejected proof dependencies do not create a certification advantage."
    return f'''## 6. Direct certification evidence on six fixed small problems

### 6.1 Prospective design and the one-method question

M-B is the sole proposed method throughout this paper. Before generating any Round126 input or seeing its difficulty, we fixed the six problems, two method entries, order, Seed and budgets in Table SC1. Cold P-GRB is the complete original compact model. It receives no H, incumbent, route, bound, Start, certificate, cache or prior solve from M-B. M-B pays for its own unchanged H, VD-P, implicit integer service, A/B, static strengthening, NEXT/AM, full cover and outputs on every problem. ENS-C is a predecessor/representation comparator retained in the historical section; it is not selected per instance or run in this panel. D1 selection is closed, D0 is not a fallback, and no engine switch or fusion is used.

**Table SC1. The entire fixed Seed0 panel.** Pickup/drop are 60/60 seconds and lambda is .15 in every row. P denotes cold P-GRB. Each method occupies the first position three times.

{design}
**Table SC1b. All six station-stock and weight totals.** Depot placeholders are excluded. Weights are maximum-normalized, not sum-normalized.

{totals}
All six inputs were generated once from the two already safe frozen station tables. CITI source identity is `9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0`. CABI source identity is `d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`, with safe-table identity `d982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa`. The family is `round126-small-certification-v1|source=<source>|source_sha256=<identity>`, and each selection ID is `r126_<problem>_<geometry>_r<replicate>`. The family enters the original anchor hash and the real selection ID enters target/inventory hash material. The adapter is `round126-thin-offline-adapter-v1`.

The original four anchors, compact/regional geometry, tie rules, three-decimal coordinates, target fractions [.44,.56], total correction/sign repair, maximum-normalized six-decimal weights, centroid depot and distances are retained. Only the declared family/ID and table parameters change. Source capacities and coordinates are geographical data; inventories, targets, weights, depot and fleet settings are constructed. No H, LP, MIP or difficulty filter chose or redrew a problem. Station overlaps are recorded. The six problems are not a complete factorial design, IID city samples or six cities.

For the four shortage problems, service stations alone satisfy s=sum D-sum b>0. Empty departure and nonnegative loaded return imply sum Y<=sum b. Thus, with delta=min(lambda*omega_i/D_i)>0,

\\[
F(Y)\\ge\\sum_i(\\lambda\\omega_i/D_i)|Y_i-D_i|
\\ge\\delta\\sum_i|Y_i-D_i|\\ge\\delta s>0.
\\]

**Table SC2. Independent positive-objective arithmetic.** The coefficients are the exact decimal interpretation of the serialized weights and lambda=.15; parsed binary64 values are also recorded. These floors are not injected into the solver or substituted for its reported L. Empty fleets remain legal, so shortage does not mean infeasibility.

{floors}
Balanced and surplus objectives were not presumed zero or positive. A qualified H zero termination is labelled startup-zero and supports termination of the complete method, without credit to a nonzero native proof or interval backend.

### 6.2 Complete production clocks and certificate admission

The production executable and DLL are the unchanged frozen identities specified in Section 5 and the reproducibility record. Both entries use Gurobi Seed0, Threads1, PresolveAuto and the original remaining parameters, requesting relative/absolute MIP gaps zero. Evidence tolerance remains 1e-7. H retains seed 20260626. The 30-second native reserve, cap-minus6 CLI request, cap-minus2 external hard stop and common absolute deadline are inherited; preparation is not moved outside the clock. A larger cap can change a path and is not treated as a freely reusable prefix.

T_produce runs from full method start through normal output sealing, including own H, all models/LP/MIP work, static rows, Start, online verification, callbacks, cleanup and required output. T_verify is independent post-seal validation without new optimization or route search. T_total is their sum; cross-arm reconciliation is separately billed group work. Define T_cert=T_produce only when the final certificate passes every own physical, numerical, identity, scope, cover, return and lifecycle gate; otherwise T_cert is null. It is not first incumbent discovery, Gurobi Runtime or the final MIP call's runtime.

Clean nonzero certification uses the inherited signed-gap admission -1e-7<=U-L<=1e-7 alongside all other gates. Raw L is not clipped to U. Clean own-zero and damaged-source exact-zero retain their distinct inherited policies. Same-input cross-arm witnesses are reconciled only after both own productions, using the unchanged 1e-7 scope/consistency rule; they never supply the other arm's starting information. A damaged bound cannot be repaired by a good fleet or another certificate.

The five main categories are BOTH_CERTIFIED, MB_ONLY_CERTIFIED, P_ONLY_CERTIFIED, BOTH_OPEN and UNEVALUABLE. Both-certification speedup is T_cert(P)/T_cert(M-B), so values above one favor M-B. We display every exact observed time difference and ratio; the descriptive materiality threshold is max(30 seconds,.10*T_cert(P)), producing MB_FASTER/P_FASTER/TIME_CLOSE. This threshold is neither statistical significance nor an engineering gate. Open U/L/gap comparisons are supplementary and generate no main WIN. A normal open native return before its nominal cap is reported at its actual duration: neither the cap nor actual open duration is substituted as a hypothetical certification time, exact speedup or unproved speedup lower bound.

### 6.3 All twelve arms, six pairs and evidence limits

**Table SC3. Complete own endpoints.** All signed gaps are retained. Full-precision CSV and source/call/model/fleet indices are part of the package.

{endpoints}
**Table SC4. All three clocks and certification costs (seconds).** Unknown certification time is shown as unknown, never replaced by the cap.

{clocks}
**Table SC5. All six fixed paired outcomes.** Positive P-minus-M-B means less M-B production time. Single-sided categories are qualitative censored observations; failures are UNEVALUABLE rather than ordinary censoring.

{comparison}
The fixed denominator is six problems and twelve arms. The pairs comprise {cs['BOTH_CERTIFIED']} both-certified, {cs['MB_ONLY_CERTIFIED']} M-B-only, {cs['P_ONLY_CERTIFIED']} P-only, {cs['BOTH_OPEN']} both-open and {cs['UNEVALUABLE']} unevaluable observations. M-B certifies {pm['M-B']['certified']}/6 problems, including {pm['M-B']['nonzero_certified']} nonzero and {pm['M-B']['zero_certified']} zero objectives ({pm['M-B']['startup_zero']} startup-zero). Cold P certifies {pm['P-GRB']['certified']}/6, including {pm['P-GRB']['nonzero_certified']} nonzero and {pm['P-GRB']['zero_certified']} zero objectives. A problem certified by both remains one problem. All certified physical values appear in Table SC3 and the summary, rather than being pooled across instances.

The BOTH_CERTIFIED intersection is {{{subset}}}, size {intersection['n']}. Its observed speedup median is {fmt(intersection['speedup_median'],9)} and geometric mean {fmt(intersection['speedup_geometric_mean'],9)}. This conditional intersection does not estimate a whole-panel mean. The neighboring single-sided and open counts above remain part of the result; no cap filling, PAR-2 time, best-of-Seed or selected-problem average is used. {total_view}

{empirical}

The preregistered evidence classification is `{summary['scientific_judgment']}`, with w={summary['w']} and l={summary['l']}. The execution state is `{summary['experiment_execution']}`. These are bounded evidence labels, not acceptance standards or universal stability tests. The mathematical propositions establish representation, valid embedding and complete proof obligations under their premises; the measured speed/certification counts are empirical statements. This cold-baseline comparison measures the complete method and does not identify the separate causal contribution of cuts, AM or H. The four positive-objective cases remain visible regardless of zero-target outcomes or losses.

'''

def build():
    assert not (OUT/'manuscript.md').exists(),'Already initialized: revise the maintained Markdown sources in place, then re-export.'
    s=read(OUT/'certification_summary.json')
    records=[read(OUT/f'reconstruction/group{n:02d}/current_core.json') for n in range(1,7)]
    arms=[a for r in records for a in r['arms']];pairs=[r['pair'] for r in records]
    main=(PRIOR/'manuscript.md').read_text(encoding='utf-8-sig')
    main=main.replace('Round125 self-contained methods revision, 18 October 2026.','Round126 complete certification-focused reading draft, 19 October 2026.')
    start=main.index('## Abstract');end=main.index('**Keywords:**')
    pm=s['per_method'];cats=s['categories']
    abstract=f'''## Abstract

Static bicycle redistribution couples attainable station inventories with capacity- and time-feasible vehicle routes. We minimize inventory-to-target ratio Gini dispersion plus weighted two-sided relative target deviation under empty departure and unique nonzero one-way station service. The sole proposed method, frozen M-B, integrates an independently paid finite startup H, inventory-state products with implicit service integrality, valid static strengthening and complete scoped interval coverage around native LP/MIP solves. We distinguish ideal validity from floating-point numerical certification. A prospectively fixed six-problem V15/V20 panel compares twelve complete M-B and cold original compact P-GRB arms under 600/1200-second per-method production caps. M-B certifies {pm['M-B']['certified']}/6 problems ({pm['M-B']['nonzero_certified']} nonzero); P-GRB certifies {pm['P-GRB']['certified']}/6 ({pm['P-GRB']['nonzero_certified']} nonzero). There are {cats['BOTH_CERTIFIED']} both-certified, {cats['MB_ONLY_CERTIFIED']} M-B-only, {cats['P_ONLY_CERTIFIED']} P-only, {cats['BOTH_OPEN']} both-open and {cats['UNEVALUABLE']} unevaluable pairs. Time ratios are reported only on the both-certified intersection and use complete normal production cost. The resulting evidence classification is {s['scientific_judgment'].lower().replace('_',' ')}. Earlier six-problem V20/V35/V50 endpoint results and one known V50 long window remain separate capability-boundary evidence; their smaller gaps are not certification speedups. The results concern this fixed problem set and complete-method budget, without a universal runtime or component-causality claim.

'''
    main=main[:start]+abstract+main[end:]
    main=main.replace('Does this integrated method improve the cold original compact formulation under a complete common production budget, and where does its certificate capability stop in the available evidence? A prospective panel from two station sources provides the primary evaluation.',
        'Does this single integrated method complete more optimality certifications than the cold original compact formulation under matched complete production budgets, and reduce full certification cost where both certify? The fixed small-instance panel provides the direct evaluation. Earlier endpoint experiments supply an extended-range comparison.')
    main=main.replace('Both successes and losses are retained, so a useful overall method need not dominate every representation variant on every role.','Both successes and losses are retained. M-B is fixed before outcomes; ENS-C is a historical predecessor/representation comparator, and no method is selected separately for each instance.')
    main=main.replace('3. It reports a finite, fully denominated comparison with the cold original model and competing frozen implementations, followed by a single known-instance long-window study. This identifies common gains, representation tradeoffs, solver-Seed sensitivity and outstanding regional proof obligations without turning open caps into times to optimality.',
        '3. It reports a preregistered six-problem, twelve-arm small-instance optimality-certification comparison against cold P-GRB. Separate historical tables retain the six R122 problems, two fixed Seed repeats, 32 arms/48 directed pairs, all unfavorable outcomes, and the known V50 long-window proof limit. They are not pooled into one certification speedup or a larger new independent sample.')
    main=main.replace('Section 6 presents the evidence, and Section 7 discusses what can and cannot be inferred.','Section 6 presents direct certification evidence; Section 7 retains the extended historical evidence; Section 8 discusses its limits.')
    a=main.index('## 6. Computational study');b=main.index('## 7. Discussion, limitations and reproducibility')
    historical=main[a:b].replace('## 6. Computational study','## 7. Extended endpoint evidence and the known long-window proof boundary').replace('### 6.','### 7.')
    historical=historical.replace('Primary prospective panel and measurement','Earlier R122 prospective panel and measurement').replace('The primary panel [@benchmark122]','The earlier R122 panel [@benchmark122]')
    historical=historical.replace('The primary panel has','The R122 panel has')
    historical=historical.replace('All primary outcomes and adverse cases','All historical outcomes and adverse cases').replace('All 32 published primary-panel arms','All 32 published R122 arms')
    historical=historical.replace('This common complete-method advantage is the main positive empirical result. It includes both certificate gains and better finite-window open endpoints.',
        'These are the historical complete-endpoint rule results, which combine certification and open-endpoint comparisons. They do not mean that all six problems certified faster, and they are not the direct certification outcome of Section 6.')
    historical=historical.replace('The fixed rule is certificate first.','The historical endpoint rule, retained only for these older tables, is certificate first.')
    main=main[:a]+direct_study(s,arms,pairs)+historical+main[b:]
    main=main.replace('## 7. Discussion, limitations and reproducibility','## 8. Discussion, limitations and reproducibility').replace('## 8. Conclusion','## 9. Conclusion')
    main=main.replace('The strongest supported empirical statement is complete-method advantage over cold P-GRB for the particular original model and matched finite budgets in the prospective panel.',
        'The direct empirical statement is the exact six-pair certification distribution and conditional both-certified time ratios in Section 6. Its scope is this original model, fixed small problem set and matched complete production budgets.')
    main=main.replace('On the primary panel, all nonzero certificates occur at V20 and every V35/V50 outcome is open.','On the earlier R122 panel, all nonzero certificates occur at V20 and every V35/V50 outcome is open. Round126 adds the separately reported V15/V20 direct evidence.')
    main=main.replace('Six non-IID problems from two station tables are not six independent cities.','Each six-problem panel uses non-IID constructed problems from two station tables; neither panel represents six independent cities, and the two panels are not pooled as one certification sample.')
    main=main.replace('The two fixed Seeds expose sensitivity','The two R122 fixed-input Seed repeats expose sensitivity')
    main=main.replace('This revision preserves its published tables byte for byte and adds a compact method-check package: rational inequalities, sampled saved matrix rows, finite decision states and declared H-move replay. It does not repeat the full historical reconstruction.',
        'R125 preserved those tables byte for byte and added a compact method-check package: rational inequalities, sampled saved matrix rows, finite decision states and declared H-move replay. Round126 retains those definitions and checks; its new work is the fixed certification panel and the complete updated reading draft. It does not repeat the full historical reconstruction.')
    start=main.index('The prospective two-source evidence shows six new-role wins');end=main.index('## References and supporting material',start)
    main=main[:start]+f'''M-B is the paper's single proposed method. On the fixed V15/V20 panel it certifies {pm['M-B']['certified']}/6 problems against cold P-GRB's {pm['P-GRB']['certified']}/6; all six categories and complete certification times are reported, including adverse, open and unknown observations. The bounded scientific judgment is `{s['scientific_judgment']}`. This empirical statement is separate from the ideal representation/coverage propositions and their floating-point implementation policy.

The earlier six R122 endpoint WIN labels are preserved under their historical definition and cannot be read as six faster certifications. The known V50 long window remains open for every method. These capability boundaries do not erase accurately limited small-instance evidence, and smaller gaps do not substitute for optimality proof. ENS-C remains a historical comparison and the unchanged project default; no per-instance dispatch, D1 reopening or automatic follow-up experiment is introduced.

'''+main[end:]
    main=main.replace('The appropriate next action is substantive academic assessment of this bounded contribution.','The next step is the one evidence-based priority stated in the final report; this manuscript does not authorize further solving.')
    main=main.replace('No solver tolerance or historical certificate field is changed in this revision.','No solver tolerance or historical certificate field is changed in this revision.')
    (OUT/'manuscript.md').write_text(main,encoding='utf-8')
    for name in ['model_appendix.md','algorithm_appendix.md','references.bib','literature_evidence.csv','literature_scope.md','historical_attribution.md','method_spec_matrix.csv']:
        text=(PRIOR/name).read_text(encoding='utf-8-sig')
        if name=='algorithm_appendix.md':
            text=text.replace('No optimization or H search was executed for this writing round.','The definitions and proofs are retained from R125. Round126 executes only the fixed complete M-B and cold P-GRB entries on the declared new panel; it changes no algorithm.')
            marker='## B.2 State, identity and order'
            command='''The unique paper entry is fully resolved in [paper_method_config.json](paper_method_config.json); [argv_freeze.json](argv_freeze.json) contains the exact six native M-B argument vectors and their independent cold controls. PE and DLL SHA256 bind every preset/default value that has no separate CLI option. H seed 20260626 and all native settings are explicit configuration values, not instance-dependent choices. The template below is one token vector (line breaks are presentation only); INPUT, OUT, physical T, producer B and B_MINUS_6 take exactly their fixed table values. The existing supervisor starts the complete production clock before admission, invokes this vector, and seals normal output; direct native Runtime alone is not T_cert.

~~~text
PE --input INPUT --lambda 0.15 --T T
   --pickup-time 60 --drop-time 60 --time-limit B_MINUS_6
   --process-wall-time-limit B --process-shutdown-margin 30
   --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1
   --method gcap-frontier
   --algorithm-preset research-round83-vds-equal-net-exchange
   --round90-lp-g-split false --round61-candidate-mode off
   --round65-witness-audit true --round65-hga-zero-stop true
   --out OUT/result.json --log OUT/native.log
   --process-phase-ledger OUT/phases.csv
   --external-gini-artifact-dir OUT/external
   --primal-heuristic-generation-log OUT/hga.csv
   --progress-log OUT/progress.csv --native-evidence-dir OUT/journal
   --round98-state-service m-binary
~~~

'''
            text=text.replace(marker,command+marker)
        (OUT/name).write_text(text,encoding='utf-8')
    (OUT/'tables').mkdir(exist_ok=True)
    for path in (PRIOR/'tables').iterdir():
        if path.is_file():shutil.copyfile(path,OUT/'tables'/path.name)
    historical_display()
    print('Complete R126 main text, two appendices, references and byte-identical six historical tables generated.')

if __name__=='__main__':build()
