"""Accepted R134/R137/R147 checks plus PF arithmetic, first-call SHA and matrix checks."""
import collections
import types
import round147_read as inherited
import round108_reader as parser
from round149_context import root_context,first_call,unique_model
from round149_math import oracle,scope_from_model,F
from round149_common import *


def pf_contract(destination,enabled):
    models=destination/'external/models'
    audits=[read(p) for p in destination.rglob('*.round149.native.json')]
    embeddings=[read(p) for p in models.glob('*.round149.json')]
    meta_path=models/'round149_root.json';meta=read(meta_path) if meta_path.exists() else None
    call=first_call(models);facts=[]
    if not enabled:
        assert meta is None and not embeddings and not audits
        assert not (destination/'round149_parameters.json').exists()
        assert all('r149_PF_' not in p.read_text(encoding='utf-8') for p in models.glob('*.lp'))
    else:
        assert read(destination/'round149_parameters.json')==dict(PF=True,root_once=True,
            proof_root_unchanged=True,extra_root_LP=0,source_solves=0,new_columns=0)
        if meta is None:
            assert call is None and not embeddings and not audits
        else:
            assert meta['root_beta_frozen'] and meta['proof_root_unchanged']
            assert meta['source_solves']==meta['extra_root_LP']==meta['new_columns']==0
            source=unique_model(models,meta['base_model_SHA']);base=parser.lp_model(source)
            scope=scope_from_model(base,meta['Bminus'],meta['B'])
            assert scope['cutoff']==meta['own_cutoff'] and scope['gamma_L']==meta['gamma_L'] and scope['gamma_U']==meta['gamma_U']
            assert [{k:s[k] for k in ['i','c','omega','lo','hi']} for s in scope['stations']]==meta['stations']
            exact=oracle(scope);assert exact['feasible']==meta['feasible_resource_box']
            if exact['feasible']:
                assert F(meta['dual_lower'])<=exact['dual'](F(meta['mu']),F(meta['nu']))<=exact['primal']
                assert 0<=F(meta['penalty_lower'])<=exact['primal']
            assert F(meta['beta'])>=min(F(meta['gamma_U']),F(meta['own_cutoff'])-F(meta['penalty_lower']))
            support={s['i']:set(s['support']) for s in scope['stations']}
            assert embeddings and audits and call is not None
            for embedding in embeddings:
                p=unique_model(models,embedding['final_SHA']);m=parser.lp_model(p)
                before=parser.lp_model(unique_model(models,embedding['base_SHA']))
                current=scope_from_model(m,meta['Bminus'],meta['B'])
                assert current['gamma_L']>=meta['gamma_L'] and current['gamma_U']<=meta['gamma_U']
                assert current['cutoff']<=meta['own_cutoff'] and current['cutoff']==embedding['cutoff']
                assert all(set(s['support'])<=support[s['i']] for s in current['stations'])
                assert [(s['i'],s['c'],s['omega']) for s in current['stations']]==[(s['i'],s['c'],s['omega']) for s in scope['stations']]
                expected=[]
                if meta['feasible_resource_box'] and meta['penalty_lower']>0 and meta['beta']<current['gamma_U'] and meta['beta']>=1e-12:
                    for s in current['stations']:
                        for y in s['support']:
                            expected.append((tuple(sorted({f"state_g_{s['i']}_{y}":1.,f"state_{s['i']}_{y}":-meta['beta']}.items())),'<=',0.))
                assert all(m[k]==before[k] for k in ['order','bounds','types','objective'])
                assert collections.Counter(m['rows'])==collections.Counter(before['rows'])+collections.Counter(expected)
                assert embedding['added_rows']==len(expected) and embedding['added_nonzeros']==2*len(expected)
                assert embedding['compatible_domain'] and not embedding['first_solve_before_append']
                matched=[a for a in audits if a['model_SHA']==embedding['final_SHA']]
                assert matched and all(a['PASS'] and a['PF_rows']==len(expected) and a['PF_nonzeros']==2*len(expected) and
                    a['new_columns']==a['source_solves']==a['Optimize_extra']==0 for a in matched)
                facts.append(dict(model_SHA=embedding['final_SHA'],base_SHA=embedding['base_SHA'],
                    PF_rows=len(expected),PF_nonzeros=2*len(expected),actual_matrix_and_Native=True))
            assert all(a['model_SHA'] in {e['final_SHA'] for e in embeddings} for a in audits)
            root=[e for e in embeddings if e['base_SHA']==meta['base_model_SHA']]
            assert len(root)==1 and call['model_sha256']==root[0]['final_SHA']
            assert Path(call['native_log_path']).name=='L0_lp.gurobi.log'
            calls=[r['payload'] for r in read(destination/'observations.json') if r['payload']['kind']=='call']
            if root[0]['added_rows']:
                assert all(c['model_sha256']!=meta['base_model_SHA'] for c in calls)
            assert len([c for c in calls if Path(c['native_log_path']).name=='L0_lp.gurobi.log'])==1
    value=dict(PASS=True,enabled=enabled,root=meta,models=facts,Native_audits=audits,
        first_call_SHA=call['model_sha256'] if call else None,extra_root_LP=0,
        exact_actual_multiplier_dual_checked=meta is not None,Optimize=0,Native_load=0,
        GD_context_selected_by_first_call_SHA=True,no_R148_source_LP_filter=True)
    write(destination/'round149_control_audit.json',value);return value


def verify(launch,identity):
    configure();destination=Path(launch['destination'])
    assert not (destination/'verification_closeout.json').exists(),'closed verification is immutable'
    enabled=launch['R149_method']=='D_PF';command=launch['command']
    assert command.count('--round149-penalty-feedback')==1
    assert command[command.index('--round149-penalty-feedback')+1]==('on' if enabled else 'off')
    assert '--round148-shared-s' not in command and '--round138-stock-rlt' not in command
    pf_contract(destination,enabled)  # Before the accepted immutable closeout.
    return types.FunctionType(inherited.verify.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,
        configure=configure,root_context=root_context))(launch,identity)
