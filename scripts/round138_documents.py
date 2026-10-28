"""Standalone R137-lineage research increment; export only after native closeout."""
from round138_common import *
import inspect,re,types,shutil

def fmt(x):
    if x is None:return 'open'
    if isinstance(x,bool):return 'yes' if x else 'no'
    if isinstance(x,(float,int)):return format(x,'.6g')
    return str(x)

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),
                     *['| '+' | '.join(fmt(x) for x in row)+' |' for row in rows]])+'\n\n'

def assemble():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');decision=read(OUT/'candidate_decision.json')
    assert full['complete'] and decision['study_complete']
    lp=read(OUT/'reports/LP.json')['rows'];by={(r['role'],r['variant']):r for r in lp}
    body='# Shared-product consistency with global inventory budgets in GI-TBC\n\n'
    body+='Round138 research increment, 29 October 2026. This separately reviewable section extends the accepted Round137 manuscript. The complete Round137 paper and historical experiment identities remain intact. It combines a selected continuous-block hull result, exact tiny witnesses, same-domain real LPs and complete-method evidence.\n\n'
    body+='\n'.join((OUT/'mathematical_analysis.md').read_text(encoding='utf-8').splitlines()[1:])+'\n\n'
    body+='## 7. Saved points and real same-domain LP reoptimization\n\n'
    saved=read(OUT/'roots/saved_points.json')['cases'];roles=list(saved)
    body+='The three motivating points are actual saved R137 roots, rather than new Round138 experiments. K-20-S is an additional known control. Inventory products are unscaled and depot stock is excluded. Integral Y does not imply integral selectors: the K35 saved point has 78 fractional station selectors.\n\n'
    body+=table(['Saved root','Auxiliary g','True G at saved Y','J - Bg'],
        [[role,saved[role]['G_aux'],saved[role]['saved_Y_true_objective']['G'],saved[role]['J_minus_Bg']] for role in roles])
    body+='All new LPs retain the exact stored input, physical horizon, lambda, supports, interval, native cutoff and original rows. Noncomparison auxiliaries reoptimize freely; AP is off. Every solve uses explicit Seed0, one thread and Gurobi13.0.2. The two resource lambdas are the original double values, not .15. Point violation is not objective-bound gain. The table uses the newly reoptimized base in each delta.\n\n'
    body+=table(['Root','Base L','Stock L','TC L','TC + stock L'],
        [[role,*[by[role,v]['L'] for v in ['base','stock','tc','tc_stock']]] for role in roles])
    body+=table(['Root','Stock delta L','Stock gap at common U','TC + stock delta L'],
        [[role,by[role,'stock']['delta_new_base'],by[role,'stock']['signed_gap'],by[role,'tc_stock']['delta_new_base']] for role in roles])
    body+='The stock rows improve all four root objectives. TC provides additional information on some roots, but the primary complete candidate deliberately contains only the minimum four inventory rows. The numerical LP optima and quality/residual checks are not exact rational optimality certificates.\n\n'
    body+=table(['Root','Base L','Independent GS L','Shared GS L','Stock L'],
        [[role,*[by[role,v]['L'] for v in ['base','gs_independent','gs_shared','stock']]] for role in ['K-35-U','R-X20-S-T1']])
    body+='On RX20 the physical stock direction gives a stronger original-objective bound than either lawful ratio aggregate control in this domain. The equal K35 objective values do not imply equal feasible regions: the optima use different J values. These observations do not generalize to dominance over all historical GS variants. Full-precision authorities are reports/LP.csv and each root result/vector.\n\n'
    body+='## 8. Complete algorithm comparison\n\n'
    body+='The primary panel has eight physical/objective configurations on six base inputs and sixteen nominal method positions. Eight accepted R137 GI-TBC baselines are reused only after checking the exact PE, input, physical parameters, lambda, Seed0, cap, single-thread runtime/affinity and complete-cost policy. A contemporaneous frozen-PE K15 bridge is additionally reported; it never replaces the earlier baseline by whichever time is better. All candidate runs independently pay complete own H, construction, validation, search and proof. No solution, bound, tree or Start is transferred across methods, seeds or weights.\n\n'
    pairs=full['core_pairs']
    body+=table(['Configuration','Base U','Stock U','Base L','Stock L'],
        [[r['role'],r['base_U'],r['stock_U'],r['base_L'],r['stock_L']] for r in pairs])
    body+=table(['Configuration','Base certificate s','Stock certificate s','Base relative gap','Stock relative gap'],
        [[r['role'],r['base_T_cert'],r['stock_T_cert'],r['base_relative_gap'],r['stock_relative_gap']] for r in pairs])
    body+='Open certificate times are null in the data and displayed as open. Lower relative gap is not used to hide an opposed U or L endpoint. Both-certificate time differences are called substantive only when the absolute difference is at least max(10 s, 10% of the smaller time). The complete production clock includes online work and seal; subsequent pure verification has its own clock.\n\n'
    other=[a for a in full['new_arms'] if a['stage'] in ['contemporaneous-baseline-bridge','micro']]
    body+=table(['Control','Method','T produce s','T cert s','U','L'],
        [[a['role'],a['method'],a['T_produce'],a['T_cert'],a['U'],a['L']] for a in other])
    body+='The K15 bridge first encountered a postreader version-adapter error after normal sealed native completion. Its original failure and fee are preserved. Independently reviewed strict modern lifecycle handling repaired only verification; the native run was not repeated. The producer, completion and postverification clocks retain their distinct definitions.\n\n'
    body+=decision['full_results_discussion']+'\n\n'
    if (OUT/'reports/seed1.json').exists():
        seed=read(OUT/'reports/seed1.json')
        body+='### 8.1 Limited second Seed\n\n'+seed['selection_rationale']+'\n\n'
        body+=table(['Configuration','Method','Seed','Certificate s','U','L'],
            [[a['role'],a['method'],a['seed'],a['T_cert'],a['U'],a['L']] for a in seed['arms']])
        body+=seed['discussion']+'\n\n'
    body+='### 8.2 What the complete data establish\n\n'+decision['interpretation']+'\n\n'
    if (OUT/'figures/paired_evidence.png').exists():
        body+='![Same-domain stock bound increments and capped complete-method endpoint gaps.](figures/paired_evidence.png)\n\n'
    body+='## 9. Stage decision and next question\n\n'+decision['decision_paragraph']+'\n\n'+decision['next_question']+'\n\n'
    body+='## 10. Evidence and scope\n\n'
    b=budget()
    body+=f'New charged experiment computation is {b["G1_seconds"]:.6f} seconds out of 86400. Nested H/LP/MIP/Work is not added twice. Reused complete baselines carry their original cost in the comparison and incur no fictitious new fee. Metered ordinary build, pure audit and delivery processes are separate. Optional work not executed is explained in the stage report.\n\n'
    body+='The source/PE, exact input and command bindings, complete entered run list, finite carriers, local semantic checks and public byte-read receipt are separate authorities. No full public semantic PASS is inferred from byte recovery. The accepted R137 recovery limitation is unchanged. This known research panel is not an independent unseen validation set.\n\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    bib=(ROOT/'results/unified_exact_round137/references.bib').read_text(encoding='utf-8-sig')
    bib+='''\n@article{AdamsSherali1990R138,
 author={Adams, Warren P. and Sherali, Hanif D.},
 title={Linearization Strategies for a Class of Zero-One Mixed Integer Programming Problems},
 journal={Operations Research}, volume={38}, number={2}, pages={217--226}, year={1990}, doi={10.1287/opre.38.2.217}}
@book{SheraliAdams1999R138,
 author={Sherali, Hanif D. and Adams, Warren P.},
 title={A Reformulation-Linearization Technique for Solving Discrete and Continuous Nonconvex Problems},
 publisher={Springer}, year={1999}, doi={10.1007/978-1-4757-4388-3}}
@article{Balas1998R138,
 author={Balas, Egon}, title={Disjunctive programming: Properties of the convex hull of feasible points},
 journal={Discrete Applied Mathematics}, volume={89}, number={1--3}, pages={3--44}, year={1998}, doi={10.1016/S0166-218X(98)00136-X}}
'''
    (OUT/'references.bib').write_text(bib,encoding='utf-8',newline='\n')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),
        references_SHA=sha(OUT/'references.bib'),R137_manuscript_unchanged=True,
        lineage='R137 maintained model/algorithm conventions; standalone incremental research section',Optimize=0))

