"""Fixed-dual conditional penalty products using exact binary64 Fractions."""
from fractions import Fraction as F
from round150_common import *


def down(value):
    value = F(value)
    out = float(value)
    if F(out)>value:
        out = math.nextafter(out, -math.inf)
    assert F(out)<=value
    return out


def up(value):
    value = F(value)
    out = float(value)
    if F(out)<value:
        out = math.nextafter(out, math.inf)
    assert F(out)>=value
    return out


def conditional(arithmetic):
    """One dual, no per-state reoptimization; exact prefix/suffix leave-one-out."""
    tick = time.perf_counter()
    scope = arithmetic['scope']
    mu, nu = F(arithmetic['mu']), F(arithmetic['nu'])
    assert mu>=0 and nu>=0
    a = nu-mu
    sites = scope['stations']
    minima = []
    for s in sites:
        c, w, lo, hi = map(F, [s['c'], s['omega'], s['lo'], s['hi']])
        assert w>=0 and lo<=hi
        points = [lo, hi]
        if c and lo<=1/c<=hi:
            points.append(1/c)
        minima.append(min(w*abs(c*z-1)+a*z for z in points))
    prefix = [F(0)]
    for value in minima:
        prefix.append(prefix[-1]+value)
    suffix = [F(0)]*(len(sites)+1)
    for j in range(len(sites)-1,-1,-1):
        suffix[j] = suffix[j+1]+minima[j]
    resource = mu*F(scope['Bminus'])-nu*F(scope['B'])
    d = resource+prefix[-1]
    assert F(arithmetic['dual_lower'])<=d
    p0, beta0, cutoff = map(F, [arithmetic['penalty_lower'], arithmetic['beta'], scope['cutoff']])
    rows, states, station_minima = [], [], []
    for j, s in enumerate(sites):
        c, w = F(s['c']), F(s['omega'])
        leave = resource+prefix[j]+suffix[j+1]
        station_minima.append(dict(i=s['i'], m_exact=str(minima[j]), leave_one_out_exact=str(leave)))
        for y in s['support']:
            h = w*abs(c*F(y)-1)
            delta = h+a*y-minima[j]
            diy = leave+h+a*y
            assert delta>=0 and diy==d+delta
            pd = max(float(p0), 0., down(diy))
            desired = min(beta0, cutoff-F(pd))
            beta = min(float(beta0), up(desired))
            assert F(beta)>=desired and beta<=float(beta0)
            emitted, reason = True, 'strictly_tighter_state_product_upper'
            if beta>=float(beta0):
                emitted, reason = False, 'no_tightening_of_old_uniform_beta'
            elif 0<abs(beta)<1e-12:
                emitted, reason = False, 'omit_entire_row_for_existing_tiny_coefficient_transport'
            rowname = f'r150_CPF_{s["i"]}_{y}'
            if emitted:
                terms = {f'state_g_{s["i"]}_{y}':1.}
                if beta:
                    terms[f'state_{s["i"]}_{y}'] = -beta
                rows.append(dict(name=rowname, sense='<', rhs=0., terms=terms))
            states.append(dict(i=s['i'], y=y, h_exact=str(h), delta_exact=str(delta),
                conditional_dual_exact=str(diy), conditional_dual_down=down(diy),
                penalty_lower=pd, beta=beta, beta_exact_target=str(desired),
                beta_upward_safe=True, emitted=emitted, reason=reason,
                empty_improvement_branch=beta<scope['gamma_L']))
    return dict(scope=scope, mu=float(mu), nu=float(nu), mu_exact=str(mu), nu_exact=str(nu),
        a_exact=str(a), d_exact=str(d), penalty_lower_global=float(p0), beta_global=float(beta0),
        station_minima=station_minima, states=states, rows=rows, state_count=len(states),
        actual_rows=len(rows), actual_nonzeros=sum(len(r['terms']) for r in rows),
        no_lower_bound_subtraction=True, exact_prefix_suffix_leave_one_out=True,
        conditional_beta_never_used_as_global_bound=True, all_old_PF_rows_retained=True,
        state_LP_or_greedy_or_dynamic_rebuilds=0, new_columns=0, Native_load=0, Optimize=0,
        seconds=time.perf_counter()-tick)
