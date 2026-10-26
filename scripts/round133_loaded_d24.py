"""One preregistered D24 LP-load comparison; zero Optimize and no point replay.

The primary agent alone runs this after other native work exits. Preparation
imports no native module. The old exact point proof is transferred only when
every loaded linear-model field has the same exact binary64 value (with the
mathematically immaterial sign of zero separately disclosed).
"""
from pathlib import Path
from fractions import Fraction as F
import argparse, ast, datetime, gzip, hashlib, importlib.metadata, importlib.util
import json, math, os, re, shutil, struct, sys, time
import round133_common as C

ROOT, OUT = C.ROOT, C.OUT
PLAN=OUT/'plans/C_R3_D24_loaded_bits.json'
PYTHON=Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
MODEL_SHA='a630251059be795777416ea1d63e6d8881c17baf1b75ccba776b5004a7294bc1'
POINT_SHA='6fde8c357fa6c1736d4e7a514ef0a72941483e4768f3eeb72a856e357ed01d2f'
PARSER=OUT/'review/directed_old_evidence_check.py'
PROOF=OUT/'review/directed_old_evidence_receipt.json'

def extract_parser():
    # Importing the old checker would repeat its top-level exact computation.
    # Compile only these three pure definitions, with a read-only byte helper.
    source=PARSER.read_text(encoding='utf-8');tree=ast.parse(source)
    names={'number','expression','model'}
    definitions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert {node.name for node in definitions}==names
    text='\n\n'.join(ast.get_source_segment(source,node) for node in definitions)
    namespace=dict(F=F,re=re,raw=lambda path:Path(path).read_bytes())
    exec(compile(ast.Module(body=definitions,type_ignores=[]),str(PARSER)+'::three_pure_definitions','exec'),namespace)
    return namespace['model'],hashlib.sha256(text.encode()).hexdigest()

