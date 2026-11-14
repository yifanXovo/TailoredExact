"""Insert the completed paired evidence into current maintained paper components."""
from round166_common import *
import csv
from fractions import Fraction
from decimal import Decimal,localcontext

PAPER=ROOT/'results/unified_exact_round137'
def num(value,digits=9):return '' if value is None else format(value,f'.{digits}g')
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(str(v) for v in row)+' |' for row in rows]])+'\n'
def endpoint(a):return a['state']+'; '+num(a['U'])+' / '+num(a['L'])
def decimal_value(integer,places):
    scale=10**places;return str(integer//scale)+'.'+str(integer%scale).zfill(places)
def upper_bound(exact,digits=12):
    value=Fraction(exact);assert value>0
    with localcontext() as context:
        context.prec=80;exponent=(Decimal(value.numerator)/Decimal(value.denominator)).adjusted()
    places=max(0,digits-1-exponent);scaled=value*10**places
    integer=-(-scaled.numerator//scaled.denominator)
    return decimal_value(integer,places) if places else str(integer)
def resource_display(r,places=10):
    scale=10**places;low=Fraction(r['lower_exact'])*scale;high=Fraction(r['upper_exact'])*scale
    a=low.numerator//low.denominator;b=-(-high.numerator//high.denominator)
    return [decimal_value(a,places),decimal_value(b,places),decimal_value(b-a,places)]

def result_text():
    s=read(OUT/'reports/summary.json');assert s['complete']
    arms=read(OUT/'reports/complete_arms.json');pairs=read(OUT/'reports/pairs.json');metrics=read(OUT/'reports/runtime_metrics.json')
    lp=read(OUT/'qualification/LP_pairs.json');mb={(a['id'],a['method']):a for a in metrics};ab={(a['id'],a['method']):a for a in arms}
    body=PAPER/'paper_body.md';raw=body.read_text(encoding='utf-8');assert '### 6.5 Compact representation' not in raw
    results=[]
    for p in pairs:
        b,c=ab[p['id'],'B'],ab[p['id'],'C166']
        results.append([p['id'].replace('R163-',''),endpoint(b),endpoint(c),num(b['T_produce'],6)+' / '+num(c['T_produce'],6)])
    joint=[p for p in pairs if p['joint_CERT']]
    ratios='; '.join(p['id'].replace('R163-','')+': '+num(p['C166_over_B_T_cert'],5)+(' (substantive)' if p['substantive_difference'] else ' (below the substantive scale)') for p in joint)
    section='''### 6.5 Compact representation and complete costs

The separately named C166 replaces only the shared-state representation in
Section 3.1.1. Six exposed inputs are compared once at Seed0, with fresh B
controls from the same new executable. Each arm independently pays its own
complete startup; offline parameter fleets and bounds enter neither method.
The original 1200 s n20 and 2400 s n35 caps, one thread, native defaults,
requested gaps 0 and complete B lifecycle are common.

Eight same-scope qualification LP pairs cover all six roots and two fixed
children. Their largest signed objective difference in absolute value is
3.33e-16, consistent with the proved common raw LP projection. Columns fall
in every pair, but rows and nonzeros can increase after retaining the exact
bit layer. The supplement reports all sizes and pre-native construction
pipeline costs. A smaller representation gives no root-bound improvement
and need not improve native search.

**Table 16. Same-build complete B/C166 comparison on the six exposed inputs.**
Entries give qualified state and physical U / global L. The final column is
T_produce for B / C166, in seconds, including startup and close. It is a
certificate time only for a CERT entry; OPEN has null T_cert. Individual
post-verification costs and full-precision endpoints are in the supplement.

'''+table(['Input','B: state; U / L','C166: state; U / L','Paid production B / C166 (s)'],results)+f'''
B certifies {s['CERT']['B']}/6 and C166 certifies {s['CERT']['C166']}/6.
The joint-CERT denominator is {s['joint_CERT_pairs']}/6; only those pairs
have certificate-time ratios C166/B: {ratios}.
The predeclared material-difference scale is max(10 s, 0.1 times the faster
certificate time). Native Runtime, Work and node counts describe nested
work within the paid clock and are not added to it. All open/adverse
endpoints remain in the table. This is one representation comparison on
previously exposed inputs, with no new B/P test or independent Seed claim.

'''
    xb,xc=mb['R163-X20-S','B'],mb['R163-X20-S','C166']
    assert all(mb[p['id'],'B']['AM_action_sequence']==mb[p['id'],'C166']['AM_action_sequence'] for p in pairs if ab[p['id'],'B']['V']==20)
    section+=f'''The three n20 pairs have the same recorded AM action sequences and
numerically equal initial raw LP values. On X20, accumulated native Runtime
is {xb['native_runtime']:.3f} s for B and {xc['native_runtime']:.3f} s for C166,
Work is {xb['native_work']:.3f} versus {xc['native_work']:.3f}, and returned
nodes are {xb['native_nodes']:.0f} versus {xc['native_nodes']:.0f}. Accumulated
writer time is {xb['writer_build_seconds']:.3f} s versus {xc['writer_build_seconds']:.3f} s.
The extra paid time is almost entirely inside native optimization. This
observes the cost difference without identifying a particular presolve,
cut or branching cause. Native MIP root processing can exploit the
different integer extensions despite equal raw LP projections. Once own
incumbents differ, cutoffs and reached paths may differ as well; the full
comparison includes those consequences of the representation.

'''
    body_updated=raw.replace('## 7. Conclusions and implications',section+'## 7. Conclusions and implications',1)

    supplement=PAPER/'supplement.md';raw=supplement.read_text(encoding='utf-8');assert '## Round166 compact representation' not in raw
    text='''
## Round166 compact representation and certified decisions

The new study changes the common inventory representation while retaining
the complete GI-TBC/B algorithm, own H, physical rows, e epigraph and native
parameters. Its mathematical object and exactness conditions appear in
Appendix A.9; the full constructive proof, counterexamples and symbolic
size formulas are in [compression_theory.md](../unified_exact_round166/compression_theory.md).
It uses standard disjunction and product tools. C166 is default off and is
never relabelled as B. Historical measurements retain their original source
and executable identities.

### Qualification and actual matrix sizes

The C++ qualification has 96 actual Optimize calls within 539.080771 s:
64 local fixed-objective LPs, 16 paired full-model LPs, 8 boundary/tiny calls
and 8 nonzero complete-controller calls. Independent zero controllers,
finite exact enumeration, algebra and export/readers add zero calls. The
nonzero tiny optimum has inventory(1,1), one unit returned loaded, objective
.15 and an interior non-breakpoint donor stock. Complete semantic Starts,
LP-to-MIP type recovery, original rows/objective and incompatible-mode
rejection are checked. Two reader failures retain their healthy raw runs;
only the readers are repaired. The diagnostic and formal costs are separate.

The eight LP pairs below use identical offline fixture incumbents/cutoffs
within each pair. These fixtures enter no formal startup. "Build" is the
qualification driver's pre-native pipeline from input/parent parsing and
physical verification through writing the canonical model, not an isolated
writer microbenchmark. Counts describe the emitted full model, before
solver cuts; binary counts are the declared integer model types before
relaxing the qualification LP.

'''
    text+=table(['Scope','B LP','C166−B LP','B cols / C166','B binary / C166','B rows / C166','B nnz / C166','Build B / C166 (s)'],[
        [q['id'].replace('R163-',''),num(q['B']['objective']),num(q['signed_LP_delta'],4),
         str(q['B']['columns'])+' / '+str(q['C166']['columns']),str(q['B']['binaries'])+' / '+str(q['C166']['binaries']),
         str(q['B']['rows'])+' / '+str(q['C166']['rows']),str(q['B']['nonzeros'])+' / '+str(q['C166']['nonzeros']),
         num(q['B']['build_seconds'],5)+' / '+num(q['C166']['build_seconds'],5)] for q in lp])
    text+='''
### All twelve complete endpoints and costs

The order was frozen before the first launch and alternates the first
method by input, independently of historical performance. All twelve
positions finish with qualified numerical endpoints. T_cert is empty for
OPEN; T_produce and T_verify retain their original meanings. Same-input
own-H semantic and fleet hashes agree, with each run paying independently.

'''
    text+=table(['Position / input','Method','State','U','L','Signed U−L','T_cert (s)','T_produce (s)','T_verify (s)','Native calls'],[
        [str(a['position'])+' / '+a['id'].replace('R163-',''),a['method'],a['state'],num(a['U'],12),num(a['L'],12),num(a['signed_gap'],6),
         num(a['T_cert'],8) if a['T_cert'] is not None else '—',num(a['T_produce'],8),num(a['T_verify'],7),a['native_Optimize']] for a in arms])
    text+='''
The next table is explanatory accounting inside those same paid clocks.
"Writer" and "read" are accumulated canonical writer and native model-read
seconds over the actual reached path, whose number of models can change.
Runtime, Work and nodes sum returned native calls. These nested quantities
are never added to T_produce/T_verify as extra scientific fees.

'''
    text+=table(['Input','Method','H (s)','Writer (s)','Read (s)','Native Runtime (s)','Native Work','Native nodes'],[
        [a['id'].replace('R163-',''),a['method'],num(a['H_seconds'],6),num(a['writer_build_seconds'],7),num(a['native_model_read_seconds'],6),
         num(a['native_runtime'],9),num(a['native_work'],10),num(a['native_nodes'],12)] for a in metrics])
    text+='''
The first continuous canonical LP below is distinct from the first Native
MIP root after integer presolve. The latter is transcribed at the log's
printed precision and is not used as a qualified global bound. Its presolved
size/relaxation can differ between integer encodings with the same original
continuous projection. An absent root line is retained as absent. AM actions
are the actual decision sequence, not a claim that equal configured policy
must realize equal paths.

'''
    root_rows=[]
    for a in metrics:
        first=a['first_MIP'];root=first['root_relaxation'] if first else None;presolved=first['presolved_model'] if first else None
        root_rows.append([a['id'].replace('R163-',''),a['method'],num(a['first_LP_lower'],10),
            num(root['objective'],8) if root else '—',
            ' / '.join(str(presolved[k]) for k in ['rows','columns','nonzeros']) if presolved else '—',
            ', '.join(a['AM_action_sequence']) or '—'])
    text+=table(['Input','Method','First raw LP','First MIP root (log)','Presolved rows / cols / nnz','AM sequence'],root_rows)
    text+=f'''
There are {s['joint_CERT_pairs']} joint-CERT pairs. Their C166/B time ratios
are {ratios}. The other pairs carry no certificate-time ratio. Aggregate
T_produce is {s['method_produce_seconds']['B']:.6f} s for B and
{s['method_produce_seconds']['C166']:.6f} s for C166; separate T_verify is
{s['method_verify_seconds']['B']:.6f} s and{s['method_verify_seconds']['C166']:.6f} s.
The fresh-wrapper outer total is {s['actual_wrapper_outer_seconds']:.6f} s;
its small management difference from summed produce/verify remains charged.
Reservations of 25200 s and watchdog settings are not reported as consumed costs.

'''
    text+='''### Continuous-weight archive and two-sided resource value

All 50 complete fleet records are recovered and physically checked: 32 weight
observations and 24 resource observations with six shared records. The
four families preserve the exact physical domain and normalized weight
vector. Every source owner, dominated fleet, original objective and clock
remains available. Archive improvement is offline and supplies no free
formal Start, bound or cutoff. Main Section 5.3 and Appendix A.10 explain
the concavity/finite-intersection argument and safety margins.

'''
    envelope=read(OUT/'analysis/parameter_envelopes.json')['families']
    text+=table(['Family','Actual covered rho (display)','Runs / distinct lines / supported','Max archive regret upper','Best fixed-plan regret upper'],[
        [f['family'],num(f['rho_range'][0]['value'],12)+' to '+num(f['rho_range'][1]['value'],12),
         str(f['records'])+' / '+str(f['unique_component_lines'])+' / '+str(len(f['supported'])),
         upper_bound(f['worst_gap']['gap']['exact']),upper_bound(f['best_fixed']['gap']['exact'])] for f in envelope])
    resource=read(OUT/'analysis/resource_intervals.json')
    text+='\nThe parameter regret bounds above are rounded upward. The resource intervals below use qualified global lowers reduced by 1e-7 and exact feasible objectives increased by 1e-12, then round endpoints outward to ten decimal places. Width is the displayed interval width; exact rational arithmetic and original source endpoints remain in the machine-readable data.\n\n'
    text+=table(['Pair / T1→T2 (s)','Safe improvement lower','Safe improvement upper','Displayed width'],[
        [r['base']+' / '+str(r['T1'])+'→'+str(r['T2']),*resource_display(r)] for r in resource])
    op_rows=[]
    for r in resource:
        a,b=r['operations_T1'],r['operations_T2']
        def totals(o):
            return o['pickups'],o['drops'],o['returns'],o['total_inventory']
        x,y=totals(a),totals(b)
        op_rows.append([r['base'],*[str(x[i])+'→'+str(y[i]) for i in range(4)]])
    text+='\n'+table(['Pair','Pickup units','Drop units','Loaded return units','Final station inventory'],op_rows)
    text+='''
All four larger-horizon witnesses improve both G and normalized penalty.
B35's returned stock rises from 2 to 3 while X35 falls from 1 to 0. More pickup and a lower
objective therefore do not imply less loaded return. Full route-level
travel/handling/unloading, prefix loads, inventory distribution and duration
utilization remain in the complete archive. These are physical descriptions,
not proofs of a binding optimal time constraint or causal mechanism.

The existing high-weight X35 fleet has feasible objective.3365058164688021
at the original unit-weight coordinate, versus.40327199886285475 for the old
unit-weight fleet, a known feasible improvement.06676618239405259. This
changes no historical incumbent or certificate clock. The broad X35
continuous quality band remains an explicit limitation.

### Current source, reproduction and CSV identity

The same-build source is 0298dd45fbc3645af927c4a4dd1d43ecbdb567a9;
candidate/build identities, frozen commands and DLL hashes are in the
[candidate manifest](../unified_exact_round166/candidate_manifest.json).
All formal positions, full-precision pairs and explanatory metrics are in
the [result directory](../unified_exact_round166/reports/summary.json).
The [reproduction entry](../unified_exact_round166/reproducibility.md)
and new-only member map preserve complete fleets, journals, matrices,
Starts and failures without redistributing commercial dependencies or the
private antecedent draft.

The 106-row requested master is absent from the bounded entry search.
The local 103-row, 28-column GB18030 copy remains unchanged. Six same-build
B control records are supplied in a separate 28-column N/A-P increment with
run/source/build mapping; all P numeric fields are empty. C166 has six
variant records only. Thus this study adds 12 complete runs, six B/C166
pairs, zero independent benchmark inputs, zero Seed values, zero strict
B/P pairs and zero new B/P wins. The two synthetic diagnostic fixtures are
not benchmark inputs. [CSV reconciliation](../unified_exact_round166/CSV_reconciliation.json).
'''
    body.write_text(body_updated,encoding='utf-8')
    supplement.write_text(raw.rstrip()+'\n\n'+text.strip()+'\n',encoding='utf-8')
    write(OUT/'result_text_receipt.json',dict(UTC=utc(),Optimize=0,full_results=bind(OUT/'reports/complete_arms.json'),
        summary=bind(OUT/'reports/summary.json'),components=[bind(body),bind(supplement)],generator=bind(Path(__file__))))
    print('Complete twelve-arm evidence inserted into the sole maintained main/supplement.')

if __name__=='__main__':result_text()
