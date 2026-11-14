"""Actual final scientific interpretation, written into the maintained components."""
from round166_common import *
PAPER=ROOT/'results/unified_exact_round137'

def finalize():
    s=read(OUT/'reports/summary.json');assert s['complete'] and s['CERT']=={'B':3,'C166':2}
    pairs=read(OUT/'reports/pairs.json');assert [p['id'] for p in pairs if p['delta_U_C166_minus_B']<-1e-7]==['R163-C35-U','R163-B35-S']
    assert all(p['delta_L_C166_minus_B']<0 for p in pairs if '35-' in p['id'])
    path=PAPER/'paper_body.md';body=path.read_text(encoding='utf-8')
    abstract='''Static bicycle redistribution must realize an equitable final inventory through routes with empty departures, prefix capacity and paid handling, including loaded returns. We develop GI-TBC, an exact method connecting shared inventory states, objective products, movement and nonzero visits with complete true-Gini interval coverage. A compact alternative preserves the joint local hull with at most five legal stock supports and a separate binary-product layer, under an explicit full-model interface condition. The historical breadth panel gives GI-TBC 9/12 certificates versus 7/12 for each compact control; a positive-resource panel gives 4/8 versus 0/8. In a new same-build six-input representation comparison, B certifies 3/6 and compact C166 2/6. C166 improves two open primal endpoints but weakens all three large-instance proof endpoints, so B remains the main method. Reconstructed physical fleets and global lower bounds also give continuous-weight quality guarantees: one fixed fleet is within an absolute objective tolerance of 1.00002e-7 throughout its covered range, while other families exhibit supported plan switches or wide unresolved bands. Two-sided route-time bounds establish strict optimal-objective improvement even for open instances. These finite, numerically qualified results distinguish information-preserving representations, complete computational value and useful bounded decisions; the controls do not establish an independent speed advantage from external interval scheduling.'''
    start=body.index('## Abstract');end=body.index('## 1. Introduction',start)
    body=body[:start]+'## Abstract\n\n'+abstract+'\n\n'+body[end:]
    marker='## 7. Conclusions and implications'
    adoption='''The complete panel supports retaining B as the uniform main method and
keeping C166 as a default-off research alternative. C166 loses C20's
certificate and has the substantive X20 certificate-cost increase. Its
C35 and B35 feasible objectives improve by about .00852312 and .01500068,
but their proof lowers weaken; on X35 both endpoints are worse. These
primal gains are retained as useful mixed evidence, without a per-input
portfolio or a single-Seed generalization. Smaller state support preserves
information at the declared interface, while its native integer search
consequences remain an empirical question.

'''
    if adoption not in body:body=body.replace(marker,adoption+marker,1)
    start=body.index(marker);end=body.index('### 7.1 Remaining scientific limits',start)
    conclusion='''## 7. Conclusions and implications

The inherited bicycle-redistribution operations and HGA-TGBC decoder lineage
provide the problem setting. GI-TBC connects inventory allocation to
objective products, movement and visits, and supplies a complete exact
method through physical embeddings and improving-region coverage. The
compact joint-state result identifies a transferable interface condition:
legal affine-piece endpoints preserve the local continuous hull, and an
independent product layer restores integer exactness. It applies standard
disjunction and product tools; it establishes neither a routing hull nor
general ideality or a capacity-independent integer encoding.

The historical breadth panel certifies 9/12 configurations versus 7/12 for
each compact control, and the positive-resource panel gives 4/8 versus
0/8. In the later six-input B/P cohort, the 3/6 versus 1/6 certificate
pattern repeats at three solver Seeds. C35 reverses its primal ordering,
all n35 observations remain open, and fixed-target diagnostics expose
incumbent deficits. E+ retains its genuine X35 proof gain without another
certificate, together with its substantive C20 cost increase. These
versioned results support finite competitiveness of the integrated method.
The selected full/root controls leave the outer controller's independent
computational value unresolved.

The new same-build representation comparison gives B 3/6 certificates and
C166 2/6. C166 reduces columns in all eight qualification LP pairs, with
unchanged common LP information, but can add rows/nonzeros and alter native
search. Two n35 primal improvements coexist with weaker proof endpoints;
X35 worsens on both sides, and X20 costs substantially more to certify.
Uniform B remains the main recommendation. The structural result and the
mixed C166 evidence remain useful without changing released defaults or
forming a best-of-two method.

Complete physical plans also turn existing runs into bounded decisions
between sampled weights. The four archive envelopes have whole-range
absolute regret upper bounds of .002356282, .000000100002, .015594269 and
.136115162. They distinguish supported component choices, stability of one
known fleet and unresolved quality. The X35 reweighting identifies a known
feasible improvement of about .0667662 over the old unit-weight incumbent,
without changing its discovery or certificate clock. All four physical
time pairs have strictly positive optimal-objective improvement bounds;
the two n35 magnitude intervals remain wide. Improved objectives can
coexist with more loaded return, as on B35, while X35 returns less stock.
These statements concern inventory-to-target ratio dispersion and the
specified objective, rather than monetary gains, demographic fairness or
causal claims about an unknown optimal route mechanism.

'''
    body=body[:start]+conclusion+body[end:]
    tail='''
The compression result leaves a specific computational question: how native
presolve, cuts and branching respond to equivalent integer extensions.
The X35 continuous-weight guarantee still has a broad quality band, while
the full/root attribution remains limited. These are separate unresolved
questions rather than consequences settled by a smaller representation.
'''
    if tail.strip() not in body:body=body.rstrip()+'\n\n'+tail.strip()+'\n'
    path.write_text(body,encoding='utf-8')
    companion=PAPER/'mathematical_analysis.md';text=companion.read_text(encoding='utf-8')
    final='''
## Completed compact-representation comparison

The sole fresh same-build Seed0 matrix completes all12 positions on six
exposed inputs. B certifies3/6 and C1662/6. All n35 runs remain OPEN;
C166 improves C35/B35 physical U by .0085231196665/.0150006843103 but has
weaker L on all three n35 inputs, and X35 has worse U as well. C20 loses
a certificate; X20's joint-CERT C166/B cost ratio is4.3487828154. B20's
1.1108187640 ratio has only.5647814283s difference and stays below the
max(10s,.1 times faster) material scale. OPEN T_cert is null.

The eight scoped LP comparisons differ by at most3.33e-16 and all new
integer/Start/type/native contracts qualify. Thus the representation result
holds in its stated interface domain, while the complete outcome is mixed.
Uniform B remains default; C166 is a distinct default-off research mode.
The primal gains are preserved rather than removed to support a negative
adoption decision. The complete endpoints and costs are in
[the six-pair table](../unified_exact_round166/reports/pairs.json).
'''
    if '## Completed compact-representation comparison' not in text:companion.write_text(text.rstrip()+'\n\n'+final.strip()+'\n',encoding='utf-8')
    decision=dict(UTC=utc(),stage='scientific artifacts complete; final independent review and delivery recorded separately',
        B_default_retained=True,C166_default=False,C166_mathematically_qualified=True,
        C166_adoption='mixed/limited complete benefits; retain structural research candidate, do not replace uniform B',
        integer_physical_projection_equal=True,common_raw_LP_projection_equal=True,
        global_embedding_condition='Every removed-state use passes through Y,M,V,G,Z; actual frozen B passes this condition.',
        generic_ideality_or_routing_hull_claim=False,arbitrary_EF_complexity_lower_bound_claim=False,
        continuous_support_max=5,integer_layer='independent inherited absolute-Y binary product, O(log C)',
        formal_summary=s,primal_improvement_inputs=['R163-C35-U','R163-B35-S'],
        n35_lower_direction='C166 weaker on all three',X35_direction='C166 worse U and L',
        C20='B CERT; C166 OPEN at equal U',X20='both CERT; C166/B T_cert=4.348782815365785; material B advantage',
        B20='both CERT;0.5647814283147454s difference below10s scale',
        diagnostic_Optimize=96,total_new_Optimize=96+s['total_native_Optimize'],
        new_complete_runs=12,new_B_C166_pairs=6,new_independent_benchmark_inputs=0,new_Seed_values=0,new_strict_B_P_pairs=0,
        parameter_analysis='four fixed families; all complete fleets; exact finite intersections; offline only',
        resource_analysis='all four nested T-pairs; positive two-sided objective-improvement intervals; n35 widths remain broad',
        OR_increment='standard tools applied to an identified joint interface, transferable conditional structure and actual complete-model integration; no general breakthrough claimed',
        measured_CPP=s['source_commit'],PE_SHA=s['PE_SHA'],released_defaults_changed=False,
        remaining_scientific_questions=['native search consequences of equivalent integer extensions','wide X35 continuous quality guarantee','incremental computational value of external interval scheduling'],
        independent_review_dispositions='review/final_review_dispositions.json',delivery_receipt='delivery_receipt.json',automatic_Round167=False)
    write(OUT/'decision.json',decision)
    print('Actual adoption judgment, abstract and conclusions written; B retained, mixed C166 gains preserved.')

if __name__=='__main__':finalize()
