"""Restore only fixed necessary members, verify saved models/points, no Optimize."""
import csv, zipfile
import round108_reader as parser
from round151_math import scope_from_model
from round143_lp import semantics, residual
from round152_common import *

def prepare():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    dest=WORK/'restore/round152-inherited';dest.mkdir(parents=True,exist_ok=True)
    dependencies=[];domains=[]
    # K35 AP is a fixed historical result, with its complete original model.
    archive_name='results/unified_exact_round135/artifacts/AP_roots_failures_and_costs.zip'
    archive=dest/'AP_roots_failures_and_costs.zip'
    if not archive.exists():archive.write_bytes(subprocess.check_output(['git','show',BASE+':'+archive_name],cwd=ROOT))
    assert sha(archive)=='25fa79b6a926db58b3f4cede8bf9f7d102ecf7af5b64c467f502e64f6075ac24'
    with zipfile.ZipFile(archive) as z:
        selected=[name for name in z.namelist() if '/roots/K-35-U/' in name and name.endswith(('original.lp','result.json','solution.json.gz','scope.json','AP_row.json','qualification.json','native.log'))]
        for name in selected:
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);data=z.read(name)
            if target.exists():assert target.read_bytes()==data
            else:target.write_bytes(data)
            dependencies.append(dict(commit=BASE,archive=archive_name,archive_SHA=sha(archive),member=name,SHA256=sha(target),bytes=len(data),restored=str(target)))
    reuse=read(ROOT/'results/unified_exact_round151/reuse_index.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for role in ['N-B35-S','K-35-U','N-C20-U']:
            folder=OUT/'domains'/role;folder.mkdir(parents=True,exist_ok=True)
            old_ap=None
            if role.startswith('N-'):
                rec=next(d for d in reuse['domains'] if d['role']==role)
                inherited=WORK/'restore/round151-inherited'/role
                source=inherited/'external/models/L0_epoch_0_generation_1.lp'
                for r in rec['members']:
                    p=inherited/('external/'+r['member'].split('/external/',1)[1] if '/external/' in r['member'] else 'observations.json')
                    assert sha(p)==r['SHA256']
                    dependencies.append(dict(commit=rec['fixed_science'],archive=rec['archive'],archive_SHA=rec['archive_SHA'],member=r['member'],SHA256=r['SHA256'],bytes=p.stat().st_size,restored=str(p)))
                point={r['name']:float(r['value']) for r in csv.DictReader((inherited/'external/round127_root_lp.csv').open(encoding='utf-8-sig'))}
                assert read(inherited/'external/round127_root_lp_status.json')['complete']
                panel=next(g['launch']['panel'] for g in read(ROOT/'results/unified_exact_round137/matrix_frozen.json')['groups'] if g['launch']['id']==role)
                oldL=next(d['old_B_L'] for d in read(ROOT/'results/unified_exact_round151/LP_frozen.json')['domains'] if d['role']==role)
                bm=max(0,panel['total_initial']-sum(panel['Q_vector']));B=panel['total_initial']
            else:
                k=dest/'results/unified_exact_round135/roots/K-35-U'
                source=k/'inherited/current_export/original.lp'
                contemporary=ROOT/'results/unified_exact_round143/inherited/roots/K-35-U'
                same=parser.lp_model(source)==parser.lp_model(contemporary/'inherited/original.lp')
                assert same,'Do not reuse a point from a different complete domain'
                meta=read(contemporary/'scope.json');panel=meta['panel'];bm=meta['Bminus'];B=meta['B']
                br=read(contemporary/'base/result.json');point=load_gz(contemporary/'base/solution.json.gz');oldL=br['L']
                assert sha(contemporary/'base/solution.json.gz')==br['solution_SHA']
                for part in ['inherited/original.lp','base/result.json','base/solution.json.gz','scope.json']:
                    p=contemporary/part
                    dependencies.append(dict(commit=BASE,path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size,restored=str(p),source_carrier='R143 inherited roots; exact member references finalized in reuse_index'))
                old_ap=dict(result=read(k/'LP/result.json'),point_path=str(k/'LP/solution.json.gz'),row=read(k/'AP_row.json'),same_R135_R143_complete_model=True)
            parsed=parser.lp_model(source);scope=scope_from_model(parsed,bm,B)
            with gp.read(str(source),env=env) as m:
                for v in m.getVars():v.VType='C'
                m.update();check=residual(m,point)
                assert max(check['constraints'],check['bounds'])<=1e-6 and abs(check['objective']-oldL)<1e-8
                m.write(str(folder/'B.mps'));save_gz(folder/'B_solution.json.gz',point)
                counts=dict(columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs)
                if old_ap:
                    before=semantics(m);names={v.VarName for v in m.getVars()};oldrows={c.ConstrName for c in m.getConstrs()}
                    vs={v.VarName:v for v in m.getVars()};rr=old_ap['row']['terms']
                    m.addConstr(gp.quicksum(a*vs[n] for n,a in rr.items())>=0,name='r135_AP');m.update()
                    assert semantics(m,names,oldrows)==before
                    apoint=load_gz(old_ap['point_path']);acheck=residual(m,apoint);aval=old_ap['result']['L_AP']
                    assert max(acheck['constraints'],acheck['bounds'])<=1e-6 and abs(acheck['objective']-aval)<1e-8
                    target=OUT/'LP'/f'{role}_AP';target.mkdir(parents=True,exist_ok=False)
                    m.write(str(target/'model.mps'));save_gz(target/'solution.json.gz',apoint)
                    write(target/'result.json',dict(role=role,variant='AP',L=aval,g=apoint['G'],qualified=True,reused=True,Optimize_new=0,
                          old_L=oldL,quality=old_ap['result']['quality'],residual=acheck,source=old_ap['result'],all_variables_free=True,
                          same_complete_domain_verified=True,model_SHA=sha(target/'model.mps')))
            item=dict(role=role,scope=scope,panel=panel,source=str(source),source_SHA=sha(source),B_L=oldL,B_residual=check,counts=counts,
                      AP_reused=bool(old_ap),B_Optimize_new=0,scope_reads_actual_objective=True)
            write(folder/'domain.json',item);domains.append(item)
    write(OUT/'reuse_index.json',dict(dependencies=dependencies,baseline_Optimize_new=0,old_producer_called=False))
    write(OUT/'domains.json',domains)
    write(OUT/'source_identity.json',dict(UTC=utc(),base=BASE,branch='codex/round152-resource-integer-objective',temporary_PR_base='codex/round151-standalone-penalty-propagation',Native=binding(),production_unchanged=True,production_PE='E:/codes/ExactEBRP-work/build-cache/round151/ExactEBRP.exe',production_PE_SHA='fbdd7c2ece5c748e086761f2490fd901ccdaeffa29df357d2d98fd8743e1dc39',python=str(PYTHON),python_SHA=sha(PYTHON)))
    print(json.dumps([{k:d[k] for k in ['role','B_L','AP_reused','counts']} for d in domains]),flush=True)

if __name__=='__main__':prepare()
