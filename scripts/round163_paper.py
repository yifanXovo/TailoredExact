"""Maintain existing manuscript sources, preserving historical tables and scope."""
from round163_common import *

PAPER=ROOT/'results/unified_exact_round137'

def preserve_write(path,text):
    old=git('show',BASE+':'+path.relative_to(ROOT).as_posix())
    text=text.replace('\r\n','\n')
    if old.count(b'\r\n')==old.count(b'\n') and b'\r\n' in old:text=text.replace('\n','\r\n')
    path.write_bytes(text.encode('utf-8'))

def preserve_existing_newlines():
    for name in ['paper_body.md','mathematical_analysis.md','supplement.md']:
        path=PAPER/name;preserve_write(path,path.read_text(encoding='utf-8-sig'))
    lineage=read(OUT/'paper_lineage.json')
    lineage['original_file_newlines_preserved']=True
    lineage['after_static_integration']={n:sha(PAPER/n) for n in lineage['before']}
    write(OUT/'paper_lineage.json',lineage)
METHOD=r'''### 3.5 A separately paid proof-only inventory source

The frozen enhancement E+ augments GI-TBC/B with an independently computed,
qualified inventory lower bound. It uses the run's own first canonical root,
actual supported inventories and valid final-stock total bounds. On an
epigraph interval \([\gamma_L,\gamma_U]\), its objective and domain are

\[
 \min_Y\;\max\{\gamma_L,G_{\rm true}(Y)\}
       +\lambda\sum_i\omega_i|Y_i/D_i-1|,
 \qquad G_{\rm true}(Y)\le\gamma_U.
\]

The lower interval endpoint constrains the epigraph; it does not impose
\(G_{\rm true}\ge\gamma_L\). At \(S=0\), \(G_{\rm true}=0\).
The inherited exact hard-total dynamic program and one uniform RN16384
producer retain their original absolute price gap, zero/fallback handling,
scope qualification and global deadline. This is an application of established
integer-inventory, normalization and proof-ledger techniques, not a new general
fractional-programming or convex-hull theorem.

Only an applicable proof ledger consumes the returned floor. Formal Native
rows, raw AM bounds, hints, Starts and branching inputs keep their intended B
design. On a common domain, independent bounds combine by maximum; complete
covering regions combine by minimum, including each source's cutoff
complement. Helper rejection supplies no new floor and retains the independent
B information. Every E+ run pays its own H, root, DP/RN work and qualification.
That cost changes remaining search time, and legitimate early certification
can change the finite trajectory. Preserving the formal expression therefore
does not guarantee identical B/E+ physical incumbents or solve times.

The C++ complete-method implementation and the historical Python inventory
helper are separately identified in the supplement. No per-instance, source,
scale, machine-speed or elapsed-time enhancement switch is used. Stable B and
the paper recommendation remain separate from released defaults.

'''

SYNTHESIS=r'''### 6.4 Structural information and complete algorithm value

The later structural studies separate five questions: exclusion of an old
point, improvement of a freely reoptimized same-scope LP, improvement of a
paid Native call, improvement of the complete own-H method, and confirmation
on configurations outside candidate development. These evidence levels are
not interchangeable. Existing STOCK certificate gains, selected reciprocal
normalization and GD improvements, and inventory-hull/proof-floor increments
remain positive evidence. Their adverse and mixed complete outcomes limit
uniform adoption; they are not erased by the stage choice.

The physical projection, an integer resource necessary domain and an inventory
necessary domain can be ordered only with a proved common objective/scope
embedding. A continuous expression replacement does not acquire an ordering
from integer equivalence alone. The retained four-station example has an exact
\(1/4\) original-objective gap on its fixed-positive-total slice even with the
complete joint service hull. At the loaded coefficient the inherited proof
also minimizes over all legal loaded-return totals; the physical problem is
not newly restricted to that slice. It distinguishes service compatibility from the integer
objective epigraph without needing a changing Gini denominator. Shared-state
movement/visit links strengthen the fractional representation; they remain
unnecessary as premises of the implicit-integrality lemma.

The full-physical shared-G completion study illustrates the same distinction
on real saved sources. Both old points fail the fixed completion diagnostic,
but RX35 freely remixes to the same qualified LP value. NB35 gains about
\(.00018725\); one projected row retains about 87% on that fixed scope, with
5348 original-column terms. Removing the complete duration rows removes the
gain conditional on the remaining Q; it does not prove time alone sufficient
or separate travel from handling. In six complete primary-role arms PC has
worse U than both fresh controls, equal proof L and no certificate. The
permitted stop leaves four positions unstarted, not four-role confirmation.

For one common global inventory relaxation and original physical problem,
\(L_I\le f_I^*\le U_I\) and \(f_I^*\le f_P^*\le U_P\) give

\[
 U_P-L_I=(U_P-f_P^*)+(f_P^*-f_I^*)+(f_I^*-L_I).
\]

Only the last term is controlled by \(U_I-L_I\). The small same-scope R156
inventory remainder limits further precision of that scalar floor, while
incumbent suboptimality may still contribute to the remaining complete gap.
Local interval/cutoff bounds require the coverage contract before any global
interpretation. A small continuous-Q increment is not an upper bound on the
integer physical gap. The supplement pins the inherited proofs, positive and
negative experiments, domains and numerical qualifications. These observations
close the current finite continuation, not every possible future structural
mechanism.

'''

