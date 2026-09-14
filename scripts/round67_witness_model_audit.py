"""Offline full-column/row audit of paid initial witnesses; no solver calls.

Extends the existing canonical mapping formulas with VD-P/LOG coordinates.
This checks retained witnesses, not general formulation equivalence. It never
submits starts, changes model domains, or feeds information into a run.
"""
import ast,copy,csv,json,math,re,time
import analyze_round67 as audit
run=audit.run

def mapped_values(p,witness,bounds):
    physical=audit.physical_module.physical(p,witness)
    assert physical['original_T_feasible']
    text=(run.ROOT/p['instance_path']).read_text()
    def vector(name):return ast.literal_eval(re.search(r'(?m)^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text)[1])
    head=text.splitlines()[0];Q=ast.literal_eval(head[head.index('['):head.index(']')+1])
    normalized=copy.deepcopy(witness);normalized['routes']=[]
    for capacity in sorted(set(Q)):
        labels=[k for k,q in enumerate(Q) if q==capacity]
        routes=[copy.deepcopy(r) for r in witness['routes'] if r['operations'] and Q[r['vehicle']]==capacity]
        routes.sort(key=lambda r:(-len(r['operations']),r['vehicle']))
        for label,route in zip(labels,routes):route['vehicle']=label;normalized['routes'].append(route)
    normalized['routes'].sort(key=lambda r:r['vehicle'])
    normalized_check=audit.physical_module.physical(p,normalized)
    assert normalized_check==physical,'Equal-capacity symmetry changed physical result'
    witness=normalized
    y=vector('initial');target=vector('target');direct={}
    for route in witness['routes']:
        k=route['vehicle'];nodes=route['nodes']
        if nodes==[0,0] and not route['operations']:continue
        operations={op['station']:(op['pickup'],op['drop']) for op in route['operations']}
        for position,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
            direct[f'x_{k}_{i}_{j}']=1
            direct[f'conn_{k}_{i}_{j}']=len(nodes)-1-position
        load=0
        for position,i in enumerate(nodes[1:-1],1):
            pickup,drop=operations[i];load+=pickup-drop;y[i]+=drop-pickup
            for prefix,value in [('z',1),('mode',int(pickup>0)),('p',pickup),('d',drop),('ord',position),('load',load)]:
                direct[f'{prefix}_{k}_{i}']=value
    ratios=[y[i]/target[i] for i in range(1,len(y))];r=[0]+ratios;G=physical['G']
    states={}
    for name in bounds:
        match=re.fullmatch(r'state_(\d+)_(\d+)',name)
        if match:states.setdefault(int(match[1]),set()).add(int(match[2]))
    values={}
    for name in bounds:
        if name in direct:value=direct[name]
        elif re.fullmatch(r'(x|conn)_\d+_\d+_\d+|(z|mode|p|d|ord|load)_\d+_\d+',name):value=0
        elif name=='G':value=G
        elif name=='r_min':value=min(ratios)
        elif name=='r_max':value=max(ratios)
        elif name=='W_SP':value=sum(ratios)*physical['P']
        else:
            match=re.fullmatch(r'(Y|r|e|zprod)_(\d+)',name)
            pair=re.fullmatch(r'(h|bit|prod|state|state_g|state_code)_(\d+)_(\d+)',name)
            if match:
                family,i=match[1],int(match[2]);value={'Y':y[i],'r':r[i],'e':abs(r[i]-1),'zprod':G*y[i]}[family]
            elif pair:
                family,i,j=pair[1],int(pair[2]),int(pair[3])
                if family=='h':value=abs(r[i]-r[j])
                elif family=='bit':value=(y[i]>>j)&1
                elif family=='prod':value=G*((y[i]>>j)&1)
                elif family=='state':value=int(y[i]==j)
                elif family=='state_g':value=G*int(y[i]==j)
                else:value=((y[i]-min(states[i]))>>j)&1
            else:raise RuntimeError('Unmapped canonical column: '+name)
        assert math.isfinite(value)
        values[name]=value
    return values,physical

def linear_terms(expression,values):
    tokens=expression.split();position=0;terms={}
    while position<len(tokens):
        sign=1
        if tokens[position] in ['+','-']:
            sign=1 if tokens[position]=='+' else -1;position+=1
        token=tokens[position];position+=1
        if token in values:
            terms[token]=terms.get(token,0)+sign;continue
        coefficient=float(token)
        if position<len(tokens) and tokens[position] not in ['+','-']:
            name=tokens[position];position+=1
            if name not in values:raise RuntimeError('Unknown expression column: '+name)
            terms[name]=terms.get(name,0)+sign*coefficient
        else:terms['__constant__']=terms.get('__constant__',0)+sign*coefficient
    return {name:value for name,value in terms.items() if value!=0}

def linear_value(expression,values):
    return sum(coefficient*(1 if name=='__constant__' else values[name])
        for name,coefficient in linear_terms(expression,values).items())

def check_model(p,witness,path):
    text=path.read_text();bounds={}
    body=text.partition('Bounds\n')[2].partition('Generals\n')[0].partition('Binaries\n')[0]
    for line in body.splitlines():
        if not line.strip():continue
        match=re.fullmatch(r'\s*(\S+) <= (\w+) <= (\S+)\s*',line)
        if not match:raise RuntimeError('Unsupported bound line: '+line)
        assert match[2] not in bounds
        bounds[match[2]]=(float(match[1]),float(match[3]))
    assert bounds
    values,physical=mapped_values(p,witness,bounds)
    if not bounds['G'][0]-1e-8<=physical['G']<=bounds['G'][1]+1e-8:
        return dict(compatible_interval=False,scope='Witness belongs to another Gini interval; no row feasibility claim')
    objective=text.partition('Minimize\n')[2].partition('Subject To\n')[0].split(':',1)[1].strip()
    objective_terms=linear_terms(objective,values);parsed_rows=[];cutoffs=[]
    for line in text.partition('Subject To\n')[2].partition('Bounds\n')[0].splitlines():
        if not line.strip():continue
        match=re.fullmatch(r'\s*(\w+): (.*) (<=|>=|=) (\S+)\s*',line)
        if not match:raise RuntimeError('Unsupported row: '+line[:120])
        terms=linear_terms(match[2],values);rhs=float(match[4]);sense=match[3]
        parsed_rows.append((match[1],terms,sense,rhs))
        if sense=='<=' and terms==objective_terms:cutoffs.append(rhs)
    assert cutoffs,'Missing explicit non-strict objective cutoff'
    cutoff=min(cutoffs)
    if physical['F']>cutoff+1e-7:
        return dict(compatible_interval=True,compatible_cutoff=False,cutoff=cutoff,
            scope='Initial witness superseded by a tighter current cutoff; no row feasibility claim')
    violations=[]
    for name,(lo,hi) in bounds.items():
        violation=max(lo-values[name],values[name]-hi,0)
        if violation>1e-7:violations.append((name,'bound',violation))
    for name in text.partition('Generals\n')[2].partition('End')[0].split():
        if name=='Binaries':continue
        if name not in values:raise RuntimeError('Unknown discrete column: '+name)
        violation=abs(values[name]-round(values[name]))
        if violation>1e-7:violations.append((name,'integrality',violation))
    count=0;maximum=0.0
    for name,terms,sense,rhs in parsed_rows:
        value=sum(coefficient*(1 if column=='__constant__' else values[column]) for column,coefficient in terms.items())
        violation=abs(value-rhs) if sense=='=' else max(0,value-rhs if sense=='<=' else rhs-value)
        count+=1;maximum=max(maximum,violation)
        if violation>1e-7:violations.append((name,'row',violation))
    assert count
    objective_error=abs(linear_value(objective,values)-physical['F'])
    if objective_error>1e-7:violations.append(('objective','F',objective_error))
    return dict(compatible_interval=True,compatible_cutoff=True,cutoff=cutoff,columns=len(bounds),rows=count,maximum_row_violation=maximum,
        objective_error=objective_error,violations=violations,all_bounds_types_rows_valid=not violations,
        mapping_symmetry='Remove empty routes; reorder only equal-capacity vehicles by served count then original label; reverify',
        scope='Offline retained-witness mapping; not a native submission or general proof')

def main():
    assert not (run.OUT/'active_run.lock').exists(),'Run full model audit only between optimizer queues'
    records=[];start=time.monotonic()
    for e in run.runner.entries():
        folder=run.ROOT/e['destination'];w=folder/'external/initial_witness.json'
        if not e['charged'] or e['arm']=='P-GRB' or not (folder/'completion.json').exists() or not w.exists():continue
        witness=run.read(w);p=run.panel()[e['id']]
        for model in sorted(folder.glob('external/models/*.lp')):
            records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],model=str(model.relative_to(run.ROOT)),
                model_sha256=run.sha(model),witness_sha256=run.sha(w),**check_model(p,witness,model)))
    run.write(run.OUT/'witness_model_checks.json',dict(checks=records,offline_wall_seconds=time.monotonic()-start,
        optimizer_calls=0,script_sha256=run.sha(__file__)))
    failures=[r for r in records if r.get('compatible_interval') and r.get('compatible_cutoff') and not r['all_bounds_types_rows_valid']]
    print('Offline witness models',len(records),'incompatible G intervals',sum(not r['compatible_interval'] for r in records),
        'superseded initial cutoff',sum(r.get('compatible_cutoff')==False for r in records),'failures',len(failures))
    for r in failures:print(r['id'],r['arm'],r['model'],r['violations'][:8])
    if failures:raise RuntimeError('Retained witness rejected; investigate before any certificate claim')
if __name__=='__main__':main()
