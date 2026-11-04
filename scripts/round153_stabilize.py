"""Select a less dispersed near-optimal RMP dual without potential boxes.

This is candidate selection only. The complete Q residual certificate and
full-domain price remain the sole lower-bound qualification.
"""
from round152_math import h_exact
from round153_lp import optimize
from round153_common import *

def select_dual(master,target,band=1e-7,cap=120.):
    gp=master.gp;primal=master.m;assert not master.phase and primal.Status==2
    target=Path(target);target.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    vs=primal.getVars();cs=primal.getConstrs();objective=primal.ObjVal
    # The dual is represented against the exact written RMP matrix and its
    # original explicit bounds. The independent final certificate instead
    # uses only the pre-column Q implied bounds.
    with gp.Model(env=master.env) as dual:
        equations={v.VarName:dual.addConstr(gp.LinExpr()==v.Obj,name=f'dual_column_{j}') for j,v in enumerate(vs)}
        value=dual.addConstr(gp.LinExpr()>=objective-band-primal.ObjCon,name='near_optimal_dual_band')
        dual.update();multipliers={}
        for j,c in enumerate(cs):
            e=primal.getRow(c);coeff=[e.getCoeff(k) for k in range(e.size())];rows=[equations[e.getVar(k).VarName] for k in range(e.size())]
            if c.RHS:coeff.append(c.RHS);rows.append(value)
            p=dual.addVar(lb=0. if c.Sense=='>' else -gp.GRB.INFINITY,
                          ub=0. if c.Sense=='<' else gp.GRB.INFINITY,
                          column=gp.Column(coeff,rows),name=f'pi_{j}')
            multipliers[c.ConstrName]=p
        for j,v in enumerate(vs):
            if v.LB>-gp.GRB.INFINITY:
                coeff=[1.];rows=[equations[v.VarName]]
                if v.LB:coeff.append(v.LB);rows.append(value)
                dual.addVar(lb=0,column=gp.Column(coeff,rows),name=f'lb_{j}')
            if v.UB<gp.GRB.INFINITY:
                coeff=[1.];rows=[equations[v.VarName]]
                if v.UB:coeff.append(v.UB);rows.append(value)
                dual.addVar(lb=-gp.GRB.INFINITY,ub=0,column=gp.Column(coeff,rows),name=f'ub_{j}')
        dual.update();centers={}
        for s in master.scope['stations']:
            anchor=s['support'][0]
            for y in s['support'][1:]:
                center=float(h_exact(s,anchor)-h_exact(s,y));k=s['i'],y;centers[k]=center
                p=multipliers[f'hull_link_{s["i"]}_{y}'];dev=dual.addVar(lb=0,obj=1,name=f'dev_{s["i"]}_{y}')
                dual.addConstr(dev>=p-center);dual.addConstr(dev>=center-p)
        dev=dual.addVar(lb=0,obj=1,name='dev_beta');p=multipliers['hull_gini']
        dual.addConstr(dev>=p-1.);dual.addConstr(dev>=1.-p)
        rr=optimize(dual,target,cap=cap)
        if rr['Status']==2 and rr['primal']['qualified']:
            selected={name:p.X for name,p in multipliers.items()};status='SELECTED'
            selected_objective=dual.getRow(value).getValue()+primal.ObjCon
        else:selected=None;status='FALLBACK_TO_BASIC_RMP_DUAL'
        record=dict(status=status,RMP_objective=objective,dual_band=band,
                    potential_objective='sum absolute deviations from AP-based price center plus abs(beta-1)',
                    actual_selected_dual_objective=selected_objective if selected else None,
                    selected_dual_deficit=objective-selected_objective if selected else None,
                    candidate_band_is_numerical_not_exact_optimal_face=True,
                    no_potential_radius=True,selected_multipliers=selected,seconds=time.perf_counter()-start,
                    solver=rr,not_itself_a_full_hull_lower=True)
        save_gz(target/'selection.json.gz',record);return selected,record
