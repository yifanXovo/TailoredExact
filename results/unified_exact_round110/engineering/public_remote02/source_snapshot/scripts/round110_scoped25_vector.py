"""Construct an offline exact vector in the actual failed scoped M-B model.

Only this observed own exact-zero fleet is mapped. All columns/types/rows and
the current G interval/cutoff must pass; no solver or native Start submission.
"""
from round110_common import *
import round108_reader as core
from fractions import Fraction
from collections import Counter
import re, math, copy


def build(label):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();ident=read(OUT/'campaign/identity.json');launch=ident['launches'][24]
    d=Path(launch['destination']);p=launch['panel'];r=read(d/'result.json');obs=read(d/'observations.json')
    c=read(d/'completion.json');assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];assert len(calls)==4
    call=calls[-1];assert call['call']==4 and call['leaf']=='L0' and call['native_preconditions']==1 and call['full_original']==0
    assert call['lower_g']==0 and call['upper_g']==call['cutoff']>0
    model_path=core.portable(ROOT,call['model_path']);assert sha(model_path)==call['model_sha256']
    info,m=core.model_contract(ROOT,p,model_path,'M-B');a=core.evidence.instance(ROOT,p)
    physical=core.full_fleet(ROOT,p,r);assert physical['F']==physical['G']==physical['P']==0.
    assert physical['Y'][1:]==a['D'][1:]
    fleet=[]
    for capacity in sorted(set(p['Q_vector'])):
        labels=[k for k,q in enumerate(p['Q_vector']) if q==capacity]
        routes=[copy.deepcopy(v) for v in physical['routes'] if v['operations'] and p['Q_vector'][v['vehicle']]==capacity]
        routes.sort(key=lambda v:(-len(v['operations']),v['vehicle']))
        for k,v in zip(labels,routes):v['vehicle']=k;fleet.append(v)
    fleet.sort(key=lambda v:v['vehicle'])
    normalized=core.full_fleet(ROOT,p,dict(r,routes=fleet))
    assert normalized['F']==0. and normalized['Y']==physical['Y']
    zero=Fraction(0);one=Fraction(1);values={n:zero for n in m['bounds']}
    for route in fleet:
        k=route['vehicle'];nodes=route['nodes'];ops={v['station']:v for v in route['operations']};load=0
        for pos,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
            for name,value in [(f'x_{k}_{i}_{j}',1),(f'conn_{k}_{i}_{j}',len(nodes)-1-pos)]:
                assert name in values;values[name]=Fraction(value)
        for pos,i in enumerate(nodes[1:-1],1):
            v=ops[i];load+=v['pickup']-v['drop']
            for name,value in {f'p_{k}_{i}':v['pickup'],f'd_{k}_{i}':v['drop'],f'z_{k}_{i}':1,
                    f'mode_{k}_{i}':int(v['pickup']>0),f'load_{k}_{i}':load,f'ord_{k}_{i}':pos}.items():
                assert name in values;values[name]=Fraction(value)
    g=Fraction(1,10**12)
    for name in values:
        family=name.split('_',1)[0]
        if family in {'x','conn','p','d','z','mode','load','ord'}:continue
        if name=='G':values[name]=g
        elif name in ['r_min','r_max']:values[name]=one
        elif name=='W_SP':values[name]=zero
        elif re.fullmatch(r'Y_\d+',name):values[name]=Fraction(physical['Y'][int(name.split('_')[1])])
        elif re.fullmatch(r'r_\d+',name):values[name]=one
        elif re.fullmatch(r'e_\d+|h_\d+_\d+',name):values[name]=zero
        elif re.fullmatch(r'state_\d+_\d+',name):
            _,i,y=name.split('_');values[name]=Fraction(int(physical['Y'][int(i)]==int(y)))
        elif re.fullmatch(r'state_g_\d+_\d+',name):
            _,_,i,y=name.split('_');values[name]=g*int(physical['Y'][int(i)]==int(y))
        elif re.fullmatch(r'bit_\d+_\d+',name):
            _,i,b=name.split('_');values[name]=Fraction((physical['Y'][int(i)]>>int(b))&1)
        elif re.fullmatch(r'prod_\d+_\d+',name):
            _,i,b=name.split('_');values[name]=g*((physical['Y'][int(i)]>>int(b))&1)
        elif re.fullmatch(r'zprod_\d+',name):values[name]=g*physical['Y'][int(name.split('_')[1])]
        else:raise AssertionError(('unmapped actual model family',name))
    coefficients={}
    def exact(v):
        if v not in coefficients:coefficients[v]=Fraction(v)
        return coefficients[v]
    ratio_rows={}
    for terms,sense,rhs in m['rows']:
        if sense!='=' or len(terms)!=2:continue
        names={n for n,_ in terms}
        for n,_ in terms:
            if re.fullmatch(r'r_\d+',n) and names=={n,'Y_'+n.split('_')[1]}:ratio_rows[n]=(dict(terms),rhs)
    assert len(ratio_rows)==p['V']
    ratios={}
    for i in range(1,p['V']+1):
        rn=f'r_{i}';yn=f'Y_{i}';terms,rhs=ratio_rows[rn]
        ratios[i]=(exact(rhs)-exact(terms[yn])*values[yn])/exact(terms[rn]);values[rn]=ratios[i];values[f'e_{i}']=abs(ratios[i]-one)
    for n in values:
        if re.fullmatch(r'h_\d+_\d+',n):_,i,j=n.split('_');values[n]=abs(ratios[int(i)]-ratios[int(j)])
    if 'r_min' in values:values['r_min']=min(ratios.values())
    if 'r_max' in values:values['r_max']=max(ratios.values())
    if 'W_SP' in values:
        # The saved M-B model uses a continuous weighted-penalty epigraph.
        # Exact reciprocal rows need not yield binary64 r_i == 1.
        epigraph=[(dict(terms),rhs) for terms,sense,rhs in m['rows']
            if sense=='>=' and any(n=='W_SP' for n,_ in terms)
            and all(n=='W_SP' or re.fullmatch(r'e_\d+',n) for n,_ in terms)]
        assert len(epigraph)==1 and epigraph[0][0]['W_SP']>0
        terms,rhs=epigraph[0]
        values['W_SP']=(exact(rhs)-sum((values[n]*exact(v) for n,v in terms.items() if n!='W_SP'),zero))/exact(terms['W_SP'])
    assert m['bounds']['G']==(call['lower_g'],call['upper_g'])
    assert any(terms==m['objective'][0] and sense=='<=' and rhs==call['cutoff']-m['objective'][1] for terms,sense,rhs in m['rows'])
    for n,(lo,hi) in m['bounds'].items():
        assert (not math.isfinite(lo) or values[n]>=exact(lo)) and (not math.isfinite(hi) or values[n]<=exact(hi)),('bound',n)
        assert m['types'][n]=='C' or values[n].denominator==1,('type',n)
    bad=[]
    for number,(terms,sense,rhs) in enumerate(m['rows'],1):
        lhs=sum((values[n]*exact(v) for n,v in terms if values[n]),zero);target=exact(rhs)
        valid=lhs==target if sense=='=' else lhs<=target if sense=='<=' else lhs>=target
        if not valid:bad.append(dict(row=number,sense=sense,violation=float(abs(lhs-target))))
    objective=sum((values[n]*exact(v) for n,v in m['objective'][0] if values[n]),exact(m['objective'][1]))
    out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
    write(out/'exact_vector.json',dict(complete_column_values={n:[v.numerator,v.denominator] for n,v in values.items()},
        current_model_SHA=sha(model_path),current_key=[25,launch['id'],launch['seed'],launch['arm']],current_call=4,
        scope=dict(lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff']),
        physical_own_zero=True,equal_capacity_normalization='stable descending operation count then original label within exact capacity class',
        continuous_penalty_epigraph_exact=True,
        exact_objective=[objective.numerator,objective.denominator],exact_objective_float=float(objective),
        model_info=info,column_type_counts=dict(Counter(m['types'].values())),row_violations=bad,
        submitted_to_native=False,Optimize=0,native_environment=0,production_PE_SHA=production['production_PE_SHA']))
    print(json.dumps(dict(rows=len(m['rows']),columns=len(values),objective=float(objective),bad_rows=bad[:20],bad_count=len(bad))),flush=True)
    assert not bad,'same scoped exact matrix vector not yet proved; HOLD'
    claims=[v['payload']['native_bound'] for v in obs if v['payload']['kind']=='bound' and v['payload']['call']==4]
    assert claims and any(exact(lb)>objective+Fraction(1,10**7) for lb in claims)


if __name__=='__main__':build(sys.argv[1])
