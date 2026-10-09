"""Unchanged R108 inequalities evaluated over explicitly recorded fault clocks.
Never substitutes an interval endpoint for an exact observed time.
"""
import copy,itertools,math
import round108_decisions as original

def clock(a):
    t=a.get('complete_seconds')
    if original.finite(t):
        assert t>0;return [t,t]
    assert t is None and a.get('original_whole_clock_unknown') is True
    assert a.get('numerical_reader_recovery') and a.get('complete_seconds_interval')
    lo,hi=a['complete_seconds_interval']
    assert all(original.finite(v) for v in [lo,hi]) and 0<lo<=hi<a['cap_seconds']
    return [lo,hi]

def outward(lo,hi):return [math.nextafter(lo,-math.inf),math.nextafter(hi,math.inf)]

def pair(candidate,control):
    if not (candidate['certificate'] and control['certificate']) or all(original.finite(a.get('complete_seconds')) for a in [candidate,control]):
        return original.pair(candidate,control)
    ca,co=clock(candidate),clock(control);corners=[]
    for x,y in itertools.product(ca,co):
        a=copy.deepcopy(candidate);b=copy.deepcopy(control);a['complete_seconds']=x;b['complete_seconds']=y
        corners.append(original.pair(a,b))
    answer=copy.deepcopy(corners[0]);classes={v['classification'] for v in corners};severity={v['severe_regression'] for v in corners}
    invariant=len(classes)==len(severity)==1
    # The WIN and LOSS boundaries are monotone in each time coordinate,
    # including the control=300 kink. Severity is likewise monotone. Equal
    # corner outcomes therefore cover the whole closed rectangle.
    answer.update(candidate_seconds=candidate.get('complete_seconds'),control_seconds=control.get('complete_seconds'),
        candidate_seconds_interval=ca,control_seconds_interval=co,certified_time_ratio=None,
        certified_time_ratio_interval=outward(ca[0]/co[1],ca[1]/co[0]),time_improvement=None,
        time_improvement_interval=outward(co[0]-ca[1],co[1]-ca[0]),
        a_t=max(30.,.1*control['complete_seconds']) if original.finite(control.get('complete_seconds')) else None,
        a_t_interval=[max(30.,.1*co[0]),max(30.,.1*co[1])],
        entire_time_rectangle_classification_invariant=invariant,
        time_corner_outcomes=[dict(candidate_seconds=x,control_seconds=y,classification=v['classification'],severe_regression=v['severe_regression']) for (x,y),v in zip(itertools.product(ca,co),corners)],
        exact_time_or_ratio_fabricated=False,original_materiality_thresholds_unchanged=True)
    if invariant:
        answer.update(basis='both_complete_certificate_original_time_inequalities_invariant_over_recorded_interval',severe_regression_qualified=True)
    else:
        answer.update(classification='UNEVALUABLE',evaluable=False,severe_regression=None,severe_regression_qualified=False,
            possible_classifications=sorted(classes),possible_severity=sorted(severity),basis='recorded_clock_interval_crosses_original_classification_or_severity_boundary')
    return answer
