"""Independent stdlib-only audit of the C++ writer's linear LP and actual Starts.

Accepts only the observed one-line linear writer grammar; rejects other syntax.
Never imports gurobipy, loads a solver DLL, creates Env, exports or optimizes.
"""
import csv,math,re,time
from round99_common import *

MODES={'ENS-C':'off','R1':'aggregate','Q-I':'q-integer',
       'M-B':'m-binary','R2':'projected','M-BL':'m-binary-linked'}
NAME=re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')
REL=re.compile(r'\s(<=|>=|=)\s(\S+)\s*\Z')

def expression(text,register):
    tokens=text.split();terms=[];constant=0.;i=0;sign=1.
    while i<len(tokens):
        token=tokens[i]
        if token in ['+','-']:
            sign=1. if token=='+' else -1.;i+=1;assert i<len(tokens);token=tokens[i]
        try:coefficient=float(token)
        except ValueError:
            assert NAME.fullmatch(token),('unsupported LP term',token)
            register(token);terms.append((token,sign));i+=1;sign=1.;continue
        assert math.isfinite(coefficient)
        i+=1
        if i<len(tokens) and NAME.fullmatch(tokens[i]):
            name=tokens[i];register(name);terms.append((name,sign*coefficient));i+=1
        else:constant+=sign*coefficient
        sign=1.
    assert terms or tokens==['0'],('unsupported constant expression',text)
    return terms,constant

def audit_model(path,starts,mode):
    order=[];seen=set();bounds={};types={};records=[];values=[]
    def register(name):
        assert NAME.fullmatch(name)
        if name not in seen:seen.add(name);order.append(name)
    for start_path,meta in starts:
        assert all(meta[k] for k in ['submitted','mapping_complete','rows_valid','objective_valid','readback_valid'])
        vector=start_path.with_name(start_path.name[:-5]+'.values.csv')
        with vector.open(newline='') as f:table=list(csv.DictReader(f))
        val={r['variable']:float(r['value']) for r in table};assert len(val)==len(table)
        assert all(math.isfinite(v) for v in val.values())
        assert all(math.isfinite(float(r['readback'])) and abs(val[r['variable']]-float(r['readback']))<=1e-7 for r in table)
        values.append((table,val,meta))
        records.append(dict(start_path=start_path.relative_to(ROOT).as_posix(),start_sha256=sha(start_path),
            vector_sha256=sha(vector),model_sha256=sha(path),maximum_absolute_residual=0.))
    section=None;rows=0;objective=None
    with path.open(encoding='utf-8') as f:
        for raw in f:
            line=raw.strip()
            if not line or line.startswith('\\'):continue
            if line in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:
                section=line;continue
            if section=='Minimize':
                assert objective is None and line.startswith('obj:')
                objective=expression(line.split(':',1)[1],register)
            elif section=='Subject To':
                assert ':' in line;body=line.split(':',1)[1];match=REL.search(body);assert match
                sense,rhs=match[1],float(match[2]);assert math.isfinite(rhs)
                terms,constant=expression(body[:match.start()],register);rows+=1
                for record,(_,val,_) in zip(records,values):
                    lhs=math.fsum(c*val[n] for n,c in terms)+constant
                    residual=abs(lhs-rhs) if sense=='=' else max(0.,lhs-rhs) if sense=='<=' else max(0.,rhs-lhs)
                    record['maximum_absolute_residual']=max(record['maximum_absolute_residual'],residual)
            elif section=='Bounds':
                tokens=line.split()
                assert len(tokens)==5 and tokens[1]==tokens[3]=='<=',('unsupported bound',line)
                lb,name,ub=float(tokens[0]),tokens[2],float(tokens[4]);register(name)
                assert name not in bounds and lb<=ub;bounds[name]=(lb,ub)
            elif section in ['Generals','Binaries']:
                for name in line.split():
                    register(name);assert name not in types;types[name]='I' if section=='Generals' else 'B'
            else:raise AssertionError(('unsupported LP section',section,line))
    assert section=='End' and objective is not None and rows>0
    assert set(bounds)==seen, 'controlled writer explicitly bounds every original column'
    quantity_type='C' if mode in ['projected','m-binary','m-binary-linked'] else 'I'
    direction=[n for n in order if n.startswith('mode_')]
    assert (not direction) if mode in ['projected','q-integer'] else (direction and all(types.get(n,'C')=='B' for n in direction))
    assert all(types.get(n,'C')==quantity_type for n in order if n.startswith(('p_','d_')))
    for record,(table,val,meta) in zip(records,values):
        assert [r['variable'] for r in table]==order, 'actual original native column order differs'
        assert [r['type'] for r in table]==[types.get(n,'C') for n in order], 'restored VType differs from canonical typed LP'
        for n in order:
            lb,ub=bounds[n];v=val[n]
            record['maximum_absolute_residual']=max(record['maximum_absolute_residual'],lb-v,v-ub,0.)
            if types.get(n,'C') in ['I','B'] or n.startswith(('p_','d_')):
                assert abs(v-round(v))<=1e-5,('physical integer contract',n,v)
            if types.get(n)=='B':assert -1e-6<=v<=1+1e-6
        terms,constant=objective;obj=math.fsum(c*val[n] for n,c in terms)+constant
        assert abs(obj-meta['objective'])<=1e-6
        assert record['maximum_absolute_residual']<=1e-6,record
        record.update(mode=mode,rows=rows,columns=len(order),objective=obj,
            actual_quantity_type=quantity_type,direction_columns=len(direction),
            per_column_restored_type_checked=True,ordered_native_columns_checked=True,
            parser_scope='strict C++ one-line linear LP grammar; actual CSV/readback; stdlib only')
    return records

