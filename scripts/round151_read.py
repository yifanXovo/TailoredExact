"""R134 physical/proof/lifecycle policy plus independent GD-off cap audit."""
import collections,types
import round147_read as inherited
import round108_reader as parser
from round149_read import pf_contract
from round149_context import first_call,unique_model,root_context
from round151_math import reference,scope_from_model,rows
from round151_common import *
def cap_contract(destination,mode):
    models=destination/'external/models';call=first_call(models)
    audits=[read(p) for p in destination.rglob('*.round151.native.json')]
    embeds=[read(p) for p in models.glob('*.round151.json')]
    p=models/'round151_root.json';meta=read(p) if p.exists() else None;facts=[]
    if mode=='off':
        assert meta is None and not embeds and not audits and not (destination/'round151_parameters.json').exists()
        assert all('r151_cap_' not in p.read_text(encoding='utf-8') for p in models.glob('*.lp'))
    else:
        assert read(destination/'round151_parameters.json')==dict(mode=mode,GD=False,root_once=True,
            proof_root_unchanged=True,extra_root_LP=0,source_solves=0,new_columns=0)
        if meta is None:
            assert call is None and not embeds and not audits
        else:
            assert meta['root_caps_frozen'] and meta['proof_root_unchanged'] and not meta['GD']
            assert meta['source_solves']==meta['extra_root_LP']==meta['new_columns']==0
            assert meta['mode']==mode
            source=unique_model(models,meta['base_model_SHA']);base=parser.lp_model(source)
            root=scope_from_model(base,meta['Bminus'],meta['B'])
            assert root['cutoff']==meta['own_cutoff'] and (root['gamma_L'],root['gamma_U'])==(meta['gamma_L'],meta['gamma_U'])
            reference(root,meta)
            root_states={(s['i'],y) for s in root['stations'] for y in s['support']}
            assert root_states=={(s['i'],s['y']) for s in meta['states']}
            support={s['i']:set(s['support']) for s in root['stations']}
            calls=[r['payload'] for r in read(destination/'observations.json') if r['payload']['kind']=='call']
            for e in embeds:
                before=parser.lp_model(unique_model(models,e['base_SHA']));path=unique_model(models,e['final_SHA']);model=parser.lp_model(path)
                current=scope_from_model(before,meta['Bminus'],meta['B'])
                assert current['gamma_L']>=root['gamma_L'] and current['gamma_U']<=root['gamma_U']
                assert current['cutoff']<=root['cutoff'] and current['cutoff']==e['cutoff']
                assert [(s['i'],s['c'],s['omega']) for s in current['stations']]==[(s['i'],s['c'],s['omega']) for s in root['stations']]
                assert all(set(s['support'])<=support[s['i']] for s in current['stations'])
                expected=rows(dict(meta,scope=root,mode=mode),current)
                assert all(model[k]==before[k] for k in ['order','bounds','types','objective'])
                added=[(tuple(sorted(r['terms'].items())),'<=',0.) for r in expected]
                assert collections.Counter(model['rows'])==collections.Counter(before['rows'])+collections.Counter(added)
                assert e['added_rows']==len(expected) and e['added_nonzeros']==sum(len(r['terms']) for r in expected)
                assert e['compatible_domain'] and not e['first_solve_before_append'] and not e['GD']
                matched=[a for a in audits if a['model_SHA']==e['final_SHA']]
                actually_called=any(c['model_sha256']==e['final_SHA'] for c in calls)
                if actually_called:assert matched
                assert all(a['PASS'] and a['cap_rows']==len(expected) and a['cap_nonzeros']==e['added_nonzeros'] and
                    a['new_columns']==a['source_solves']==a['Optimize_extra']==0 and not a['GD'] for a in matched)
                facts.append(dict(base_SHA=e['base_SHA'],model_SHA=e['final_SHA'],cap_rows=len(expected),
                    cap_nonzeros=e['added_nonzeros'],actual_matrix=True,actually_called=actually_called,Native_audits=len(matched)))
            assert embeds and call is not None
            assert all(a['model_SHA'] in {e['final_SHA'] for e in embeds} for a in audits)
            first=[e for e in embeds if e['base_SHA']==meta['base_model_SHA']];assert len(first)==1
            assert call['model_sha256']==first[0]['final_SHA'] and Path(call['native_log_path']).name=='L0_lp.gurobi.log'
            if first[0]['added_rows']:assert all(c['model_sha256']!=meta['base_model_SHA'] for c in calls)
    value=dict(PASS=True,mode=mode,GD=False,root=meta,models=facts,Native_audits=audits,
        first_call_SHA=call['model_sha256'] if call else None,first_model_before_Optimize=True,
        actual_C_subset_P=True,source_solves=0,extra_root_LP=0,new_columns=0,Optimize=0,Native_load=0,
        no_model_own_H_supported=True)
    write(destination/'round151_control_audit.json',value);return value
def verify(launch,identity):
    configure();destination=Path(launch['destination']);command=launch['command']
    assert not (destination/'verification_closeout.json').exists(),'Closed evidence immutable'
    assert command.count('--round151-penalty-propagation')==1
    mode=command[command.index('--round151-penalty-propagation')+1]
    assert launch['R147_method']=='BASE' and command[command.index('--round146-gd')+1]=='off'
    assert command[command.index('--round149-penalty-feedback')+1]=='off'
    assert all(f not in command for f in ['--round138-stock-rlt','--round148-shared-s','--round135-ap'])
    types.FunctionType(pf_contract.__code__,dict(pf_contract.__globals__,ROOT=ROOT,OUT=OUT))(destination,False)
    cap_contract(destination,mode)
    return types.FunctionType(inherited.verify.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,
        configure=configure,root_context=root_context))(launch,identity)
