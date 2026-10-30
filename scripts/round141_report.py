"""Render finite scientific tables from sealed aggregates and a reviewed decision."""
from round141_common import *
from round141_analyze import ROLE_ORDER,require_idle

METHODS=['base','both','TC_STOCK','TC2_STOCK','D0','D1']
LABELS={'base':'GI-TBC','both':'STOCK','TC_STOCK':'TC+STOCK','TC2_STOCK':'TC2+STOCK','D0':'D0','D1':'D1'}

def value(x):
    if x is None:return 'unavailable'
    if isinstance(x,bool):return 'yes' if x else 'no'
    if isinstance(x,float):return format(x,'.9g')
    return str(x)

def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join(
        '| '+' | '.join(value(x).replace('|','/') for x in row)+' |\n' for row in rows)+'\n'

def selected():
    full=read(OUT/'reports/full.json');new=full['new_arms'];roles={r['role'] for r in new}
    refs=[r for r in full['reused_arms'] if r['role'] in roles]
    ordered=sorted(refs+new,key=lambda r:(r.get('seed',0),ROLE_ORDER.index(r['role']),METHODS.index(r['method'])))
    return full,new,refs,ordered

def main():
    require_idle();decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    full,new,refs,ordered=selected();b=budget();counts=[]
    for method in METHODS:
        arms=[r for r in ordered if r['method']==method and r.get('seed',0)==0]
        if arms:counts.append([LABELS[method],len(arms),sum(r['certificate'] for r in arms)])
    body='# Round141 scientific result\n\n'+decision['decision_paragraph']+'\n\n'
    body+='## What is established\n\n'
    body+='The count axis supplies new numerical information beyond a matched Gini midpoint on three diagnostic domains. Keeping parent TC/TC2 and adding conditional numerator chords raises each complete two-sided cover. Standard cardinality identities, concave chords and disjunctive formulations remain standard tools. The project-specific study connects physical threshold counts, nested support information, count-scoped evidence and a finite complete-method evaluation.\n\n'
    body+='D1 separates two actual D0 optima in the scalar projection with fractional b, yet its reoptimized common-root LP value is unchanged in all three domains. This distinguishes feasible-set separation from optimal-objective improvement. Two different floors alone are not credited as an effect. The mathematical contract and numerical precision boundaries are in mathematical_analysis.md and LP_report.md; reports/LP.csv and projection.csv retain both sides and costs.\n\n'
    body+='## Actual complete comparisons\n\n'
    body+=decision['complete_discussion']+'\n\n'
    panels={r['role']:r for r in new if r['method']=='D1' and r['seed']==0}
    body+=table(['Role','Physical T s','lambda','Experimental cap s'],[
        [r['role'],r['physical_T'],r['lambda_value'],r['cap']] for r in panels.values()])
    body+=table(['Role','Method','Seed','Verified U','Supported L','T_cert (s)'],[
        [r['role'],LABELS[r['method']],r.get('seed',0),r['U'],r['L'],r['T_cert'] if r['T_cert'] is not None else 'open'] for r in ordered])
    body+='Open certificate times are null and displayed as open. No cap is substituted for convergence. Lower U and higher L are reported separately when they disagree. New arms retain the original legacy formal_performance=false field as historical R108 metadata; their current formal scope is the preregistered full-cap research stage with qualified physical/proof/performance evidence. This does not change any raw record.\n\n'
    body+=table(['Method','Actual matched Seed0 positions','Qualified certificates'],counts)
    body+='The D0 denominator is its necessary attribution subset. It is not a second uniform full panel. The known selected configurations are not an independent holdout set; eight potential configurations share six base inputs. Only entered new positions count as new experiments. R140 has five actual TC2 configurations, and absent TC2 cells are never inferred.\n\n'
    body+='## Three comparison layers\n\n'
    body+=decision['conditional_discussion']+'\n\n'
    body+=table(['Role','D1-D0 U','D1-D0 L','D1-D0 produce s','D1-D0 total s'],[
        [r['role'],r['delta_U'],r['delta_L'],r['delta_T_produce'],r['delta_T_total']] for r in full['conditional_pairs']])
    body+='Each D0/D1 pair independently pays own H and the same selection, count links, two conditional LPs and validation. The aggregate asserts identical PE/source, physical input/objective/cap/Seed/H, root model and pivot, actual two probe matrices and exact pair floors. Only the final floor changes. D0 versus TC2 measures the combination of links, binary, probes and common floor. D1 versus GI-TBC, with STOCK and old TC references, measures full-method value. Old references retain their original source/PE; cross-version reuse is not a same-PE causal intervention.\n\n'
    body+='Both-certificate time differences are substantive under the inherited threshold max(10 seconds, 10% of the smaller clock); producer and total clocks remain separate. Endpoint differences on open runs are not converted into convergence speedups. reports/full.json retains every matched delta and identity check.\n\n'
    body+='## Paid online mechanism\n\n'+decision['mechanism_discussion']+'\n\n'
    body+=table(['Role','Mode/Seed','Root LP s','Probe total s','Target s','Terminal s','Terminal Work'],[
        [r['role'],r['method']+'/'+str(r['seed']),r['root_LP_seconds'],r['probe_total_seconds'],r['target_seconds'],r['terminal_seconds'],r['terminal_Work']] for r in new])
    body+='Root/probe/target/terminal solver clocks and Work explain observed paths but are not added again to complete outer clocks. Probe total includes its construction/solve/qualification; its construction component and actual Native solver runtime remain separate fields in reports/new_arms.csv. No unobserved claim of branching on b or additive allocation of search time is made.\n\n'
    body+=table(['Role','Mode/Seed','Native return ObjVal','Native return ObjBoundC','External merged L'],[
        [r['role'],r['method']+'/'+str(r['seed']),r['terminal_native_return_ObjVal'],r['terminal_native_return_ObjBoundC'],r['external_merged_final_L']] for r in new])
    body+='The exact Native quality attributes above are distinct from rounded log summaries and the physically replayed objective U. Each terminal bound is rebuilt through the qualified evidence journal and complete original-domain Gini cover. Count-local LP bounds are never inserted as Gini frontier children or promoted singly to global evidence.\n\n'
    body+='## Complete clocks and gaps for every new formal position\n\n'
    body+=table(['Role','Mode/Seed','Signed U-L','Relative gap','Produce s','Verify s','Total s'],[
        [r['role'],r['method']+'/'+str(r['seed']),r['signed_gap'],r['relative_gap'],r['T_produce'],r['T_verify'],r['T_total']] for r in new])
    body+='The producer is sealed once; the mandatory pure reader closes its verification cost. Later independent reviews and supplemental floor-to-call checks are separately measured. Online proof construction and validation are included in production. Qualification-only cap90 outcomes remain outside performance counts.\n\n'
    body+='## Conditional work and stopping decision\n\n'+decision['conditional_work_discussion']+'\n\n'
    body+='## Qualification, fixes and independent review\n\n'
    body+='Finite writer/Start/evidence checks cover both binary endpoints with positive and negative floor deltas and nonzero ObjCon, both physical Start sides, same/opposite-side witnesses, source revocation, invalid scope, one contained successor and default-off reset semantics. Actual Native row/type/priority/ObjCon reads cover each newly used artifact. Source/runtime lineage binds the controlled five-unit hybrid build and final tree-only repair; it is not described as a fresh recompilation of every source.\n\n'
    body+='The first cap90 K20 v5 producer returned with disposable count probes failing the pre-existing LP-to-integer type-restoration lifecycle check. Its sealed raw/cost are preserved as an implementation failure, not a mathematical failure or performance sample. V6 restores original types under the normal lifecycle then immediately discards each probe; it does not reuse a probe state or add Optimize. Two healthy cap90 qualifications then passed (K20 D1, K15 D0). Early selector/init/reset/readback/writer defects and their finite preflight snapshots are retained. Pure-reader repairs after a sealed qualification have zero Optimize and never rerun that producer.\n\n'
    body+=table(['Qualification','Mode','U','L','Certificate','Produce s','Verify s'],[
        [r['role'],r['method'],r['U'],r['L'],r['certificate'],r['T_produce'],r['T_verify']] for r in full['qualification']])
    body+='The unusually long K20 qualification verification includes the finite pure-reader correction/wait and is excluded from full-performance timing. Superseded unstarted qualification identities remain listed as NOT_STARTED; they are not invented observations. All entered failures and all ordinary adverse/open results are retained. Independent math/writer preflight, production admissions, LP integration, selection and final integration remain distinct records in review/.\n\n'
    body+='## Cost and reproducibility\n\n'
    body+=f'New charged experimental computation is {b["G1_seconds"]:.6f} seconds ({b["G1_seconds"]/3600:.6f} hours), below the 36000-second ceiling. Qualification and failed experimental attempts are included. cost_report.json also reports the stricter sum of complete experimental outers including pure postverification, plus separately measured builds, offline checks, manuscript/PDF and public I/O. Nested H/LP/MIP/Work is not charged twice. Old references keep their original clocks without fictitious new fees. Interactive reading, editing and Git receive no invented time precision.\n\n'
    body+='The governing goal, actual matrices, candidate source/PE/DLL and source domains are bound by candidate_manifest.json, each frozen matrix/identity and the canonical model SHA. Explicit solver Seed0, single thread, serial timing and affinity mask4 apply to every primary call; H seed is separately 20260626. The ordinary carrier is BOTH stock + old TC + TC2, with M-B/VD-P, pair-only, AM=.08, depth8, minimum width1e-4 and AP off. No instance-specific mechanism, size switch, elapsed-time switch, cross-method proof/solution/Start or native-tree import is used.\n\n'
    body+='Fixed old science and necessary member hashes are referenced without reopening old public acceptance or recovering all history. The supplied same-objective K35 return-upper-bound witness supersedes R140\'s earlier priority suggestion; its precise numerical and historical limits are in mathematical_analysis.md. No new return-product benchmark was opened.\n\n'
    body+='## Stable entry and one next question\n\n'
    body+='Stable R137 GI-TBC and the R138/R139/R140 launchers and profiles remain byte-identical to the verified R140 base. The default-off C++ switch has a separate explicit research entry; no promotion changes the stable algorithm. All new build/raw/temp/restore assets are under ExactEBRP-work. Original user content, old rounds, unique raw/failures and necessary PE/DLL remain protected.\n\n'
    body+=decision['remaining_question']+'\n\n'
    body+='Scientific completion, normal push/English Draft PR, actual base/head/draft readback, bounded new-carrier public byte/member check and post-PR current-round cleanup are separate facts. RESUME.md records delivery as it actually occurs; public byte readability is not a solver or semantic replay.\n'
    (OUT/'final_report.md').write_text(body,encoding='utf-8',newline='\n')
    write(OUT/'report_assembly.json',dict(UTC=utc(),report_SHA=sha(OUT/'final_report.md'),
        full_aggregate_SHA=sha(OUT/'reports/full.json'),decision_SHA=sha(OUT/'candidate_decision.json'),Optimize=0))

if __name__=='__main__':main()
