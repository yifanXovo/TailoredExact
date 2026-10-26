"""Scientific and protection closeout; delivery completion uses actual receipts."""
from round135_common import *
import collections

def protected():
    b=read(OUT/'baseline.json');checks={}
    for name,expected in b['protected_dirty'].items():
        value=sha(Path('E:/codes/ExactEBRP')/name);assert value==expected
        checks['original_dirty/'+name]=value
    for name,expected in b['protected_assets'].items():
        value=sha(name);assert value==expected;checks[name]=value
    head=git('rev-parse','HEAD',cwd=Path('E:/codes/ExactEBRP')).decode().strip()
    assert head==b['original_tree_head']
    candidate=read(OUT/'candidate_manifest.json')
    assert sha(E3)==candidate['production_PE_SHA'] and sha(DLL)==candidate['DLL_SHA']
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name
    return dict(UTC=utc(),passed=True,checks=checks,original_HEAD=head,
        candidate_PE_SHA=sha(E3),candidate_source_hashes_unchanged=True,
        default_ENS_entry_unchanged=True,old_worktrees_and_unique_raw_not_deleted=True)

def account():
    a=budget();assert not a['unclosed'] and a['G1_seconds']<=28800
    conservative=a['G1_seconds']+a['separately_reported_seconds']
    assert conservative<=28800, 'Conservative computation plus all metered postverification exceeds the hard ceiling'
    arms=read(OUT/'reports/arms.json')
    separate={}
    for method in ('S2','AP'):
        rows=[r for r in arms if r['method']==method]
        separate[method]=dict(arms=len(rows),T_production_sum=sum(r['T_produce'] for r in rows),
            T_postverification_sum=sum(r['T_verify'] for r in rows),T_total_sum=sum(r['T_total'] for r in rows))
    document={}
    for name in ('pdf_export.json','review/pdf_render_receipt.json','delivery_archive_receipt.json',
                 'public_bootstrap.json','public_restore_receipt.json','review/local_preflight.json'):
        path=OUT/name
        if path.exists():
            r=read(path);document[name]={k:r[k] for k in ('seconds','separate_document_seconds','cumulative_seconds') if k in r}
    result=dict(UTC=utc(),new_computation=a,
        conservative_computation_plus_metered_postverification_seconds=conservative,
        conservative_total_also_below_28800=True,
        complete_method_clocks=separate,document_and_delivery=document,
        production_build_and_LP_outers_charged_once=True,nested_H_LP_MIP_Work_never_added=True,
        explicit_offline_verification_segments_reported_separately=True,
        authoring_window_start=read(OUT/'document_edit_plan.json')['UTC'],
        authoring_window_end=utc(),authoring_window_overlaps_native_wait_not_exclusive_CPU_time=True,
        journal_submission_or_external_messaging=0)
    write(OUT/'resource_accounting.json',result)
    return result

