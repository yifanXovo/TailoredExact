"""Portable stdlib-only raw-evidence reader: zero solver/native/subprocess calls."""
import argparse,ast,csv,hashlib,json,math,re
from pathlib import Path

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def table(p,data):
    if not data:return
    fields=list(dict.fromkeys(k for r in data for k in r))
    with Path(p).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(data)
def portable(root,path):
    s=str(path).replace('\\','/')
    for marker in ['results/','reference/','scripts/','src/','include/']:
        if marker in s:return root/s[s.index(marker):]
    p=Path(s);assert not p.is_absolute(),('unsupported original absolute path',path);return root/p
def vec(text,name):return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
def physical(root,p,w):
    text=(root/p['input_path']).read_text();b=vec(text,'initial');D=vec(text,'target');c=vec(text,'capacities');points=vec(text,'points');weights=vec(text,'weights')
    if abs(max(weights[1:])-10)<=1e-6:weights=[x/10 for x in weights]
    Q=ast.literal_eval('['+text.splitlines()[0].split('[',1)[1])
    Y=b.copy();seen=set();cars=set();durations=[];returns=[];pickups=[]
    for r in w['routes']:
        k=r['vehicle'];assert k not in cars and 0<=k<len(Q);cars.add(k);nodes=r['nodes'];assert nodes[0]==nodes[-1]==0
        op={}
        for o in r['operations']:
            i,a,d=(o['station'],o['pickup'],o['drop']) if isinstance(o,dict) else o
            assert i not in op and a>=0 and d>=0 and int(a)==a and int(d)==d and bool(a)!=bool(d);op[i]=(a,d)
        assert set(nodes[1:-1])==set(op);load=0;P=0
        for i in nodes[1:-1]:
            assert i not in seen and 1<=i<len(b);seen.add(i);a,d=op[i];load+=a-d;P+=a;assert 0<=load<=Q[k]
            Y[i]+=d-a;assert 0<=Y[i]<=c[i]
        travel=sum(math.hypot(points[a][0]-points[d][0],points[a][1]-points[d][1])/1.5 for a,d in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*P
        assert duration<=p['T_seconds']+1e-7;durations.append(duration);returns.append(load);pickups.append(P)
    assert sum(Y[1:])==sum(b[1:])-sum(returns)
    r=[Y[i]/D[i] for i in range(1,len(b))];S=sum(r)
    G=sum(abs(a-d) for i,a in enumerate(r) for d in r[i+1:])/(len(r)*S) if S>0 else 0
    F=G+p['lambda']*sum(weights[i]*abs(r[i-1]-1) for i in range(1,len(b)))
    reported=w.get('F',w.get('objective'));assert reported is not None and abs(F-reported)<1e-7
    return dict(F=F,Y=Y,maximum_duration=max(durations,default=0),pickups=pickups,return_loads=returns)

def native(out,root):
    records=[]
    current_scopes=None
    if out.name=='unified_exact_round106':
        current_scopes={'qualification','fixed_Y'}
        for p in out.iterdir():
            if p.is_dir() and (p/'identity.json').exists() and 'launches' in read(p/'identity.json'):
                current_scopes.add(p.name)
    for p in sorted(out.rglob('calls.csv')):
        if 'r105_supplement' in p.parts:continue
        # Failed recovery copies are inherited evidence, not new native calls.
        # Count only this round's declared qualification/diagnostic/campaign roots.
        if current_scopes is not None and p.relative_to(out).parts[0] not in current_scopes:continue
        rr=rows(p)
        for phase in ['master','oracle','iis','core_confirm']:
            before=[r for r in rr if r['phase']==phase and r['stage']=='before'];after=[r for r in rr if r['phase']==phase and r['stage']=='after']
            if before:
                assert len(after)<=len(before)
                records.append(dict(path=p.relative_to(root).as_posix(),phase=phase,started=len(before),returned=len(after),missing_after=len(before)-len(after),native_seconds=sum(float(r['seconds']) for r in after)))
    return records
def fees(out,root,legacy=False):
    records=[]
    for folder in sorted((out/'fees').iterdir()):
        launch=read(folder/'launch.json');receipt=read(folder/'receipt.json');cmd=launch['command'];children=0
        script=str(cmd[1]).replace('\\','/').split('/')[-1] if len(cmd)>1 else ''
        if legacy:
            if script=='round105_campaign.py' and cmd[2]=='prepare':children=read(out/cmd[3]/'identity.json')['reference_children']
            elif script=='round105_campaign.py' and cmd[2]=='run':
                a=read(out/cmd[3]/'identity.json')['launches'][int(cmd[4])-1];children=int((portable(root,a['destination'])/'process_start_marker.json').exists())
            elif script=='round105_batch.py':
                q=read(out/cmd[2]/'identity.json');children=sum((portable(root,a['destination'])/'process_start_marker.json').exists() for a in q['launches'][int(cmd[3])-1:int(cmd[4])])
            elif script=='round105_modes.py' and cmd[2]=='batch':
                plan=read(portable(root,cmd[3]));children=sum((root/read(out/'modes'/j['label']/'manifest.json')['modes'][j['number']-1]['path']/'native_launch.json').exists() for j in plan['jobs'])
            elif 'review' in str(cmd[1]):
                record=out/'review/native_execution.json';children=read(record).get('subprocess_starts',0) if record.exists() else 0
        else:
            children=launch['declared_nested_process_starts'];assert receipt['conservative_process_starts']==1+children
        records.append(dict(label=folder.name,outer_seconds=receipt['outer_seconds'],exit_code=receipt['exit_code'],stop_reason=receipt['stop_reason'],outer_process_starts=1,nested_process_starts=children,conservative_process_starts=1+children))
    return records
def pairs(arms,campaign,candidate_prefix):
    pp=[]
    for role in sorted({a['id'] for a in arms if a['campaign']==campaign}):
        g=[a for a in arms if a['campaign']==campaign and a['id']==role]
        for a in g:
            if not a['arm'].startswith(candidate_prefix):continue
            for c in g:
                if c['arm'] not in ['P-GRB','ENS-C']:continue
                assert a['audit_passed'] and c['audit_passed']
                cl='both_certified' if a['certificate'] and c['certificate'] else 'candidate_certified_control_censored' if a['certificate'] else 'control_certified_candidate_censored' if c['certificate'] else 'both_censored'
                pp.append(dict(id=role,candidate=a['arm'],control=c['arm'],classification=cl,candidate_seconds=a['observed_end_to_end_seconds'],control_seconds=c['observed_end_to_end_seconds'],candidate_U=a['U'],candidate_L=a['L'],control_U=c['U'],control_L=c['L'],certified_time_ratio=a['observed_end_to_end_seconds']/c['observed_end_to_end_seconds'] if cl=='both_certified' else None))
    return pp
def legacy(root,dest):
    out=root/'results/unified_exact_round105';arms=[]
    for camp in sorted(out.iterdir()):
        if not (camp/'identity.json').exists():continue
        identity=read(camp/'identity.json')
        for a in identity['launches']:
            d=portable(root,a['destination'])
            if not (d/'completion.json').exists():continue
            completion=read(d/'completion.json');recovered=(d/'audit_recovery.json').exists();audit=read(d/('audit_recovery.json' if recovered else 'audit.json'))
            summary=read(d/'external/round105/summary.json') if (d/'external/round105/summary.json').exists() else {};ep=audit.get('endpoint') or {}
            if ep and audit['passed'] and (d/'result.json').exists():
                checked=physical(root,a['panel'],read(d/'result.json'));assert abs(checked['F']-ep['U'])<1e-7 and ep['L']<=ep['U']+1e-7
            arms.append(dict(campaign=camp.name,id=a['id'],arm=a['arm'],cap_seconds=a['cap_seconds'],reserve_seconds=identity['prereg']['common']['shutdown_margin_seconds'],observed_end_to_end_seconds=completion['fully_observed_end_to_end_seconds'],audit_passed=audit['passed'],audit_recovery=recovered,status=ep.get('status','FAILED_NO_QUALIFIED_ENDPOINT'),certificate=ep.get('certificate',False),U=ep.get('U'),L=ep.get('L'),gap=ep.get('gap'),
                **{k:summary.get(k) for k in ['U0','iterations','conflicts','cache_hits','master_calls','oracle_calls','iis_calls','core_confirmation_calls','master_seconds','oracle_seconds','iis_seconds','core_confirmation_seconds']},
                control_native_calls=audit.get('native_scope_adapter',{}).get('native_calls'),PE_sha256=identity['candidate_binary_sha256'],input_sha256=a['panel']['input_sha256'],destination=d.relative_to(root).as_posix()))
    fee=fees(out,root,True);nc=native(out,root);controls=sum(a['control_native_calls'] or 0 for a in arms);ind=read(out/'review/native_execution.json')
    ii=sum(a['started'] for a in nc if a['phase']=='iis');reviewopt=ind.get('Optimize_starts',0);reviewiis=ind.get('IIS_starts',0)
    summary=dict(paid_process_starts=sum(a['conservative_process_starts'] for a in fee),paid_outer_seconds=sum(a['outer_seconds'] for a in fee),native_started=sum(a['started'] for a in nc),native_returned=sum(a['returned'] for a in nc),iis_started=ii,P_ENS_native_Optimize_calls=controls,independent_review_Optimize_starts=reviewopt,independent_review_IIS_starts=reviewiis,all_IIS_starts=ii+reviewiis,all_Optimize_starts=sum(a['started'] for a in nc)-ii+controls+reviewopt,missing_after=sum(a['missing_after'] for a in nc),nested_native_seconds_are_not_added_to_outer_fees=True,failed_fees=[a['label'] for a in fee if a['exit_code']!=0])
    assert summary['all_Optimize_starts']==163 and summary['all_IIS_starts']==37
    table(dest/'r105_arm_results.csv',arms);table(dest/'r105_paired_results.csv',pairs(arms,'control01','IR-'));table(dest/'r105_fees.csv',fee);table(dest/'r105_native_calls.csv',nc);write(dest/'r105_summary.json',summary)
    for name,new in [('arm_results.csv',dest/'r105_arm_results.csv'),('paired_results.csv',dest/'r105_paired_results.csv'),('fees.csv',dest/'r105_fees.csv'),('native_calls.csv',dest/'r105_native_calls.csv')]:compare_csv(out/'reports02'/name,new)
    for k,v in summary.items():
        old=read(out/'reports02/summary.json')[k];assert same(old,v),(k,old,v)
    return summary
def same(a,b):
    if str(a)==str(b):return True
    try:return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-9)
    except (ValueError,TypeError):return False
