"""Separate offline readback of actual matrices, primal points and exact dual boxes.

This script is by the same agent; it is not an independent person/review agent.
No Optimize occurs here. Exact fractions interpret each loaded binary64 exactly.
"""
from round162_common import *
from fractions import Fraction as F
import re

def records(path):
    with Path(path).open(encoding='utf-8') as stream:
        return {v['name']:v for v in map(json.loads,stream)}

def point(folder):
    return {r.split()[0]:float(r.split()[1]) for r in (folder/'lp_values.tsv').read_text().splitlines()}

def matrix(folder):
    oc=records(folder/'original_columns.jsonl');ac=records(folder/'actual_columns.jsonl')
    original=records(folder/'original_rows.jsonl');actual=records(folder/'actual_rows.jsonl')
    assert all(ac[n]==v for n,v in oc.items())
    assert all(actual[n]==v for n,v in original.items())
    intended=records(folder/'new_rows_intended.jsonl')
    assert all(actual[n]==v for n,v in intended.items())
    physical={r['column'] for r in map(json.loads,(folder/'Q_columns.jsonl').read_text().splitlines())}
    qrows={r['row'] for r in map(json.loads,(folder/'Q_rows.jsonl').read_text().splitlines()) if r['in_Q']}
    assert qrows=={n for n,r in original.items() if set(r['terms'])<=physical}
    assert all(math.isfinite(ac[n]['lb']) and math.isfinite(ac[n]['ub']) and -1e100<ac[n]['lb']<=ac[n]['ub']<1e100 for n in physical)
    block=read(folder/'block.json')
    if block['full'] and block['lower']<block['upper']:
        assert {n for n in ac if n not in oc}=={'pc162_lambda_L','pc162_lambda_U'}|{'pc162_'+e+'_'+n for e in ('L','U') for n in physical}
        omitted=[]
        for e in ('L','U'):
            for n in qrows:
                if 'pc162_q'+e+'_'+n not in intended:
                    omitted.append(n);continue
                r=original[n];t={'pc162_'+e+'_'+k:v for k,v in r['terms'].items()}
                if r['rhs']:t['pc162_lambda_'+e]=-r['rhs']
                assert intended['pc162_q'+e+'_'+n]==dict(name='pc162_q'+e+'_'+n,sense=r['sense'],rhs=0,terms=t)
        assert len(omitted)==block.get('omitted_endpoint_time_rows',0)
    stats=dict(PASS=True,old_columns=len(oc),old_rows=len(original),Q_columns=len(physical),Q_rows=len(qrows),
        new_columns=len(ac)-len(oc),new_rows=len(intended),old_penalty_objective_types_rows_exact=True,
        actual_new_rows_exact=True,unknown_columns=0,endpoint_boxes_same_Q=True)
    return oc,ac,original,actual,stats

def exact_dual(folder,columns,rows):
    dual=records(folder/'lp_duals.jsonl');residual={n:F(v['obj']) for n,v in columns.items()};lower=F(0);repaired=0;used=0
    for n,r in rows.items():
        raw=dual[n]['dual'];pi=min(0.,raw) if r['sense']=='<' else max(0.,raw) if r['sense']=='>' else raw
        repaired+=pi!=raw
        if not pi:continue
        used+=1;p=F(pi);lower+=p*F(r['rhs'])
        for v,c in r['terms'].items():residual[v]-=p*F(c)
    box=F(0)
    for n,v in residual.items():
        b=columns[n]['lb'] if v>=0 else columns[n]['ub']
        assert math.isfinite(b) and abs(b)<1e100,(n,b)
        box+=v*F(b)
    bound=lower+box;rounded=float(bound)
    if F(rounded)>bound:rounded=math.nextafter(rounded,-math.inf)
    return dict(exact_lower=str(bound),lower_down=rounded,row_aggregate=float(lower),box_compensation=float(box),
        sign_repairs=repaired,nonzero_duals=used,exact_binary64_rational=True,
        max_reduced_cost_box_coefficient=float(max(map(abs,residual.values()))),Optimize=0)

def primal(folder,columns,rows):
    x=point(folder);worst=0.;rowname=None
    for n,c in columns.items():worst=max(worst,c['lb']-x[n],x[n]-c['ub'])
    for n,r in rows.items():
        d=math.fsum(v*x[k] for k,v in r['terms'].items())-r['rhs']
        v=abs(d) if r['sense']=='=' else d if r['sense']=='<' else -d
        if v>worst:worst,rowname=v,n
    obj=sum((F(c['obj'])*F(x[n]) for n,c in columns.items() if c['obj']),F(0))
    upper=float(obj)
    if F(upper)<obj:upper=math.nextafter(upper,math.inf)
    products=[abs(x[n]-x['G']*x['state_'+n[8:]]) for n in x if n.startswith('state_g_')]
    inventory=[abs(x[n]-x['G']*x['Y_'+n[6:]]) for n in x if n.startswith('zprod_')]
    return dict(max_residual=worst,worst_row=rowname,objective_up=upper,G=x['G'],
        max_state_product_residual=max(products,default=0),max_inventory_product_residual=max(inventory,default=0),
        qualifies_under_inherited_1e_6=worst<=1e-6)

