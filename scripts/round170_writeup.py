"""Focused manuscript/report integration from qualified data and an authored decision."""
from round170_common import *
import re
PAPER=ROOT/'results/unified_exact_round137'
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(map(str,r))+' |' for r in rows]])+'\n'
def f(x):return '-' if x is None else format(x,'.9g')
def label(a):return a['role'].split('-')[1]+'/'+str(a['Native_Seed'])+'/'+a['arm']
def main():
    arms=read(OUT/'complete_arms.json')['rows'];cost=read(OUT/'cost_report.json');dec=read(OUT/'decision.json')
    comps={k:read(OUT/f'comparison_{k}.json')['rows'] for k in ['CB','CM','BP','CP']}
    by={(a['role'],a['Native_Seed'],a['arm']):a for a in arms}
    roles=[p['id'] for p in read(OUT/'inputs_frozen.json')['roles']]
    endpoint=table(['Run: role/Seed/arm','Initial U','True U','Qualified L','Gap %','State','Process s'],
        [[label(a),f(a['initial_U']),f(a['U']),f(a['L']),f(100*a['relative_gap']),a['state'],f(a['process_outer_seconds'])] for a in arms])
    fee=table(['Run','H s','Build s','LP/MIP','Native s','Work','Nodes','Audit s'],
        [[label(a),f(a['H_seconds']),f(a['all_model_build_seconds']),f"{a['LP']}/{a['MIP']}",f(a['Native_seconds']),f(a['Work']),f(a['nodes']),f(a['audit_seconds'])] for a in arms])
    cb=table(['Role/Seed','Delta U (%)','Delta L','Delta abs. gap','C/B T_cert'],
        [[p['role'].split('-')[1]+'/'+str(p['Native_Seed']),f(p['U_difference'])+' ('+f(p['U_change_percent'])+'%)',f(p['L_difference']),f(p['absolute_gap_difference']),f(p['T_cert_ratio'])] for p in comps['CB']])
    other=table(['Role','Comparison','Delta U','Delta U %','Delta L','Delta abs. gap'],
        [[p['role'].split('-')[1],p['comparison'],f(p['U_difference']),f(p['U_change_percent']),f(p['L_difference']),f(p['absolute_gap_difference'])]
            for key in ['CM','BP','CP'] for p in comps[key]])
    mechanism=read(OUT/'mechanism_initialization.json')['rows']
    initial=table(['Role','B initial U','M initial U','C initial U','Delta restart','Delta weight'],
        [[p['role'].split('-')[1],f(p['B_initial_U']),f(p['M_initial_U']),f(p['C_initial_U']),f(p['Delta_restart']),f(p['Delta_weight'])] for p in mechanism])
    raw_qual=sum(a['certificate'] for a in arms)
    report=f"""# Round170 fixed reweighted initialization: paid confirmation

{dec['headline']}

{dec['rationale']}

Uniform GI-TBC/B remains default; C166, D167 and C169 remain default off.
The fixed candidate is evaluated on four already exposed original problems,
Native Seeds 1/2, a common 600s nominal process cap and the unchanged complete
C++ method. M and new cold P occur only on the three n35 Seed1 roles.
These are finite search-trajectory confirmations, not holdouts, new physical
inputs, independent H-randomness samples, statistical tests or long-cap claims.

## Eight new C/B pairs

{dec['CB_interpretation']}

Delta below is subject minus reference. Original U, qualified global L and
absolute gap are reported separately. The fixed descriptive materiality
scale is max(1e-6,0.001 max(abs(U_reference),1e-12)); it changes neither online
selection nor solution/certificate qualification. Ratios exist only for
jointly qualified CERT pairs. There is no composite win score.

{cb}

## Matched M and new cold P, Seed1 only

{dec['CM_interpretation']}

{initial}

{dec['BP_interpretation']}

{dec['CP_interpretation']}

{other}

M's equal extra H count is not equal work or solver time. When its initial
fleet is unchanged, an endpoint difference reflects finite search progress
and cutoff, not improved H. `mechanism_initialization.json` preserves the
same-fleet/first-model readback and actual Work/nodes. B/P alone updates the
default-method comparison; C/P is a separately named candidate comparison.
No method is assembled from other arms' U or L.

## All actual endpoints and clocks

{endpoint}

All 22 positions returned normally and passed the independent pure reader;
{raw_qual} certify and {len(arms)-raw_qual} remain OPEN. CERT uses the measured
outer process endpoint T_cert_process. OPEN process times are censored budget
endpoints, not certification or convergence times. The 600s nominal cap has
a 6s shutdown margin; actual Native requests use remaining shared time.
Tiny signed numerical gaps remain in complete_arms.json/.csv; display gaps
are nonnegative. Post-return audit is separately audit_seconds and
T_total_with_independent_audit; it is never added to T_cert_process.
Buffered/rounded logs identify no exact global first-hit time.

## Complete paid costs and evidence

{fee}

There are {cost['H_calls']} independently produced complete H calls, zero
new H-only/screen/qualification calls, and {cost['actual_Optimize']} actual
Optimize calls = {cost['LP']} LP + {cost['MIP']} MIP. Total process outer time
is {cost['process_outer_seconds']:.6f}s, Native Runtime {cost['Native_seconds']:.6f}s,
H {cost['H_seconds']:.6f}s and Work {cost['Work']:.9g}. H/Native/model/check
work is nested within each process total, never added a second time.
Tailored model builds have C++ timers; plain P has no separate build timer.
The residual includes other construction, transformations, checks, logging,
serialization and process overhead, not a fabricated pure-verifier timer.
The full process/inner audit attempt costs are in cost_report.json; all
research reading, adaptation, analysis, limited manuscript builds and agent
review remain inside the conservative 21,600s science window. Ordinary
Git/public recovery transfer is recorded separately at delivery.

Every arm uses actual measured source {MEASURED}, PE {PE_SHA}, DLL {DLL_SHA}.
Actual bytes, build records and all 254 source files were read back rather
than merely copying method_freeze. Production uses one unchanged C++ PE;
only orchestration/readers/documents are new. Actual per-Optimize settings
and linked complete LP/Start/journal records establish Seed/Threads/gaps,
original objective, physical feasibility and qualified scope. P's model
matches its inherited compact reference and reads NumStart=0; it uses custom,
plain baseline, no H/ENS/user Start/AM, and default internal heuristics.
B/M/C use their own freshly paid complete H and unchanged frontier cover.
Every new fixed H matches R169's returned fleet/order/target/work metadata.
The five-path necessary_H_complete label is not the ordinary full-arm
initialization predicate; all actual required one/three paths qualify.

## CSV, manuscript and finite decision

Eight qualified new B records and three actual new strict B/P pairs are
delivered; new physical inputs=0. Five B records explicitly remain N/A-P.
C's eight rows and M's three stay outside the default GI-TBC CSV.
The specified 118-row package was absent from the bounded local attachment
lookup. Actual master append=0: no 126-row master or missing old row is
fabricated. The UTF8-BOM 28-column increment is mergeable into the actual
byte-pinned base, and each source/metadata/run/clock reconciles explicitly.
Older 91/103-row copies stay unchanged. New pair counts are not win counts;
the per-indicator evidence above determines the actual added advantages.

{dec['decision_explanation']}

{dec['next_recommendation']}

The maintained R137 body moves the old paid table out of Conclusions and
integrates the fixed method and new endpoints into computational evidence
Section 4.6, retaining one compact main table and all old B/P/adverse evidence.
Full endpoint, cost, negative and scope information is in Supplement S170;
S169 preserves the separately identified old Seed0/300-600s study. The existing
Paquete-Stutzle aggregation/local-search attribution is retained. Finite
primal/proof tradeoffs support the bounded EJOR/TRE computational argument,
not a new OR theorem or broad generalization. The author memo changes only
the judgment affected here. Three actual independent agent reviews, targeted
PDF inspection, the new-only raw member map and public receipt are linked
through the final delivery. No merge or Round171 is started.
"""
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    (OUT/'research_decision.md').write_text('# Finite candidate decision\n\n'+dec['headline']+'\n\n'+dec['rationale']+'\n\n'+dec['decision_explanation']+'\n\n'+dec['next_recommendation']+'\n',encoding='utf-8')
    (OUT/'author_decision_memo.md').write_text('# Change to the author assessment\n\n'+dec['rationale']+'\n\n'+dec['author_assessment']+'\n',encoding='utf-8')
    supplement=subprocess.check_output(['git','show',BASE+':results/unified_exact_round137/supplement.md'],cwd=ROOT).decode('utf-8-sig')
    supplement+=f"""

## S170 Fixed paid initialization and matched cold controls

Four already exposed original problems are selected from R169's three n35
positive signals and C20 proof-cost protection. All positions use the same
measured PE, Threads=1, a 600s shared process cap and 6s shutdown margin.
Native Seeds1/2 were exposed previously; they are finite search trajectories,
not independent physical or H-randomness samples. M/P occur on n35 Seed1
only. B remains default; C166/D167/C169 remain off. The R169 Seed0 study in
S169 has separate identity and C20's different 300s cap.

**Table S170.1. All 22 qualified original-objective endpoints.** Initial U is
the arm's own selected complete-H original F; P is cold. Gap is a percentage.
Process seconds are T_cert_process only for CERT and censored endpoints for
OPEN. Exact signed gaps and binary64 values remain in the machine table.

{endpoint}

**Table S170.2. All 22 paid H/model/Native/audit expenses.** Build is the
reported tailored C++ build timer; P has no separate measured build timer.
Native/H/build overlap the process total. Audit is independent post-return
reading, reported separately from certification; its full process and any
reader failures are accounted for in the cost report.

{fee}

**Table S170.3. C/B paired differences on both Native Seeds.** U differences
and percentages use B as reference; lower and absolute gap differences remain
separate. Joint-CERT process time ratio is absent for OPEN pairs.

{cb}

**Table S170.4. Seed1 mechanism and benchmark comparisons.** Each difference
is the first arm minus the named reference. B/P updates the default-method
evidence. C/P is candidate-only and uses no across-arm endpoint splicing.
There are no M/P Seed2 observations.

{other}

**Table S170.5. Independently paid Seed1 initialization decomposition.**
Delta restart = F_B-F_M; Delta weight = F_M-F_C. Equal finite call counts
do not imply equal actual H work or equal remaining Native time.

{initial}

{dec['CB_interpretation']}

{dec['CM_interpretation']}

{dec['BP_interpretation']}

{dec['CP_interpretation']}

{dec['decision_explanation']}

The fixed materiality scale max(1e-6,0.001 max(abs(U_reference),1e-12)) is
descriptive, not significance or a qualification rule. Complete H includes
joint construction, 24 random orders, the constructed 25th seed, interroute
decoded descent and R83 physical closure. Each extra path starts from the
original input. Only original-target reverified fleet/UB/Start enters the
unchanged exact layer; no foreign lower, cutoff, domain, tree or certificate
is transferred. Inclusion of base guarantees initialization, not terminal
dominance. Full path/control/parameter/fleet/Start/coverage and cost evidence
is available in [the fixed confirmation report](https://github.com/yifanXovo/TailoredExact/blob/{BRANCH}/results/unified_exact_round170/final_report.md)
and its separate comparison CSVs. Global first-hit timing is unobserved.
"""
    (PAPER/'supplement.md').write_text(supplement,encoding='utf-8')
    body=subprocess.check_output(['git','show',BASE+':results/unified_exact_round137/paper_body.md'],cwd=ROOT).decode('utf-8-sig')
    old_tail=body.index('Objective diversification has direct local-search precedents')
    body=body[:old_tail].rstrip()+'\n\n'+dec['paper_conclusion']+'\n'
    body=re.sub(r'\bTable (7|8|9|10)\b',lambda m:'Table '+str(int(m[1])+1),body)
    compact=[]
    for role in roles:
        for seed in [1,2]:
            cells=[]
            for arm in ['B','C','M','P']:
                a=by.get((role,seed,arm));cells.append('-' if a is None else f"{a['U']:.6g}/{a['L']:.6g}"+(' C' if a['certificate'] else ''))
            compact.append([role.split('-')[1]+'/'+str(seed),*cells])
    main_table=table(['Role/Seed','B: U/L','C: U/L','M: U/L','P: U/L'],compact)
    section=f"""### 4.6 Paid objective diversification

Objective diversification has direct local-search precedents [@paquete2003two].
The fixed default-off C169 initializer retains complete base H at original
lambda and seed20260626, adds independent complete H at lambda/2 and 2lambda
with seeds20260627/28, and selects by the reverified original objective.
M instead adds two original-weight complete restarts at those same seeds.
Only original-target fleet/UB/Start transfers to unchanged B. Base inclusion
protects initialization, not equal-budget final U, L, gap or certificate time.

In the preceding exposed-input Seed0 study, all35 H paths completed and four
of six roles triggered eighteen paid B/M/C runs. C lowered all three n35 U
endpoints by about18.8%,14.5%,10.0% versus B and also beat M, while weakening
C35/X35 L and increasing C20 certificate time from211.5 to219.5s. All n35
runs stayed open. S169 preserves that historical 300/600s study separately.

The confirmation freezes that recipe on C20 and those three n35 roles,
Native Seeds1/2 and22 predeclared serial runs. Every run pays its own H,
construction, LP/MIP and checks under a common600s process cap. M and new
cold compact P are measured only on n35 Seed1. P retains its own method
definition and internal heuristics, with actual NumStart=0. The four inputs
and Seeds1/2 were exposed earlier and selected for the known positive and
protection signals; this is no held-out or new-input validation.

**Table 7. Fixed paid confirmation at 600s.** Cells are original U / qualified
global L, with C marking a qualified certificate; all other observed cells
are OPEN. A dash is an unmeasured cell, never an imported old control. B
remains default; C is the fixed research candidate. M/P have Seed1 only.

{main_table}

{dec['paper_results']}

The materiality scale max(1e-6,0.001 max(abs(U_reference),1e-12)) is descriptive;
there is no significance or population claim. Certification uses the
qualified process endpoint T_cert_process, with independent audit costs
separate. S170 gives every initial U, endpoint, signed gap, expense and
negative result. {dec['paper_decision']}

"""
    marker='## 5. Certified transportation decisions';assert marker in body
    body=body.replace(marker,section+marker,1)
    (PAPER/'paper_body.md').write_text(body,encoding='utf-8')
    appendix=subprocess.check_output(['git','show',BASE+':results/unified_exact_round137/model_and_algorithm_appendices.md'],cwd=ROOT).decode('utf-8-sig')
    appendix=appendix.replace('difference interval in Table 8;','difference interval in Table 9;')
    (PAPER/'model_and_algorithm_appendices.md').write_text(appendix,encoding='utf-8')
    write(OUT/'manuscript_change_record.json',dict(UTC=utc(),base=BASE,
        authority='results/unified_exact_round137',old_Table11_removed_from_conclusions=True,
        new_compact_paid_table=7,old_resource_weight_tables_7_to_10_renumbered_8_to_11=True,
        updated_appendix_main_table_reference=True,main_section='4.6',new_supplement='S170',
        old_S169_and_main_B_P_adverse_evidence_retained=True,whole_manuscript_rewrite=False))
    print('Wrote actual finite report/decision/memo and focused R137 Section4.6/S170 integration',flush=True)
if __name__=='__main__':main()
