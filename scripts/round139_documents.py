"""Assemble the research increment from final qualified evidence, then reuse PDF flow."""
from round139_common import *
import inspect,re,types,shutil

def fmt(value):
    if value is None:return 'open'
    if isinstance(value,bool):return 'yes' if value else 'no'
    if isinstance(value,(int,float)):return format(value,'.7g')
    return str(value)

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),
        *['| '+' | '.join(fmt(v) for v in r)+' |' for r in rows]])+'\n\n'

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
    full=read(OUT/'reports/full.json');decision=read(OUT/'candidate_decision.json');assert full['complete'] and decision['study_complete']
    marker()
    old=read(OUT/'baseline_reuse.json')['positions'];rows=full['new_arms'];reused=full['reused_arms']
    body='# Where inventory-product consistency belongs in GI-TBC\n\n'
    body+='Round139 research increment, 29 October 2026 (Asia/Shanghai). This independent section extends the complete Round137 manuscript and Round138 resource-product increment. The inherited experiments keep their original source, PE and scientific identities. The study concerns uniform placement across explicit LP control and native MIP search.\n\n'
    body+='## 1. Mathematical and algorithmic scope\n\n'
    body+='\n'.join((OUT/'mathematical_analysis.md').read_text(encoding='utf-8').splitlines()[1:])+'\n\n'
    body+='The RLT rows are standard reformulation-linearization tools [@AdamsSherali1990R138; @SheraliAdams1999R138]. Round138 supplies the problem-specific shared-stock analysis and accepted witnesses. Round139 contributes a controlled placement study and its implementation/proof interface, without renaming this standard construction.\n\n'
    body+=table(['Placement','Outer explicit LP','Native MIP, including internal LPs'],
        [['BASE / 00','base','base'],['BOTH / 11','stock','stock'],['LP-only / 10','stock','base'],['MIP-only / 01','base','stock']])
    body+='All methods keep complete own H (seed 20260626), M-B/VD-P, pair-only support, AM .08, depth 8, minimum width 1e-4 and AP/TC off. Solver calls use explicit Gurobi Seed0 unless a registered limited Seed1 repeat is shown, one thread, the same 13.0.2 DLL and affinity mask 4. No instance identity, size-specific placement or elapsed-time algorithm switch is used.\n\n'
    body+='## 2. Actual inherited calls and matrix controls\n\n'
    inherited=read(OUT/'reports/inherited_mechanisms.json')
    body+=table(['Role','Method','LP / target / terminal calls','Initial H','Common matrix'],
        [[r['role'],m['method'],f'{m["LP"]} / {m["target"]} / {m["terminal"]}','same','same after four rows'] for r in inherited['roles'] for m in r['methods']])
    body+='The root and both probed child matrices are identical in variable order, types, bounds, objective and common row multiplicities after removing the four stock rows. This includes K20 and RB35-T2. H cannot explain their opposite changes. K20 BASE target consumes about .33 s and supplies no new solution; its later terminal log retains a previous-solve Start. BOTH bypasses that target. The approximately 100 s versus cap1200 result cannot be attributed to saving .33 s of direct target time. RB35-T2 has direct terminal calls in both methods, and their incumbent traces cross repeatedly.\n\n'
    body+='Native incumbent lines are rounded model objectives on their own diagnostic clock. All saved witness vectors from selected K20/RB35-T2 runs are independently replayed in reports/native_trajectories_and_witnesses.json; actual source/call fields distinguish MIPSOL vectors from H, before-call and final vectors. Same-call numerical matching to a rounded log objective is approximate and does not establish unique vector identity or exact discovery timestamps. Other-call numerical coincidences are listed separately. Controller publication/qualification after native return is not discovery time.\n\n'
    body+='## 3. Registered finite comparison\n\n'
    body+='The panel has eight physical/objective configurations on six base inputs; T1/T2 are shared-input horizons. Three declared behavior roles form the placement pilot. All sixteen accepted BASE/BOTH Seed0 reference positions are reused after identity checks. The new 00/11 small qualification preserves the historical canonical SHA; measured R138 primary BOTH remains V1, with the accepted V2 matrix/native bridge. New placements use the unchanged V2 writer and a separately frozen Round139 PE. The qualification cap90 runs do not enter performance counts.\n\n'
    body+=table(['Configuration','Stations / vehicles','Physical T (s)','Objective / cap (s)'],
        [[r['role'],f'{r["panel"]["V"]} / {r["panel"]["M"]}',r['panel']['T_seconds'],
          ('lambda=.15' if not r['role'].startswith('R-') else 'rho=1')+f' / {r["panel"]["cap_seconds"]}'] for r in old])
    body+='Resource weights preserve the original binary64 lambda = 1/Omega, rather than .15. Each new complete method independently pays H, model construction/reconstruction, online checks, native solve and proof. It imports no other method/Seed/diagnostic solution, bound, Start or tree.\n\n'
    body+='### 3.1 Three-role placement results, Seed0\n\n'
    pilot_roles=['K-15-S','K-20-S','R-B35-S-T2'];pilot=[]
    for role in pilot_roles:
        for method in ['base','both','lp-only','mip-only']:
            match=[r for r in reused+rows if r['role']==role and r['method']==method and r['seed']==0]
            if match:pilot.append(match[0])
    body+=table(['Role','Placement','Verified U','Supported L','Certificate (s)'],
        [[r['role'],r['method'],r['U'],r['L'],r['T_cert']] for r in pilot])
    body+='Open certificate times are null, not imputed caps. Both-certificate differences are substantive only if absolute time differs by at least max(10 s, 10% of the smaller time). Raw T_produce/T_cert/T_verify/T_total, signed gaps and relative gaps remain in reports/new_arms.csv and reports/reused_arms.csv. Opposed U and L changes are reported separately.\n\n'
    body+=decision['pilot_discussion']+'\n\n'
    body+='### 3.2 Control and execution paths\n\n'
    body+=table(['Role','Placement','AM action sequence','LP / target / terminal','Native reuse by call'],
        [[r['role'],r['method'],' -> '.join(r['AM_action_sequence']),f'{r["LP_calls"]} / {r["target_calls"]} / {r["terminal_calls"]}',str(r['retained_reuse'])] for r in rows if r['batch']=='pilot'])
    body+='The LP-only transition explicitly discards the stock LP model before loading the base integer matrix. MIP-only discards the base LP model before loading stock; later target-to-terminal reuse is retained when the matrix and epoch stay unchanged. The loss of reuse and explicit rebuild are part of each complete method. These comparisons are interventions on whole execution paths, not additive causal allocations of runtime.\n\n'
    body+='K20 MIP-only initially has the BASE LP bounds and native-target action. Its stock native target returns a qualified parent bound about .204825779, above the cached left LP bound .196078260; the next AM evaluation consequently takes exact-close. Its complete certificate time is about 100.71 s, close to BOTH at 101.64 s despite their different first actions. LP-only keeps the stronger outer LP and immediate exact-close, but remains open. Native-side placement retains this proof benefit in the finite comparison while outer-LP-only does not; this does not assign exact time shares to rows, reuse or Start state.\n\n'
    body+='### 3.3 Uniform extension and limited Seed1\n\n'+decision['extension_discussion']+'\n\n'
    selected=decision.get('selected_uniform_candidate')
    if selected:
        panel=[]
        for role in [r['role'] for r in old]:
            for method in dict.fromkeys(['base','both',selected]):
                match=[r for r in reused+rows if r['role']==role and r['method']==method and r['seed']==0]
                if match:panel.append(match[0])
        body+=table(['Configuration','Placement','U','L','Signed U-L'],
            [[r['role'],r['method'],r['U'],r['L'],r['signed_gap']] for r in panel])
    if (OUT/'reports/seed1.json').exists():
        seed=read(OUT/'reports/seed1.json');body+=seed['selection_rationale']+'\n\n'
        body+=table(['Role','Placement','Seed','U','L','Certificate (s)'],
            [[r['role'],r['method'],r['seed'],r['U'],r['L'],r['T_cert']] for r in seed['arms']])
        body+=seed['discussion']+'\n\n'
    if (OUT/'figures/placement_endpoints.png').exists():
        body+='![Complete-method Seed0 endpoint changes relative to reused BASE. Positive delta U is worse; positive delta L is stronger. BOTH is reused R138; the asymmetric positions are new.](figures/placement_endpoints.png)\n\n'
    if (OUT/'figures/native_search.png').exists():
        body+='![Terminal native incumbent diagnostics. Zero denotes the already submitted own Start, timed updates come from rounded logs, and the last value is the native return. This clock is separate from verified physical U and formal complete clocks.](figures/native_search.png)\n\n'
    body+='## 4. Research decision and contribution\n\n'+decision['decision_paragraph']+'\n\n'+decision['mechanism_conclusion']+'\n\n'+decision['remaining_question']+'\n\n'
    body+='## 5. Cost, evidence and scope\n\n'
    b=budget();body+=f'New charged experiment computation is {b["G1_seconds"]:.6f} s ({b["G1_seconds"]/3600:.6f} h), within 57,600 s. Native complete runs and qualification/failures are charged once at their outer process; nested H/LP/MIP/Work are not added again. Historical references retain their original comparison clocks without fictitious new charges. Measured builds, PDF/public I/O and pure audits are reported separately; unmetered human reading is not assigned invented precision.\n\n'
    body+='The first source commit triggered automatic Git maintenance, which was stopped before formal timed runs. The affected cap90 qualification times are not performance samples. Subsequent Git commands disable automatic maintenance locally per invocation. Three subsecond qualification-runner/runtime launch failures are retained; they performed no Optimize and did not replace any solve.\n\n'
    body+='Independent preflight, actual qualification and batch admission are in review/. Source/PE/input/config/Seed, actual matrix and call identities, all entered ordinary adverse/open outcomes, finite carriers, local semantic checks and public byte/member readability have distinct receipts. A public byte check does not imply a fresh solver replay. The known selected panel and result-selected Seed1 are not independent unseen validation sets. The stable R137 entry and R138 research entry remain independently usable.\n\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    shutil.copyfile(ROOT/'results/unified_exact_round138/references.bib',OUT/'references.bib')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),references_SHA=sha(OUT/'references.bib'),
        R137_and_R138_manuscripts_unchanged=True,lineage='Standalone incremental method/mechanism section extending accepted R137/R138',Optimize=0))

def pdf():
    assert not budget()['unclosed'];assert read(OUT/'PDF_marker.json')['success']
    import round138_documents as old
    # Reuse the accepted assembly/LaTeX path with only this round's identities.
    source=inspect.getsource(old.pdf).replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round139 standalone placement increment: mathematical analysis, qualified full placement reports and decision, references and scientific figures')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,read=read,write=write,budget=budget,environment=environment)
    exec(compile(source,__file__+'::accepted_increment_PDF_flow','exec'),ns);ns['pdf']()

if __name__=='__main__':globals()[sys.argv[1]]()
