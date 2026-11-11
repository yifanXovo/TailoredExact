"""One post-panel saved-evidence readback, separate from the online algorithm.

Same agent, different verification script; no independent personnel and no
Optimize. Run only after all timed producers and their original readers exit.
"""
from round162_common import *
from round162_audit import records,matrix,primal,exact_dual
from round162_analyze import inherited_functions
from fractions import Fraction as F
import ast,csv,collections,re

def native_log_stats(destination):
    result=[]
    for path in sorted((destination/'external/native_logs').glob('*.gurobi.log')):
        text=path.read_text(encoding='utf8',errors='replace')
        pattern=r'Explored ([0-9]+) nodes \(([0-9]+) simplex iterations\) in ([0-9.]+) seconds \(([0-9.]+) work units\)'
        for m in re.finditer(pattern,text):
            result.append(dict(path=path.relative_to(ROOT).as_posix(),kind='MIP',nodes=int(m[1]),iterations=int(m[2]),seconds=float(m[3]),Work=float(m[4])))
        pattern=r'Solved in ([0-9]+) iterations and ([0-9.]+) seconds \(([0-9.]+) work units\)'
        for m in re.finditer(pattern,text):
            result.append(dict(path=path.relative_to(ROOT).as_posix(),kind='LP',nodes=0,iterations=int(m[1]),seconds=float(m[2]),Work=float(m[3])))
    assert result
    return result

def source_audit(folder):
    s=read(folder/'source.json');assert s['source_calls']<=1
    if not s.get('source_calls'):return dict(source_calls=0,applicable=False,reason=s['reason'])
    assert not s['lower_consumed_by_formal_ledger'] and not s['primal_consumed'] and s['released']
    assert s['formal_new_columns']==0 and s['source_SHA256']==sha(folder/'model.lp')
    if not s['qualified']:
        assert not s['PC_ready'];return dict(source=s,qualified=False,projection_consumed=False)
    oc,ac,original,actual,stats=matrix(folder)
    pp=primal(folder,ac,actual);dd=exact_dual(folder,ac,actual)
    assert pp['qualifies_under_inherited_1e_6'] and s['diagnostic_global_transport']==min(s['raw_lower'],s['cutoff'])
    result=dict(source=s,matrix=stats,primal=pp,exact_dual_box=dd)
    cf=folder/'compact'
    if not (cf/'projection.json').exists():
        assert not s['PC_ready'];result['projection_consumed']=False;return result
    cut=read(cf/'projection.json');assert cut['source_SHA256']==sha(folder/'model.lp') and cut['duals_SHA256']==sha(folder/'lp_duals.jsonl')
    cc=records(cf/'actual_columns.jsonl');cr=records(cf/'actual_rows.jsonl')
    assert cc==oc==records(cf/'original_columns.jsonl') and original==records(cf/'original_rows.jsonl')
    assert all(cr[n]==r for n,r in original.items())
    assert len(cr)==len(original)+int(cut['active']) and cut['new_columns_submitted']==0
    assert set(cut['row']['terms'])<=set(oc)
    if cut['active']:assert cr['pc162_projected']==cut['row']
    dual=records(folder/'lp_duals.jsonl');aggregate={n:F(0) for n in ac};rhs=F(0);used=set()
    for w in map(json.loads,(cf/'projection_multipliers.jsonl').read_text().splitlines()):
        n=w['row'];assert n.startswith('pc162_') and not n.startswith('pc162_saved_') and n not in used;used.add(n)
        r=actual[n];raw=dual[n]['dual'];p=min(0.,raw) if r['sense']=='<' else max(0.,raw) if r['sense']=='>' else raw
        assert w['used']==p and w['raw']==raw and p!=0
        rhs-=F(p)*F(r['rhs'])
        for name,c in r['terms'].items():aggregate[name]-=F(p)*F(c)
    for n,r in actual.items():
        if n.startswith('pc162_'):
            raw=dual[n]['dual'];p=min(0.,raw) if r['sense']=='<' else max(0.,raw) if r['sense']=='>' else raw
            assert bool(p)==(n in used)
    old_box=F(0);new_box=F(0)
    for n,a in aggregate.items():
        b=ac[n];c=F(cut['row']['terms'].get(n,0));delta=c-a
        support=max(delta*F(b['lb']),delta*F(b['ub']))
        if n in oc:old_box+=support
        else:
            assert n.startswith('pc162_') and c==0;new_box+=support
            if n not in ('pc162_lambda_L','pc162_lambda_U'):
                old=n[8:];assert b['lb']==min(0,oc[old]['lb']) and b['ub']==max(0,oc[old]['ub'])
    slack=F(cut['row']['rhs'])-rhs-old_box-new_box;assert slack>=0
    result['projection']=dict(PASS=True,terms=len(cut['row']['terms']),nonzero_source_rows=len(used),new_columns=0,
        new_box_support=float(new_box),old_conversion_support=float(old_box),outward_slack_exact=str(slack),
        actual_row_exact=True,all_original_physical_terms_retained=True,source_SHA256=cut['source_SHA256'],
        families=sorted({n.split('_')[0] for n in cut['row']['terms']}))
    return result

