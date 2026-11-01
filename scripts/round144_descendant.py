"""One useful saved actual descendant: full RN vs inherited root-PC LP.

The compact child optimization is reused from the completed health qualifier;
only its matched full-RN comparison is newly optimized. No new projection is
installed and no diagnostic information enters formal runs.
"""
import csv,shutil
from round143_qualify import actual_spec,expected_rows
from round143_lp import semantics,residual
from round144_lp import save_gz
import round108_reader as parser
from round144_common import *
configure()
def solve():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    raw=OUT/'qualification03/runs/001/raw/R144_qualification03_001_R-X20-S-T1_S0_RNP'
    assert read(raw/'verification_closeout.json')['native_proof_qualified']
    source=raw/'external/models/L0.1_epoch_0_generation_3_round144_compact.lp'
    expected_SHA=sha(source);control=read(raw/'round144_control_audit.json')
    assert any(v['model_SHA']==expected_SHA and v['kind']=='formal_compact' for v in control['models'])
    with (raw/'external/lp_status_ledger.csv').open(newline='') as f:status=next(r for r in csv.DictReader(f) if r['leaf_id']=='L0.1')
    assert status['optimal']==status['terminal_valid']==status['bound_available']=='1';old_L=float(status['lower_bound'])
    panel=read(OUT/'qualification03_matrix.json')['groups'][0]['launch']['panel'];B=panel['total_initial'];bm=max(0,B-sum(panel['Q_vector']))
    parsed=parser.lp_model(source);spec=actual_spec(parsed,bm,B);assert spec['applicable']
    target=OUT/'LP/R-X20-S-T1_actual_high_child';target.mkdir(parents=True,exist_ok=False);shutil.copyfile(source,target/'inherited_root_PC_child.lp')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(source),env=env) as m:
            for v in m.getVars():v.VType=gp.GRB.CONTINUOUS
            m.remove(m.getConstrByName('r144_PC'));m.update();old=semantics(m);names={v.VarName for v in m.getVars()};row_names={c.ConstrName for c in m.getConstrs()}
            supports={int(i):ys for i,ys in spec['supports'].items()};ut=spec['U_t'];m.addVar(lb=spec['L_t'],ub=ut,name='rn_t')
            for i,ys in supports.items():
                m.addVar(lb=0.,ub=math.nextafter(ut*max(ys),math.inf) if max(ys) else 0.,name=f'rn_Y_{i}')
                for y in ys:m.addVar(lb=0.,ub=ut,name=f'rn_w_{i}_{y}')
                for j in supports:
                    if i<j:m.addVar(lb=0.,ub=1.,name=f'rn_h_{i}_{j}')
            m.update();vs={v.VarName:v for v in m.getVars()};rows=expected_rows(spec)
            for r in rows:
                e=gp.quicksum(v*vs[k] for k,v in r['terms'].items());m.addConstr(e>=r['rhs'] if r['sense']=='>' else e<=r['rhs'] if r['sense']=='<' else e==r['rhs'],name=r['name'])
            m.update();assert semantics(m,names,row_names)==old;m.write(str(target/'RN_child.mps'))
            m.Params.Seed=0;m.Params.Threads=1;m.Params.TimeLimit=120;m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',model_SHA=sha(target/'RN_child.mps'),Seed=0,Threads=1))
            m.optimize();assert m.Status==gp.GRB.OPTIMAL
            point={v.VarName:v.X for v in m.getVars()};quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
            assert max(quality.values())<=1e-6
            save_gz(target/'primal_dual.json.gz',dict(X=point,Pi={c.ConstrName:c.Pi for c in m.getConstrs()},RC={v.VarName:v.RC for v in m.getVars()},VBasis={v.VarName:v.VBasis for v in m.getVars()},CBasis={c.ConstrName:c.CBasis for c in m.getConstrs()}))
            result=dict(PASS=True,role='R-X20-S-T1',domain='Saved actual upper AM-lookahead child L0.1',g_domain=list(parsed['bounds']['G']),
                old_scope_and_complete_objective_retained=True,source_old_compact_SHA=expected_SHA,source_health_batch='qualification03',
                root_PC_child_L=old_L,full_RN_child_L=m.ObjVal,root_PC_descendant_loss=m.ObjVal-old_L,
                compact_child_Optimize_reused=True,new_LP_Optimize=1,Seed=0,Threads=1,Runtime=m.Runtime,Work=m.Work,iterations=m.IterCount,
                quality=quality,residual=residual(m,point),RN=spec,canonical_SHA=sha(target/'RN_child.mps'),
                interpretation='Validity of the root row is inherited; equal descendant optimal values are not a theorem. This is one measured descendant, not the full tree.')
            write(target/'result.json',result);print(json.dumps(result),flush=True)
def run():assert metered('actual_descendant_RN','diagnostic',[LP_PYTHON,'-B',__file__,'solve'],150,180)==0
if __name__=='__main__':globals()[sys.argv[1]]()