def pdf():
    assert not budget()['unclosed'] and read(OUT/'candidate_decision.json')['study_complete']
    marker=OUT/'PDF_marker.json'
    if not marker.exists():
        script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1017.22136/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
        node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
        result=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],
            cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
        assert result.returncode==0,(result.stdout,result.stderr)
        write(marker,dict(UTC=utc(),success=True,stdout=result.stdout,successful_invocations=1))
    import round126_export as old
    source=inspect.getsource(old.export)
    substitutions=[("for name in ['model_appendix.md','algorithm_appendix.md','tables/historical_display.md']:","for name in []:"),
        ("Path(os.environ.get('ROUND126_PDF_DEST',str(OUT/'manuscript.pdf')))","OUT/'manuscript.pdf'"),
        ("Path(os.environ.get('ROUND126_PDF_RECEIPT',str(OUT/'pdf_export.json')))","OUT/'pdf_export.json'"),
        ('date=19 October 2026','date=29 October 2026'),
        ('text=landscape_tables(text)','text=keep_captions(text)'),
        (r'\usepackage{etoolbox}',r'\usepackage{etoolbox}'+'\n'+r'\usepackage{needspace}'),
        (r'\setlength{\emergencystretch}{3em}',r'\setlength{\emergencystretch}{8em}'+'\n'+r'\widowpenalty=10000\clubpenalty=10000')]
    for before,after in substitutions:
        assert source.count(before)==1,before
        source=source.replace(before,after)
    def keep_captions(value):
        return re.sub(r'(^#{2,4} [^\n]+\n\n)(?=\|)',lambda m:'\n```{=latex}\n\\Needspace{10\\baselineskip}\n```\n\n'+m[0],value,flags=re.M)
    ns=dict(vars(old),OUT=OUT,TEMP_PARENT=TEMP/'pdf',keep_captions=keep_captions)
    exec(compile(source,__file__+'::R137_lineage_increment_export','exec'),ns);ns['export']()

if __name__=='__main__':globals()[sys.argv[1]]()