def prepare():
    tick=time.perf_counter();assert not PLAN.exists(),'keep original registration immutable'
    proof=C.read(PROOF)['D24']['rounded_matrix_completion']
    assert proof['exactly_feasible'] and proof['completion_SHA256']==POINT_SHA
    assert proof['rows']==22996 and proof['columns']==9391 and proof['maximum_violation']['exact']=='0'
    old=Path('E:/codes/ExactEBRP-work/worktrees/round132/results/unified_exact_round132/campaign/D_group24/raw/02_X-35-U_S1_R1_S2/external/models/L0_epoch_0_generation_1.lp')
    assert C.sha(old)==MODEL_SHA
    staged=OUT/'dependencies/C/D24_call4_serialized.lp';staged.parent.mkdir(parents=True,exist_ok=True)
    if staged.exists():assert C.sha(staged)==MODEL_SHA
    else:shutil.copyfile(old,staged)
    assert C.sha(staged)==MODEL_SHA
    parser,definition_sha=extract_parser()  # Extraction only; no model/point calculation.
    assert callable(parser)
    runtime=C.read(OUT/'plans/C_diagnostics_runtime_repair.json')['runtime_repair']
    assert C.sha(PYTHON)==runtime['python_SHA256']
    plan=dict(schema='round133-C-R3-D24-loaded-bits-v1',UTC=C.utc(),status='FROZEN_BEFORE_NATIVE_LOAD',
        purpose='Close B3 layer3 serialization-to-engine-loading identity for the known D24 bound counterexample',
        hypothesis='Python binary64 parsing of the serialized LP and the same-DLL LP reader may differ in coefficients, bounds, types or objective',
        cap_seconds=120,budget_category='C',subscope='C-R3 targeted read-only model diagnosis; not a transfer of unused C-R1 allowance',
        model=staged.relative_to(ROOT).as_posix(),model_SHA256=MODEL_SHA,
        original_model_path=str(old),original_scope='D_group24 / X-35-U / Seed1 / S2 / call4',
        python=str(PYTHON),python_SHA256=C.sha(PYTHON),gurobipy_version=runtime['gurobipy_version'],
        gurobipy_init=runtime['gurobipy_init'],gurobipy_init_SHA256=runtime['gurobipy_init_SHA256'],
        DLL=str(C.DLL),DLL_SHA256=C.DLL_SHA,
        script=Path(__file__).relative_to(ROOT).as_posix(),script_SHA256=C.sha(__file__),
        helper_bindings={name:C.sha(ROOT/name) for name in ('scripts/round133_common.py','scripts/round99_gurobi_runtime.py')},
        pure_parser=dict(path=PARSER.relative_to(ROOT).as_posix(),file_SHA256=C.sha(PARSER),
                         names=['number','expression','model'],definitions_SHA256=definition_sha,
                         executes_old_checker_top_level=False),
        exact_point_proof=dict(path=PROOF.relative_to(ROOT).as_posix(),SHA256=C.sha(PROOF),
            completion_SHA256=POINT_SHA,rows=proof['rows'],columns=proof['columns'],
            exact_objective=proof['objective']['exact'],new_Fraction_row_check=False),
        expected_model=dict(rows=22996,columns=9391,sense=1,objective_constant=0),
        settings=dict(Threads=1,Seed=1,Presolve=-1,MIPFocus=0,Cuts=-1,MIPGap=0,MIPGapAbs=0,
                      FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        comparison='Name-bijection for rows/columns; every coefficient/RHS/bound/type/objective compared by IEEE binary64 bits; no duplicate named LP terms accepted',
        signed_zero_policy='Record raw signed-zero bit differences; +0 and -0 denote the same exact rational linear-model value. Never claim raw bit identity if they differ.',
        admission_to_proof_transfer='All nonzero binary64 fields and all types/names/dimensions identical; only a separately disclosed sign-of-zero normalization may be algebraically immaterial',
        mismatch_exit='Preserve every delta and stop after this load; no Optimize, new parameters, second load or repeated point calculation',
        limitations=['This new initial-model load is not a snapshot of the historical retained LP/MIP state',
                     'No assertion about hidden presolve/cut/tree matrices or native internal pruning'],
        wording_correction='Earlier D24 proof is serialized-binary64 matrix feasibility; engine-loaded equivalence is established only by this new comparison if it passes',
        destination=(OUT/'diagnostics/C_R3_D24_loaded_bits').relative_to(ROOT).as_posix(),
        native_Optimize_limit=0,Start_limit=0,compilation_limit=0,point_recalculation_limit=0,
        primary_agent_is_unique_meter_starter=True,preparation_outer_seconds=time.perf_counter()-tick)
    C.write(PLAN,plan)
    print(json.dumps(dict(plan=str(PLAN),SHA256=C.sha(PLAN),Optimize=0,native_imports=0)))

def bits(value): return struct.pack('>d',float(value)).hex()

def run():
    tick=time.perf_counter();assert os.environ.get('ROUND133_METERED_PARENT_LABEL'),'primary agent common meter required'
    plan=C.read(PLAN);assert C.sha(__file__)==plan['script_SHA256']
    assert C.sha(sys.executable)==plan['python_SHA256'] and C.sha(C.DLL)==plan['DLL_SHA256']
    for name,digest in plan['helper_bindings'].items():assert C.sha(ROOT/name)==digest
    assert C.sha(ROOT/plan['model'])==plan['model_SHA256']
    assert C.sha(PARSER)==plan['pure_parser']['file_SHA256'] and C.sha(PROOF)==plan['exact_point_proof']['SHA256']
    assert importlib.metadata.version('gurobipy')==plan['gurobipy_version']
    origin=Path(importlib.util.find_spec('gurobipy').origin);assert C.sha(origin)==plan['gurobipy_init_SHA256']
    parser,definition_sha=extract_parser();assert definition_sha==plan['pure_parser']['definitions_SHA256']
    bounds,types,rows,objective=parser(ROOT/plan['model'])
    # No point, row feasibility evaluation, physical reconstruction or enumeration.
    expected_rows={name:(terms,sense,rhs) for name,terms,sense,rhs in rows}
    assert len(expected_rows)==len(rows)==22996 and len(bounds)==9391
    for label,terms,sense,rhs in rows:
        nn=[n for n,c in terms if n is not None];assert len(nn)==len(set(nn)),('duplicate named row term',label)
    nn=[n for n,c in objective if n is not None];assert len(nn)==len(set(nn)),'duplicate objective term'
    expected_obj={n:c for n,c in objective if n is not None}
    expected_constant=sum((c for n,c in objective if n is None),F(0))
    dest=ROOT/plan['destination'];dest.mkdir(parents=True,exist_ok=False)
    C.write(dest/'launch.json',dict(UTC=C.utc(),plan_SHA256=C.sha(PLAN),command=sys.argv,source_SHA256=C.sha(__file__),Optimize=0))
    from round99_gurobi_runtime import gp,binding
    runtime=binding();assert runtime['sha256']==C.DLL_SHA
    deltas=[];comparisons=0;numeric_delta_count=0;zero_delta_count=0
    def compare(label,expected,actual,numeric=True):
        nonlocal comparisons,numeric_delta_count,zero_delta_count
        comparisons+=1
        if numeric:
            eb,ab=bits(expected),bits(actual)
            if eb==ab:return
            zero_only=float(expected)==0.0 and actual==0.0
            if zero_only:zero_delta_count+=1
            else:numeric_delta_count+=1
            deltas.append(dict(field=label,expected=str(expected),actual=repr(actual),expected_bits=eb,actual_bits=ab,
                               kind='SIGNED_ZERO_ONLY' if zero_only else 'BINARY64_VALUE_MISMATCH'))
        elif expected!=actual:
            numeric_delta_count+=1;deltas.append(dict(field=label,expected=expected,actual=actual,kind='STRUCTURAL_MISMATCH'))
    snapshot={}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0)
        for name,value in plan['settings'].items():env.setParam(name,value)
        env.start()
        with gp.read(str(ROOT/plan['model']),env=env) as model:
            model.update();variables=model.getVars();constrs=model.getConstrs()
            names=model.getAttr('VarName',variables);rnames=model.getAttr('ConstrName',constrs)
            assert len(names)==len(set(names)) and len(rnames)==len(set(rnames))
            compare('column_names',sorted(bounds),sorted(names),False)
            compare('row_names',sorted(expected_rows),sorted(rnames),False)
            compare('rows',22996,model.NumConstrs,False);compare('columns',9391,model.NumVars,False)
            compare('sense',1,model.ModelSense,False);compare('objective_constant',expected_constant,model.ObjCon)
            compare('NumStart',0,model.NumStart,False);compare('native_status_loaded',1,model.Status,False)
            readback={name:model.getParamInfo(name)[2] for name in plan['settings']}
            assert readback==plan['settings']
            lower=model.getAttr('LB',variables);upper=model.getAttr('UB',variables)
            vtypes=model.getAttr('VType',variables);obj=model.getAttr('Obj',variables)
            snapshot=dict(model_SHA256=MODEL_SHA,engine_version=list(gp.gurobi.version()),runtime=runtime,
                model_sense=model.ModelSense,objective_constant=model.ObjCon.hex(),native_status=model.Status,
                columns=[],rows=[],loaded_original_model=True,presolve=False,Optimize=0)
            for index,name in enumerate(names):
                snapshot['columns'].append(dict(name=name,lower=lower[index].hex(),upper=upper[index].hex(),
                    type=vtypes[index],objective=obj[index].hex()))
                if name not in bounds:continue
                compare(name+'.lower',bounds[name][0],lower[index]);compare(name+'.upper',bounds[name][1],upper[index])
                compare(name+'.type',types.get(name,'C'),vtypes[index],False)
                compare(name+'.objective',expected_obj.get(name,F(0)),obj[index])
            senses=model.getAttr('Sense',constrs);rhss=model.getAttr('RHS',constrs)
            for index,constr in enumerate(constrs):
                name=rnames[index];expr=model.getRow(constr)
                actual={names[expr.getVar(j).index]:expr.getCoeff(j) for j in range(expr.size())}
                assert len(actual)==expr.size(),'duplicate native coefficient terms'
                snapshot['rows'].append(dict(name=name,sense=senses[index],RHS=rhss[index].hex(),
                    coefficients={n:a.hex() for n,a in actual.items()}))
                if name not in expected_rows:continue
                terms,sense,rhs=expected_rows[name]
                expected={n:c for n,c in terms if n is not None and c}
                constant=sum((c for n,c in terms if n is None),F(0))
                compare(name+'.sense',{'=':'=','<=':'<','>=':'>'}[sense],senses[index],False)
                compare(name+'.RHS',rhs-constant,rhss[index])
                compare(name+'.support',sorted(expected),sorted(n for n,a in actual.items() if a!=0),False)
                for variable,coefficient in expected.items():
                    if variable in actual:compare(name+'.'+variable,coefficient,actual[variable])
            status=model.Status
    # Preserve the actual native-read field values exactly as hexadecimal
    # binary64 strings, in one small compressed scientific carrier.
    with gzip.open(dest/'loaded_model_bits.json.gz','wt',encoding='utf-8') as stream:
        json.dump(snapshot,stream,allow_nan=False,separators=(',',':'))
    with gzip.open(dest/'all_deltas.json.gz','wt',encoding='utf-8') as stream:
        json.dump(deltas,stream,allow_nan=False,separators=(',',':'))
    algebraically_same=numeric_delta_count==0
    C.write(dest/'comparison.json',dict(UTC=C.utc(),plan_SHA256=C.sha(PLAN),model_SHA256=MODEL_SHA,
        prior_proof_SHA256=plan['exact_point_proof']['SHA256'],proven_point_SHA256=POINT_SHA,
        comparisons=comparisons,raw_bitwise_or_structural_mismatches=len(deltas),
        signed_zero_only_differences=zero_delta_count,other_differences=numeric_delta_count,
        raw_all_bits_identical=not deltas,exact_rational_linear_model_identical=algebraically_same,
        source_point_proof_transfer=algebraically_same,point_recalculation=False,
        strict_status='EXACT_LOADED_IDENTITY' if not deltas else 'SIGNED_ZERO_EQUIVALENCE_ONLY' if algebraically_same else 'LOADED_MODEL_DIFFERENCE_STOP',
        exact_proven_objective=plan['exact_point_proof']['exact_objective'],
        loaded_native_status=status,Optimize=0,Start=0,compilation=0,outer_seconds=time.perf_counter()-tick,
        loaded_bits_SHA256=C.sha(dest/'loaded_model_bits.json.gz'),deltas_SHA256=C.sha(dest/'all_deltas.json.gz'),
        runtime=runtime,first_deltas=deltas[:30],limitations=plan['limitations'],
        no_automatic_retry=True,prior_wording='serialized-binary64 matrix',
        new_wording='fresh same-DLL engine-loaded initial matrix' if algebraically_same else 'serialized matrix only; loaded mismatch unresolved'))
    print(json.dumps(dict(status='PASS' if algebraically_same else 'DIFFERENCE_STOP',comparisons=comparisons,
        zero_sign_deltas=zero_delta_count,other_deltas=numeric_delta_count,Optimize=0,seconds=time.perf_counter()-tick)))
    return 0 if algebraically_same else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run'])
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:sys.exit(run())