def science():
    s=read(OUT/'reports/summary.json');stage=read(OUT/'stage_decision.json');d=read(OUT/'candidate_decision.json')
    assert d['study_complete'] and s['stage1']['completed']==10 and not s['stage1']['missing']
    advanced=stage.get('advanced_seed1_positions',[])
    assert s['completed']==(32 if stage['enter_stage2'] else 10+len(advanced))
    assert s['complete_pairs']*2==s['completed']
    assert not budget()['unclosed']
    arms=read(OUT/'reports/arms.json');pairs=read(OUT/'reports/pairs.json')
    assert all(r['PE_SHA']==read(OUT/'candidate_manifest.json')['production_PE_SHA'] for r in arms)
    assert all(r['T_cert'] is None for r in arms if not r['certificate'])
    assert all(r['AP_models_audited']>0 for r in arms if r['method']=='AP')
    assert all(r['AP_models_audited']==0 for r in arms if r['method']=='S2')
    counts=collections.Counter(r['method'] for r in arms if r['certificate'])
    den=collections.Counter(r['method'] for r in arms)
    text='# Round135 scientific report\n\n'
    text+='This report answers the scientific goal. Actual public recovery, PR readback and final delivery completion are recorded separately in their completed receipts. No pending delivery is represented as passed.\n\n'
    text+='## 1. Accepted S2 and finite scope\n\n'
    text+='R134 S2 is preserved: own complete H, M-B shared service states, VD-P, pair-only support, controller, physical model, numerical tolerances and native/outer/independent-zero rules are unchanged. Default-off exports are byte-identical on both inherited roots. The repository ENS-C default is unchanged. The only research variant is AP, one weighted aggregate row in the unified writer, default off. No TC, GEOM/SP grid, forced NEXT or hidden native-tree numerical engineering is reopened.\n\n'
    text+='## 2. State penalty and the two actual roots\n\n'
    text+='The cancellation identity and AP validity are proved in ap_math_and_history.md. AP and all stationwise lower bounds have the same ideal (x,P_e) projection when every local lower bound is at most phi_i, phi_i is at most the actual finite upper bound, and other uses of e depend only on weighted total P_e. The proof covers zero weights and zero residual capacity. It does not assert coordinatewise equality, VD-J equality, or compatibility with independent S e_i products. Loaded binary64 expressions and machine-precision upper-bound exceptions are explicitly distinguished from the ideal theorem.\n\n'
    for role in ('K-20-S','K-35-U'):
        r=read(OUT/'roots'/role/'LP/result.json')
        text+=f"{role}: reused S2 {r['L0_reused']:.17g}, reused IND {r['L_IND_reused']:.17g}, new AP {r['L_AP']:.17g}; AP-IND {r['delta_AP_IND']:.17g}. "
        text+=f"AP gives {r['after']['rows']} rows, {r['after']['columns']} columns and {r['after']['nonzeros']} nonzeros; LP-row insertion/update {r['construct_AP_seconds']:.6g}s, native LP {r['native_runtime']:.6g}s. Total export/process costs and quality and Start/physical-extension checks are retained; production C++ construction is included in each complete-method clock.\n\n"
    text+='The fixed-root confirmation used exactly two new continuous LP Optimize calls. Each adds only AP to the same inherited domain and reoptimizes all auxiliaries. These are numerical OPTIMAL observations, not new rational global certificates; the separate complete-method runs include their own ordinary LP and MIP calls.\n\n'
    text+='## 3. Complete algorithm, protection roles and decision\n\n'
    text+=d['study_scope_paragraph']+'\n\n'+d['paper_results_paragraph']+'\n\n'
    text+=f"Entered positions: {s['completed']}/32 registered; complete pairs {s['complete_pairs']}/16. Certificates: S2 {counts['S2']}/{den['S2']}, AP {counts['AP']}/{den['AP']}. "
    text+='All ordinary adverse and open results remain in reports/arms.csv and reports/pairs.csv. Open runs have null certification times. Complete production, required postverification and total clocks are retained, along with Work, nodes and exposed root/child/MIP/split/target costs.\n\n'
    text+='The R55 antecedent is tested VD-J, not an untried proposal: root/pilot/development were live. The old D13 300-second L0.1.0 subinterval result is a risk reference, not a new whole-method comparator. New D13 uses its exact original physical input and route horizon with current S2/AP whole-method caps. Only the later penalty-cover branch had zero live rows.\n\n'
    text+='Candidate disposition: '+d['decision']+'. '+d['paper_conclusion_paragraph']+'\n\n'
    text+='## 4. Manuscript and remaining author facts\n\n'
    text+='The full paper is edited as an academic manuscript. Its abstract centers the integrated method and strongest supported results; the main text now includes the objective-state embedding, implicit service integrality, ordered supply and support/handling arguments. Zero proof sits with termination. One evidence-version table replaces repeated chronology. Representative advantages, PS reversals, positive-objective scale and the weight experiment have substantive interpretations; complete numerical evidence, TC and historical controls remain in the supplement.\n\n'
    text+='The actual HGA-TGBC project manuscript is identified by title, Equity-aware Bike Repositioning in Station-based Bike-sharing Systems. Its model/heuristic lineage and the exact-method increment are explicit. Missing bibliographic author order, affiliations and current publication status are not invented. The remaining data-source question concerns the original capture URL/date and selection provenance of the old CITI 443-row lists; CABI and Divvy have archived request receipts. No private manuscript or foreign full text is redistributed.\n\n'
    text+='## 5. Scientific advance and smallest next work\n\n'
    text+=d['advance_assessment']+'\n\n'
    text+='The revised manuscript can be taken to advisor/coauthor discussion after actual PDF QA and independent integration. TRE has its strongest account in coupled redistribution operations and effective-weight interpretation; EJOR in the shared-state exact method, validity and complete-cost comparisons. Journal-specific author/front-matter facts remain before actual submission. The elementary AP projection explanation and two root LPs do not themselves establish a higher Operations Research contribution. Further work should follow the actual candidate decision and named generalization boundary, rather than require every instance to be fastest or reopen finished numerical engineering.\n'
    (OUT/'final_report.md').write_text(text,encoding='utf-8')
    write(OUT/'protection_science_freeze.json',protected());account()
    write(OUT/'scientific_closeout.json',dict(UTC=utc(),passed=True,completed_positions=s['completed'],
        registered_positions=32,complete_pairs=s['complete_pairs'],candidate_decision=d['decision'],
        G1_seconds=budget()['G1_seconds'],G1_limit=28800,Optimize=0,delivery_completion_not_implied=True))
    print('Scientific closeout complete; actual PDF/review/public recovery/PR receipts remain separate')
if __name__=='__main__':
    if sys.argv[1]=='protect':write(OUT/'protection_final.json',protected())
    elif sys.argv[1]=='account':account()
    else:science()