def endpoints():
    m=read(OUT/'complete_matrix.json');values=[]
    for g in m['groups']:
        path=Path(g['launch']['destination'])/'round162_endpoint.json'
        if path.exists():values.append(dict(position=g['position'],**read(path)))
    return values

def gate():
    values=endpoints();assert {v['position'] for v in values}>={1,2,3,4,5,6}
    pairs=[]
    for role in ('R-X35-S-T2','N-B35-S'):
        samples={a['R162_method']:a for a in values if a['id']==role}
        for control in ('Eplus','Stock'):
            p,c=samples['PC'],samples[control]
            pairs.append(dict(role=role,control=control,U_gain=c['U']-p['U'],L_gain=p['L']-c['L'],
                gap_reduction=c['signed_gap']-p['signed_gap'],PC_certificate=p['certificate'],control_certificate=c['certificate'],
                PC_T_total=p['T_total'],control_T_total=c['T_total'],PC_U=p['U'],control_U=c['U'],PC_L=p['L'],control_L=c['L']))
    write(OUT/'reports/complete_main_gate_metrics.json',dict(pairs=pairs,automatic_mechanism_change=False,
        decision_required='Apply only the predeclared stop-after-six condition; other outcomes retain the four small roles'))
    print(json.dumps(pairs,indent=2),flush=True)

