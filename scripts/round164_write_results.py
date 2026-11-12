"""Author the completed finite study from already qualified numerical reports.

No solver, physical replay or new scientific sample is executed here.
"""
from round164_common import *
from round164_evidence_tables import table

NUMERIC='b93a8a01ff1b7f3cbee67807be3ac6591db4767f'

def f(x):return format(x,'.10g')
def delta(x):return '0' if abs(x)<=1e-7 else format(x,'.9g')
def vector(xs):return ' / '.join(delta(x) for x in xs)
def put(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    before=path.read_bytes() if path.exists() else b''
    first=before.find(b'\n')
    ending='\r\n' if first>0 and before[first-1:first]==b'\r' else '\n'
    path.write_text(text.rstrip()+'\n',encoding='utf-8',newline=ending)

def run():
    assert read(OUT/'science_identity.json')['PASS']
    configs=read(OUT/'reports/within_configuration.json')
    arms=read(OUT/'reports/three_seed_arms.json')
    new=read(OUT/'reports/complete_arms.json')
    pairs=read(OUT/'reports/three_seed_comparisons.json')
    summary=read(OUT/'reports/summary.json')
    assert len(new)==24 and len(pairs)==18 and len(configs)==6
    by={(a['id'],a['seed'],a['method']):a for a in arms}
    paired=table(['Configuration','B CERT /3','P CERT /3','ΔU: S0 / S1 / S2','ΔL: S0 / S1 / S2'],[
        [c['id'],c['B_CERT'],c['P_CERT'],vector(c['delta_U']['values']),vector(c['delta_L']['values'])] for c in configs])
    clocks=table(['Configuration','B T_cert: S0 / S1 / S2','P T_cert: S0 / S1 / S2'],[
        [c['id'],*(' / '.join(f(by[(c['id'],s,m)]['T_cert']) if by[(c['id'],s,m)]['certificate'] else '—' for s in (0,1,2)) for m in ('B','P'))]
        for c in configs[:3]])
    cert=table(['Seed','B20 B T_cert','B20 P T_cert','ΔT=B−P /s','B/P','Substantive scale /s'],[
        [p['gurobi_seed'],f(p['B_T_cert']),f(p['P_T_cert']),f(p['paid_cert_absolute_difference']),f(p['paid_cert_B_over_P']),f(p['material_time_scale_seconds'])]
        for p in sorted(pairs,key=lambda p:p['gurobi_seed']) if p['joint_CERT']])
    medians=table(['Input','Median ΔU [minimum, maximum]','Median ΔL [minimum, maximum]'],[
        [c['id'],*(f(v['median'])+' ['+f(v['minimum'])+', '+f(v['maximum'])+']' for v in (c['delta_U'],c['delta_L']))]
        for c in configs])
    c35=table(['Seed','B U / L','P U / L','State B/P'],[
        [s,*(' / '.join(f(by[('R163-C35-U',s,m)][k]) for k in ('U','L')) for m in ('B','P')),'OPEN / OPEN'] for s in (0,1,2)])
    block=r'''
#### Finite solver-Seed confirmation on the exposed cohort

The same six inputs were subsequently registered together for Gurobi Seeds1/2,
giving 24 additional B/P runs and twelve new paired comparisons. Historical
Seed0 qualifies under the same input, physical, method, executable, numerical
and paid-clock contracts, with matching documented runtime observations.
Each new run starts a fresh lifecycle; B recomputes and pays its own H with
seed20260626. These are six mathematical inputs with three within-input
observations each, rather than eighteen independent new inputs. No best Seed,
cross-Seed certificate, additional method or outcome-dependent stop is used.

**Table 14. Within-input paired differences in Seed order 0/1/2.** Seed0 is
historical; Seeds1/2 are new. ΔU=B−P is favorable to B when negative; ΔL=B−P
is favorable when positive. Values within the frozen 1e-7 equivalence scale
are displayed as 0. Full individual U/L, raw search bounds, paid costs,
medians/ranges and binary64 values remain in the supplement.

{paired}

At each Seed, B certifies 3/6 inputs and P 1/6. The three n20 B certificate
patterns persist, while cold P certifies only B20. B35 and X35 retain lower
B U and higher B L at every Seed, but all eighteen n35 method observations
remain OPEN. C35's primal ordering reverses: P is better at Seed0, whereas
B is better at Seeds1/2. B's C35 L remains higher at all three Seeds.
These input-specific consistencies do not establish a general success
probability or a structural cause of the observed differences.

**Table 15. Paid n20 certificate times, seconds.** A dash means OPEN, without
an imputed convergence time.

{clocks}

Certificate-status consistency does not imply constant complete cost. B's
C20 and X20 times vary substantively across these observations under the
declared scale; its B20 spread is below 10 s, whereas P's B20 range is
235.8555019–303.0333761 s. Within each Seed, the joint-CERT B/P intersection
contains only B20 (1/6). Its B/P time ratios at Seeds0/1/2 are
.02144657385/.01637985662/.01977901536 and its signed paid differences are
−230.7972095/−298.0697328/−261.5235357 s. Each exceeds the 10 s substantive
scale in B's favor. These conditional comparisons supply no full-panel
speedup, and an OPEN budget is never treated as a certificate time.

The uniform offline target is the better qualified Seed0 U, frozen before
any new Optimize and absent from production. B reaches the saved target on
all three observations of each n20 input and B35; on C35 it reaches none,
and on X35 only the historical Seed0 observation reaches it. P reaches it
on all three B20 observations, two C20 observations and historical C35
Seed0, with none observed on X20/B35/X35. In particular, B's new X35 U are
both worse than its own Seed0 U while its L are stronger, despite favorable
within-Seed B/P directions. Recorded availability intervals and censoring,
not exact first-discovery times or impossible-target claims, support these
statements.

The C35 H value is .17449020363402973 at all three fixed-H-seed lifecycles.
Native improves B's U to .12956638965196035/.10742986645444105/
.10808393649972804; P's U are .09331934374779818/.15762431259566606/
.14676445594619023. The historical P fleet therefore still supplies a known
better feasible point for every B run. Its advantage is not a persistent
within-Seed P-over-B ranking. Seed0's fleets differ in ownership, service
amounts and co-served relative order simultaneously; no single operator or
route-feedback benefit is isolated. The fixed unserved-station penalty
.011402553447730399 cannot exclude attaining P's target. Setting the other
visited inventories to target gives .03359254619609878, but exceeds the
saved routes' time limits and one prefix capacity. It is neither a physical
solution nor a certificate about every legal service choice on that skeleton.
'''.format(paired=paired,clocks=clocks)
    paper=ROOT/'results/unified_exact_round137/paper_body.md'
    body=paper.read_text(encoding='utf-8')
    start=body.index('### 6.5 ');end=body.index('## 7.',start)
    historical=body[start:end].split('#### Finite solver-Seed confirmation on the exposed cohort')[0].rstrip()
    conclusion=r'''## 7. Conclusions and implications

Physical equivalence, the shared inventory-state formulation and complete
interval coverage provide the algorithmic foundation. The historical breadth
panel certifies 9/12 inputs versus cold P 7/12 and paid-start PS 7/12; the
separate positive-resource panel certifies 4/8 versus 0/8 and 0/8. Their
versions and denominators remain distinct from the exposed-cohort repeats.
Conditional mechanism effects, time reversals and adverse endpoints remain
part of the evidence, rather than additive component shares or new theorems.

The completed three-Seed cohort supports a precise finite claim for uniform
GI-TBC/B: the n20 certificate patterns repeat, B35/X35 retain favorable
primal and proof directions, and B's C35 proof advantage persists. It does
not support a universal primal ordering, constant certificate time or
certification of the n35 inputs. C35 reverses the feasible-solution ranking,
and the known-feasible-target diagnostic exposes unreproduced absolute
primal values even where within-Seed B/P signs agree. These observations
support B as the paper's main method within the tested scope, without a
dominance theorem or population-level robustness claim.

E+ remains a separately named limited proof enhancement. Its historical
X35 lower-bound gain and earlier qualified inventory-proof gains are real;
the six Seed0 physical upper endpoints equal B's. Only C20's paired
certificate-time increase meets the substantive scale. The new B/P Seeds
do not establish E+ robustness. The unresolved B35/X35 inventory widths
also prevent transferring an earlier near-tight inventory remainder to this
cohort. A valid relaxation, stronger local information and improved complete
paid performance remain different conclusions.

The studied algorithm is the frozen S2/ms2 B configuration. Its mathematical
identity, the paper recommendation and released software defaults are
separately specified in the reproducibility material. The finite study ends
with these results; remaining capacity supplies no additional Seed or method.

### 7.1 Remaining scientific limits

A suboptimal feasible incumbent and an unresolved proof lower are different
shortcomings. C35's historical P fleet witnesses suboptimality of all three
B incumbents, while the within-Seed P/B ordering changes. Joint ownership,
relative order and integer service differences do not identify a causal
operator. A weak necessary penalty or an infeasible target-inventory vector
also cannot settle the whole fixed-skeleton value question.

Finite repeated endpoints cannot identify structural causality or an
eventual proof-time ranking. Any future claim of improved joint service
information requires its own physical-domain contract and complete paid
evidence. Existing fixed-route quantity and route-feedback objects already
address parts of that question; their positive, mixed and adverse evidence
remains relevant. The archived diagnostic prerequisites are in the research
navigation, rather than a new mechanism or an executed query in this study.
'''
    body=body[:start]+historical+'\n\n'+block.strip()+'\n\n'+conclusion
    abstract_old=next(p for p in body.split('\n\n') if p.startswith((
        'The separately frozen one-Seed B/E+/P confirmation',
        'A separately frozen six-input archived-source cohort gives')))
    abstract_new='A separately frozen six-input archived-source cohort gives B/E+ 3/6 certificates versus cold P 1/6 at Seed0. E+ preserves B\'s physical upper endpoints and strengthens one proof lower, with one substantive certificate-time increase. Two additional solver Seeds supply 24 new B/P runs on the same exposed inputs: each Seed repeats B 3/6 versus P 1/6, with favorable B35/X35 endpoint directions but OPEN n35 outcomes. C35\'s primal ordering reverses while B\'s proof advantage persists. The finite evidence supports B as the main method and E+ as a limited proof supplement, without stable-runtime, universal-primal or population claims.'
    body=body.replace(abstract_old,abstract_new)
    design='Main results use Seed 0; four preselected full-method triplets and small overlapping AM/mechanism blocks use Seed 1.'
    body=body.replace(design,'The earlier main panels use Seed 0; four preselected full-method triplets and small overlapping AM/mechanism blocks use Seed 1.')
    anchor='They are finite repeated observations, not independent new inputs or an estimated runtime distribution.'
    extra=' The later six-input archived-source cohort uses Seed0 for its B/E+/P comparison and Seeds1/2 for the complete B/P confirmation in §6.5. The additional 24 commands and offline feasible targets are frozen together; this extends existing Seed research on exposed inputs rather than supplying new unseen inputs.'
    if extra.strip() not in body:body=body.replace(anchor,anchor+extra)
    body=body.replace('| Second Seed | 12 main+4 AM+8 mechanism methods | Preselected limited repeat check |','| Earlier second Seed | 12 main+4 AM+8 mechanism methods | Preselected limited repeat check |\n| Exposed-cohort Seeds1/2 | 24 new B/P arms, plus 12 historical Seed0 B/P arms | Six inputs; three within-input paired observations |')
    put(paper,body)
    math=ROOT/'results/unified_exact_round137/mathematical_analysis.md'
    text=math.read_text(encoding='utf-8')
    if '## Completed finite-Seed interpretation' not in text:
        text+='''\n\n## Completed finite-Seed interpretation\n\nThe completed six-input readback gives eighteen within-input B/P pairs,\nincluding six historical Seed0 pairs. C35 has ΔU signs +/−/− and ΔL signs\n+/+/+; its median ΔU is descriptive and cannot erase the adverse Seed0\nfleet. B35/X35 have ΔU<0 and ΔL>0 in all three observations but no own\ncertificate. B20's differences within the frozen 1e-7 scale are equivalent\nendpoints, with three independently paid joint-CERT comparisons.\n\nThese are numerical observations under the original source, exact-zero and\ninclusive-cutoff qualification; they change no physical equivalence,\nepigraph/S=0 convention or coverage theorem. The complete own-run values\nand all target-availability intervals are in the\n[finite evidence tables](../unified_exact_round164/reports/seed_evidence.md).\n'''
    put(math,text)
    supplement=ROOT/'results/unified_exact_round137/supplement.md'
    text=supplement.read_text(encoding='utf-8').split('## Round164 completed finite solver-Seed evidence')[0].rstrip()
    structural=read(OUT/'structural_synthesis.json')
    decomposition=table(['Seed','Method','G','Weighted penalty','Physical U'],[
        [v['seed'],v['method'],*(f(v['final_fleet'][k]) for k in ('G','weighted_penalty','F'))] for v in structural['runs']])
    text+='''\n\n## Round164 completed finite solver-Seed evidence\n\nAll 24 registered new B/P positions complete at Seeds1/2, keyed on input,\nSeed, method and actual repeat1. Twelve new pairs and six qualified historical\nSeed0 pairs form six within-input groups. The\n[complete full-precision evidence tables](../unified_exact_round164/reports/seed_evidence.md)\nreport all 36 own-run physical U, raw/qualified search L, final proof L,\noriginal gaps, certificate states, paid clocks, own-H and Native effort.\nThe [new 24-arm CSV](../unified_exact_round164/reports/complete.csv),\n[paired differences](../unified_exact_round164/reports/three_seed_comparisons.json),\n[within-input summaries](../unified_exact_round164/reports/within_configuration.json)\nand [finite report](../unified_exact_round164/final_report.md) retain every\nOPEN observation and both endpoint directions. No E+ floor is included in B.\n\nHistorical Seed0 reuses the same input/physical/method/PE/DLL/deadline and\nnumerical contracts. Its selected original physical fleets and all Native\nSeed settings are reread; live OS module/affinity records and original native\nCPU/Windows/Gurobi headers match both new Seeds. The\n[reuse qualification](../unified_exact_round164/Seed0_reuse_qualification.json)\ndoes not assert identical incidental OS load or statistical exchangeability.\nThe [identity audit](../unified_exact_round164/science_identity.json) binds\nall 24 fresh serial lifecycles and independently paid fixed-seed H.\n\n### Descriptive within-input summaries\n\nThe medians and ranges below summarize three differences, not a new feasible\nsolution, proof endpoint or independent sample. Full binary64 values and\ntolerance-qualified signs remain in the linked machine reports.\n\n'''+medians+'''\n\n### Joint-CERT paid time intersection\n\nThe intersection is exactly B20, 1/6 inputs at each Seed (three within-input\npairs overall). Every listed difference exceeds its 10 s substantive scale.\nOPEN observations supply no convergence time and are not removed to infer\na full-panel acceleration.\n\n'''+cert+'''\n\n### Offline saved-feasible targets and clocks\n\nThe [six targets](../unified_exact_round164/primal_targets_frozen.json) were\nfrozen before any new Optimize from min(two historical qualified physical U).\nThey enter no argv, Start, cutoff or stop. The\n[all-36 records](../unified_exact_round164/reports/primal_target_arrival.json)\napply one rule to every input/method/Seed. Each saved journal fleet is\nphysically replayed. Its conservative paid upper is the observed availability\nplus T_produce minus the matching supervisor wrapper duration, including\nprelaunch. The global earliest-save lower is unknown and conservatively zero;\nreceipt-qualified journal availability has a separately recorded lower bound.\nOther full-fleet emitters may precede a journal receipt, so these are not exact\nfirst-find times. Endpoint-only records would supply producer-close uppers;\nno attainment observed is right-censored at that run's own producer close.\nThe [source clock contract](../unified_exact_round164/target_clock_contract.json)\nbinds the original C++ receipt order and matching supervisor time origin.\n\n### Bounded C35 witness explanation\n\nAll C35 H values equal .17449020363402973 with the same fixed H seed, each\nrecomputed and paid. The six final fleets decompose as follows.\n\n'''+decomposition+'''\n\nThe [saved-fleet synthesis](../unified_exact_round164/structural_synthesis.json)\nretains routes, operations, travel/handling times, prefix peaks, loaded returns\nand native improvement events. In the Seed0 B/P comparison, 26 common stations\nchange vehicle ownership, 15 common stations change service amount/direction\nand 15 co-served pairs reverse relative order. None of those reversals occurs\namong stations keeping the same vehicle label; the broader co-served comparison\nrecords simultaneous owner/order changes and does not isolate an order effect.\n\nThe unserved station18 contributes .011402553447730399, below P's known feasible\nobjective. Setting all other saved visited stocks to target gives the inventory\nobjective .03359254619609878, but route0 peaks at32 against capacity20 and all\nthree route times exceed10800 s (12501.7845/11130.8908/10939.8293 s). This point\nis infeasible, not a restricted-domain optimum or proof that every legal\nquantity choice fails. No R96 restricted MIP, route oracle or feedback producer\nis executed. Earlier R62/R96/R97/R160 evidence retains its actual mixed scope.\n\n### Reproduction and maintained format\n\nThe immutable numeric source is `'''+NUMERIC+'''`; original instance metadata\nremains the fixed R163 manifest. The\n[historical member map](../unified_exact_round164/historical_member_access.json)\nand [source map](../unified_exact_round164/historical_source_map.json) bind\nfinite old reads by commit/member/SHA. The\n[execution dispositions](../unified_exact_round164/execution_dispositions.json)\nretain a prelaunch-only idle-screen failure and an analysis-only overstrong\norder assertion; no healthy formal producer is repeated. The\n[cost report](../unified_exact_round164/cost_report.json) pays nonoverlapping\nouter processes and final independent review without adding nested Native/H\ncounters. Main CSV reconciliation, real review identities and publication/\nnew-only recovery are linked from the final report.\n\nMarkdown body/math/supplement are current for this revision. No maintained\nTeX is changed; the existing R137 PDF remains a historical snapshot. The\nfrozen B research configuration, paper recommendation and released main\ndefaults are distinct, and this study changes no released default.\n'''
    put(supplement,text)
    put(OUT/'decision.json',json.dumps(dict(UTC=utc(),round=164,science_complete=True,new_arms=24,new_pairs=12,
        mathematical_inputs=6,total_within_input_pairs=18,historical_Seed0_eligible=True,
        B_CERT_by_Seed=[3,3,3],P_CERT_by_Seed=[1,1,1],n20_certificate_pattern_repeated=True,
        n35_all_OPEN=True,B35_X35_relative_U_L_directions_consistent=True,
        C35_delta_U_signs=[1,-1,-1],C35_delta_L_signs=[1,1,1],
        constant_certificate_times_claimed=False,population_or_IID_claim=False,
        B_main_paper_method=True,Eplus_limited_historical_proof_supplement=True,Eplus_retested=False,
        broad_or_primal_dominance_claim=False,new_mechanism_or_extra_Seed=False,
        released_main_defaults_changed=False,predecessor_merged=False,
        numeric_science_commit=NUMERIC,independent_review_status='pending',publication_status='pending'),indent=2))
    report='''# Round164 finite solver-Seed confirmation\n\nAll 24 preregistered new B/P runs are complete and qualified. They provide\ntwelve new paired observations on six already exposed R163 inputs. The twelve\nqualified historical Seed0 method endpoints supply six additional within-input\npairs. Each Seed has B CERT 3/6 and P CERT 1/6. All n35 observations remain OPEN.\nB35/X35 retain favorable B primal/proof directions; C35's ΔU signs reverse\n+/−/− while ΔL stays +/+/+. This is finite within-input evidence, without\neighteen-IID-input, significance, best-Seed or universal-dominance claims.\n\nThe task is inherited from [goal.md](goal.md). The\n[historical increment](historical_increment.md) distinguishes existing\nR130–134/R137 Seed work and earlier structural/feedback studies. B stays the\npaper's main method; E+ retains its genuine historical proof gain and cost,\nwithout a new E+ run or robustness extrapolation. No spare capacity is used\nfor another Seed, mechanism, price or R96 query.\n\n## Complete evidence and competitive endpoints\n\nThe [readable full-precision tables](reports/seed_evidence.md) contain all\n36 identified own-run endpoints and original gaps; raw search, qualified\nsearch and final proof L are separate. They include T_cert/T_produce/\nT_verify/T_total, Native Work/nodes and actual own-H costs.\n[complete.csv](reports/complete.csv) gives all 24 new arms;\n[three_seed_arms.json](reports/three_seed_arms.json) gives all 36.\nThe [signed pair data](reports/three_seed_comparisons.json) preserve both\nΔU=B−P and ΔL=B−P under the frozen1e-7 scale. Every U is supported by its\nown full physical fleet and every L/state by its own original-problem\nsource/coverage; no cross-Seed U/L or E+ floor is composed into B.\n\n'''+paired+'''\n\nThe [within-input summaries](reports/within_configuration.json) give each\nthree-Seed vector, sign, descriptive median and range. Those summaries are\nnot new endpoints or certificates.\n\n'''+medians+'''\n\n## Certificates and paid time\n\nThe n20 certificate pattern repeats, with timing variation: C20 B ranges\n199.7793504–354.3877476s, X20 B 119.7493879–136.9986099s. B20 B varies below\nthe substantive scale while P 235.8555019–303.0333761s varies substantively.\nThe only B/P joint-CERT input is B20, 1/6 at each Seed, or three within-input\npairs. Only that intersection supplies paid certificate-time comparisons.\nThe declared threshold is max(10s,10% of the faster paid time); all three\nB20 differences favor B substantively. No OPEN cap is a certificate time,\nand no conditional average is promoted to a full-panel speedup.\n\n'''+cert+'''\n\n## Uniform offline primal diagnostic\n\nThe [frozen targets](primal_targets_frozen.json) equal the better qualified\nSeed0 physical U, not a known optimum, and were committed before any new\nOptimize. They enter no production input/Start/cutoff/stop. All 36 records\nin [primal_target_arrival.json](reports/primal_target_arrival.json) apply\nthe same saved-fleet/clock qualification. Reported upper bounds retain\nunknown earliest-save lower0 and separate receipt-qualified journal bounds;\nthere is no interpolated exact find time or verifier-clock backdating.\n\nB hits every n20 and B35 target at all three Seeds; it hits no C35 target\nand only the historical X35 target. P hits B20 at all three, C20 at0/1 and\nC35 only at0, with none observed on X20/B35/X35. New C35 and X35 runs of both\nmethods fail to observe the old target within their own windows. This is\nright-censored evidence, not a proof that the targets are unattainable.\nIn particular, favorable relative B/P signs do not imply reproducing an\ninput's best known feasible value.\n\n## Bounded C35 interpretation\n\n'''+c35+'''\n\nAll six runs are OPEN; B's L stays stronger while the primal ranking changes.\nThe same independently paid H has F=.17449020363402973. Native improves all\nB incumbents, yet historical P's .09331934374779818 remains better than all\nthree. The [structural synthesis](structural_synthesis.json) gives complete\nH/final fleets, trajectories and objective/physical operations. Seed0 has 26\ncommon-station owner changes,15 amount/direction changes and15 co-served\npair-order reversals, with zero same-owner pair-order reversals. These\nsimultaneous differences do not isolate a causal operator or feedback benefit.\n\nThe unserved penalty .011402553447730399 is too weak to exclude P's target.\nThe visited-target inventory .03359254619609878 violates all three route\ntimes and route0 prefix capacity (peak32>20). It is neither a physical upper\nnor a proof over every legal integer choice on the skeleton. Existing R96\ndiagnostics and R62/R97/R160 mixed evidence remain separately identified;\nno restricted solve, oracle or additional producer is run.\n\n## Identity, timing and failures\n\n[science_identity.json](science_identity.json) binds24 distinct serial C++\nlifecycles, every actual Native Seed1/2, own-H seed20260626 and all-three-Seed\nH semantics. Source/PE/DLL and physical/numerical/deadline contracts match\nthe original qualified production. [Seed0 qualification](Seed0_reuse_qualification.json)\nreplays twelve historical fleets and all old call Seed settings, plus actual\nPE/DLL/affinity records and matching native Gurobi/Windows/CPU headers. It\ndoes not claim identical incidental OS load or statistical exchangeability.\n\nThe six input bytes are referenced, not regenerated. Threads/MIPThreads=1;\nB is frozen S2/ms2 with own H, AM.08/depth8/width1e-4/pair-only/APoff, original\ninclusive/source/exact-zero policy. P is cold original compact, NumStart0,\nMIPFocus0/Cuts−1/Presolve−1 and requested gaps0, without PS or transferred\ninformation. New B uses no E+ floor. Physical T is independent of cap.\nAll1200/2400s producer contracts include startup/H/models/Native/online\nchecks/closure and retain the original watchdog/shutdown. The cap+300\nscientific reservation is separate from the inherited cap+900 fault timeout\nand grants no additional Native time.\n\nThere are two retained non-performance failures: one prelaunch-only idle\nregex false positive(1.1666751001030207s) with no Native/destination, and one\noffline order assertion(3.3629244999028742s) after analysis had passed. The\nlatter incorrectly demanded same-owner common-station inversions; the repair\nreports both same-owner and co-served order relations and retains actual\nabsences. It resumes only the post-analysis readback(4.214931599795818s).\nNo healthy producer or successful endpoint analysis is replayed.\n[execution_dispositions.json](execution_dispositions.json) and original\nfee receipts retain both failures.\n\nBefore extra independent review, closed scientific cost is\n34749.89784079837/57600s, including qualification11.829855800140649s,\nall formal outers and both failures. The final authoritative\n[cost report](cost_report.json) includes later review segments exactly once;\nnested Native Runtime/Work/H is diagnostic, never an additional fee.\nOrdinary writing, table authoring, packaging and recovery I/O are separate.\nNo production rebuild or helper Optimize is introduced.\n\n## Maintained paper, master table and delivery\n\nThe single maintained [body](../unified_exact_round137/paper_body.md),\n[mathematical analysis](../unified_exact_round137/mathematical_analysis.md) and\n[supplement](../unified_exact_round137/supplement.md) contain these results.\nThe old §5.4 four-input Seed panel is unchanged. §§3.5/6.4/6.5/7 distinguish\nproof, physical and complete-method conclusions and retain historical\npositive/adverse evidence; the C35/R96 worklist is in\n[research navigation](research_navigation.md). Markdown is current and the\nexisting R137 PDF is historical; no TeX update or new PDF is claimed.\n\nThe immutable numerical source for new CSV rows is `'''+NUMERIC+'''`.\nOriginal metadata remains at the fixed R163 manifest. The\n[master update receipt](main_table_update.json), exact twelve-row increment\nand pending three-row historical union explanation retain actual local\nsource counts,28 columns, encoding, precision and historical bytes.\nNo inaccessible 106-row master is claimed updated.\n\nExtra independent reviews, publication, new-only archive/member hashes,\nbounded anonymous public recovery and zero-delete cleanup are recorded\nseparately before final completion. Their status is pending at this\nmanuscript-authoring checkpoint; no Draft publication is claimed yet.\n'''
    put(OUT/'final_report.md',report)
    put(ROOT/'docs/round164_seed_confirmation.md','''# Round164 finite solver-Seed confirmation\n\nThe complete 24-arm B/P repeat on the same six exposed R163 inputs confirms\nthe n20 certificate pattern at Seeds1/2 without stable-time or universal\nprimal claims. At each of the three qualified Seeds B certifies3/6 and\ncold P 1/6. All n35 runs remain OPEN. B35/X35 retain favorable relative U/L\ndirections, while C35's primal ordering reverses and B's proof L stays\nhigher. These are eighteen within-input pairs on six mathematical inputs.\n\nSee the [full report](../results/unified_exact_round164/final_report.md),\n[complete readable evidence](../results/unified_exact_round164/reports/seed_evidence.md),\n[decision](../results/unified_exact_round164/decision.json) and\n[maintained paper](../results/unified_exact_round137/paper_body.md).\nB remains the paper's main method; E+ retains its scoped historical proof\ngain/cost and has no new Seed runs. Released main/defaults are unchanged.\nThe original R137 PDF remains a historical snapshot; Markdown is current.\n\nThe master-table fallback preserves actual accessible user files and provides\nthe exact 12-pair increment, with the unavailable three historical N/A-P\nrecords explicitly pending union. Publication/recovery/review closeout is\nlinked from the final report and RESUME. No extra study uses the remainder.\n''')
    navigation=ROOT/'docs/current_mainline.md';text=navigation.read_text(encoding='utf-8')
    heading='# Current mainline and Round137 paper branch\n'
    top='''\nThe completed [Round164 finite solver-Seed confirmation](round164_seed_confirmation.md)\nadds 24 frozen B/P arms at Seeds1/2 on the six exposed R163 inputs. Each of\nthe three qualified Seeds gives B 3/6 and cold P 1/6 certificates. All n35\nobservations remain OPEN; B35/X35 retain better B U/L, while C35's primal\nordering reverses and B's L stays stronger. These are six mathematical\ninputs with eighteen within-input pairs, without a population or constant-time\nclaim. B is the paper's main method; E+ retains its genuine historical proof\ngain and cost, without new E+ robustness evidence. The maintained R137\n[body](../results/unified_exact_round137/paper_body.md),\n[math](../results/unified_exact_round137/mathematical_analysis.md) and\n[supplement](../results/unified_exact_round137/supplement.md) are current\nMarkdown. The existing R137 PDF is historical; released defaults and prior\nPRs are unchanged. Full identities, fees, CSV reconciliation and delivery\nreceipts are in the [report](../results/unified_exact_round164/final_report.md).\n\n'''
    if '[Round164 finite solver-Seed confirmation]' not in text:text=text.replace(heading,heading+top)
    text=text.replace('The current [Round163 stage confirmation]','The preceding [Round163 stage confirmation]')
    text=text.replace('now integrate the structural-stage evidence and one next research question.','retain the historical structural-stage evidence; the later Seed results above distinguish observed limits from the unexecuted research navigation.')
    put(navigation,text)
    print('Authored scoped maintained paper, supplement, finite report and navigation from completed qualified data.')

if __name__=='__main__':run()
