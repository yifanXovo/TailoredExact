"""Fixed serial table, complete bounded selection, and resumable formal stages."""
from round127_common import *
from round127_campaign import prepare_group,execute,reconstruct
import copy,csv,math

def fixed_remaining_nominal():
    m=read(OUT/'experiment_manifest.json');total=0
    for pos in m['E1_training']:
        p=pos['role'];name=f'training/{pos["position"]:02d}_{p["id"]}_S{pos["seed"]}_{pos["configuration"]["id"]}'
        if not (OUT/name/'reconstructed.json').exists():total+=p['cap_seconds']
    for j,p in enumerate(m['E0_main'],1):
        if not (OUT/f'main/{j:02d}_{p["id"]}/reconstructed.json').exists():total+=2*p['cap_seconds']
    for g in m['E0_tiny']:
        p=g['role'];name=f'tiny/{g["group"]:02d}_{p["id"]}_S{g["seed"]}_R{g["repeat"]}'
        if not (OUT/name/'reconstructed.json').exists():total+=2*p['cap_seconds']
    selected=read(OUT/'tuning_selection.json')['selected']['id'] if (OUT/'tuning_selection.json').exists() else None
    admitted=read(OUT/'review/performance_admission.json')['qualified_methods']
    for g in m['E1_core']:
        if not (OUT/f'core/{g["group"]:02d}_{g["role"]["id"]}/reconstructed.json').exists():
            total+=g['role']['cap_seconds']*sum(x in admitted and not (x=='PT' and selected=='q0') for x in g['methods'])
    return total
def result(name):return read(OUT/name/'reconstructed.json')['arms']
def run(name,kind,p,methods,seed,repeat=1,config=None):
    gate=read(OUT/'review/performance_admission.json')
    assert all(method in gate['qualified_methods'] for method in methods),(name,methods)
    camp=OUT/name
    if not (camp/'identity.json').exists():prepare_group(name,'E0' if name.startswith(('main/','tiny/')) else 'E1',p,methods,seed,repeat,config)
    if (camp/'reconstructed.json').exists():return result(name)
    b=budget();remaining_nominal=fixed_remaining_nominal()
    assert b['remaining_outer_seconds']>=remaining_nominal+1800,('remaining fixed caps plus management reserve no longer covered',b,remaining_nominal)
    label=name.replace('/','_')
    attempts=len(list((OUT/'fees').glob(label+'*')))
    # A failed verifier may resume a sealed producer once its administrative
    # issue is explained; execution never reruns an existing native arm.
    if attempts:label+=f'_read_recovery{attempts:02d}'
    rc=metered(label,kind,[PYTHON,'-B','scripts/round127_campaign.py',name])
    if rc:raise RuntimeError('Preserved failed group '+name+'; inspect evidence before any recovery')
    return result(name)
def training():
    gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
    assert sha(E1)==gate['E1_SHA'] and source_bindings()==read(OUT/'E1_frozen.json')['source_bindings']
    manifest=read(OUT/'experiment_manifest.json')
    for position in manifest['E1_training']:
        p=copy.deepcopy(position['role']);p.update(source='development',inventory='unspecified')
        name=f'training/{position["position"]:02d}_{p["id"]}_S{position["seed"]}_{position["configuration"]["id"]}'
        run(name,'training',p,['P'],position['seed'],config=position['configuration'])
        (OUT/'RESUME.md').write_text(f'Round127 v3 training.\n\nSealed {position["position"]}/36 fixed positions. Next={position["position"]+1}.\nAll input/config orders remain immutable. No evaluation outcome used for selection.\n',encoding='utf-8')
    select()