def role(name):
    selection=read(OUT/'reports'/f'{name}_capability.json');output={}
    common=None
    for key in ('S','completion','F'):
        label=selection[key]
        if label is None:continue
        folder=OUT/'runs'/label;o=read(folder/'outcome.json');oc,ac,original,actual,stats=matrix(folder)
        signature=(oc,original)
        if common is None:common=signature
        else:assert common==signature,'S/F original domain differs'
        result=dict(label=label,outcome=o,matrix=stats)
        if o['status']=='OPTIMAL':
            assert o['LP_primal_dual_available'] and o['LP_duals_available']
            result['primal']=primal(folder,ac,actual)
            result['dual']=exact_dual(folder,ac,actual)
            assert result['primal']['qualifies_under_inherited_1e_6']
            result['dual']['primal_dual_gap']=result['primal']['objective_up']-result['dual']['lower_down']
            result['dual']['gap_within_1e_7']=result['dual']['primal_dual_gap']<1e-7
        output[key]=result
    s=output['S'];f=output.get('F',output['completion'])
    assert f['outcome']['status']=='OPTIMAL'
    reliable_gain=f['dual']['lower_down']-s['primal']['objective_up']
    indistinguishable=f['primal']['objective_up']-s['dual']['lower_down']<=1e-7
    output['decision']=dict(reliable_original_J_increment=reliable_gain>1e-7,
        increment_lower=reliable_gain,increment_upper=f['primal']['objective_up']-s['dual']['lower_down'],
        no_identifiable_increment=indistinguishable,precision=1e-7,all_original_variables_free_in_F=selection['F'] is not None,
        old_saved_point_completed=output['completion']['outcome']['status']=='OPTIMAL',
        exact_equality_claim=False,only_current_scope=True)
    write(OUT/'reports'/f'{name}_audit.json',output)
    print(json.dumps(dict(role=name,decision=output['decision'],S=s['primal'],F=f['primal'])),flush=True)

def single(label):
    folder=OUT/'runs'/label;oc,ac,original,actual,stats=matrix(folder)
    result=dict(label=label,outcome=read(folder/'outcome.json'),matrix=stats,
        primal=primal(folder,ac,actual),dual=exact_dual(folder,ac,actual))
    write(OUT/'reports'/f'{label}_audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('outcome','matrix')}),flush=True)

def projection(role_name,c_label,f_label):
    cf=OUT/'runs'/c_label;ff=OUT/'runs'/f_label
    oc,ac,original,actual,stats=matrix(cf)
    fc=records(ff/'actual_columns.jsonl');fr=records(ff/'actual_rows.jsonl')
    cut=read(cf/'projection.json');assert cut['source_SHA256']==sha(ff/'model.lp')
    assert cut['duals_SHA256']==sha(ff/'lp_duals.jsonl')
    weights=list(map(json.loads,(cf/'projection_multipliers.jsonl').read_text().splitlines()))
    aggregate={n:F(0) for n in fc};rhs=F(0)
    duals=records(ff/'lp_duals.jsonl')
    used=set()
    for w in weights:
        n=w['row'];assert n.startswith('pc162_') and not n.startswith('pc162_saved_') and n not in used;used.add(n)
        r=fr[n];p=w['used'];raw=duals[n]['dual'];assert raw==w['raw']
        assert p==(min(0.,raw) if r['sense']=='<' else max(0.,raw) if r['sense']=='>' else raw)
        rhs-=F(p)*F(r['rhs'])
        for name,a in r['terms'].items():aggregate[name]-=F(p)*F(a)
    for n,r in fr.items():
        if n.startswith('pc162_'):
            raw=duals[n]['dual'];p=min(0.,raw) if r['sense']=='<' else max(0.,raw) if r['sense']=='>' else raw
            assert bool(p)==(n in used)
    new_box=F(0);round_box=F(0)
    for n,a in aggregate.items():
        c=F(cut['row']['terms'].get(n,0));delta=c-a;b=fc[n]
        margin=max(delta*F(b['lb']),delta*F(b['ub']))
        if n.startswith('pc162_'):
            assert c==0;new_box+=margin
            # Independent endpoint boxes are derived from lambda in [0,1].
            if n not in ('pc162_lambda_L','pc162_lambda_U'):
                old=n[8:];assert b['lb']==min(0,oc[old]['lb']) and b['ub']==max(0,oc[old]['ub'])
        else:round_box+=margin
    slack=F(cut['row']['rhs'])-rhs-new_box-round_box
    assert slack>=0,'projection unsafe'
    assert cut['new_columns_submitted']==0 and len(ac)==len(oc)
    assert len(actual)==len(original)+(1 if cut['active'] else 0)
    cp=primal(cf,ac,actual);cd=exact_dual(cf,ac,actual)
    s=read(OUT/'reports'/f'{role_name}_audit.json') if (OUT/'reports'/f'{role_name}_audit.json').exists() else None
    result=dict(PASS=True,label=c_label,source=f_label,matrix=stats,primal=cp,dual=cd,
        new_column_elimination_support=float(new_box),old_coefficient_conversion_support=float(round_box),
        outward_slack_exact=str(slack),outward_slack=float(slack),sign_repairs=cut['sign_repairs'],
        cut_terms=len(cut['row']['terms']),nonzero_source_rows=len(weights),new_columns=0,
        old_physical_families=sorted({re.sub(r'_[0-9]+','_#',n) for n in cut['row']['terms']}),
        source_objective=read(ff/'outcome.json')['LP_objective'],projected_objective=cp['objective_up'])
    if s:
        S=s['S']['primal']['objective_up'];Fval=s['F']['primal']['objective_up']
        result.update(retained_increment=cd['lower_down']-S,retained_fraction=(cp['objective_up']-S)/(Fval-S) if Fval>S+1e-7 else None)
    write(OUT/'reports'/f'{c_label}_projection_audit.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    if sys.argv[1] in ('single','projection'):globals()[sys.argv[1]](*sys.argv[2:])
    else:role(sys.argv[1])