def compare_csv(expected,actual):
    a,b=rows(expected),rows(actual);assert len(a)==len(b),(expected,len(a),len(b))
    # row order is immaterial; full fields remain material.
    def key(r):return tuple(str(r.get(k,'')) for k in ['campaign','id','candidate','control','arm','label','path','phase'])
    for x,y in zip(sorted(a,key=key),sorted(b,key=key)):
        assert set(x)==set(y),(expected,set(x)^set(y))
        for k in x:
            a,b=(x[k].replace('\\','/'),y[k].replace('\\','/')) if k in ['destination','path'] else (x[k],y[k])
            assert same(a,b),(expected,k,x[k],y[k])

def current(root,dest):
    out=root/'results/unified_exact_round106';arms=[];events_all=[];cuts_all=[];modes_all=[]
    for camp in sorted(out.iterdir()):
        if not (camp/'identity.json').exists():continue
        ident=read(camp/'identity.json')
        if 'launches' not in ident:continue
        for a in ident['launches']:
            d=portable(root,a['destination']);completion=read(d/'completion.json');audit=read(d/'audit.json');assert audit['passed'];ep=audit['endpoint'];p=a['panel']
            result=read(d/'result.json');checked=physical(root,p,result);assert abs(checked['F']-ep['U'])<1e-7
            assert ep['L']<=ep['U']+1e-7;f=d/'external/round106';s=read(f/'summary.json') if f.exists() else {}
            row=dict(campaign=camp.name,id=a['id'],arm=a['arm'],cap_seconds=a['cap_seconds'],reserve_seconds=ident['prereg']['common']['shutdown_margin_seconds'],observed_end_to_end_seconds=completion['fully_observed_end_to_end_seconds'],audit_passed=audit['passed'],status=ep['status'],certificate=ep['certificate'],U=ep['U'],L=ep['L'],gap=ep['U']-ep['L'],control_native_calls=audit.get('native_scope_adapter',{}).get('native_calls'),PE_sha256=ident['candidate_binary_sha256'],input_sha256=p['input_sha256'],destination=d.relative_to(root).as_posix())
            for k in ['U0','events','distinct_fleet_candidates','distinct_Y','distinct_car_modes','repeat_events','cache_hits','structural_proofs','pool_rows','lazy_calls','rejected_events','feasible_candidates','unknown_candidates','new_physical_UBs','submission_attempts','master_calls','oracle_calls','iis_calls','core_confirmation_calls','master_inclusive_seconds','callback_inclusive_seconds','master_exclusive_seconds','oracle_seconds','iis_seconds','core_confirmation_seconds','separation_seconds','audit_mapping_seconds','callback_other_seconds','first_new_candidate_seconds','first_new_physical_UB_seconds','outer_cancelled','inner_cancelled','unresolved_candidate','final_native_bound_qualified']:row[k]=s.get(k)
            if s:
                assert abs(s['UB']-ep['U'])<1e-7 and abs(s['LB']-ep['L'])<1e-7 and s['certified']==ep['certificate']
                seed=physical(root,p,read(f/'seed.json'));assert abs(seed['F']-s['U0'])<1e-7
                pp=[s[k] for k in ['master_exclusive_seconds','oracle_seconds','iis_seconds','core_confirmation_seconds','separation_seconds','audit_mapping_seconds','callback_other_seconds']]
                assert min(pp)>=-1e-6 and abs(sum(pp)-s['master_inclusive_seconds'])<1e-6
                ev=[json.loads(line) for line in (f/'events.jsonl').read_text().splitlines()];cuts=rows(f/'lazy.csv')
                assert len(ev)==s['events'] and len(cuts)==s['lazy_calls']
                events_all.extend(dict(campaign=camp.name,id=a['id'],arm=a['arm'],**e) for e in ev)
                cuts_all.extend(dict(campaign=camp.name,id=a['id'],arm=a['arm'],**c) for c in cuts)
                seen=set()
                for e in ev:
                    for k,q in enumerate(e['operations']):
                        key=(k,tuple(q))
                        if key not in seen:
                            seen.add(key);modes_all.append(dict(campaign=camp.name,id=a['id'],arm=a['arm'],source='current_formal_MIPSOL',event=e['event'],vehicle=k,Y=json.dumps(e['Y']),operations=json.dumps(q),nonzero=sum(v!=0 for v in q),candidate=d.relative_to(root).as_posix()+f'/external/round106/candidate_{e["event"]}.sol',outcome=e['outcome']))
                row['A_lazy_calls']=sum(c['family'].startswith('A_') for c in cuts);row['B_lazy_calls']=sum(c['family'].startswith('B_') for c in cuts);row['fallback_lazy_calls']=sum(c['family'] in ['FULL','CORE'] for c in cuts)
                row['same_Y_distinct_fleet_excess']=s['distinct_fleet_candidates']-s['distinct_Y']
                row['native_exact_vector_acceptances']=sum(int(r['final_native_accepted']) for r in rows(f/'submission_acceptance.csv'))
            arms.append(row)
    fee=fees(out,root);nc=native(out,root);controls=sum(a['control_native_calls'] or 0 for a in arms)
    ii=sum(a['started'] for a in nc if a['phase']=='iis');starts=sum(a['conservative_process_starts'] for a in fee);seconds=sum(a['outer_seconds'] for a in fee)
    assert starts<=72 and seconds<=80000
    summary=dict(paid_process_starts=starts,paid_outer_seconds=seconds,native_started=sum(a['started'] for a in nc),native_returned=sum(a['returned'] for a in nc),all_IIS_starts=ii,all_Optimize_starts=sum(a['started'] for a in nc)-ii+controls,P_ENS_Optimize_starts=controls,missing_after=sum(a['missing_after'] for a in nc),failed_fees=[a['label'] for a in fee if a['exit_code']!=0],formal_arms=len(arms),nested_time_not_added=True,Optimize_calls=0,IIS_calls=0)
    table(dest/'arm_results.csv',arms);table(dest/'paired_results.csv',pairs(arms,'development01','EVENT-'));table(dest/'fees.csv',fee);table(dest/'native_calls.csv',nc);table(dest/'candidate_events.csv',events_all);table(dest/'conflict_submissions.csv',cuts_all);table(dest/'car_modes.csv',modes_all);write(dest/'summary.json',summary)
    return summary
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--legacy-root',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--inherited-only',action='store_true');ap.add_argument('--compare',type=Path);a=ap.parse_args()
    root=a.root.resolve();dest=a.out.resolve();dest.mkdir(parents=True,exist_ok=False)
    legacy_root=a.legacy_root.resolve() if a.legacy_root else root/'inherited_r105' if (root/'inherited_r105').exists() else root
    old=legacy(legacy_root,dest);new=None
    if not a.inherited_only:new=current(root,dest)
    if a.compare:
        for p in a.compare.glob('*.csv'):compare_csv(p,dest/p.name)
        expected=read(a.compare/'summary.json');actual=read(dest/'summary.json');assert expected==actual
    write(dest/'execution.json',dict(passed=True,root=str(root),legacy_root=str(legacy_root),reader_SHA=sha(__file__),Optimize_calls=0,IIS_calls=0,subprocess_starts=0,import_scope='Python standard library only; portable path separators normalized for old Windows CSV comparison',R105=old,R106=new))
    print(json.dumps(dict(passed=True,R105=old,R106=new,Optimize_calls=0,IIS_calls=0)))
if __name__=='__main__':main()