def readback():
    account=budget();own=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(p['label']==own for p in account['unclosed'])
    m=read(OUT/'complete_matrix.json');manifest=read(OUT/'complete_candidate_manifest.json')
    assert m['candidate_manifest_SHA256']==sha(OUT/'complete_candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for name,digest in manifest['source_hashes'].items():
        if sha(ROOT/name)==digest:continue
        # This inventory also lists unused translation units. The late default
        # build repair is not linked into the frozen Gurobi performance PE.
        fix=read(OUT/'engineering/default_stub_fix.json')
        assert name=='src/Round160PhysicalNeighborhoodStub.cpp' and not fix['compiled_by_measured_Gurobi_PE']
        assert digest==fix['before_SHA256'] and sha(ROOT/name)==fix['after_SHA256']
    for name,digest in m['helpers'].items():assert sha(ROOT/name)==digest,name
    legacy=inherited_functions();tree=ast.parse((ROOT/'scripts/round157_fleet.py').read_text(encoding='utf-8-sig'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify');ns=dict(math=math)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'round157_saved_fleet_verifier','exec'),ns)
    samples=[];checks=[];fleets=[];own_h={};skipped=[]
    for group in m['groups']:
        l=group['launch'];dest=Path(l['destination']);ep=dest/'round162_endpoint.json'
        if not ep.exists():skipped.append(group['position']);continue
        tick=time.perf_counter();arm=read(ep);receipt=read(OUT/'fees'/f"complete_{group['position']:03}"/'receipt.json')
        assert receipt['exit_code']==0 and receipt['exit_observed'] and not receipt['timeout']
        assert arm['H_complete'] and arm['evidence_complete'] and arm['formal_protocol_qualified'] and arm['native_proof_qualified']
        assert arm['PE_SHA']==manifest['production_PE_SHA'] and arm['DLL_SHA']==DLL_SHA and arm['input_SHA']==l['panel']['input_sha256']
        assert sha(OUT/group['group']/'identity.json')==group['identity_SHA256']
        live=read(OUT/group['group']/'runtime_os_binding.json')
        assert Path(live['PE'])==Path(manifest['production_PE'])
        assert any(Path(v['FileName'])==Path(DLL) for v in live['DLL'])
        assert arm['T_cert'] is None or arm['certificate']
        assert abs(arm['T_total']-arm['T_produce']-arm['T_verify'])<1e-8
        assert arm['T_produce']<=l['cap_seconds']+1
        assert abs(arm['signed_gap']-(arm['U']-arm['L']))<1e-10
        role=l['id'];d=legacy['instance'](role)
        assert (d['n'],len(d['Q']),d['Q'],d['T'],d['tp'],d['td'],d['lam'])==(arm['V'],arm['M'],arm['Q_vector'],arm['T_seconds'],60,60,float(l['command'][l['command'].index('--lambda')+1]))
        distance=[[math.hypot(a[0]-b[0],a[1]-b[1])/1.5 for b in d['points']] for a in d['points']]
        data=dict(n=d['n'],Q=d['Q'],initial=d['initial'],capacity=d['capacity'],target=d['target'],weights=d['weights'],distance=distance,
            T=d['T'],pickup=d['tp'],drop=d['td'],lam=d['lam'])
        events=legacy['events'](dest);qualities=[];calls=[];count=0;best=math.inf
        for e in events:
            assert e['kind'] not in ('source_rejected','failure'),e
            if e['kind']=='witness':
                checked=ns['verify'](data,e);assert checked['original_T_feasible'];count+=1;best=min(best,checked['J'])
                fleets.append(dict(position=group['position'],event=e['sequence'],**checked))
            elif e['kind']=='call':
                assert e['native_preconditions']==1
                for key,value in dict(Threads=1,Seed=0,MIPFocus=0,MIPGap=0,MIPGapAbs=0,Presolve=-1).items():assert e['settings'][key]==value
                calls.append(e)
            elif e['kind']=='native_quality':qualities.append(e)
        assert count>0 and abs(best-arm['U'])<1e-7
        assert own_h.setdefault(role,arm['H_semantic_SHA'])==arm['H_semantic_SHA']
        extra={};sf=dest/'external/round162'
        if l['R162_method']=='PC':
            status_path=dest/'external/round162_run.json'
            if status_path.exists():
                status=read(status_path);assert status['source_calls']<=1 and not status['source_lower_formal_floor'] and status['formal_new_columns']==0
                extra['lifecycle']=status
            if (sf/'source.json').exists():extra['source_audit']=source_audit(sf)
            audits=[]
            for path in dest.rglob('*.round162.native.json'):
                a=read(path);assert a['PASS'] and a['NodeLimit_unlimited']
                if not a['temporary_source']:assert a['endpoint_columns']==0 and a['PC_rows']<=1
                audits.append(dict(path=path.relative_to(ROOT).as_posix(),**a))
            extra['actual_Native_audits']=audits
        else:assert not sf.exists()
        stats=native_log_stats(dest)
        additional=time.perf_counter()-tick
        arm.update(T_verify_initial_closeout=arm['T_verify'],T_total_initial_closeout=arm['T_total'],
            T_verify_additional_readback=additional,T_verify=arm['T_verify']+additional,T_total=arm['T_total']+additional,
            position=group['position'],outer_scientific_fee=receipt['outer_seconds'],
            source_seconds=extra.get('source_audit',{}).get('source',{}).get('source_seconds',0),
            projection_seconds=extra.get('source_audit',{}).get('source',{}).get('project_seconds',0),
            source_Work=extra.get('source_audit',{}).get('source',{}).get('Work',0),
            formal_quality_events=qualities,formal_calls=len(calls),formal_log_stats=stats,
            formal_Work_log_rounded=math.fsum(v['Work'] for v in stats),formal_nodes=sum(v['nodes'] for v in stats),
            formal_Runtime_log_rounded=math.fsum(v['seconds'] for v in stats),
            Work_precision='Gurobi terminal log precision; Source Work is separately captured at full API precision')
        samples.append(arm);checks.append(dict(position=group['position'],fleets=count,actual_calls=len(calls),
            additional_verification_seconds=additional,**extra))
    if skipped:assert skipped==[7,8,9,10] and read(OUT/'complete_small_role_decision.json')['stop_after_six']
    assert len(samples) in (6,10)
    protected=read(OUT/'infra/protected_initial.json');protected_count=0
    for t in protected['trees']:
        for path,digest in t['dirty'].items():assert sha(Path(t['tree'])/path)==digest;protected_count+=1
    write(OUT/'reports/complete.json',dict(samples=samples,skipped=skipped,full_four_role_confirmation=len(samples)==10,
        scientific_fee_seconds=sum(x['outer_scientific_fee'] for x in samples),new_source_lower_in_formal_ledger=False,
        same_frozen_recipe_all_inputs=True,formal_NodeLimit_unlimited=True,main_benchmark_CSV_changed=False))
    write(OUT/'reports/complete_fleets.json',fleets)
    write(OUT/'complete_review.json',dict(PASS=True,UTC=utc(),reviewer='same Codex agent, separate saved-evidence script; no independent personnel',
        source_SHA256=sha(__file__),checks=checks,protected_dirty_count=protected_count,protected_unchanged=True,
        Optimize=0,all_actual_fleets_recomputed_under_original_T=True,no_additional_comparison_arm=True))
    keys=['position','id','R162_method','U','raw_search_L','own_floor','L','signed_gap','relative_gap','certificate','T_cert','T_produce','T_verify','T_total',
          'native_Optimize','formal_Work_log_rounded','formal_nodes','formal_Runtime_log_rounded',
          'source_seconds','projection_seconds','source_Work','T_verify_initial_closeout','T_verify_additional_readback','outer_scientific_fee']
    with (OUT/'reports/complete.csv').open('w',newline='',encoding='utf8') as stream:
        w=csv.DictWriter(stream,fieldnames=keys);w.writeheader();w.writerows({k:s.get(k) for k in keys} for s in samples)
    print(json.dumps(dict(PASS=True,samples=len(samples),fleets=len(fleets),protected=protected_count)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
