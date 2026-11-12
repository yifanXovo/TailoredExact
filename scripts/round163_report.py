"""Render the completed finite evidence and explicit human-readable stage choice."""
from round163_common import *
import collections

def fmt(v):
    if v is None:return ''
    if isinstance(v,bool):return str(v)
    if isinstance(v,float):return format(v,'.10g')
    return str(v)

def table(headers,records):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),
        *['| '+' | '.join(fmt(v).replace('|','/') for v in row)+' |' for row in records]])+'\n\n'

def costs():
    b=budget();assert not b['unclosed']
    fees=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        r=read(p);launch=read(p.with_name('launch.json'))
        fees.append(dict(label=p.parent.name,kind=launch['kind'],exit_code=r['exit_code'],outer_seconds=r['outer_seconds'],
            scientific_seconds=r['G1_seconds'],timeout=r['timeout'],receipt_SHA256=sha(p)))
    io_records=[]
    for name,key in [('infra/plot_dependency_install.json','ordinary_dependency_IO_seconds'),
                     ('table_authoring.json','ordinary_document_IO_seconds'),('main_table_update.json','ordinary_append_IO_seconds'),
                     ('carrier_manifest.json','packaging_IO_seconds'),('public_restore_receipt.json','recovery_IO_seconds')]:
        p=OUT/name
        if p.exists():io_records.append(dict(receipt=name,seconds=read(p)[key],scientific_seconds=0))
    value=dict(UTC=utc(),total_limit_seconds=72000,scientific_seconds=b['G1_seconds'],scientific_hours=b['G1_seconds']/3600,
        remaining_seconds=b['remaining_G1_seconds'],by_category=b['by_category'],fees=fees,
        separate_engineering_or_IO_seconds=b['separately_reported_seconds']+sum(r['seconds'] for r in io_records),
        separately_observed_engineering_IO=io_records,
        initial_preparation=read(OUT/'infra/external_costs.json'),all_fees_closed=True,
        nominal_production_seconds=32400,conservative_panel_reservation_seconds=48600,
        original_stage_capacities=dict(qualification=3600,panel_and_validation=57600,final_readback=3600,repair=7200),
        diagnostic_H_helper_Runtime_Work_not_added_twice=True,no_new_production_compilation=True,
        policy='outer fees include all current scientific work and retained technical failures; nominal windows are not solve/certificate times')
    write(OUT/'cost_report.json',value)
    return value

