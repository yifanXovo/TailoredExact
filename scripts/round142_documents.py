"""Independent incremental reading PDF, exported only after timed work is idle."""
from round142_common import *
from round142_analyze import require_idle
import inspect,re,shutil
configure()

SHORT={'K-15-S':'K15','K-20-S':'K20','K-35-U':'K35','R-B35-S-T2':'RB35-T2'}
LABEL={'CP':'Selected CP','D1':'R141 D1','base':'GI-TBC','both':'Stock','TC_STOCK':'TC+stock','TC2_STOCK':'TC2+stock'}

def fmt(v):
    if v is None:return 'open'
    if isinstance(v,float):return format(v,'.9g')
    return str(v)

def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(fmt(v) for v in r)+' |\n' for r in rows)+'\n'

def marker():
    path=OUT/'PDF_marker.json';assert not path.exists(),'One successful marker per PDF authoring operation'
    script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1017.22136/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
    node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    p=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],
        cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
    assert p.returncode==0,(p.stdout,p.stderr)
    write(path,dict(UTC=utc(),success=True,successful_invocations=1,stdout=p.stdout))

def assemble():
    require_idle();assert read(OUT/'PDF_marker.json')['success']
    decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    lp=read(OUT/'reports/LP.json');full=read(OUT/'reports/full.json');cost=read(OUT/'cost_report.json')
    body=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8-sig')
    body=body.replace('# Conditional counts and a shared Gini factor',
        '# Conditional count consistency in shared-factor proof sources',1)
    body+='\n## 8. Matched continuous source results\n\n'
    body+='The table shows numerical optimal objectives. Every inherited source row, variable, objective constant, cutoff and domain remains. C uses complete saved primal and old qualified optimum, without another Optimize. S appends four selected CP facets plus the missing opposite count range. ALL explicitly adds every propagated range and four facets per threshold. All twelve new LPs pass the unchanged 1e-6 quality gates.\n\n'
    by={(r['role'],r['side'],r['mode']):r for r in lp['positions']}
    body+=table(['Role / side','Old L','Selected L','ALL L','Selected floor'],[
        [SHORT[role]+' / '+side,by[role,side,'selected']['old_L'],by[role,side,'selected']['L'],
         by[role,side,'all']['L'],by[role,side,'selected']['floor']]
        for role in SHORT if role!='K-15-S' for side in ['low','high']])
    body+=table(['Role','Old min cover','Selected min cover','Gain','ALL - selected'],[
        [SHORT[r['role']],r['old_cover'],r['selected_cover'],r['selected_gain'],r['ALL_minus_selected']] for r in lp['covers']])
    body+='ALL requires 384--548 CP rows per source, selected only four; its further optimized gains are at roundoff scale. It is not selected for online use. The three original weak points are separated by product residuals .414570726 (K35 high), .167523020 (RB low), .228635736 (K20 low), although their average physical counts already satisfy the source range. These violations and the exact strict witness do not predict the size of an objective gain. Per-side construction, Native solve, Work, rows/nonzeros and endpoint counts are in the full precision LP CSV/JSON.\n\n'
    body+='\n## 9. Complete methods, clocks and adverse outcomes\n\n'
    body+='The only candidate is selected CP in the two R141 D1 sources. Each method pays for its own H (separate fixed seed20260626), ordinary root/lookahead, count-source construction and both proofs, validation and Native search. Primary Gurobi Seed0, Threads1 and affinity4 apply. M-B/VD-P, pair-only, AM=.08, depth8, minimum width1e-4 and AP off remain fixed. There is no per-instance product set, timed switching rule, imported diagnostic floor or extra probe. Physical route horizon and experimental cap are separate.\n\n'
    launches=[g['launch'] for g in read(OUT/'pilot_matrix.json')['groups']]
    body+=table(['Role','Stations / vehicles','Physical T s','lambda','Cap s'],[
        [SHORT[l['id']],str(l['panel']['V'])+'/'+str(l['panel']['M']),l['panel']['T_seconds'],l['panel']['lambda'],l['cap_seconds']] for l in launches])
    roles=[l['id'] for l in launches];display=[]
    for role in roles:
        for r in full['reused_arms']+full['new_arms']:
            if r['role']==role and r.get('seed',0)==0 and r['method'] in LABEL:
                # Same-PE bridges get a separate identity below.
                if r.get('batch')=='bridge':continue
                display.append(r)
    body+=table(['Role','Method','Verified U','Supported L','T cert s'],[
        [SHORT[r['role']],LABEL[r['method']],r['U'],r['L'],r['T_cert']] for r in display])
    body+=decision['complete_discussion']+'\n\n'
    body+=table(['Role / method','Produce s','Verify s','Total s','Relative gap'],[
        [SHORT[r['role']]+'/'+LABEL[r['method']],r['T_produce'],r['T_verify'],r['T_total'],r['relative_gap']] for r in full['new_arms']])
    body+='Open T_cert stays null and is displayed as open. No cap is imputed as convergence time. Signed gap, returned Native ObjVal/ObjBoundC, externally merged L, all probe/target/terminal work and nodes remain separate fields. Nested H/LP/MIP/Work is descriptive and never charged twice. Historical rows retain their original source/PE/full clocks; missing roles are not inferred.\n\n'
    body+=decision['attribution_discussion']+'\n\n'
    if full['same_PE_bridges']:
        body+=table(['Same-PE role','CP - old U','CP - old L','Produce delta s','Total delta s'],[
            [SHORT[r['role']],r['delta_U'],r['delta_L'],r['delta_T_produce'],r['delta_T_total']] for r in full['same_PE_bridges']])
    body+='\n## 10. Scope, decision and reproducibility\n\n'
    body+=decision['decision_paragraph']+'\n\n'+decision['conditional_work_discussion']+'\n\n'
    body+='Independent checks before the expensive pilot confirm CP directions/constants, loaded support and current g endpoints, full Native row readback under a single source SHA, absence from the parent/MIP and actual source-floor binding. The retained R141 physical-side, Start, cutoff-complement, source revocation and disposable-probe lifecycle checks are reused. Positive-alpha, fixed-g and tiny-coefficient fixtures avoid relying only on root alpha=0. The separate C++ switch defaults off; prior stable/research launchers and configurations retain their bytes.\n\n'
    charged=cost['experiment']['G1_seconds']
    body+=f'New charged experimental computation is {charged:.6f} seconds ({charged/3600:.6f} hours) of the 28800-second ceiling. The complete experimental outer including pure postverification is {cost["experimental_outer_including_pure_postverification_seconds"]:.6f} seconds. Qualifications, failed fixtures and all entered positive/adverse runs are included. Builds, offline analysis, documents and public I/O are separate; unmeasured interactive editing/review receives no invented timing precision.\n\n'
    body+='The fixed diagnostic carrier and inherited members, actual source/PE/DLL and hybrid compile lineage, frozen input/parameter matrices, complete returned evidence and costs are bound by manifests. This appendix is a standalone research increment; the formal R137 manuscript remains available. Local scientific validation and finite anonymous public archive/member readability are different claims. Post-PR cleanup is bounded to this round and retains unique raw/failures and necessary runtime dependencies. No merge, historical deletion or unrelated production line follows.\n\n'
    body+='The standard antecedents remain McCormick envelopes and reformulation-linearization [@mccormick1976; @AdamsSherali1990R138]; the continuous endpoint theorem is the retained R138 result, not a newly claimed general convexification principle.\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    shutil.copyfile(ROOT/'results/unified_exact_round138/references.bib',OUT/'references.bib')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),
        references_SHA=sha(OUT/'references.bib'),Optimize=0,formal_and_previous_manuscripts_unchanged=True))

def pdf():
    require_idle();assert read(OUT/'PDF_marker.json')['success']
    import round138_documents as old
    source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=31 October 2026').replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round142 independent research increment: shared count products, matched sources, full methods, decision and qualified costs')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,read=read,write=write,budget=budget,environment=environment)
    exec(compile(source,__file__+'::increment_export','exec'),ns);ns['pdf']()

if __name__=='__main__':
    if sys.argv[1]=='all':marker();assemble();pdf()
    else:globals()[sys.argv[1]]()
