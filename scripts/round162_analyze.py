"""Read completed Native evidence, verify original fleets and summarize paid pairs."""
from round162_common import *
from fractions import Fraction as F
from round162_audit import records,point
import ast,re,csv

def inherited_functions():
    source=ROOT/'scripts/round161_analyze.py';tree=ast.parse(source.read_text(encoding='utf-8-sig'))
    namespace=dict(globals())
    for name in ('instance','fleet','events'):
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    return namespace

def analyze():
    legacy=inherited_functions();samples=[];fleets=[];identities=[];common={}
    plan=read(OUT/'development_plan.json')
    for arm in plan['order']:
        tick=time.perf_counter()
        role,form,label=arm['role'],arm['form'],arm['label'];folder=OUT/'runs'/label
        o=read(folder/'outcome.json');ad=read(folder/'admission.json');events=legacy['events'](folder);d=legacy['instance'](role)
        launch=read(OUT/'launches'/f'{label}.json');receipt=read(OUT/'fees'/label/'receipt.json')
        assert receipt['exit_code']==0 and receipt['exit_observed'] and not receipt['timeout']
        assert launch['PE_SHA256']==plan['PE_SHA256'] and o['model_matches'] and o['feasibility_gate'] and o['zero_gaps']
        call=next(e for e in events if e['kind']=='call')
        assert call['model_sha256']==sha(folder/'model.lp') and call['native_preconditions']==1
        for k,v in {'Threads':1,'Seed':0,'MIPFocus':0,'MIPGap':0,'MIPGapAbs':0,'Presolve':-1}.items():assert call['settings'][k]==v
        params=read(folder/'native.log.round162_parameters.json');assert params['NodeLimit']==4096
        assert o['bound_available'] and o['proof_usable'] and not o['source_rejected']
        base=(records(folder/'original_columns.jsonl'),records(folder/'original_rows.jsonl'))
        start=read(folder/'start.json')
        if form=='S':common[role]=(base,start,ad)
        else:
            assert base==common[role][0] and start==common[role][1]
            for k in ('parent_J','G','P','cutoff','gamma_L','gamma_U'):assert ad[k]==common[role][2][k]
        first=None;trajectory=[dict(time=0.,J=ad['parent_J'],source='input parent')]
        all_fleets=[];bound_events=[]
        for e in events:
            assert e['kind'] not in ('source_rejected','failure'),e
            if e['kind']=='witness':
                checked=legacy['fleet'](d,e);all_fleets.append(checked)
                fleets.append(dict(label=label,event=e['sequence'],time=e['outer_observation_seconds'],**checked))
                if checked['J']<trajectory[-1]['J']-1e-10:
                    trajectory.append(dict(time=e['outer_observation_seconds'],J=checked['J'],source=e['source']))
                    if first is None:first=e['outer_observation_seconds']
            elif e['kind']=='bound':
                bound_events.append(dict(time=e['outer_observation_seconds'],raw=e['native_bound'],
                    local=e.get('local_bound'),global_lower=e.get('global_bound')))
        assert all_fleets and bound_events
        U=min(f['J'] for f in all_fleets);L=min(o['qualified_restricted_lower'],ad['cutoff'])
        assert abs(U-o['physical_U'])<1e-9 and abs(L-o['global_transported_floor'])<1e-10
        assert max(e['raw'] for e in bound_events)<=U+1e-7
        source=read(folder/'source/source_outcome.json') if form=='C' else None
        if source:assert source['qualified'] and o['source_qualified']
        sample=dict(role=role,form=form,label=label,status=o['status'],physical_U=U,raw_lower=o['raw_lower'],
            qualified_lower=o['qualified_restricted_lower'],global_lower=L,absolute_gap=U-L,relative_gap=(U-L)/U,
            first_strict_improvement=first,Work=o['work'],nodes=o['nodes'],iterations=o['iterations'],Native_seconds=o['runtime'],
            outer_seconds=receipt['outer_seconds'],process_internal_seconds=o['outer_seconds'],source_seconds=o['source_seconds'],
            project_seconds=o['project_seconds'],other_build_Start_registry_return_seconds=o['outer_seconds']-o['runtime']-o['source_seconds']-o['project_seconds'],
            source_Work=source['work'] if source else 0.,source_Runtime=source['runtime'] if source else 0.,
            original_columns=len(base[0]),original_rows=len(base[1]),actual_columns=o['cols'],actual_rows=o['rows'],nonzeros=o['nonzeros'],
            source_raw_lower=source['raw_lower'] if source else None,Start_submitted=o['Start_submitted'],Start_status=o['Start_status'],
            T_cert=None,certified=False,production_cap=900,node_capacity=4096,formal_GI=False,trajectory=trajectory,bounds=bound_events)
        sample['T_produce']=receipt['outer_seconds']
        sample['T_verify']=time.perf_counter()-tick
        sample['T_total']=sample['T_produce']+sample['T_verify']
        samples.append(sample)
        identities.append(dict(label=label,PE_SHA256=launch['PE_SHA256'],DLL=read(folder/'runtime_binding.json'),
            input_SHA256=sha(OUT/'inputs'/role/'instance.txt'),parent_SHA256=sha(OUT/'inputs'/role/'parent.txt'),
            model_SHA256=sha(folder/'model.lp'),columns_SHA256=sha(folder/'actual_columns.jsonl'),rows_SHA256=sha(folder/'actual_rows.jsonl'),
            scope=call,Start_SHA256=sha(folder/'start.json')))
    pairs=[]
    for role in plan['roles']:
        s=next(x for x in samples if x['role']==role and x['form']=='S');c=next(x for x in samples if x['role']==role and x['form']=='C')
        pairs.append(dict(role=role,S_U=s['physical_U'],C_U=c['physical_U'],S_L=s['global_lower'],C_L=c['global_lower'],
            U_gain=s['physical_U']-c['physical_U'],L_gain=c['global_lower']-s['global_lower'],S_Work=s['Work'],C_Work=c['Work'],
            S_nodes=s['nodes'],C_nodes=c['nodes'],C_source_seconds=c['source_seconds'],C_project_seconds=c['project_seconds'],
            S_outer=s['outer_seconds'],C_outer=c['outer_seconds'],S_first_improvement=s['first_strict_improvement'],C_first_improvement=c['first_strict_improvement'],
            C_gap=c['absolute_gap'],S_gap=s['absolute_gap'],same_PE=True,same_original_matrix=True,same_Start=True,source_paid_inside_C_cap=True))
    write(OUT/'reports/native.json',dict(samples=samples,pairs=pairs))
    write(OUT/'reports/fleets.json',fleets);write(OUT/'reports/native_identities.json',identities)
    flat=[{k:v for k,v in x.items() if k not in ('trajectory','bounds')} for x in samples]
    with (OUT/'reports/native.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print(json.dumps(pairs,indent=2),flush=True)

def endpoints():
    output=[]
    for role in ('R-X35-S-T2','N-B35-S'):
        audit=read(OUT/'reports'/f'{role}_audit.json');S=OUT/'runs'/audit['S']['label'];Ffolder=OUT/'runs'/audit['F']['label']
        s=point(S);f=point(Ffolder);families={}
        for n in s:
            delta=abs(s[n]-f[n])
            if delta>1e-8:
                fam=re.sub(r'_[0-9]+','_#',n);v=families.setdefault(fam,dict(count=0,max_change=0.))
                v['count']+=1;v['max_change']=max(v['max_change'],delta)
        d=read(OUT/'inputs'/role/'source.json')['panel'];entry=dict(role=role,free_remix_changed_families=families)
        choices=[('F',Ffolder)]
        if role=='N-B35-S':choices.append(('F-no-time',OUT/'runs/N-B35-S_F_no_time_LP_v1'))
        entry['endpoint_checks']=[]
        for tag,folder in choices:
            x=point(folder);qrows={r['row'] for r in map(json.loads,(folder/'Q_rows.jsonl').read_text().splitlines()) if r['in_Q']}
            rows=records(folder/'original_rows.jsonl');actual=records(folder/'actual_rows.jsonl');columns=records(folder/'original_columns.jsonl')
            omitted=[n for n in qrows if 'pc162_qL_'+n not in actual]
            for e in ('L','U'):
                weight=x['pc162_lambda_'+e];y={n:x['pc162_'+e+'_'+n]/weight for n in columns if 'pc162_'+e+'_'+n in x} if weight>0 else {}
                total=math.fsum(v for n,v in y.items() if n.startswith('Y_'));worst=0.;worst_row=None
                for n in qrows:
                    r=rows[n];a=math.fsum(c*y[v] for v,c in r['terms'].items())-r['rhs']
                    violation=abs(a) if r['sense']=='=' else a if r['sense']=='<' else -a
                    if violation>worst:worst,worst_row=violation,n
                times=[dict(row=n,endpoint_lhs=math.fsum(c*y[v] for v,c in rows[n]['terms'].items()),rhs=rows[n]['rhs']) for n in omitted]
                entry['endpoint_checks'].append(dict(form=tag,endpoint=e,weight=weight,total_inventory=total,
                    maximum_Q_violation=worst,worst_Q_row=worst_row,omitted_time_rows=times,
                    continuous_point=True,integer_fleet=False))
        output.append(entry)
    write(OUT/'reports/endpoint_explanation.json',output)
    print(json.dumps(output,indent=2),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