def prepare():
    body=PAPER/'paper_body.md';text=body.read_text(encoding='utf-8-sig')
    assert '### 3.5 A separately paid' not in text and '### 6.4 Structural' not in text
    before={n:sha(PAPER/n) for n in ['paper_body.md','mathematical_analysis.md','supplement.md']}
    text=text.replace('## 4. Computational design',METHOD+'## 4. Computational design',1)
    text=text.replace('## 7. Conclusions and implications',SYNTHESIS+'## 7. Conclusions and implications',1)
    preserve_write(body,text)
    math=PAPER/'mathematical_analysis.md'
    detail=(OUT/'structural_synthesis.md').read_text(encoding='utf-8')
    # Add the full checkable chain to the maintained mathematical source.
    detail='\n'.join('#'+line if line.startswith('#') else line for line in detail.splitlines())
    preserve_write(math,math.read_text(encoding='utf-8-sig')+'\n\n'+detail+'\n')
    supplement=PAPER/'supplement.md'
    extra='''\n\n## Round163 structural-stage evidence and prospective protocol

The original R132/R134/R137 observations above retain their measured versions,
Seeds, budgets and denominators. They are not concatenated with Round163 as
independent samples. The frozen B/E+/P comparison has six new configurations,
18 separately paid arms, one Gurobi Seed and no result-dependent redraw or
candidate switch. It is prospective confirmation on archived-source station
data with synthetic inventories/targets/weights, not new cities or independent
observed-demand validation. All six become exposed after this study.

The [fixed recipe](../unified_exact_round163/source_recipe.json),
[six-input identities](../unified_exact_round163/input_manifest.json),
[source overlap disclosure](../unified_exact_round163/source_overlap.json) and
[18 complete commands](../unified_exact_round163/matrix_frozen.json) preserve
the pre-performance protocol. The [stage synthesis](../unified_exact_round163/structural_synthesis.md)
gives the inherited-conclusion/evidence/new-increment/inference-boundary table;
its [source map](../unified_exact_round163/historical_source_map.json) binds all
25 directly read files to fixed commits and byte hashes. The expanded
[mathematical analysis](mathematical_analysis.md) states the actual helper
epigraph objective, nested-domain premises, coverage/cutoff contracts and gap
identity. No previous producer or full historical raw carrier is replayed.

The three methods share the actually hashed R162 complete_v2 C++ executable
and Gurobi 13.0.2. E+ additionally invokes the unchanged historical Python
RN16384 inventory helper on its own canonical root; its mixed implementation
and complete paid cost are explicit. Every arm has one production deadline.
The ordinary C++ methods, helper, stable profiles, complete physical objective,
loaded-return convention and numerical qualification remain fixed.
The final tables and algorithm choice are appended only after all 18 arms
and their original-objective audits close.
'''
    preserve_write(supplement,supplement.read_text(encoding='utf-8-sig')+extra)
    write(OUT/'paper_lineage.json',dict(UTC=utc(),authority='maintained R137 Markdown body/math/supplement',base=BASE,before=before,
        after_static_integration={n:sha(PAPER/n) for n in before},old_theory_and_tables_retained=True,
        inherited_old_research_priorities_to_be_superseded_by_actual_stage_decision=True,
        existing_R137_PDF_is_historical_snapshot=True,TeX_changed=False))
    print('Maintained R137 body/math/supplement updated with checkable structural chain; final results pending.')

def supersede_historical_priorities():
    path=PAPER/'supplement.md';text=path.read_text(encoding='utf-8-sig')
    text=text.replace('## Current stage analysis','## Historical Round137 stage analysis',1)
    text=text.replace('#### Stage decision and next research',
        '#### Historical Round137 stage decision and research priorities\n\n'
        'The following three priorities are preserved historical Round137 text. '
        'They are superseded as current next-stage instructions by the single '
        'Round163 question and prerequisites in [paper body section 7.1](paper_body.md#71-one-next-research-question) '
        'and the [Round163 decision](../unified_exact_round163/decision.json).',1)
    preserve_write(path,text)

