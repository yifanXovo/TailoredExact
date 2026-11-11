"""One separate final saved-evidence audit by the same agent; no Optimize."""
from round161_common import *
from fractions import Fraction as F
import ast,re

def review():
    report=read(OUT/'reports/bridge.json');manifest=read(OUT/'measured_manifest.json')
    from round161_qualify import exact_witnesses
    assert exact_witnesses()['PASS']
    assert sha(manifest['research_PE'])==manifest['research_PE_SHA'] and sha(DLL)==DLL_SHA
    # Use the separately established R157 physical verifier's AST only. Imports
    # and its old producer / budget are not evaluated.
    source=ROOT/'scripts/round157_fleet.py';tree=ast.parse(source.read_text())
    fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='verify')
    namespace={'math':math};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),namespace)
    physical=namespace['verify'];checks=[]
    for sample in report['samples']:
        role=sample['role'];form=sample['formulation'];mode=sample['mode']
        label=f'{role}_RNP_{mode}_v2' if form=='RN-P' else f'{role}_{form}_{mode}_v1';folder=OUT/'runs'/label
        measured=read(OUT/'measured_manifest_RNP.json') if form=='RN-P' else manifest
        launch=read(OUT/'launches'/f'{label}.json');assert launch['PE_SHA']==measured['research_PE_SHA']
        assert launch['DLL_SHA']==DLL_SHA and sha(launch['command'][1])==launch['input_SHA']
        assert sha(launch['command'][6])==launch['parent_SHA']
        assert launch['outer_cap']==(300 if sample['mode']=='LP' else 900)
        original=[json.loads(x) for x in (folder/'original_rows.jsonl').read_text().splitlines()]
        actual=[json.loads(x) for x in (folder/'actual_rows.jsonl').read_text().splitlines()]
        columns=[json.loads(x) for x in (folder/'actual_columns.jsonl').read_text().splitlines()]
        start=read(folder/'start.json');ad=read(folder/'admission.json');worst=0
        for row in actual:
            e=math.fsum(c*start[n] for n,c in row['terms'].items())-row['rhs']
            worst=max(worst,abs(e) if row['sense']=='=' else e if row['sense']=='<' else -e)
        for col in columns:
            v=start[col['name']];worst=max(worst,col['lb']-v,v-col['ub'])
            if col['type']!='C':assert abs(v-round(v))<=1e-5
        assert worst<1e-6 and abs(sum(c['obj']*start[c['name']] for c in columns)-ad['parent_J'])<1e-9
        # Direct original penalty row check: no normalized column can enter e.
        penalty=[r for r in actual if any(n.startswith('e_') for n in r['terms'])]
        assert all(not any(n.startswith('rn_') for n in r['terms']) for r in penalty)
        info=read(OUT/'inputs'/role/'source.json');d=info['data'];d['T']=info['panel']['T_seconds']
        count=0;bounds=[];call=None;rejected=0
        for p in (folder/'journal').glob('event_*.json'):
            e=read(p)
            if e['kind']=='call':
                call=e;assert e['model_sha256']==sha(folder/'model.lp')
                assert e['native_preconditions']==1 and e['cutoff']==ad['cutoff'] and e['upper_g']==ad['gamma_U']
                for k,v in {'Threads':1,'Seed':0,'MIPFocus':0,'MIPGap':0,'MIPGapAbs':0,'Presolve':-1}.items():assert e['settings'][k]==v
            elif e['kind']=='witness':
                checked=physical(d,e);assert checked['original_T_feasible'];count+=1
            elif e['kind']=='bound':bounds.append(e['native_bound'])
            elif e['kind']=='witness_rejected':rejected+=1
            elif e['kind'] in ('source_rejected','failure'):raise AssertionError(e)
        assert call and count>0 and max(bounds)<=sample['physical_U']+1e-7
        assert abs(min(max(bounds),ad['cutoff'])-sample['global_transported_floor'])<1e-9
        block=read(folder/'block.json')
        if form in ('RN','RN-P'):
            supports={i:[] for i in range(1,d['n']+1)}
            for c in columns:
                m=re.fullmatch(r'state_(\d+)_(\d+)',c['name'])
                if m and c['ub']>0:supports[int(m[1])].append(int(m[2]))
            c={i:F(1./d['target'][i]) for i in supports};minimum=sum(min(v) for v in supports.values());maximum=sum(max(v) for v in supports.values())
            B=sum(d['initial'][1:]);Q=sum(d['Q']);lo=max(1,B-Q,minimum);hi=min(B,maximum)
            def extremum(total,reverse):
                left=total-minimum;value=sum((c[i]*min(supports[i]) for i in supports),F(0))
                for i in sorted(supports,key=lambda i:(c[i],i),reverse=reverse):
                    take=min(left,max(supports[i])-min(supports[i]));value+=c[i]*take;left-=take
                assert left==0;return value
            exactlo,exacthi=extremum(lo,False),extremum(hi,True)
            if block.get('penalty_envelope'):
                diagnostic=next(x for x in read(OUT/'reports/envelope_diagnostic.json')['results'] if x['role']==role)
                exactlo=max(exactlo,F(diagnostic['exact_sl']))
                exacthi=min(exacthi,F(diagnostic['exact_su']))
            assert F(block['S_lower'])<=exactlo and F(block['S_upper'])>=exacthi
            assert F(block['t_lower'])<=1/exacthi and F(block['t_upper'])>=1/exactlo
            assert block['zero_possible']==(B<=Q and all(0 in ys for ys in supports.values()))
        checks.append(dict(label=label,verified_fleets=count,rejected_candidates_not_consumed=rejected,Start_max_violation=worst,full_scope=True,original_penalty=True,
            common_original_rows=len(original),actual_rows=len(actual)))
    protected=read(OUT/'infra/protected_initial.json')
    for tree in protected['trees']:
        for path,h in tree['dirty'].items():assert sha(Path(tree['tree'])/path)==h
    current=os.environ.get('ROUND140_METERED_PARENT_LABEL');account=budget()
    assert all(p['label']==current for p in account['unclosed']) and account['G1_seconds']<86400
    fees=[dict(label=p.parent.name,**read(p)) for p in (OUT/'fees').glob('*/receipt.json')]
    failures=[dict(label=r['label'],exit_code=r['exit_code'],seconds=r['outer_seconds']) for r in fees if r['exit_code']]
    decision=read(OUT/'decision.json')
    write(OUT/'final_review.json',dict(PASS=True,UTC=utc(),reviewer='same Codex agent, separate saved-evidence script; no independent personnel',
        physical_verifier_source_SHA=sha(source),checks=checks,failed_receipts_preserved=failures,
        protected_initial_hashes_unchanged=True,zero_positive_qualification=read(OUT/'qualification/tiny.json')['PASS'],
        common_block_review=read(OUT/'reports/matrix_audits.json')['PASS'],decision=decision,Optimize=0,
        complete_method_panel_not_inferred_from_development=True,scientific_account_before_this_receipt=account))
    print('PASS separate final saved-evidence audit; no independent personnel claimed')

if __name__=='__main__':review()
