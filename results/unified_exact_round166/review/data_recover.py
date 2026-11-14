"""Independent Round166 physical/source audit. Standard library, no optimizer.

Only the selected endpoint/audit/result members are read from existing carriers.
The scientific exact fractions below use the actual parsed binary64 weights and
lambda. Native qualification remains numerical (the inherited 1e-7 policy).
"""
from pathlib import Path
from fractions import Fraction as F
import ast, hashlib, json, math, re, subprocess, time, zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
START = time.perf_counter()
TOL = 1e-7

def sha(data): return hashlib.sha256(data).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
def frac(x): return F(x) if isinstance(x, int) else F.from_float(x)
def fstr(x): return str(x.numerator)+'/'+str(x.denominator)
def source_bytes(rel):
    p=ROOT/rel
    if p.is_file(): return p.read_bytes()
    return subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)

def parse_input(p):
    raw=source_bytes(p['input_path']); text=raw.decode('utf-8-sig')
    def vec(name): return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    first=text.splitlines()[0]
    q=ast.literal_eval(first[first.index('['):])
    n,m=map(int,first[:first.index('[')].split())
    assert n==p['V'] and m==p['M'] and q==p['Q_vector']
    a=dict(n=n,m=m,Q=q,b=vec('initial'),D=vec('target'),c=vec('capacities'),xy=vec('points'),w=vec('weights'))
    if abs(max(a['w'][1:])-10)<1e-6: a['w']=[v/10 for v in a['w']]
    assert all(len(a[k])==n+1 for k in ['b','D','c','xy','w'])
    assert sha(raw)==p['input_sha256']
    return a,raw

def physical(a,p,routes):
    y=a['b'].copy(); seen=set(); cars=set();facts=[];complete=[]
    for rt in routes:
        k=rt.get('vehicle',rt.get('vehicle_id')); assert k not in cars and 0<=k<a['m'];cars.add(k)
        nodes=rt['nodes'];assert nodes[0]==nodes[-1]==0
        ops={}
        for op in rt['operations']:
            i,x,d=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in ops and int(x)==x and int(d)==d and x>=0 and d>=0 and bool(x)!=bool(d)
            ops[i]=(x,d)
        assert len(nodes[1:-1])==len(ops) and set(nodes[1:-1])==set(ops)
        load=pickup=drop=peak=0;prefix=[]
        for i in nodes[1:-1]:
            assert 1<=i<=a['n'] and i not in seen;seen.add(i);x,d=ops[i]
            load+=x-d;pickup+=x;drop+=d;peak=max(peak,load)
            assert 0<=load<=a['Q'][k];prefix.append(load)
            y[i]+=d-x;assert 0<=y[i]<=a['c'][i]
        travel=math.fsum(math.hypot(a['xy'][i][0]-a['xy'][j][0],a['xy'][i][1]-a['xy'][j][1])/1.5 for i,j in zip(nodes,nodes[1:]))
        handling=pickup*p['pickup_seconds']+drop*p['drop_seconds']+load*p['drop_seconds']
        duration=travel+handling
        assert duration<=p['T_seconds']+TOL
        facts.append(dict(vehicle=k,Q=a['Q'][k],nodes=nodes,pickups=pickup,drops=drop,return_load=load,prefix_loads=prefix,peak_prefix_load=peak,travel_seconds=travel,station_handling_seconds=pickup*p['pickup_seconds']+drop*p['drop_seconds'],return_unloading_seconds=load*p['drop_seconds'],handling_seconds=handling,duration_seconds=duration,time_utilization=duration/p['T_seconds']))
        complete.append(dict(vehicle=k,nodes=nodes,operations=[dict(station=i,pickup=ops[i][0],drop=ops[i][1]) for i in nodes[1:-1]]))
    for k in range(a['m']):
        if k not in cars:
            complete.append(dict(vehicle=k,nodes=[0,0],operations=[]))
            facts.append(dict(vehicle=k,Q=a['Q'][k],nodes=[0,0],pickups=0,drops=0,return_load=0,prefix_loads=[],peak_prefix_load=0,travel_seconds=0,station_handling_seconds=0,return_unloading_seconds=0,handling_seconds=0,duration_seconds=0,time_utilization=0))
    assert sum(y[1:])+sum(q['return_load'] for q in facts)==sum(a['b'][1:])
    ratios=[F(y[i],a['D'][i]) for i in range(1,a['n']+1)];s=sum(ratios,F(0))
    g=sum((abs(x-z) for j,x in enumerate(ratios) for z in ratios[j+1:]),F(0))/(a['n']*s) if s else F(0)
    penalty=sum((frac(a['w'][i])*abs(ratios[i-1]-1) for i in range(1,a['n']+1)),F(0))
    omega=sum((frac(x) for x in a['w'][1:]),F(0)); lam=frac(p['lambda']);rho=lam*omega
    obj=g+lam*penalty
    return dict(Y=y,G=float(g),P=float(penalty),F=float(obj),p=float(penalty/omega),Omega=float(omega),lambda_value=p['lambda'],rho_binary64=p['lambda']*math.fsum(a['w'][1:]),exact=dict(G=fstr(g),P=fstr(penalty),p=fstr(penalty/omega),Omega=fstr(omega),lambda_value=fstr(lam),rho=fstr(rho)),routes=sorted(complete,key=lambda q:q['vehicle']),operations=sorted(facts,key=lambda q:q['vehicle']),pickups=sum(q['pickups'] for q in facts),drops=sum(q['drops'] for q in facts),returns=sum(q['return_load'] for q in facts),total_inventory=sum(y[1:]),total_initial=sum(a['b'][1:]),total_target=sum(a['D'][1:]),maximum_duration=max(q['duration_seconds'] for q in facts),target_under=sum(y[i]<a['D'][i] for i in range(1,a['n']+1)),target_equal=sum(y[i]==a['D'][i] for i in range(1,a['n']+1)),target_over=sum(y[i]>a['D'][i] for i in range(1,a['n']+1)))