def finish():
    """Insert the closed panel and actual decision, without altering old samples."""
    from round163_report import table,fmt
    assert read(OUT/'panel_complete.json')['arms']==18
    arms=read(OUT/'reports/complete_arms.json');summary=read(OUT/'reports/summary.json')
    pairs=read(OUT/'reports/comparisons.json');decision=read(OUT/'decision.json')
    assert len(arms)==18 and decision['complete_arms']==18
    by={}
    for a in arms:by.setdefault(a['id'],{})[a['method']]=a
    part='### 6.5 Frozen prospective configuration confirmation\n\n'
    part+='The recipe and methods were committed before once-only generation; the six-input seal preceded the single tiny qualification smoke, and all 18 commands were committed before the first formal run. The balanced/surplus and shortage selections were retained regardless of observed difficulty or floor value. No performance-dependent redraw, seed grid, role-dependent algorithm or early panel stop was used. Three archived sources, two sizes and three compact/three regional selections provide finite configuration coverage. Synthetic inventories, targets and weights are not observed demand. This is prospective confirmation on archived sources, not new-city or IID validation. All six configurations are now exposed.\n\n'
    part+='Each configuration has independently paid B, E+ and cold P runs under one common PE/DLL, original physical T, actual lambda and cap. The n20 cap is 1200 s and n35 cap 2400 s, including startup and helper. P has NumStart=0; B/E+ each execute their own H. Original complete fleets are independently recomputed. Qualified proof endpoints and the inherited signed/near-zero certificate policy determine state. OPEN cap values are not certificate times.\n\n'
    part+='**Table 13. New configuration confirmation, separate from the previous panels.** Each entry is state, physical U / qualified proof L, then paid T_cert for CERT (seconds). Full binary64 values, verification costs, Work/nodes and source identities are in the supplement.\n\n'
    def entry(a):
        time_text=('; T_cert='+fmt(a['T_cert'])) if a['certificate'] else ''
        return a['state']+'; '+fmt(a['U'])+' / '+fmt(a['L'])+time_text
    part+=table(['Configuration','B','E+','P'],[[role,*[entry(v[m]) for m in ['B','Eplus','P']]] for role,v in by.items()])
    part+='The all-six certificate counts are '+', '.join(m+' '+str(summary['methods'][m]['CERT'])+'/6' for m in ['B','Eplus','P'])+'. '
    part+='B/P tests the integrated stable method; E+/B tests the enhancement and E+/P its complete competitiveness. Both-certified time ratios are conditioned on their reported intersection; every OPEN endpoint and its paid cost remains in the full panel. Single-Seed timing differences are observations, not runtime-distribution estimates. No result is formed by choosing B or E+ per configuration.\n\n'
    part+=decision['evidence_and_tradeoffs']+'\n\n'
    part+='The proof-only helper changes applicable proof information without adding its floor to Native rows or raw AM. The detailed return-time/floor/search-L ledger distinguishes dominated inventory values, zero optima, rejected sources and capacity-limited pricing. It also discloses the unchanged historical Python helper and its real paid process duration. A tighter inventory proof source is not a physical incumbent and does not imply net complete-method improvement.\n\n'
    conclusion='## 7. Conclusions and implications\n\n'
    conclusion+='The established physical equivalence, shared-state formulation and coverage proof remain the algorithmic foundation. The separately registered historical panels retain their own versions, Seeds and denominators: the twelve-input breadth panel certifies 9/12 versus P 7/12 and PS 7/12, and the independent positive-resource panel certifies 4/8 versus P 0/8 and PS 0/8. The mechanism, AM and limited Seed studies retain their adverse results and conditional interpretation; Round163 is not appended to them as an IID sample.\n\n'
    conclusion+=decision['recommendation']+'\n\n'
    conclusion+='This recommendation combines correctness and evidence completeness, certificate counts, paid times on both-certified configurations, and both endpoints plus actual costs on OPEN configurations. The frozen research configuration, paper recommendation and released main/defaults are distinct. This study changes no released default and merges no predecessor PR. The earlier R161/R162 continuous-Q continuation is closed at its tested scope. The old R156 near-tight inventory remainder does not apply to the new B35/X35 capacity-limited prices; these remain interval-valued results, without a capacity increase in this study. No claim rules out all future structural progress.\n\n'
    conclusion+='### 7.1 One next research question\n\n'+decision['single_next_question']+'\n\n'+decision['next_stage_prerequisites']+'\n\n'
    conclusion+='No next-stage producer, mechanism or parameter expansion is part of this study.\n'
    body=PAPER/'paper_body.md';text=body.read_text(encoding='utf-8-sig')
    assert text.count('## 7. Conclusions and implications')==1 and '### 6.5 Frozen prospective' not in text
    text=text.split('## 7. Conclusions and implications')[0]+part+conclusion
    abstract_add=' The separately frozen B/E+/P confirmation then completes all 18 arms on six archived-source new configurations. '+decision['abstract_sentence']
    text=text.replace('## 1. Introduction',abstract_add+'\n\n## 1. Introduction',1)
    preserve_write(body,text)
    supplement=PAPER/'supplement.md';extra='\n\n## Round163 completed configuration evidence\n\n'
    extra+='All six first-valid inputs and all 18 qualified endpoints are retained. The [complete table](../unified_exact_round163/reports/complete.csv), [binary64 endpoints](../unified_exact_round163/reports/complete_arms.json), [three comparisons](../unified_exact_round163/reports/comparisons.csv) and [helper/fee interpretation](../unified_exact_round163/final_report.md) give the full denominator, original gap policy, T_cert/T_produce/T_verify/T_total, actual Native Work/nodes, own-H and helper costs. [Stage choice](../unified_exact_round163/decision.json), [closed fees](../unified_exact_round163/cost_report.json) and [science identities](../unified_exact_round163/science_identity.json) separate the paper algorithm, frozen research implementation and released main.\n\n'
    extra+=decision['recommendation']+'\n\n'+decision['evidence_and_tradeoffs']+'\n\n'
    extra+='The [master-table receipt](../unified_exact_round163/main_table_update.json) appends only verified B/P pairs to the existing CSV copies; E+ is separately labelled throughout. The [final report](../unified_exact_round163/final_report.md) and [delivery/recovery status](../unified_exact_round163/RESUME.md) link independent review identities and the bounded new-only public recovery. Original source-row overlaps and retrospective master-table reconciliation are disclosed without changing the frozen generation or selecting on outcomes.\n\n'
    extra+='Maintained Markdown body/math/supplement are authoritative for this revision. The pre-existing R137 manuscript PDF is an earlier historical snapshot; no TeX source was substantively changed, so no updated PDF is claimed.\n'
    preserve_write(supplement,supplement.read_text(encoding='utf-8-sig')+extra)
    supersede_historical_priorities()
    lineage=read(OUT/'paper_lineage.json');lineage.update(final_UTC=utc(),complete_arms=18,configurations=6,
        old_priorities_superseded=True,single_next_question=True,after_final_integration={n:sha(PAPER/n) for n in lineage['before']})
    write(OUT/'paper_lineage.json',lineage)
    nav='The current [Round163 stage confirmation](round163_stage_confirmation.md) completes all 18 frozen B/E+/P arms on six new configurations from archived CITI/CABI/DIVVY sources. '+decision['recommendation']+' The [complete report](../results/unified_exact_round163/final_report.md) retains all certificates, two-sided endpoints, helper timing and paid costs. The maintained [paper body](../results/unified_exact_round137/paper_body.md), [mathematical analysis](../results/unified_exact_round137/mathematical_analysis.md) and [supplement](../results/unified_exact_round137/supplement.md) now integrate the structural-stage evidence and one next research question. Their Markdown sources are current; the existing R137 PDF is an earlier snapshot. Frozen research implementation and paper recommendation do not change released main/defaults.\n\n'
    for name in ['current_mainline.md','unified_exact_research_index.md','paper_review.md']:
        path=ROOT/'docs'/name;old=path.read_text(encoding='utf-8-sig')
        assert '[Round163 stage confirmation]' not in old
        first,rest=old.split('\n',1)
        if name=='unified_exact_research_index.md':rest=rest.replace('Current finite study:','Historical Round159 study:',1)
        if name=='paper_review.md':
            rest=rest.replace('Read the [complete PDF]','Historical R137 snapshot: [complete PDF]',1)
        preserve_write(path,first+'\n\n'+nav+rest.lstrip('\n'))
    guide=ROOT/'docs/round163_stage_confirmation.md'
    text=guide.read_text(encoding='utf-8-sig')
    text=text.replace('The final Round163 comparison, recommendation, costs, independent review and\ndelivery records are completed after all 18 arms close.',
        'All 18 qualified arms have closed. The [report](../results/unified_exact_round163/final_report.md), [decision](../results/unified_exact_round163/decision.json), [costs](../results/unified_exact_round163/cost_report.json) and [delivery status](../results/unified_exact_round163/RESUME.md) retain the actual findings and independent reviews. '+decision['recommendation'])
    guide.write_text(text,encoding='utf-8',newline='\n')
    print('Maintained body and supplement now contain the actual 18-arm result and one next question.')

if __name__=='__main__':globals()[sys.argv[1]]()
