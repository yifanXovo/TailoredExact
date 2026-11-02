"""A coherent research section, exported and rendered only while timing is idle."""
import inspect,re,types
from round146_common import *
SHORT={'K-20-S':'K20','K-35-U':'K35','R-X20-S-T1':'RX20-T1','R-B35-S-T2':'RB35-T2','K-15-S':'K15','R-X35-S-T2':'RX35-T2'}
LABEL={'BASE':'BASE','STOCK':'STOCK','STOCK_GD':'STOCK+GD'}
def table(headers,data):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(str(x) for x in row)+' |' for row in data])+'\n\n'
def assemble():
    assert not budget()['unclosed'];decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    full=read(OUT/'reports/full.json');lp=read(OUT/'reports/LP.json')['new_LPs'];m=read(OUT/'candidate_manifest.json');cost=read(OUT/'cost_report.json')
    text=r'''# Direct Gini deviation rows on discrete inventory states

Round146 research section, 2 November 2026. This section extends the stable
Round137 GI-TBC manuscript with a finite study of a default-off mechanism.
The complete routing model, physical objective and original proof policy
remain unchanged. All roles are known research configurations, not an
independent validation set.

## 1. From shared resource information to direct deviation rows

The earlier studies distinguish relaxation information from complete search
value. STOCK retained real certificate benefits: K15 improved from about
112.77 to 33.82 seconds, and K20 certified in about 101.64 and 90.23 seconds
on the two tested seeds while the matched BASE runs stayed open at cap1200.
The second seed has the disclosed V2 coefficient-transport identity; it is
not a pure seed-only intervention. Later count and reciprocal-normalization
studies established complementary information without uniform full-method
promotion. Those positive results remain part of the evidence.

In Round145, K35's joint NC/TS/RN LP value .234508197894 exceeded the strong
RN+STOCK+TC+TC2 value .229222197461; adding the old carrier to joint did not
raise it further. Compiled compact projections lost only about
\(2.75\times10^{-14}\) and \(1.73\times10^{-14}\) on the two tested domains.
However, four same-PE pairs and a K35 RN-P bridge did not justify adoption.
RN-JP improved K35 U against OFF but weakened its supported L/gap; old RN-P
was better at both endpoints. K20 weakened L, RX20 gave no material time
gain, and RB35 had an important U/gap regression. These complete negative
results coexist with the structural theorems and root-value preservation.

The present question is whether a classical normalized-deviation principle
can supply useful integer-objective information directly on the existing
selectors, without an RN source solve, dual projection, callback, extra
variable or new controller. Gini and Hoover/Pietra are established indices
[@ChenHooker2023, section 4.2]. No new general inequality theorem is claimed.

## 2. Validity and the state-conditioned construction

Let \(r_i=c_iY_i\ge0\), \(S=\sum_i r_i>0\), and
\(A=\sum_{i<j}|r_i-r_j|\). The project Gini is \(G=A/(nS)\), and the
original epigraph variable satisfies \(g\ge G\). For any station set J,

\[
A\ge\sum_{i\in J,j\notin J}(r_j-r_i)
=|J|S-n\sum_{i\in J}r_i.
\]

Choose the components below their normalized mean and use
\(\sum_i r_i/S=1\). This proves the classical bound

\[
G\ge\sum_i(1/n-r_i/S)_+
=\sum_i(r_i/S-1/n)_+.
\]

With global bounds \(0<S^-\le S\le S^+\), this gives the integer-valid
original-selector rows

\[
ng\ge\sum_{i,y}(1-nc_iy/S^-)_+s_{iy},
\qquad ng\ge\sum_{i,y}(nc_iy/S^+-1)_+s_{iy}.
\]

The conditional construction below strengthens the denominator bounds
without adding rows or variables beyond these two.

At a supported state \(Y_i=y\), take valid conditional bounds
\(0<D^-_{iy}\le S\le D^+_{iy}\). The physical stock interval is
\(B^-=\max(0,B-\sum_kQ_k)\le\sum_jY_j\le B\). Fix \(Y_i=y\),
start the remaining inventories at their support minima, and fill to the
smallest admissible total in increasing \(c_j\) order for the minimum.
Fill to the largest total in decreasing order for the maximum. Nonnegative
costs justify these choices. Replacing holey supports by their interval
boxes enlarges the domain, so the extrema remain safe bounds; they are not
claimed as exact discrete-support extrema.

The two direct state-conditioned deviation rows (GD-state) are

\[
ng\ge\sum_{i,y}\left(1-\frac{nc_iy}{D^-_{iy}}\right)_+s_{iy},
\qquad
ng\ge\sum_{i,y}\left(\frac{nc_iy}{D^+_{iy}}-1\right)_+s_{iy}.
\]

The low deviation increases with its denominator; the high deviation
decreases with it. At an integer point each selected state's conditional
bound applies at the same point. The coefficients lower-bound individual
Hoover deviation terms, which can be summed. This does not sum independent
full-Gini lower bounds. Conditional domains are subsets of the global
domain, so ideal conditional coefficients dominate the corresponding
global-bound coefficients termwise. An infeasible necessary state box
receives zero coefficients; this study adds no state-removal mechanism.

If the whole root domain lacks a proved positive denominator lower bound,
both rows are omitted, preserving the existing all-zero convention.
Otherwise a zero ratio is allowed and contributes one to the low deviation
at its supported states. The objective remains the original
\(g+\lambda P\), including the old penalty and constant.

## 3. Numerical transport, scope and a simple local hull closure

The production implementation uses existing checked exact dyadic arithmetic
for the actual loaded binary64 ratios, inventory units, water-fill sums and
\(nc_iy\). Lower denominators are converted downward and upper denominators
upward. The low coefficient uses an upward enclosed ratio followed by a
downward subtraction; the high coefficient uses a downward enclosed ratio
and subtraction. Tiny positive coefficients below 1e-12 are omitted, which
only relaxes the row because selectors are nonnegative. The coefficient n
on g and each feasible zero-state low coefficient one are exact.

There are at most two rows and no new variables. Root coefficients are
computed once and inherited only with identical input SHA, actual ratios
and physical stock interval and with a subset of the original selectors.
Removed selectors are identically zero, so their terms are deleted.
Expanded support or changed input/ratios/stock is rejected. No root LP,
dual or stored solution is used to generate these coefficients. The
generation timer measures the coefficient routine; complete outer clocks
also pay support parsing, file transport, Native audit and verification.

If z stations have zero inventory, zero-positive pairs give \(A\ge zS\),
and therefore \(ng\ge z=\sum_i s_{i0}\). The low GD row contains this
simple inequality. In the Round145 equal-cost binary-support family,
stock in [1,n-1] and fixed half/half selectors imply \(g\ge1/2\), which
attains that local integer Gini epigraph hull. It closes the joint value
\((3n-4)/(2n(n-1))\). The earlier strict complementarity result remains
valid, but its remaining gap does not establish a need to reconstruct a
more elaborate joint integer hull. This is not the full routing hull.

Eight exact-oracle fixtures cover heterogeneous and zero ratios, support
holes, fixed states, infeasible states/domains and all-zero domains. Actual
canonical/Native checks cover both rows, unchanged default-off matrices,
strict sub-support inheritance, changed-scope rejection, and complete
physical Starts with minimal and nonminimal g. Three affected production
translation units were rebuilt. One short complete health run and the
inherited physical/proof/lifecycle verifier qualified the production path.
Independent review corrected only an offline reader's root-file ordering;
the original helper is preserved and no solver run was repeated.

## 4. Saved-point evidence and matched optimization

The supplied preliminary attachment was unavailable locally. Existing
fixed carriers permit an exact reconstruction of the four decision-relevant
saved points, with no Optimize and no point normalization. K20 joint has
positive low/high violations .0258580381333/.0495572135569 despite zero
zero-state selector mass. K35 and RX20 joint optima satisfy both rows,
so they witness unchanged numerical optimal values on those particular
strong models; these two cells were not reoptimized. RX20's transported
compact point has violations .235260517665/.0186545799038.

A saved extension violation, exclusion of the same original point,
optimized objective increment, and complete algorithm improvement are four
different claims. Five new matched LPs retain the full original objective,
matrix, support, g bounds and cutoff, while reusing sealed baseline optima
and solutions. All use Seed0 and one thread. The table gives numerical
continuous optima, not rational certificates or Native root-after-cuts bounds.

'''
    text+=table(['Role','Carrier','Old L','With GD','Increment'],[[SHORT[r['role']],r['carrier'],f'{r["old_L"]:.9f}',f'{r["L"]:.9f}',f'{r["gain"]:.9f}'] for r in lp])
    text+='The K20 STOCK combination reaches .251016109922, above standalone GD .236010302342 and STOCK .204590439178. This motivates one uniform STOCK+GD candidate with STOCK as the complete reference. The direct rows also add optimized information beyond K20 joint and on all three BASE domains. Coefficient generation takes approximately 0.38-1.95 ms in these tests, with 97-405 added nonzeros and no paid source solve. The optional state-level Hoover extension and global/state parameter grids are unnecessary for this decision and are not opened.\n\n'
    text+='## 5. Complete same-PE experiments and the adoption decision\n\n'
    text+='Every entered method pays its own complete H (seed20260626), ordinary root/lookahead, formal search and required verification. Gurobi Seed0, Threads1, affinity4, M-B/VD-P, pair-only support, AM=.08, depth8, minimum width1e-4, AP off and the R134 proof policy remain fixed. Physical route horizons and original lambda values are distinct from experimental caps. Rows apply in formal initial LP, target and terminal models, with complete Starts and the unchanged proof reconstruction.\n\n'
    seen={}
    for path in OUT.glob('*_matrix.json'):
        matrix=read(path)
        if 'batch' not in matrix or matrix['batch'].startswith('qualification'):continue
        for g in matrix['groups']:
            l=g['launch'];seen[l['id']]=l
    text+=table(['Role','Stations/vehicles','Physical T','Lambda','Cap'],[[SHORT[k],f'{l["panel"]["V"]}/{l["panel"]["M"]}',l['panel']['T_seconds'],f'{l["panel"]["lambda"]:.10g}',l['cap_seconds']] for k,l in seen.items()])
    text+=decision['complete_discussion']+'\n\n'
    text+=table(['Role','Method','Verified U','Supported L','Gap %','T cert'],[[SHORT[a['role']],LABEL[a['method']],f'{a["U"]:.9f}',f'{a["L"]:.9f}',f'{100*a["relative_gap"]:.3f}',f'{a["T_cert"]:.2f}' if a['T_cert'] is not None else 'open'] for a in full['new_arms']])
    text+='Open certificate times stay null in the data and are displayed as open. Native returned bounds and the external supported L are separate fields. Tiny certified endpoint differences remain under the inherited proof policy; no solver tolerance is changed.\n\n'
    text+=table(['Role','Method','T produce','T verify','T total'],[[SHORT[a['role']],LABEL[a['method']],f'{a["T_produce"]:.2f}',f'{a["T_verify"]:.2f}',f'{a["T_total"]:.2f}'] for a in full['new_arms']])
    text+=table(['Role','Method','Initial LP','Root after cuts','GD NZ'],[[SHORT[a['role']],LABEL[a['method']],f'{a["initial_root_L"]:.6f}',f'{a["printed_root_after_cuts_bound"]:.5f}' if a.get('printed_root_after_cuts_bound') is not None else 'not printed',a['GD_nonzeros']] for a in full['new_arms']])
    text+='Printed root-after-cuts values have log precision. They do not equal the initial standalone LP values. Full CSV authorities retain simplex iterations, Work, nodes, splits, Native returned bounds, row sizes and verified physical-witness trajectories. The observed changes are not attributed solely to row density or initial LP strength.\n\n'
    text+=decision['historical_discussion']+'\n\n'
    text+='## 6. Cost, identity and reproducibility\n\n'
    text+=f'New experimental outer cost is {cost["charged_new_experiment_seconds"]:.6f} seconds out of 28800; {28800-cost["charged_new_experiment_seconds"]:.6f} seconds remain unused. Own H, all solves, qualifications, failures if any and necessary postverification are counted once. Nested LP/MIP runtime and Work are not added again. The five standalone LPs and one short health qualification have separate identities from the complete positions. Build cost is {cost["build_seconds_separate"]:.6f} seconds separately; pure arithmetic, authoring, PDF export and public I/O are also separate. Timed runs are serial and do not overlap compilation, PDF export or heavy I/O.\n\n'
    text+=f'Measured production source is `{m["source_commit"]}`; PE SHA256 is `{m["production_PE_SHA"]}`. Actual source/compiler/object/DLL bytes and Git EOL distinctions remain in the source and carrier manifests. The separate research entry is `scripts/paper_s2_gd.py` with `config/gi_tbc_gd_round146.json`; its default research profile selects STOCK+GD, while `--gd off` selects STOCK. The executable research switch itself defaults off. Stable R137 and all prior launchers/profiles and formal manuscript remain unchanged.\n\n'
    text+=decision['decision_discussion']+'\n\n'
    text+='This section is suitable for integration into the stable GI-TBC paper and does not add invented authorship, affiliations, funding or global fractional-integer-programming claims. Source/raw publication, public byte/member recovery and the Draft PR are separate delivery checks; public recovery performs no Optimize, compilation or commercial Native loading.\n'
    (OUT/'manuscript.md').write_text(text,encoding='utf-8',newline='\n')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),references_SHA=sha(OUT/'references.bib'),
        formal_stable_manuscript_unchanged=True,no_author_affiliation_funding_invented=True,Optimize=0,Native_load=0))
