"""Inherited physical/proof lifecycle plus independent own-root floor audit."""
import collections,types
from fractions import Fraction as F
import round147_read as inherited
import round108_reader as parser
from round149_read import pf_contract
from round151_read import cap_contract
from round149_context import first_call,unique_model,root_context
from round151_math import scope_from_model
from round152_math import h_exact,unary_dp
from round153_pricing import stock_value
from round153_common import *

def floor_contract(destination,enabled):
    models=destination/'external/models';call=first_call(models)
    audits=[read(p) for p in destination.rglob('*.round153.native.json')]
    embeds=[read(p) for p in models.glob('*.round153.json')]
    path=models/'round153_root.json';meta=read(path) if path.exists() else None;facts=[]
    if not enabled:
        assert meta is None and not embeds and not audits and not (destination/'round153_parameters.json').exists()
        assert all('r153_root_floor' not in p.read_text(encoding='utf-8') for p in models.glob('*.lp'))
    else:
        parameters=read(destination/'round153_parameters.json')
        assert parameters['root_once'] and parameters['node_limit']==4096 and parameters['wall_step_limit'] is None
        assert parameters['price_gap_target']==1e-4 and not parameters['offline_data_used']
        if meta is None:assert call is None and not embeds and not audits
        else:
            assert meta['helper_SHA']==parameters['helper_SHA'] and meta['helper_manifest_SHA']==parameters['manifest_SHA']
            assert meta['root_once'] and not meta['offline_data_used'] and meta['owned_helper_job_kill_on_close']
            assert meta['formal_new_columns']==meta['extra_root_LP']==0 and not meta['formal_AP_GD_RN_NC_TS']
            source=unique_model(models,meta['source_SHA']);base=parser.lp_model(source)
            root=scope_from_model(base,meta['Bminus'],meta['B'])
            assert (root['gamma_L'],root['gamma_U'],root['cutoff'])==(meta['gamma_L'],meta['gamma_U'],meta['own_cutoff'])
            if meta['qualified']:
                helper=destination/'external/round153_floor';r=read(helper/'result.json');s=read(helper/'source.json')
                assert meta['helper_exit']==0 and not meta['global_deadline_stop'] and not r['global_deadline_stop']
                assert r['qualified'] and r['scope']==root and s['scope']==root and r['source_SHA']==s['source_SHA']==meta['source_SHA']
                assert r['lower']==meta['lower'] and r['source_helper_manifest_SHA']==meta['helper_manifest_SHA']
                assert r['no_historical_inventory_or_price_loaded'] and not r['physical_upper_claim']
                assert r['node_limit']==4096 and r['absolute_price_gap']==1e-4 and s['Seed']==0 and s['Threads']==1
                deps=s['dependencies'];assert all(deps[k]==v for k,v in r['loaded_project_sources'].items())
                assert deps['scripts/round153_online.py']==meta['helper_SHA']
                p=read(helper/'pricing/result.json');assert p['scope']==root and p['complete_domain'] and p['beta']==1.
                costs={(s['i'],y):h_exact(s,y) for s in root['stations'] for y in s['support']}
                assert {tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}==costs
                dp=unary_dp(root,costs);fallback=F(root['gamma_L'])+F(dp['exact'])
                assert F(p['fallback_lower'])<=fallback
                lower=fallback
                if p['calls']:
                    c=read(helper/'pricing/call.json');q=p['calls'][0]
                    assert c['scope']==root and c['model_SHA']==sha(helper/'pricing/model.mps')
                    assert c['Seed']==0 and c['Threads']==1 and c['node_limit']==4096 and c['cap'] is None
                    assert c['whole_method_global_deadline_present'] and not c['online_wall_time_switch']
                    assert c['old_joint'] and c['full_support'] and c['matrix_readback']
                    if q['bound_status_qualified']:
                        assert q['Status'] in (2,8) and math.isfinite(q['native_bound'])
                        lower=max(lower,F(c['scale'])*(F(q['native_bound'])-F(c['numerical_guard_scaled'])-F(c['objective_correction_scaled_exact']))+
                            sum((F(v) for v in c['anchors_exact'].values()),F(0)))
                    else:assert q['native_bound'] is None
                    if p['zero_lower'] is not None:lower=min(lower,F(p['zero_lower']))
                assert F(p['lower'])<=lower and p['lower']==meta['lower']
                for v in p['stocks']:
                    exact=stock_value(root,v['Y'],1.,costs);assert exact['feasible'] and F(v['price_exact'])==exact['price']
            support={s['i']:set(s['support']) for s in root['stations']}
            observations=read(destination/'observations.json')
            calls=[r['payload'] for r in observations if r['payload']['kind']=='call']
            for e in embeds:
                before=parser.lp_model(unique_model(models,e['base_SHA']));model=parser.lp_model(unique_model(models,e['final_SHA']))
                current=scope_from_model(before,meta['Bminus'],meta['B'])
                assert current['gamma_L']>=root['gamma_L'] and current['gamma_U']<=root['gamma_U'] and current['cutoff']<=root['cutoff']
                assert [(s['i'],s['c'],s['omega']) for s in current['stations']]==[(s['i'],s['c'],s['omega']) for s in root['stations']]
                assert all(set(s['support'])<=support[s['i']] for s in current['stations'])
                expected=int(meta['qualified'] and meta['lower']>current['gamma_L']+1e-7)
                assert e['added_rows']==expected and e['new_columns']==0 and e['compatible_domain']
                assert e['root_source_SHA']==meta['source_SHA'] and e['qualified_source']==meta['qualified']
                assert all(model[k]==before[k] for k in ['order','bounds','types','objective'])
                added=[(before['objective'][0],'>=',meta['lower'])] if expected else []
                assert collections.Counter(model['rows'])==collections.Counter(before['rows'])+collections.Counter(added)
                matched=[a for a in audits if a['model_SHA']==e['final_SHA']]
                actually_called=any(c['model_sha256']==e['final_SHA'] for c in calls)
                if actually_called:assert matched
                assert all(a['PASS'] and a['floor_rows']==expected and a['new_columns']==a['formal_extra_Optimize']==0 and a['helper_paid_inside_process'] for a in matched)
                facts.append(dict(base_SHA=e['base_SHA'],model_SHA=e['final_SHA'],floor_rows=expected,actually_called=actually_called,Native_audits=len(matched)))
            assert embeds and (call is not None or meta['global_deadline_stop'])
            if call:
                first=[e for e in embeds if e['base_SHA']==meta['source_SHA']];assert len(first)==1 and call['model_sha256']==first[0]['final_SHA']
            assert all(a['model_SHA'] in {e['final_SHA'] for e in embeds} for a in audits)
    value=dict(PASS=True,enabled=enabled,root=meta,models=facts,Native_audits=audits,
        own_source_scope=True,all_original_columns_bounds_objective_preserved=True,helper_paid_inside_process=True,
        Optimize=0,Native_load=0)
    write(destination/'round153_control_audit.json',value);return value

def verify(launch,identity):
    configure();destination=Path(launch['destination']);command=launch['command']
    assert not (destination/'verification_closeout.json').exists(),'Closed evidence immutable'
    assert command.count('--round153-root-floor')==1
    enabled=command[command.index('--round153-root-floor')+1]=='on'
    assert launch['R147_method']=='BASE' and command[command.index('--round146-gd')+1]=='off'
    assert command[command.index('--round149-penalty-feedback')+1]==command[command.index('--round151-penalty-propagation')+1]=='off'
    types.FunctionType(pf_contract.__code__,dict(pf_contract.__globals__,ROOT=ROOT,OUT=OUT))(destination,False)
    types.FunctionType(cap_contract.__code__,dict(cap_contract.__globals__,ROOT=ROOT,OUT=OUT))(destination,'off')
    floor_contract(destination,enabled)
    return types.FunctionType(inherited.verify.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,configure=configure,root_context=root_context))(launch,identity)
