"""Maintain the R127 reading source with one bounded R128 results section."""
from round128_common import *
import csv,copy,inspect
import round126_export as inherited_export

def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n'
def fmt(x):return 'open' if x is None else f'{x:.3f}'

def documents():
    summary=read(OUT/'stratified_summary.json');decision=read(OUT/'scientific_decision.json');manifest=read(OUT/'experiment_manifest.json')
    assert summary['actual_formal_arms']==16 and summary['typed_pairs']==17
    assert (OUT/'review/final_independent_review.md').is_file(),'finish the separate final review before document authoring'
    arms=[]
    for g in manifest['groups']:arms.extend(read(OUT/g['name']/'reconstructed.json')['arms'])
    with (OUT/'pairs.csv').open(newline='',encoding='utf-8-sig') as f:pairs=list(csv.DictReader(f))
    with (OUT/'mechanism_costs.csv').open(newline='',encoding='utf-8-sig') as f:costs=list(csv.DictReader(f))
    differences=read(OUT/'actual_method_differences.json')['records'];same_roots=all(d['component_interpretation_eligible'] for d in differences)
    lookup={(a['id'],a['seed'],a['method']):a for a in arms}
    cost_lookup={(c['id'],int(c['seed']),c['method']):c for c in costs}
    observed_cost='All three Seed0 MB arms actually pay one root LP, two child LPs and one terminal MIP; only K1 adds one child-bound-target MIP. No NEXT call or split occurs. Each MD-R pays exactly its root LP and root MIP. '
    for seed in [0,1]:
        a=cost_lookup['SC-B20-S',seed,'MB'];b=cost_lookup['SC-B20-S',seed,'MS2']
        observed_cost+=f"At K2 Seed{seed}, MB/MS2 native MIP seconds are {float(a['MIP_native_seconds']):.3f}/{float(b['MIP_native_seconds']):.3f}, work is {float(a['MIP_native_work']):.3f}/{float(b['MIP_native_work']):.3f}, and nodes are {int(float(a['native_nodes']))}/{int(float(b['native_nodes']))}. Model generation plus native read costs are {float(a['model_generation_seconds'])+float(a['native_model_read_seconds']):.3f}/{float(b['model_generation_seconds'])+float(b['native_model_read_seconds']):.3f} seconds; Start checks/submission cost {float(a['Start_precheck_submission_seconds']):.4f}/{float(b['Start_precheck_submission_seconds']):.4f} seconds. "
    observed_cost+='Thus the K2 difference mainly accompanies changed MIP work rather than fixed row-writing cost; even the node-count direction differs between Seeds. The observed MB/MS2 root LP bounds agree within 1e-12 on every role/Seed. This finite root observation does not prove global redundancy of the deleted rows. Native Runtime is nested solver work, not certification time. Missing compact modeling subclocks remain explicitly unavailable rather than inferred from the clock remainder.'
    core_rows=[]
    for g in manifest['groups'][:3]:
        p=g['role'];aa={a['method']:a for a in arms if a['id']==p['id'] and a['seed']==0}
        split=next(c['split_count'] for c in costs if c['id']==p['id'] and c['seed']=='0' and c['method']=='MB')
        core_rows.append([p['id'],*[fmt(aa[m]['T_cert']) for m in ['P','MB','MD-R','MS2']],split])
    support_rows=[]
    for p in manifest['groups'][:2]:
        for seed in [0,1]:
            a=lookup[p['role']['id'],seed,'MB'];b=lookup[p['role']['id'],seed,'MS2']
            d=next(r for r in pairs if r['id']==a['id'] and int(r['seed'])==seed and r['left']=='MB' and r['right']=='MS2')
            saving=a['T_cert']-b['T_cert'] if a['T_cert'] is not None and b['T_cert'] is not None else None
            support_rows.append([a['id'],seed,fmt(a['T_cert']),fmt(b['T_cert']),fmt(saving) if saving is not None else 'N/A',d['direction']])
    core_table=table(['Known role, Seed0','P T_cert','MB T_cert','MD-R T_cert','MS2 T_cert','MB splits'],core_rows)
    support_table=table(['Known role','Seed','MB T_cert','MS2 T_cert','MS2 saving (s)','MB/MS2 direction'],support_rows)
    labels={'BOTH_CERTIFIED':'both certified','LEFT_ONLY_CERTIFIED':'left only certified','RIGHT_ONLY_CERTIFIED':'right only certified','BOTH_OPEN':'both open','UNEVALUABLE':'unevaluable'}
    counts=table(['Comparison, core Seed0','Typed statuses','Directions'],[[k,'; '.join(f'{labels[x]}: {n}' for x,n in v['classes'].items()),'; '.join(f'{x}: {n}' for x,n in v['directions'].items())] for k,v in summary['core_by_comparison'].items()])
    section=r'''### 6.8 Inclusive-root control and a bounded support Seed check (Round128)

Round128 follows the separately preserved PARTIAL Round127 study. It evaluates MD-R (inclusive-root control v1), a newly corrected research control, rather than relabelling the three unstarted historical MD positions. Frozen M-B / GI-TBC remains the sole proposed method; P-GRB remains the primary benchmark. One separately sealed E2 build supplies all 16 formal arms: twelve Seed0 arms on the same three known research roles, followed by only MB/MS2 on K1 and K2 at Seed1. These yield 15 core typed comparisons and two additional support comparisons, not 17 independent trials or five distinct problems. Each Seed has one matched observation per role. E1 Seed1 times are historical context, never same-build comparators.

The old named penalty-closure shortcut can write \(0\le-1\) at an equal-cutoff lower bound. A legal empty-stock two-station fleet at \(T=60\) has \(F=U_0=.3\) and violates that shortcut. On an actual interval \(I=[a,b]\), suppose the cutoff domain supports \(F(x)\ge L_a:=a+\lambda\underline P\). The complement has \(F(x)>c\), so coverage of the two domains gives the regional bound

\[
B_I=\min\{L_a,c\}.
\]

This minimum follows from coverage; it is not numerical clipping. If \(L_a>c\), the inclusive cutoff domain is empty, subject to investigating any contradicting known witness first. At \(L_a=c\), strict improvement is excluded but an equal-\(c\) physical solution may remain. When \(c-10^{-9}\le L_a<c\), the directly supported bound remains \(L_a\); it is not exact \(c\) and does not rule out every arbitrarily small improvement. The shortcut is therefore an encoding of proof/control closure rather than an ordinary valid inequality for every non-strict cutoff solution. This finite counterexample does not itself revoke every frozen M-B numerical result. In the three saved R127 core MB call histories, none of the nine actual matrices contains the shortcut.

MD-R suppresses only that semantically marked pseudo-infeasibility row, in both shared and fallback emission paths. It retains the physical model, all valid domains and strengthening, \(P\ge\underline P\), the same complete independently paid H, and fixed own-\(U_0\) root \(I_0=[0,\min\{U_0,(n-1)/n\}]\) with \(F_{model}\le U_0\) and the original \(n=1\) convention. Before LP, its own entire physical fleet is mapped and checked against actual columns, original types, bounds, every row and objective. It then pays one complete root LP, restores integer VTypes and submits the complete legal own Start to one complete root MIP. It has no child LP, target handoff, split or root rebuild. The original startup-zero policy is retained. A numerical relevance threshold cannot waive the nonzero two-call obligation; TIME_LIMIT/INTERRUPTED cannot become native optimality. Raw signed-gap and full physical/source/return/coverage checks remain, without a new analytic certificate or rational error claim. Finite native boundary, nonempty-fleet, open-return and full E1/E2 model/H/parameter bridges precede the E2 seal.

**Table R128.1. All core Seed0 certification times (seconds).** Open entries have null T_cert in the authority, not the cap or a native Runtime substituted as certification time.

'''+core_table+'''
Every formal arm independently pays its entire method. T_produce includes admission, H where applicable, modeling, LP/MIP, Start checks and required output; T_verify and T_total remain separate. Only final qualified certificates receive T_cert=T_produce. Actual same-H action/fleet, initial U0, root scope and complete matrix differences are retained in the current evidence. '''+('All prescribed component comparisons pass that finite eligibility check. ' if same_roots else 'Some comparisons lack pure component eligibility; their complete-method results remain but their component attribution is restricted. ')+'''The per-arm call counts distinguish actual splits, child probes, target calls and terminal calls. An observed absence of splits restricts the outer-control interpretation to the exposed probing, target handoff and scheduling work; it cannot demonstrate multi-leaf decomposition speedup.

**Table R128.2. The complete same-E2 two-Seed support observations (seconds).** A positive MS2 saving means MB takes longer. Directions use unrounded complete certification time and certification priority.

'''+support_table+'''
MS2 deletes only three-station support cover/conditional-handling rows. Pair rows, ordered supply, enumeration order and the shared 50000 cap remain; the three roles' 1120, 2660 and 21420 candidates do not bind that cap. K3's endpoint and certification risks remain visible in Table R128.1 and the complete endpoint authority. Deleting rows need not improve MIP work monotonically, and the same native Seed does not force identical search paths. Fixed modeling/Start cost and actual MIP work are reported separately rather than attributing every elapsed-time difference to strengthening. Two Seed observations on known roles do not establish general statistical stability.

'''+observed_cost+'''

The complete core comparisons are:

'''+counts+'''
The default compact benchmark is newly paid in E2 at Seed0. No old E1 P time is borrowed for the additional support observations. The earlier six-configuration training choice q2 and its adverse held-out PT result remain in Section 6.7: PT certifies 0/3 versus default P's 1/3 in that separate E1 study. Round128 adds no tuning, tiny rerun, evaluation input or longer window, and does not establish superiority over the strongest possible tuned compact baseline. Artificial boundary fixtures are separately identified qualification work.

The bounded stage decision is `'''+decision['tag']+'`. '+decision['rationale']+'\n\n'+decision['next_priority']+'\n\n'
    parent=ROOT/'results/unified_exact_round127';main=(parent/'manuscript.md').read_text(encoding='utf-8-sig')
    main=main.replace('Round127 v3 complete integrated-diagnostics reading draft, 21 October 2026. R126 results below retain their historical scope.','Round128 inclusive-root and support reading draft, 22 October 2026. R126/R127 results below retain their historical scope.')
    assert main.count('## 7. Extended endpoint evidence')==1
    main=main.replace('## 7. Extended endpoint evidence',section+'## 7. Extended endpoint evidence',1)
    abstract_note='\n\nRound128 separately reports the corrected inclusive-root and fixed support panel in Section 6.8. Its execution is '+summary['execution']+'; the bounded decision is `'+decision['tag']+'`. The three original Round127 MD arms remain unstarted, and no research control replaces the frozen paper method.\n'
    main=main.replace('\n## 1. Introduction',abstract_note+'\n## 1. Introduction',1)
    old='The single next priority is substantive review of that MD specification; no follow-up algorithm or enlarged experiment is executed here.'
    main=main.replace(old,'That remains the historical Round127 disposition. Section 6.8 supplies the separately qualified Round128 revision and all its fixed observations; it does not rewrite those blocked entries. The current priority is substantive review of the single unexecuted uniform triple-support simplification design in Section 6.8. The frozen full M-B remains the sole paper method.')
    main=main.replace('the remaining specification decision must not be hidden by wins elsewhere.','that historical specification issue is addressed by the new separately identified MD-R contract in Section 6.8, while its original blocked results remain unchanged.')
    main=main.replace('The unchanged mathematical appendices retain the complete R125 derivations and declared numerical-closure distinction.','The maintained mathematical appendices retain the complete R125 derivations and declared numerical-closure distinction; the Round128 clarification and separate research-control note are labelled explicitly.')
    (OUT/'manuscript.md').write_text(main,encoding='utf-8')
    clarification=r'''Round128 clarification (the frozen ordinary rule is unchanged): if the actual cutoff-domain bound is \(L_a=\alpha+\lambda\underline P\), its unconditional regional bound is \(\min\{L_a,c\}\) by coverage with the cutoff complement. \(L_a>c\) excludes the inclusive cutoff domain; \(L_a=c\) permits equality and excludes only strict improvement. For \(c-10^{-9}\le L_a<c\), the raw supported bound remains \(L_a\) and does not rule out every arbitrarily small improvement. The impossible-row shortcut is not a physical embedding inequality for all \(F\le c\). A known witness contradicting its alleged own-domain bound takes priority for investigation. The separately defined MD-R omits only this named shortcut and checks its own Start against the inclusive root; no frozen production numerical policy is upgraded by that control.'''+ '\n\n'
    model=(parent/'model_appendix.md').read_text(encoding='utf-8-sig')
    assert model.count('### A.5.7 Scalar objective')==1
    model=model.replace('### A.5.7 Scalar objective',clarification+'### A.5.7 Scalar objective',1)
    (OUT/'model_appendix.md').write_text(model,encoding='utf-8')
    algorithm=(parent/'algorithm_appendix.md').read_text(encoding='utf-8-sig')
    algorithm+='\n\n## B.12 Separately identified inclusive-root research control (Round128)\n\nMD-R version 1 is a research ablation, not another proposed algorithm. Section 6.8 and the root contract define its same-H inclusive domain, semantic shortcut omission, mandatory actual own-Start pre-LP check, one LP plus one integer MIP, fixed cutoff and complete native optimal-root return obligation. It retains the physical and signed numerical evidence policy. TIME_LIMIT/INTERRUPTED may yield a qualified open endpoint with null T_cert; a near-equal bound alone cannot satisfy its missing optimal-return obligation. Its extra checks and complete costs are paid. These control-specific guards leave the frozen ordinary procedure and the historical evidence in this appendix unchanged.\n'
    (OUT/'algorithm_appendix.md').write_text(algorithm,encoding='utf-8')
    shutil.copyfile(parent/'references.bib',OUT/'references.bib')
    historical='results/unified_exact_round127/tables/historical_display.md';dest=OUT/'tables/historical_display.md';dest.parent.mkdir(exist_ok=True)
    dest.write_bytes(git('show',BASE+':'+historical))
    write(OUT/'manuscript_lineage.json',dict(parent='Round127 complete reading source',parent_SHA=sha(parent/'manuscript.md'),
        changes=['one Section 6.8 with actual fixed results','abstract and historical-priority clarification','A.5.6 bounded mathematical clarification','B.12 research-control contract'],
        R125_model_and_cuts_derivations_retained=True,R127_Seed_tiny_PT_positive_negative_tables_retained=True,
        original_MD_unstarted_status_unchanged=True,historical_tables_byte_SHA=sha(dest)))
    all_arm_table=table(['Role','Seed','Method','Certified','T_produce','T_cert','U','L'],[[a['id'],a['seed'],a['method'],a['certificate'],fmt(a['T_produce']),fmt(a['T_cert']),f'{a["U"]:.12g}',f'{a["L"]:.12g}'] for a in arms])
    pair_table=table(['Role','Seed','Comparison','Typed status','Direction'],[[r['id'],r['seed'],r['left']+'/'+r['right'],r['classification'],r['direction']] for r in pairs])
    report='# Round128 final report\n\nExecution: **'+summary['execution']+'**. Scientific judgment: **'+decision['tag']+'**.\n\n'+decision['rationale']+'\n\n'
    report+='The sole paper method remains frozen M-B / GI-TBC; P-GRB remains the primary benchmark and historical ENS-C defaults remain. R127 is still PARTIAL with its three original MD arms unstarted. MD-R is the explicitly revised inclusive-root control, not a retroactive historical completion.\n\n'
    report+='## Contract and qualification\n\nThe named pseudo-infeasibility shortcut is suppressed only for MD-R in both emitters; all other valid rows/domains remain. Complete native Start and physical replay, finite boundaries (including U0=3e-9), actual open return, and small/medium E1/E2 full model/H/settings bridges pass. The separate executor found and checked the MD-R-only relevance, pre-LP, deadline and native-return corrections; the failed preliminary Start-counter gate is retained. The three R127 core MB histories contain no sentinel in their nine saved actual matrices. No blanket historical revocation or full rational-matrix theorem is claimed.\n\n'
    report+='The separate final executor independently recomputed all 17 typed directions and their denominators from retained receipts, checked null uncertified T_cert and same-build identity, and inspected actual H/root/exposure plus representative complete MD-R Start/native-chain, boundary deletion, MS2 deletion and nonempty-fleet physical evidence. The precise finite scope and observations are in review/final_independent_review.md; this is not external replication or a rational proof of all matrices.\n\n'
    report+='## D and support evidence\n\n'+core_table+'\n'+support_table+'\nActual same-H actions/fleet, initial scope, root differences and exposure eligibility are in actual_method_differences.json. Cost records retain probes, targets, splits, nodes, LP/MIP, modeling/Start and the three clocks. An absent split limits D attribution to exposed control scheduling. Definition-level legality is not a performance win. K3 open or adverse evidence is retained without replacement; same-Seed search paths need not be identical.\n\n'+observed_cost+'\n\n'
    report+='## Benchmark and complete fixed observations\n\n'+counts+'\nThere are 16 arms, 17 typed shared-arm comparisons and three distinct known inputs. Only K1/K2 MB/MS2 have the second Seed; neither repeat is a new input or an independent extra benchmark. All times below are rounded for display; directions use the full-precision authority, and open T_cert is null. Prior PT 0/3 versus P 1/3, tiny 10 Win/2 Lose, and all other R127 outcomes remain in the manuscript.\n\n'+all_arm_table+'\n'+pair_table
    report+='\n## Scope, fees and sole next priority\n\n'+decision['next_priority']+'\n\nNo additional confirmation, tuning, evaluation input, Seed beyond the fixed panel, or longer cap was executed. Artificial boundary fixtures remain qualification work. No normal formal result was retried. E2 PE SHA256: '+read(OUT/'E2_frozen.json')['PE_SHA']+'. All formal methods share that PE and the original Gurobi 13.0.2 DLL. Full-precision arms/pairs, support and mechanism costs are the authorities. Current fee closure, public recovery and safe owned cleanup are recorded separately in resource_accounting.json and the actual delivery receipts; native nested seconds are never added again.\n'
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    print(json.dumps(dict(documents_written=True,execution=summary['execution'],decision=decision['tag'],formal_arms=16,pairs=17)))

def pdf():
    def current_layout(text):
        # The two small new six-column tables fit portrait; retain the inherited
        # landscape treatment of every historical table unchanged.
        import re
        saved=[]
        def hold(match):
            saved.append(match.group(0));return f'ROUND128PORTRAITTABLE{len(saved)-1}TOKEN'
        pattern=r'^\*\*Table R128\.[12][^\n]*\n\n^\|[^\n]*(?:\n\|[^\n]*)*'
        value=re.sub(pattern,hold,text,flags=re.M);assert len(saved)==2
        value=inherited_export.landscape_tables(value)
        for n,block in enumerate(saved):value=value.replace(f'ROUND128PORTRAITTABLE{n}TOKEN',block)
        return value
    namespace=dict(vars(inherited_export),OUT=OUT,TEMP_PARENT=TEMP/'pdf',landscape_tables=current_layout)
    source=inspect.getsource(inherited_export.export).replace('date=19 October 2026','date=22 October 2026').replace('ROUND126_PDF_','ROUND128_PDF_')
    exec(compile(source,__file__+'::maintained_reading_export','exec'),namespace);namespace['export']()

if __name__=='__main__':{'documents':documents,'pdf':pdf}[sys.argv[1]]()