def run():
    assert read(OUT/'panel_complete.json')['arms']==18
    arms=read(OUT/'reports/complete_arms.json');pairs=read(OUT/'reports/comparisons.json')
    summary=read(OUT/'reports/summary.json');decision=read(OUT/'decision.json');cost=costs()
    assert len(arms)==18 and decision['complete_arms']==18 and decision['configurations']==6
    text='# Round163: frozen complete methods and the research-stage choice\n\n'
    text+=decision['recommendation']+'\n\n'+decision['evidence_and_tradeoffs']+'\n\n'
    text+='The complete denominator is six new configurations and 18 qualified arms. All method results remain in the comparison. These are prospective configurations on archived CITI/CABI/DIVVY sources with synthetic demand fields, one Gurobi Seed, two sizes and three compact/three regional selections. They are not new cities, IID population samples, or a factorial identification of city/size/geometry effects. All six are now exposed.\n\n'
    text+='The recipe, once-only inputs, history-manifest canonical keys and 18 commands were sealed before formal performance. The primary CSV was located and its new IDs checked before the panel; its additional row-to-input reconciliation was inspected after the first arm had begun and completed in the final bounded readback. This ordering deviation is disclosed: that particular crosswalk is not represented as preregistered. It finds no base/configuration collision, does not change the frozen inputs or methods, and triggers no redraw. The retained R57 ephemeral structural-pilot metadata is separately checked and its source-row overlap disclosed.\n\n'
    text+='## Complete physical and proof endpoints\n\n'
    text+='Display values are rounded; the JSON/CSV reports retain authoritative binary64 values and the original signed/near-zero gap qualification. L is the final qualified proof lower, not an unqualified raw Native claim. OPEN T_cert is blank. A cap is not a convergence time.\n\n'
    text+='Under the inherited paid closure policy, a qualified CERT uses its fully paid producer-close T_produce as T_cert. An unobserved first Native witness or hypothetical earlier proof time is not substituted. Required after-the-fact verification and the small reader/exit trailer remain in T_verify and T_total.\n\n'
    text+='The raw reused reader retains historical compatibility labels formal_performance=false and not_holdout=true. Those labels are preserved, not used to classify Round163 novelty. Round163 formal-panel status follows its own committed recipe/input/matrix admission and verified performance_eligible/implementation/evidence flags. All six were new at that freeze and are exposed after this study.\n\n'
    text+=table(['Configuration','Method','State','Physical U','Raw search L','Proof L','Original gap %','T_cert','T_produce','T_verify','T_total'],[
        [a['id'],a['method'],a['state'],a['U'],a['raw_search_L'],a['L'],None if a['relative_gap'] is None else 100*a['relative_gap'],
         a['T_cert'],a['T_produce'],a['T_verify'],a['T_total']] for a in arms])
    text+='![All qualified endpoints](figures/prospective_endpoints.png)\n\n'
    text+='## Three complete-method questions\n\n'
    text+='B/P assesses the stable complete package. E+/B assesses the net effect and paid cost of the sole enhancement. E+/P assesses the enhanced complete package. No per-instance best-of-B/E+ method is constructed. B/P gains are not attributed solely to GI splits; the existing P/PS and conditional mechanism controls retain their original identities and denominators.\n\n'
    for name,values in summary['pairs'].items():
        x,y=name.split('_vs_');current=[p for p in pairs if p['candidate']==x and p['control']==y]
        text+=f'### {x} versus {y}\n\n'
        text+=f'All-six certificate counts are {values["candidate_CERT"]}/6 and {values["control_CERT"]}/6. The both-certified time-ratio subset has {values["joint_CERT"]} configurations; the ratios below condition on that intersection. No OPEN observation is dropped to make a full-panel time superiority claim. Single-Seed small timing differences do not establish stable speed advantages.\n\n'
        text+=table(['Configuration','States','delta U','delta proof L','delta total cost','Paid T_cert ratio (joint CERT only)'],[
            [p['id'],p['candidate_state']+'/'+p['control_state'],p['delta_U'],p['delta_proof_L'],p['delta_T_total'],p['paid_cert_ratio']] for p in current])
    text+='## What the inventory producer actually contributed\n\n'
    enhanced=[a for a in arms if a['method']=='Eplus']
    text+=table(['Configuration','Helper paid s','Return on C++ clock s','Floor','Inventory value upper','Price decision','Native price statuses','Price width','Final raw search L','Final proof L','Available mid-proof gain','Endpoint explanation'],[
        [a['id'],a['helper_seconds'],a.get('helper_first_return_cpp_seconds'),a['helper_floor'],a.get('helper_inventory_upper'),
         a.get('helper_price_decision'),a.get('helper_native_statuses'),a.get('helper_inventory_width'),a['raw_search_L'],a['L'],a.get('max_available_mid_proof_increment_over_logged_raw_search'),a['helper_effect']] for a in enhanced])
    text+='The original helper decision field and optimization status are different observations. Status2 denotes the native optimizer\'s OPTIMAL return under its original requested tolerances; status8 denotes NODE_LIMIT. The B35 and X35 prices both stop at RN16384, with inventory intervals about .0143871 and .0229556 wide. Their remaining price uncertainty is not the tiny same-scope remainder of the old R156 RX35 study. B35\'s returned floor is below its final search bound, but its inventory upper is above that search bound, so this result does not prove all further pricing information useless. X35\'s floor raises final proof L while remaining short of both its own inventory upper and physical U. No capacity increase or second pricing design is tried here.\n\n'
    text+='Helper return placement is reconstructed from the process phase ledger and the actual remaining-deadline/process-duration receipt. The helper executes in its own first canonical-root construction, before the first formal LP Optimize. The unchanged implementation checks its separate proof ledger at outer checkpoints before selection, after solveLp and at final closeout. There is no separate first-application timestamp or continuously updated proof-floor callback trace. A mid-proof gain therefore means qualified available floor information above a logged raw-search bound; it is not claimed as continuous Native adoption, does not rewrite raw AM and cannot backdate a certificate. A tight inventory upper below final search L also limits any further precision benefit from that same scoped scalar floor. Inventory uppers never become physical fleet U. Zero optima, unavailable floors, solved prices and capacity-limited prices retain separate dispositions.\n\n'
    text+='## Native work, startup and complete paid costs\n\n'
    text+=table(['Configuration','Method','Native Work','Native nodes','Native calls','Startup reported s','Helper process s','Outer scientific fee s'],[
        [a['id'],a['method'],a['Native_Work'],a['Native_nodes'],a['Native_calls'],a['H_seconds'],a['helper_seconds'],a['scientific_outer_seconds']] for a in arms])
    text+='Native Work/nodes use inherited result counters, with individual Optimize ledger diagnostics retained separately. P has cold NumStart=0, MIPFocus=0/Cuts=-1/Presolve=-1 and requested gaps0; it receives no H or cross-arm Start. B/E+ independently complete and pay their own H with seed20260626. Actual call settings, original compact references/types/objectives, full fleet checks and complete scope/coverage audits remain bound to each arm.\n\n'
    text+='The same R162 complete_v2 C++ PE and Gurobi13.0.2 DLL serve all methods. E+ pays the unchanged historical Python helper with RN16384, original absolute price gap1e-4 and the original global-deadline/DP/fallback contract. This is explicitly a mixed C++/Python enhancement, with no new algorithm core. R138–162 noncandidate mechanisms stay off.\n\n'
    text+=f'The closed scientific charge is **{cost["scientific_seconds"]:.9f} / 72000 seconds** ({cost["scientific_hours"]:.6f} h). Failed qualification and reader repair costs are retained. Per-arm outer fees pay startup/import, H/helper, model creation, Native calls, validation, trailers and observed exits; nested Runtime/Work are not added again. Initial metadata/history work has a separately disclosed conservative enclosing preparation charge. Ordinary documentation, packaging and public recovery I/O are separately recorded.\n\n'
    text+='## Structural interpretation and the single next question\n\n'
    text+='The [structural synthesis](structural_synthesis.md) connects original physical/integer equivalence, inventory/resource/physical scopes, the epigraph-interval objective, cutoff/coverage composition, proof-only placement and five evidence levels. Its [fixed source map](historical_source_map.json) retains positive as well as negative historical results. R156 inventory precision does not allocate the residual complete gap entirely to physical coupling; incumbent suboptimality remains possible. R162 continuous-Q gain is not an upper bound on the integer physical gap. These are scoped explanations using existing proofs and standard identities, not new general theorems.\n\n'
    text+=decision['single_next_question']+'\n\n'+decision['next_stage_prerequisites']+'\n\n'
    text+='No next-stage solve, mechanism, seed or parameter grid is launched. The paper recommendation, frozen research configuration and released main identity are recorded separately. Stable defaults are not changed and no earlier PR is merged.\n\n'
    text+='## Evidence and delivery\n\n'
    text+='[Goal](goal.md), [method/dependency freeze](method_freeze.json), [recipe](source_recipe.json), [input manifest](input_manifest.json), [full actual argv matrix](matrix_frozen.json), [qualification](qualification/result.json), [all endpoints](reports/complete_arms.json), [all comparisons](reports/comparisons.json), [costs](cost_report.json), [decision](decision.json), [main CSV write receipt](main_table_update.json), [recovery scope](reproducibility.md) and [live delivery status](RESUME.md) give the auditable chain. Independent reviewer identities/findings and the actual Open Draft PR/public byte-recovery/cleanup receipts are linked from the final delivery record after those steps occur.\n'
    (OUT/'final_report.md').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps(dict(report=str(OUT/'final_report.md'),scientific_seconds=cost['scientific_seconds'])))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='costs':costs()
    else:run()