def select():
    manifest=read(OUT/'experiment_manifest.json');rows=[];scores=[]
    for pos in manifest['E1_training']:
        p=pos['role'];name=f'training/{pos["position"]:02d}_{p["id"]}_S{pos["seed"]}_{pos["configuration"]["id"]}'
        arms=result(name);assert len(arms)==1;a=arms[0]
        good=all(a.get(k) for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) and not a.get('source_reduced')
        rows.append(dict(position=pos['position'],id=p['id'],seed=pos['seed'],configuration=pos['configuration']['id'],
            qualified=good,certificate=bool(a.get('certificate')),T_cert=a['T_cert'],T_produce=a['T_produce'],cap_seconds=p['cap_seconds'],
            U=a['U'],L=a['L'],signed_gap=a['U']-a['L'],q_score=a['T_cert']/p['cap_seconds'] if good and a.get('certificate') else 1 if good else None,
            identity_SHA=sha(OUT/name/'identity.json'),result_SHA=sha(OUT/name/'reconstructed.json'),destination=a['destination']))
    assert len(rows)==36
    for c in manifest['configurations']:
        rr=[r for r in rows if r['configuration']==c['id']];assert len(rr)==6
        perseed={str(s):sum(r['certificate'] and r['qualified'] for r in rr if r['seed']==s) for s in [2,3]}
        scores.append(dict(c,complete_qualified=all(r['qualified'] for r in rr),N=sum(r['certificate'] and r['qualified'] for r in rr),
            N_by_seed=perseed,N_min=min(perseed.values()),S_q=sum(r['q_score'] for r in rr)/6 if all(r['qualified'] for r in rr) else None))
    q0=scores[0];eligible=[]
    if q0['complete_qualified']:
        for q in scores[1:]:
            if q['complete_qualified'] and q['N']>=q0['N'] and q['N_min']>=q0['N_min'] and (
                q['N']>q0['N'] or q['N']==q0['N']>0 and q['S_q']<q0['S_q'] and q['S_q']<=.90*q0['S_q']):eligible.append(q)
        selected=sorted(eligible,key=lambda q:(-q['N'],-q['N_min'],q['S_q'],q['nondefault_parameters'],int(q['id'][1:])))[0] if eligible else q0
    else:selected=None
    value=dict(UTC=utc(),status='SELECTED' if selected else 'PT_BLOCKED_Q0_INCOMPLETE',selected=selected,scores=scores,
        eligible_nondefault=[q['id'] for q in eligible],training_positions=36,training_inputs=3,evaluation_results_consulted=0,
        all_rows=rows,unqualified_not_scored_as_open=True,open_penalty_is_not_T_cert=True,
        interpretation='No stable increment identified within this bounded screen' if selected and selected['id']=='q0' else 'One predeclared configuration selected; held-out evaluation pending',
        selected_prm_SHA=sha(OUT/'tuning_manifest'/(selected['id']+'.prm')) if selected else None,
        E1_SHA=sha(E1),DLL_SHA=sha(DLL))
    if (OUT/'tuning_selection.json').exists():
        old=read(OUT/'tuning_selection.json');value['UTC']=old['UTC'];assert value==old,'selection drift'
    else:
        write(OUT/'tuning_selection.json',value)
        table(OUT/'training_arms.csv',rows);table(OUT/'training_scores.csv',scores)
        if selected:(OUT/'selected_P.prm').write_bytes((OUT/'tuning_manifest'/(selected['id']+'.prm')).read_bytes())
    print(json.dumps(dict(status=value['status'],selected=selected,scores=scores)),flush=True)
def table(path,rows):
    p=Path(path);keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
def formal(stage):
    m=read(OUT/'experiment_manifest.json');inputs=read(OUT/'input_manifest.json')
    if stage=='main':
        for j,p in enumerate(m['E0_main'],1):
            methods=['P' if x=='P-GRB' else 'MB' for x in p['method_order']]
            run(f'main/{j:02d}_{p["id"]}','formal_E0_main',p,methods,1)
    elif stage=='tiny':
        byid={p['id']:p for p in inputs['tiny_roles']}
        for g in m['E0_tiny']:
            p=byid[g['role']['id']]
            run(f'tiny/{g["group"]:02d}_{p["id"]}_S{g["seed"]}_R{g["repeat"]}','formal_E0_tiny',p,g['methods'],g['seed'],g['repeat'])
    elif stage=='core':
        sel=read(OUT/'tuning_selection.json');assert sel['status']=='SELECTED'
        # Verify that the selection bytes were committed before any evaluation.
        commit=git('rev-parse','HEAD').decode().strip()
        assert git('show',commit+':results/unified_exact_round127/tuning_selection.json')==(OUT/'tuning_selection.json').read_bytes()
        selected=sel['selected'];aliases=[];blocked=[]
        admitted=read(OUT/'review/performance_admission.json')['qualified_methods']
        for g in m['E1_core']:
            methods=[x for x in g['methods'] if x in admitted and (x!='PT' or selected['id']!='q0')]
            blocked.extend(dict(id=g['role']['id'],method=x,status='BLOCKED_BEFORE_FORMAL',reason='MD inclusive-root/own-U0-Start obligation fails inherited equality closure boundary',
                review='review/preformal_cutoff_boundary_review.md',not_a_mechanism_negative=True) for x in g['methods'] if x not in admitted)
            name=f'core/{g["group"]:02d}_{g["role"]["id"]}'
            arms=run(name,'formal_E1_core',g['role'],methods,1,config=selected)
            if selected['id']=='q0':
                p=next(a for a in arms if a['method']=='P')
                aliases.append(dict(id=g['role']['id'],alias='PT',target_method='P',target_destination=p['destination'],
                    target_result_SHA=sha(OUT/name/'reconstructed.json'),reason='q0 selected; identical method; no additional observation or zero-time speedup'))
        write(OUT/'PT_aliases.json',aliases)
        write(OUT/'blocked_core_arms.json',blocked)
    else:raise ValueError(stage)
if __name__=='__main__':
    if sys.argv[1]=='training':training()
    elif sys.argv[1]=='select':select()
    else:formal(sys.argv[1])