def pdf():
    assert not budget()['unclosed'] and read(OUT/'candidate_decision.json')['study_complete']
    if (OUT/'pdf_export.json').exists():
        history=read(OUT/'pdf_export_history.json') if (OUT/'pdf_export_history.json').exists() else []
        prior=dict(PDF_SHA=sha(OUT/'manuscript.pdf'),export=read(OUT/'pdf_export.json'),
            render=read(OUT/'pdf_render_manifest.json') if (OUT/'pdf_render_manifest.json').exists() else None,
            reason='Remove unnecessary contents from a short paper section and avoid a sparse final page')
        if not any(item['PDF_SHA']==prior['PDF_SHA'] for item in history):history.append(prior)
        write(OUT/'pdf_export_history.json',history)
    marker=OUT/'PDF_marker.json'
    if not marker.exists():
        script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1026.10807/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
        node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
        result=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
        assert result.returncode==0,(result.stdout,result.stderr)
        write(marker,dict(UTC=utc(),success=True,stdout=result.stdout,successful_invocations=1))
    import round138_documents as old
    source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=2 November 2026').replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round146 integrated research section: direct GD mathematics, finite LP and complete evidence, history and decision')
    toc_clause="'--toc','--toc-depth=2',"
    source=source.replace('substitutions=[',f'substitutions=[({toc_clause!r}, ""),')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,read=read,write=write,budget=budget,environment=environment)
    exec(compile(source,__file__+'::R146_export','exec'),ns);ns['pdf']()
def render():
    assert not budget()['unclosed'];import round138_pdf_qa as old
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,budget=budget,read=read,write=write,sha=sha,environment=environment)
    source=inspect.getsource(old.render).replace("dest=OUT/'qa_pages';dest.mkdir(exist_ok=False)",
        "dest=OUT/'qa_pages'/('render-'+sha(OUT/'manuscript.pdf')[:12]);dest.mkdir(parents=True,exist_ok=False)")
    exec(compile(source,__file__+'::R146_render','exec'),ns);ns['render']()
if __name__=='__main__':globals()[sys.argv[1]]()
