"""Recheck the complete archived D24 point and saved loaded bits, zero native."""
from pathlib import Path
from fractions import Fraction as F
import argparse, ast, datetime, gzip, hashlib, json, re, struct, sys, time

MODEL_SHA='a630251059be795777416ea1d63e6d8881c17baf1b75ccba776b5004a7294bc1'
PREFIX='results/unified_exact_round132/campaign/D_group24/raw/02_X-35-U_S1_R1_S2/'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=args.root.resolve();out=root/'results/unified_exact_round133';tick=time.perf_counter()
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
    index=read(out/'dependencies/historical_snippets.json')
    by={r['source_path']:r for r in index['files']}
    def old(name):
        row=by[name];path=root/row['path'];assert path.resolve().is_relative_to(root)
        assert path.stat().st_size==row['bytes'] and sha(path)==row['SHA256'];return read(path)
    scope=old(PREFIX+'journal/event_9.json');witness=old(PREFIX+'journal/event_21.json')
    bounds_claimed=[old(PREFIX+f'journal/event_{i}.json')['native_bound'] for i in (17,18,19)]
    assert bounds_claimed==[2.2155204177669103e-7,2.3794866331140976e-7,2.889725344877011e-7]
    assert scope['call']==witness['call']==4 and witness['objective']==witness['G']==witness['P']==0
    assert scope['lower_g']==0 and scope['upper_g']==scope['cutoff']==0.16038610038610038
    identity=old('results/unified_exact_round132/campaign/D_group24/identity.json')
    panel=dict(identity['launches'][0]['panel']);panel['input_path']=str(out/'inputs/X-35-U.txt')
    assert sha(panel['input_path'])==panel['input_sha256']
    data=Path(panel['input_path']).read_text(encoding='utf-8-sig')
    vector=lambda name:ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',data,re.M)[1])
    initial,target,weights=vector('initial'),vector('target'),vector('weights')
    def guard(event,values):
        vendor_import=event=='import' and str(values[0]).split('.')[0]=='gurobipy'
        if vendor_import or event.startswith('subprocess.') or (event=='ctypes.dlopen' and 'gurobi' in str(values).lower()):
            raise AssertionError(('native/process prohibited',event))
    sys.addaudithook(guard);sys.dont_write_bytecode=True
    sys.path.insert(0,str(root/'scripts'))
    import round108_reader as core
    physical=core.full_fleet(root,panel,witness)
    assert physical['F']==physical['G']==physical['P']==0 and physical['Y'][1:]==target[1:]
    source=out/'review/directed_old_evidence_check.py'
    plan=read(out/'plans/C_R3_D24_loaded_bits.json')
    assert sha(source)==plan['pure_parser']['file_SHA256']
    names={'number','expression','value','rational','model','zero_point','audit'}
    tree=ast.parse(source.read_text(encoding='utf-8-sig'))
    definitions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert {node.name for node in definitions}==names
    reads={}
    def raw(path):
        path=Path(path);assert path.resolve().is_relative_to(root)
        blob=path.read_bytes();reads[str(path.relative_to(root))]=hashlib.sha256(blob).hexdigest();return blob
    namespace=dict(F=F,re=re,hashlib=hashlib,raw=raw,read_weights=weights)
    exec(compile(ast.Module(body=definitions,type_ignores=[]),str(source)+'::definitions_only','exec'),namespace)
    path=out/'dependencies/C/D24_call4_serialized.lp';assert sha(path)==MODEL_SHA
    limits,types,rows,objective=namespace['model'](path)
    tight=namespace['audit'](limits,types,rows,objective,namespace['zero_point'](limits,witness,initial,target))
    point=namespace['zero_point'](limits,witness,initial,target,True,rows)
    exact=namespace['audit'](limits,types,rows,objective,point)
    prior=read(out/'review/directed_old_evidence_receipt.json')['D24']
    assert exact==prior['rounded_matrix_completion'] and tight==prior['tight_mathematical_completion']
    assert exact['exactly_feasible'] and (exact['rows'],exact['columns'],exact['equalities'])==(22996,9391,601)
    assert not tight['exactly_feasible'] and tight['maximum_violation']['exact']=='1/18014398509481984'
    assert all(F.from_float(value)>F(exact['objective']['exact'])+F.from_float(1e-7) for value in bounds_claimed)
    # Compare every saved engine-loaded field against the serialized matrix.
    # This consumes the actual recorded readout; no engine is loaded here.
    folder=out/'diagnostics/C_R3_D24_loaded_bits';receipt=read(folder/'comparison.json')
    assert sha(folder/'loaded_model_bits.json.gz')==receipt['loaded_bits_SHA256']
    snapshot=json.loads(gzip.decompress((folder/'loaded_model_bits.json.gz').read_bytes()))
    assert snapshot['model_SHA256']==MODEL_SHA and snapshot['engine_version']==[13,0,2]
    assert snapshot['model_sense']==1 and snapshot['native_status']==1
    assert snapshot['runtime']['sha256']=='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
    assert snapshot['Optimize']==0 and snapshot['loaded_original_model'] and not snapshot['presolve']
    cols={v['name']:v for v in snapshot['columns']};rs={r['name']:r for r in snapshot['rows']}
    assert set(cols)==set(limits) and set(rs)=={r[0] for r in rows}
    differences=[];comparisons=0
    def compare(label,left,right):
        nonlocal comparisons
        comparisons+=1
        a=struct.pack('>d',float(left)).hex();b=struct.pack('>d',float(right)).hex()
        if a!=b:
            assert left==0 and right==0,(label,left,right)
            differences.append(dict(field=label,expected_bits=a,actual_bits=b))
    objectives={n:c for n,c in objective if n is not None}
    compare('objective_constant',sum((c for n,c in objective if n is None),F(0)),float.fromhex(snapshot['objective_constant']))
    for name,record in cols.items():
        assert record['type']==types.get(name,'C')
        compare(name+'.lower',limits[name][0],float.fromhex(record['lower']))
        compare(name+'.upper',limits[name][1],float.fromhex(record['upper']))
        compare(name+'.objective',objectives.get(name,F(0)),float.fromhex(record['objective']))
    for name,terms,sense,rhs in rows:
        record=rs[name];assert record['sense']=={'=':'=','<=':'<','>=':'>'}[sense]
        compare(name+'.RHS',rhs-sum((c for n,c in terms if n is None),F(0)),float.fromhex(record['RHS']))
        expected={n:c for n,c in terms if n is not None and c}
        actual={n:float.fromhex(v) for n,v in record['coefficients'].items()}
        assert set(expected)=={n for n,c in actual.items() if c}
        for n,value in expected.items():compare(name+'.'+n,value,actual[n])
    assert len(differences)==receipt['signed_zero_only_differences']==3 and receipt['other_differences']==0
    assert {r['field'] for r in differences}=={'c3016.RHS','c3018.RHS','c3019.RHS'}
    result=dict(status='PASS',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        physical=physical,complete_serialized_point=exact,naive_tight_point=tight,
        native_claims_refuted=bounds_claimed,source_remains='REJECTED',
        saved_loaded_numeric_fields_recompared=comparisons,saved_loaded_signed_zero_only=differences,
        loaded_comparison_attestation_SHA=sha(folder/'comparison.json'),
        no_claim_of_historical_presolve_cuts_or_MIP_tree=True,
        current_native_assets_remeasured=False,reads=reads,Optimize=0,native_starts=0,compilation=0,
        source_SHA=sha(__file__),seconds=time.perf_counter()-tick)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',rows=exact['rows'],columns=exact['columns'],
        objective=exact['objective']['exact'],zero_signs=3,Optimize=0)))

if __name__=='__main__':main()
