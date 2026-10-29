"""Assemble the finite mathematical/experimental increment; reuse accepted PDF flow."""
from round140_common import *
from round140_tables import table,ROLE_ORDER
import inspect,re,shutil

def marker():
    path=OUT/'PDF_marker.json'
    if path.exists():assert read(path)['success'];return
    script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1017.22136/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
    node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    r=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
    assert r.returncode==0,(r.stdout,r.stderr)
    write(path,dict(UTC=utc(),success=True,stdout=r.stdout,successful_invocations=1))

def assemble():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');d=read(OUT/'candidate_decision.json');lp=read(OUT/'reports/LP.json')
    assert full['complete'] and d['study_complete'];marker()
    new=sorted(full['new_arms'],key=lambda a:(ROLE_ORDER.index(a['role']),a['method'],a['seed']))
    roles=[r for r in ROLE_ORDER if any(a['role']==r and a['seed']==0 for a in new)]
    allrows=full['reused_arms']+new
    def chosen(role,method):
        matches=[a for a in allrows if a['role']==role and a['method']==method and a['seed']==0]
        return matches[0] if matches else None
    fullrows=[]
    for role in roles:
        for method in ['base','both','TC_STOCK','TC2_STOCK']:
            a=chosen(role,method)
            if a:fullrows.append([role,method,a['U'],a['L'],a['T_cert']])
    body='# Inventory budgets strengthen discrete Gini threshold counts\n\n'
    body+='Round140 research increment, 29-30 October 2026 (Asia/Shanghai). This standalone section extends the maintained Round137 complete manuscript and the Round138/Round139 increments. The selected panel is known research data. The study separates a valid structural strengthening, an optimized continuous bound gain, and complete-method performance.\n\n'
    body+='## 1. Mathematical structure and exact scope\n\n'
    math=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8').splitlines()[1:]
    body+='\n'.join(('###'+line[2:] if line.startswith('## ') else line) for line in math)+'\n\n'
    body+='McCormick/RLT product envelopes are inherited standard tools [@AdamsSherali1990R138; @SheraliAdams1999R138]. The project-specific contribution is the inventory-driven two-sided count information, its qualified implementation, and its finite complete-method evaluation. No general chord inequality, cardinality bound, or product envelope is claimed as a new theorem.\n\n'
    body+='## 2. Saved points and same-domain reoptimization\n\n'
    body+='The fixed R138 diagnostics archive and saved solution SHA values were checked before new Optimize. All four saved old TC+stock optima are separated. This does not imply a bound gain until reoptimization. RB35-T2 was absent from the old four-root TC panel; its old-TC control is newly optimized here. Nine new explicit continuous LPs use exactly matched objective, support, cutoff and g endpoints, explicit Seed0, one thread and serial execution.\n\n'
    body+=table(['Role','STK L','STK+TC L','STK+TC+TC2 L','Increment'],[[a['role'],a['stock']['L'],a['tc_stock']['L'],a['tc2_stock']['L'],a['tc2_stock']['L']-a['tc_stock']['L']] for a in lp['roles']])
    body+=table(['Role','Thresholds','Budget adds q>0','Forced-only ell>0'],[[a['role'],a['thresholds'],a['lower_budget_adds_count'],a['forced_only_positive_lower']] for a in lp['roles']])
    body+='RB35-T2 and RX35-T2 have no forced-high stations at any threshold. Their positive lower counts and bound increments require the inventory lower budget. RX20 has q=0 at every threshold: its small gain instead uses forced-high support information. K20 and K35 combine these sources without an additive allocation of objective gains. Detailed G, H_sum, J, tau, legal U, coefficient distributions, construction costs, row counts, residuals and identity hashes remain in reports/LP.json and sealed position records. These are numerical continuous optima, not Native MIP root bounds or complete performance samples.\n\n'
    if (OUT/'reports/LP_precision.json').exists():
        precision=read(OUT/'reports/LP_precision.json')
        body+=f'Two additional finite RX20 LP confirmations use FeasibilityTol and OptimalityTol 1e-9, explicit Seed0 and one thread. The increment remains {precision["delta"]:.12g}; both objectives match the primary observations. This is numerical confirmation of a small effect, with unchanged complete-algorithm parameters and original result identities.\n\n'
    body+='The K20 no-stock BASE/TC/TC+TC2 control confirms complementarity with the shared-stock product rows on the same domain. The additional RB35-T2 no-stock TC+TC2 position remains a labelled auxiliary, not a complete no-stock ablation panel. The return-product alternative is screened offline only: all four old stock points admit W extensions within the recorded numerical residual tolerance. K35 old TC+stock first violates a linear vehicle-return upper bound, so it cannot establish a product benefit.\n\n'
    current_path=OUT/'math/return_product_current_points.json'
    if current_path.exists():
        current=read(current_path)
        def obstruction(a):
            return 'return bound' if not a['return_bounds_feasible'] else ('product projection' if a['product_signal_beyond_linear_bounds'] else 'none at this point')
        body+='The five newly optimized TC2+stock vectors receive a separate zero-Optimize projection check with an explicit 1e-7 numerical residual tolerance. Return bounds are checked before the W interval-sum condition; passing this numerical screen does not assert exact rational feasibility of the saved binary64 vector. A saved-point obstruction is distinct from an optimized objective gain; absence of an obstruction does not prove global redundancy.\n\n'
        body+=table(['Role','First obstruction','Bg-J'],[[a['role'],obstruction(a),a['target']] for a in current['cases']])
    body+='## 3. Complete uniform algorithms\n\n'
    body+='The initial five-role candidate uses STK+TC+TC2 uniformly in outer LP and native target/terminal. Independent old STK+TC controls start with K20 and RB35-T2; result-selected additional comparisons and the final uniform candidate choice are stated below. BASE and STK reuse the accepted matched R137/R138 evidence, retaining primary V1 and accepted V2 bridge identities. Every new method starts independently and pays complete own H, construction, validation, search and online proof; no cross-method or cross-Seed solution, bound, Start or tree is injected.\n\n'
    body+='All primary solves use explicit Gurobi Seed0, one thread, affinity mask 4, the same verified 13.0.2 DLL, and separately fixed H seed 20260626. Resource roles retain rho=1 and original binary64 lambda=1/Omega. Physical T and experiment cap retain their frozen meanings; they are not elapsed-time algorithm switches. The two cap90 qualifications are excluded from performance counts.\n\n'
    body+=table(['Role','Method','Verified U','Supported L','T_cert (s)'],fullrows)
    body+='Open T_cert is null and displayed as open. No cap is imputed as convergence time or exact speedup. Signed/relative gap and T_produce/T_cert/T_verify/T_total, Work, nodes and all actual call controls remain in reports/. Native returned ObjBoundC and externally merged final L are separate columns. The table contains only actual entered complete comparisons and matching references; missing old-TC positions are not inferred.\n\n'
    body+=d['complete_discussion']+'\n\n'
    body+=table(['Role','Method','Seed','Signed U-L','Relative gap'],[[a['role'],a['method'],a['seed'],a['signed_gap'],a['relative_gap']] for a in new])
    body+=table(['Role','Method','Seed','T_produce','T_verify','T_total'],[[a['role'],a['method'],a['seed'],a['T_produce'],a['T_verify'],a['T_total']] for a in new])
    body+='These two compact tables cover every new formal complete position. Qualifications are separate. Matched old references retain their full costs and gaps in reports/reused_arms.csv. Physical T, actual binary64 objective weight and experiment cap are independent fields in reports/new_arms.csv.\n\n'
    body+='### 3.1 Observable mechanism\n\n'+d['mechanism_discussion']+'\n\n'
    body+=table(['Role','Method','First AM action','LP / target / terminal'],[[a['role'],a['method'],a['first_AM_action'],f"{a['LP_calls']} / {a['target_calls']} / {a['terminal_calls']}"] for a in new if a['seed']==0])
    body+='AM decisions use parent-relative child gains. A stronger parent bound need not increase this gain. Actual calls, parent bounds and action sequences support mechanism interpretation; they do not allocate additive causal runtime to the two new rows. Saved native witness vectors are physically replayed. Rounded native-log timestamps and controller publication after return do not establish exact discovery clocks.\n\n'
    body+='### 3.2 Conditional extensions and limited Seed1\n\n'+d['conditional_discussion']+'\n\n'
    if (OUT/'reports/seed1.json').exists():
        seed=read(OUT/'reports/seed1.json')
        ordered=sorted(seed['arms'],key=lambda a:['BASE','STOCK','TC_STOCK'].index(a['method']))
        body+=table(['Role','Method','Seed','Verified U','Supported L','T_cert (s)'],
            [[a['role'],a['method'],a['seed'],a['U'],a['L'],a['T_cert']] for a in ordered])
        body+='The two Seed1 references retain their accepted original BASE/V2 STOCK source, PE and complete clocks; the fresh TC_STOCK method uses the current PE. This is a matched complete-method comparison, not a same-PE intervention. Original reference and new production/verification/total clocks remain in reports/seed1_arms.csv. No favorable confirmation replaces an adverse Seed0 observation.\n\n'
    body+='## 4. Research decision and remaining question\n\n'+d['decision_paragraph']+'\n\n'+d['remaining_question']+'\n\n'
    body+='## 5. Cost and reproducibility\n\n'
    b=budget();body+=f'New charged experiment computation is {b["G1_seconds"]:.6f} seconds ({b["G1_seconds"]/3600:.6f} hours), within 43200 seconds. All qualification and failed native attempts are included. Complete outer methods are charged once; nested H/LP/MIP/Work are not added twice. Old references retain their original clocks without fictitious new charges. Builds, pure offline checks, postverification, documents and public I/O are separately measured where explicit, without invented precision for interactive reading or editing.\n\n'
    body+='The pre-Optimize Path-type LP failure and narrow retry are retained. The singleton empty-row defect was fixed before qualification; the earlier build supplies no performance sample. An early pure postreader ordering failure had zero Optimize/Native loads and was corrected by explicit sealed scope. Final all-group checks pass; no native observation was rerun or replaced. Actual Native coefficient/RHS/type reads cover root, child, cutoff refresh and every used LP/target/terminal artifact. Independent preflight, admission, selection and integration records remain distinct.\n\n'
    body+='The actual source/PE/DLL, input, configuration, controls and helper identities are bound by candidate_manifest.json and frozen batches. Local physical/scientific/semantic checks and once-only public archive/member readability are different claims. No public check runs Optimize, compilation or a commercial Native load. Stable GI-TBC remains independently usable. The final continuation record gives actual Draft PR, base/head, fixed science, public read and bounded cleanup status; it does not infer completed delivery from a scientific decision.\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    shutil.copyfile(ROOT/'results/unified_exact_round138/references.bib',OUT/'references.bib')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),references_SHA=sha(OUT/'references.bib'),
        inherited_manuscripts_unchanged=True,lineage='Standalone Round140 increment extending accepted R137/R138/R139',Optimize=0))

def pdf():
    assert not budget()['unclosed'] and read(OUT/'PDF_marker.json')['success']
    import round139_documents as old
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,read=read,write=write,budget=budget,environment=environment)
    source=inspect.getsource(old.pdf).replace('Round139 standalone placement increment: mathematical analysis, qualified full placement reports and decision, references and scientific figures',
        'Round140 standalone count increment: mathematical validity and scope, qualified same-domain LP and complete uniform algorithms, costs and decision')
    before='source=inspect.getsource(old.pdf).replace('
    assert source.count(before)==1
    source=source.replace(before,"source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=30 October 2026').replace(")
    exec(compile(source,__file__+'::accepted_increment_PDF_flow','exec'),ns);ns['pdf']()

if __name__=='__main__':globals()[sys.argv[1]]()