def compact_qualified_cover(cover,audit_binding,row):
    """Reference the old audited cover without republishing its trajectory.

    The SHA of the complete parsed cover is over canonical UTF-8 JSON; the
    separate audit/member SHA binds its original bytes. This function makes
    no new native/global qualification decision. All old original evidence
    remains in the pinned historical carrier.
    """
    canonical=json.dumps(cover,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    result=dict(schema='round166-historical-cover-reference-v1',
        historical_source_reference_not_new_qualification=True,
        source_audit=dict(archive=audit_binding['archive'],archive_SHA256=audit_binding['archive_SHA'],
            member=audit_binding['member'],member_SHA256=audit_binding['SHA256'],member_bytes=audit_binding['bytes']),
        complete_parsed_cover_canonical_JSON_SHA256=sha(canonical),
        cover_hash_serialization='UTF-8 json.dumps(sort_keys=True,separators=(comma,colon),ensure_ascii=False,allow_nan=False)',
        original_global_L=row['L'],original_certificate_basis=row['certificate_basis'],present=cover is not None)
    if cover is None:
        result['summary']=dict(qualification_kind='complete original compact native source; no interval-cover object',
            original_native_proof_qualified=row['native_proof_qualified'])
        return result
    scalar_keys=['L','raw_trace_final_L','complete_coverage','all_relevant_closed','live_leaves','open_leaves','covered_gini_upper']
    leaf_keys=['leaf_id','parent_id','gamma_L','gamma_U','lower_bound','status',
        'coalesced_block_id','coverage_member_ids','closure_source','lower_bound_sources',
        'single_child_contraction_parent','strict_infeasible_half_verified',
        'contracted_infeasible_gamma_L','contracted_infeasible_gamma_U','contraction_source']
    proof_keys=['call','lo','hi','L','cutoff','sequence','source','native_status','full_original','native_log_SHA']
    result['summary']={k:cover[k] for k in scalar_keys if k in cover}
    result['summary'].update(leaf_scopes=[{k:l[k] for k in leaf_keys if k in l and l[k]!=''} for l in cover.get('leaves',[])],
        scoped_proof_sources=[{k:p[k] for k in proof_keys if k in p} for p in cover.get('scoped_proofs',[])],
        omitted_historical_timeline_rows=len(cover.get('timeline',[])),
        historical_full_cover_recoverable_from_pinned_audit=True)
    return result

if __name__ == "__main__":
    records=[];members=[];inputs={};missing=[];qualifications=[]
    for rnd,stage in [(134,'C'),(134,'D'),(137,None)]:
        d=ROOT/f'results/unified_exact_round{rnd}'
        rows=read(d/f'reports/{stage+"/" if stage else ""}arms.json')
        rows=[r for r in rows if r['role'] in ['K-15-S','UC-B20-B']] if rnd==134 else [r for r in rows if r['stage'] in ['B2','B3']]
        matrix=read(d/(stage+'_matrix_frozen.json' if stage else 'matrix_frozen.json'))
        carriers={q['name']:q for q in read(d/'raw_archive_manifest.json')['archives']}
        for row in rows:
            group=next(q for q in matrix['groups'] if q['position']==row['position'])
            launch=group['launch'];p=launch['panel'];rel=row['destination'].replace('\\','/').split(f'results/unified_exact_round{rnd}/',1)[1]
            sub=rel.split('/')[1];name='campaign_'+sub+'.zip';archive=d/'artifacts'/name
            try:
                raw=archive.read_bytes();assert sha(raw)==carriers[name]['SHA256']
                with zipfile.ZipFile(archive) as z:
                    vals={}
                    for suffix in ['audit.json','result.json',f'round{134 if rnd==134 else 135}_endpoint.json','verification_closeout.json']:
                        member=f'results/unified_exact_round{rnd}/{rel}/{suffix}'
                        b=z.read(member);vals[suffix]=json.loads(b)
                        members.append(dict(archive=archive.relative_to(ROOT).as_posix(),archive_SHA=sha(raw),member=member,bytes=len(b),SHA256=sha(b)))
            except (FileNotFoundError,KeyError) as e:
                missing.append(dict(round=rnd,stage=stage,position=row['position'],role=row['role'],reason=str(e)));continue
            audit=vals['audit.json'];endpoint=vals[f'round{134 if rnd==134 else 135}_endpoint.json'];closeout=vals['verification_closeout.json']
            assert audit['passed'] and audit['implementation_qualified'] and audit['evidence_complete']
            assert closeout['necessary_verification_complete'] and closeout['evidence_complete']
            assert endpoint['native_proof_qualified'] and endpoint['implementation_qualified'] and endpoint['formal_protocol_qualified']
            assert not row['source_rejected'] and not audit['source_rejections']
            assert abs(row['L']-endpoint['L'])<1e-14 and abs(row['U']-endpoint['U'])<1e-14
            a,input_raw=parse_input(p);v=physical(a,p,audit['physical']['routes'])
            assert v['Y']==audit['physical']['Y']
            assert all(abs(v[k]-row[k])<1e-12 for k in ['G','P','F'])
            assert abs(v['F']-row['U'])<TOL and row['L']<=v['F']+TOL
            assert row['certificate'] or row['T_cert'] is None
            base=row['role'].split('-rho',1)[0]
            family=f'R{rnd}:{base}'
            physical_signature=dict(a,T=p['T_seconds'],pickup_seconds=p['pickup_seconds'],drop_seconds=p['drop_seconds'])
            phys_sha=sha(json.dumps(physical_signature,sort_keys=True,separators=(',',':')).encode())
            normalized=[fstr(frac(w)/F(v['exact']['Omega'])) for w in a['w'][1:]]
            if family not in inputs:
                inputs[family]=dict(family=family,physical=physical_signature,physical_SHA=phys_sha,normalized_weights=normalized,input_path=p['input_path'],input_SHA=sha(input_raw),input_text=input_raw.decode('utf-8-sig'))
            else:
                assert inputs[family]['physical_SHA']==phys_sha and inputs[family]['normalized_weights']==normalized
            rid=f'R{rnd}:{row["stage"]}:{row["position"]}'
            audit_binding=next(m for m in members[-4:] if m['member'].endswith('/audit.json'))
            rec=dict(record_id=rid,round=rnd,stage=row['stage'],position=row['position'],role=row['role'],base_role=base,method=row['method'],seed=row['seed'],repeat=row['repeat'],family=family,physical_SHA=phys_sha,parameter_analysis=rnd==134 or base in ['R-B20-S-T1','R-X35-S-T2'],resource_analysis=rnd==137 and row['stage']=='B2',original=row,verified=v,source=dict(archive=archive.relative_to(ROOT).as_posix(),archive_SHA=sha(raw),member_prefix=f'results/unified_exact_round{rnd}/{rel}',input_path=p['input_path'],input_SHA=sha(input_raw)),lower_qualified=True,lower_safety_margin=TOL,global_L=row['L'],conservative_global_L=float(F.from_float(row['L'])-F(1,10_000_000)),qualification=dict(basis=row['certificate_basis'],endpoint_qualified=True,implementation_qualified=True,evidence_complete=True,native_proof_qualified=True,source_rejected=False,qualified_cover=compact_qualified_cover(audit.get('qualified_cover'),audit_binding,row),endpoint_numbers_qualified=endpoint.get('numbers_qualified'),original_numeric_policy='inherited absolute closure/source tolerance 1e-7; this analysis subtracts 1e-7 before chord construction',lower_is_global_original_physical_problem=True))
            records.append(rec)
    
    write('data_physical_archive.json',dict(schema='round166-independent-physical-archive-v1',records=records,inputs=list(inputs.values()),missing=missing,source_members=members,source_methods_preserved=True,offline_only=True,new_Optimize=0))
    resource=[]
    for base in ['R-B20-S','R-X20-S','R-B35-S','R-X35-S']:
        rr=[r for r in records if r['resource_analysis'] and r['base_role'].startswith(base+'-T')]
        one=[r for r in rr if r['base_role']==base+'-T1'];two=[r for r in rr if r['base_role']==base+'-T2']
        ia=inputs[one[0]['family']]['physical'].copy();ib=inputs[two[0]['family']]['physical'].copy();t1=ia.pop('T');t2=ib.pop('T')
        assert ia==ib and t1<t2
        assert all(r['verified']['exact']['lambda_value']==one[0]['verified']['exact']['lambda_value'] for r in rr)
        lo1=max(one,key=lambda r:r['global_L']);lo2=max(two,key=lambda r:r['global_L']);up1=min(one,key=lambda r:r['verified']['F']);up2=min(two,key=lambda r:r['verified']['F'])
        b1=next(r for r in one if r['method']=='S2');b2=next(r for r in two if r['method']=='S2')
        low=max(0,lo1['global_L']-up2['verified']['F']);high=up1['verified']['F']-lo2['global_L']
        resource.append(dict(base=base,T1=t1,T2=t2,physical_nested_verified=True,L1=lo1['global_L'],U1=up1['verified']['F'],L2=lo2['global_L'],U2=up2['verified']['F'],lower_improvement=low,upper_improvement=high,width=high-low,conservative_lower_improvement=max(0,low-2*TOL),conservative_upper_improvement=high+2*TOL,lower1_source=lo1['record_id'],upper1_source=up1['record_id'],lower2_source=lo2['record_id'],upper2_source=up2['record_id'],B_T1=b1['record_id'],B_T2=b2['record_id'],B_operations_T1=b1['verified'],B_operations_T2=b2['verified']))
    write('data_resource_pairs.json',resource)
    summary=dict(UTC=datetime.now(timezone.utc).isoformat(),reviewer='independent data_review agent',passed=not missing,records=len(records),parameter_records=sum(r['parameter_analysis'] for r in records),resource_records=sum(r['resource_analysis'] for r in records),physical_families=len(inputs),missing=missing,source_members_read=len(members),full_fleets_verified=len(records),all_global_L_qualification_pass=True,input_physical_and_normalized_weight_identity_verified=True,actual_float_rho_kept=True,exact_rational_objective_available=True,route_and_all_inventory_prefixes_verified=True,empty_departure_and_loaded_return_unloading_verified=True,new_Optimize=0,outer_seconds=time.perf_counter()-START,resource_summaries=[{k:v for k,v in r.items() if not k.startswith('B_operations')} for r in resource])
    write('data_review_initial.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
