"""Write scoped scientific interpretation from already sealed observations."""
from round132_common import *
import collections,math

def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n'
def fmt(x):return 'unknown' if x is None else format(x,'.12g')

def joint():
    result=read(OUT/'joint_results.json');rows=[];strict=[];numeric=[]
    for c in result['cases']:
        rows.append([c['id'],' / '.join(map(str,c['single_plans'])),c['joint_pairs'],c['threshold_ranks'],
            c['queried_directions'],c['positive_numeric_gaps'],'yes' if c['best_strict'] else 'no',
            fmt(c['full_current_micro_objective_reference']),fmt(c['full_current_micro_objective_joint']),fmt(c['current_objective_increment'])])
        if c['best_strict']:strict.append(c['id'])
        if c['best_numeric']:numeric.append(c['id'])
    complete=result['execution']=='COMPLETE_BOUNDED_TINY_STEP'
    summary=f"The preregistered complete four-station/two-vehicle study has execution status {result['execution']}. "
    summary+=f"It completed {len(result['cases'])} case records; exact full-reference strict service-coordinate witnesses were retained in {strict or 'no case'}, while numerical separation candidates were retained in {numeric or 'no case'}. "
    increments=[c['id'] for c in result['cases'] if c['current_objective_increment'] is not None and c['current_objective_increment']>1e-7]
    summary+=f"Reoptimizing the current complete micro objective after adding every enumerated joint column gives increments beyond the numerical policy in {increments or 'no case'}. "
    summary+="This is a finite tiny-domain result. A strict witness, if present, concerns the exact loaded reference matrix; a numerical candidate without a complete rational extension is not a strict projection proof. Finite no-separation or zero objective change does not establish equality of the hulls. No full-size cut or production replacement is admitted: the exact tiny support maxima do not include outside donors and receivers."
    text='# Joint quantities, ownership and resource compatibility\n\n<!-- manuscript-summary -->\n'+summary+'\n<!-- /manuscript-summary -->\n\n'
    text+='## Sets and actual reference\n\n'
    text+='Each case is a complete four-station universe, with two heterogeneous-capacity vehicles, station capacities2, target1, weight1, lambda0.15, all coordinates coincident, empty departure and loaded return. Every integral one-way service vector is enumerated from the full station options. It obeys the actual instantaneous/operation capacity, nonnegative return at mostQ, and120 times cumulative pickup at mostT. Every ordering is considered until a prefix-feasible route is found; only the first such route is retained per service vector. This is complete for the service projection, not a file listing of every route permutation. Cumulative pickup is not bounded byQ.\n\n'
    text+='P_sep is the product of these same single-vehicle convex hulls intersected with unique station service. H_joint is the convex hull of every pair of these same integer plans that obeys unique service. Their elementary inclusion H_joint subset P_sep is not claimed as new. All disjoint fleet pairs are enumerated; a restricted-column maximum is never used as a valid support upper bound.\n\n'
    text+='B_ref contains the actual frozen S2 canonical root with every variable relaxed continuously, plus the same complete single-vehicle mixing rows, R98 vehicle/state theta, all station-distinct threshold-event rank rows defined over this exact universe, and all30 IR-IN/OUT subset rows. The exact-domain event RHS can be stronger than an older necessary-travel rank; no containment with a different R_k is presumed. B_joint adds the full enumerated joint mixing extension on top of this same reference. Arbitrary noncomparison coordinates can reoptimize.\n\n'
    text+=table(['Case','Car plans','Joint pairs','Rank rows','Directions','Numeric gaps','Exact strict','Reference objective','Joint objective','Signed increment'],rows)
    text+='\n## What the evidence can establish\n\n'
    text+='For each fixed integer normal w, Psi(w) is the exact maximum over all listed joint integer pairs. A strict claim additionally requires a saved rational point satisfying every row and bound of B_ref, including each car mixture, theta, rank and IR. The saved matrix interprets the actually loaded binary64 coefficients as exact rationals; it is not a theorem about unrounded ideal coefficient matrices. Full values, matrix SHA and enumeration SHA accompany every retained strict candidate. Failure of the finite90-free-column/45-second active-basis procedure yields an explicit UNKNOWN obstacle and keeps the point numerical only.\n\n'
    text+='The eight pure-event controls precede quantity queries in each case. OPTIMAL values at most their retained exact rank plus1e-7 pass; unavailable native bounds remain UNKNOWN. Any excessive control violation or reference/joint infeasibility against the known empty fleet stops as a contradiction. It is not scored as a new inequality or negative strengthening. Full-objective reoptimization uses the same original objective before/after joint columns; it does not mistake separation of one arbitrary support point for a cost improvement. An apparent objective decrease outside1e-7 also stops for investigation.\n\n'
    for c in result['cases']:
        d=OUT/'joint'/c['id'];best=c['best_strict'] or c['best_numeric']
        if best:
            text+=f"For {c['id']}, the retained representative is direction{best['direction']}, numerical excess{fmt(best['gap'])}, exact Psi={best['Psi_exact']}, extension status `{best['proof']['status']}`. "
            if best['proof'].get('strict'):text+=f"Its exact saved lhs is {best['proof']['lhs']}. "
            else:text+=f"The unresolved obstacle is `{best['proof'].get('obstacle','no strict rational extension')}`. "
            text+=f"See `joint/{c['id']}/best_separation.json`, `B_ref_exact_matrix.json`, `enumeration.json` and the independent pure replay receipt.\n\n"
        controls=collections.Counter(x['qualification'] for x in c['event_controls'])
        scope=c['canonical_scope']
        text+=f"{c['id']} controls: {dict(controls)}. Actual canonical cutoff present={scope['actual_objective_cutoff_present']}, W present={scope['W_present']}, domain={scope['G_bounds']}; exposure is {scope['production_backend_exposure']}. "
        text+='In particular a diagnostic canonical model for a physical startup-zero case is not evidence of a production native call.\n\n'
    text+='## Historical relation and conditional stops\n\n'
    text+='R98 local theta and the current A/B rows are already included rather than credited to joint coupling. R101 rank/Hall treats event compatibility; quantity/ownership normals test what can remain beyond the exact event controls. R54 inventory-route rows also remain on both sides. R103 support functions combined only with the same independent car hulls and unique-access multipliers cannot separate a point already in that product/intersection: sum(mu)+sum(h_k(w_k-E_k^T mu)) is at least sum(w_k^T v_k) for mu>=0. A genuinely joint support maximum is different. R105–107 route-oracle/decomposition architectures are not restarted.\n\n'
    text+='The full-real-role gate is not met. A four-station support maximum cannot be transplanted to a15/20/35-station instance by removing outside suppliers or receivers. The present complete R_k is tied to the entire coincident tiny universe and small capacities; a full-universe valid support upper bound and a comparably defined reference extension are not supplied. This is a concrete unresolved interface/tractability obstacle, not evidence that all joint quantity structure is invalid. No real-role LP, separator, oracle, production cut or performance matrix is claimed from an unentered step.\n\n'
    text+=f"Measured complete E child cost is recorded in `fees/E_complete_tiny01/receipt.json` (the runner reports{result['seconds']:.6f}s; do not add nested native Runtime/Work). Enumeration and exact-basis work belong to G1 E. Execution {'completed the fixed finite search' if complete else 'hit the recorded finite budget exit; missing queries/cases are not negative observations'}. All outcomes, including zero increments and numerical-only candidates, remain in the public carrier.\n"
    (OUT/'joint_structure_note.md').write_text(text,encoding='utf-8')
    write(OUT/'conditional_step_decisions.json',dict(E_tiny_execution=result['execution'],E_real_role_steps='NOT_ADMITTED',
        E_reason='No proved same-full-universe support upper bound/interface for outside donors and receivers',
        C3='NOT_ENTERED_OPTIONAL',C3_reason='No optional extra component is needed to support the scoped frozen-method and equivalent-expression conclusions; no candidate grid or production replacement',
        production_change=False,new_roles_Seeds_or_caps=0))

if __name__=='__main__':{'joint':joint}[sys.argv[1]]()