def main():
    begin=time.perf_counter();plan=read(OUT/'final_start_audit_plan.json');all_records=[];scopes=[]
    assert plan['finite_model_scopes']==22
    for group in plan['scopes']:
        campaign=group['campaign'];q=read(OUT/campaign/'identity.json')
        for number in group['numbers']:
            a=q['launches'][number-1];d=Path(a['destination']);mode=MODES[a['arm']]
            models={sha(p):p for p in (d/'external/models').glob('*.lp')}
            starts=[(p,read(p)) for p in (d/'external/native_logs').glob('*.round68.start.json')]
            submitted=[(p,j) for p,j in starts if j.get('submitted')];assert submitted
            records=[]
            for h in sorted({j['model_sha256'] for _,j in submitted}):
                assert h in models
                records.extend(audit_model(models[h],[(p,j) for p,j in submitted if j['model_sha256']==h],mode))
            label=f'pure_start_{campaign}_{number:02d}.json'
            write(OUT/'pure_qualification'/label,dict(passed=True,optimizer_calls=0,starts=records))
            scopes.append(dict(campaign=campaign,number=number,arm=a['arm'],submitted_starts=len(records),
                output=label,output_sha256=sha(OUT/'pure_qualification'/label)))
            all_records.extend(records)
            print(json.dumps(dict(campaign=campaign,number=number,passed=True,starts=len(records))),flush=True)
    assert len(scopes)==22
    write(OUT/'pure_qualification/final_start_summary.json',dict(passed=True,model_scopes=22,
        actual_submitted_starts=len(all_records),optimizer_calls=0,native_env_starts=0,
        maximum_absolute_residual=max(r['maximum_absolute_residual'] for r in all_records),
        all_column_types_and_order_checked=True,scopes=scopes,
        scope='independent strict LP text and actual native CSV/readback; not Model.presolve or solver reproduction',
        engineering_seconds=time.perf_counter()-begin,script_sha256=sha(__file__),plan_sha256=sha(OUT/'final_start_audit_plan.json')))

if __name__=='__main__':main()
