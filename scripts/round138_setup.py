"""Read only the four declared R137 root carriers; register fixed domains."""
from round138_common import *
import collections, csv, io, zipfile
import round108_reader as core

POSITIONS = [14,43,59,12]

def stock_rows(n, alpha, beta, Bminus, B):
    result=[]
    for slope,budget,sense in [(alpha,Bminus,'>='),(beta,B,'>='),
                               (beta,Bminus,'<='),(alpha,B,'<=')]:
        terms={f'zprod_{i}':1. for i in range(1,n+1)}
        if slope: terms.update({f'Y_{i}':-slope for i in range(1,n+1)})
        if budget: terms['G']=-float(budget)
        rhs=-slope*budget
        if slope and budget: rhs=math.nextafter(rhs,math.inf if sense=='<=' else -math.inf)
        result.append((tuple(sorted(terms.items())),sense,rhs))
    return result

def main():
    tick=time.perf_counter()
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('rev-parse','origin/main').decode().strip()=='b2b940c1e517a72e226ec60fc49ff19651737632'
    old=ROOT/'results/unified_exact_round137'
    manifest=read(old/'candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA']
    plan=read(old/'experiment_plan.json');dependencies=[];cases={}
    for position in POSITIONS:
        arm=next(a for a in plan['arms'] if a['position']==position)
        assert arm['method']=='S2' and arm['seed']==0
        p=arm['panel'];role=p['id'];folder=OUT/'roots'/role/'inherited'
        folder.mkdir(parents=True,exist_ok=True)
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        archive=old/'artifacts'/f'campaign_{position:03}.zip';members=[]
        with zipfile.ZipFile(archive) as z:
            prefix=f'results/unified_exact_round137/campaign/{position:03}/'
            raw=next(n for n in z.namelist() if n.endswith('/round127_root_lp.csv')).rsplit('/external/',1)[0]
            selections={'identity.json':prefix+'identity.json',
                        'original.lp':raw+'/external/models/L0_epoch_0_generation_1.lp'}
            for part in ['round127_root_lp.csv','round127_root_lp_status.json','lp_status_ledger.csv',
                         'paper_optimize_ledger.csv','initial_witness.json']:
                selections[part]=raw+'/external/'+part
            if position==14:
                for leaf,gen in [('L0.0',2),('L0.1',3)]:
                    selections[leaf+'.lp']=raw+f'/external/models/{leaf}_epoch_0_generation_{gen}.lp'
            for target,name in selections.items():
                data=z.read(name)
                if (folder/target).exists(): assert (folder/target).read_bytes()==data
                else: (folder/target).write_bytes(data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        dependencies.append(dict(commit='e735c3447eb1443713c700942d873de1783a4a26',
            archive=archive.relative_to(ROOT).as_posix(),SHA256=sha(archive),members=members))
        model=core.lp_model(folder/'original.lp')
        point={r['name']:float(r['value']) for r in csv.DictReader(io.StringIO((folder/'round127_root_lp.csv').read_text()))}
        assert read(folder/'round127_root_lp_status.json')['complete'] and set(point)==set(model['order'])
        ledger=list(csv.DictReader((folder/'lp_status_ledger.csv').open(newline='')))
        root=next(r for r in ledger if r['leaf_id']=='L0')
        calls=list(csv.DictReader((folder/'paper_optimize_ledger.csv').open(newline='')))
        root_call=next(r for r in calls if r['leaf_id']=='L0' and r['solve_kind']=='LP')
        assert sha(folder/'original.lp')==root_call['model_sha256']
        alpha,beta=model['bounds']['G'];assert alpha==float(root['gamma_L']) and beta==float(root['gamma_U'])
        data=core.evidence.instance(ROOT,p);B=sum(data['b'][1:]);Bminus=max(0,B-sum(p['Q_vector']))
        tau=math.fsum(point[f'Y_{i}'] for i in range(1,p['V']+1))
        J=math.fsum(point[f'zprod_{i}'] for i in range(1,p['V']+1));g=point['G']
        added=stock_rows(p['V'],alpha,beta,Bminus,B);checks=[]
        for terms,sense,rhs in added:
            lhs=math.fsum(c*point[n] for n,c in terms)
            checks.append(dict(sense=sense,lhs=lhs,rhs=rhs,violation=max(0.,lhs-rhs if sense=='<=' else rhs-lhs)))
        physical=core.evidence.physical(ROOT,p,read(folder/'initial_witness.json'))
        U=physical['F'];assert abs(U-beta)<1e-9
        Y=[0]+[point[f'Y_{i}'] for i in range(1,p['V']+1)]
        true=core.evidence.objective(data,Y,p['lambda'])
        objective=math.fsum(c*point[n] for n,c in model['objective'][0])+model['objective'][1]
        assert abs(objective-float(root['lower_bound']))<1e-7
        report=dict(role=role,panel=p,source_position=position,alpha=alpha,beta=beta,B=B,Bminus=Bminus,
            tau=tau,G_aux=g,J=J,J_minus_Bg=J-B*g,four_rows=checks,L_saved=objective,validated_U=U,
            saved_Y_true_objective=true,Y_all_integer=all(abs(y-round(y))<1e-8 for y in Y[1:]),
            fractional_selectors=sum(abs(v-round(v))>1e-8 for n,v in point.items() if n.startswith('state_') and not n.startswith('state_g_')),
            saved_LP_SHA256=sha(folder/'original.lp'),no_new_Optimize=True,
            physical_initial=physical,stock_uses_unscaled_Z=True,depot_excluded=True,
            stock_rows=[dict(terms=dict(t),sense=s,rhs=b) for t,s,b in added])
        write(folder.parent/'scope.json',report);cases[role]=report
    write(OUT/'roots/saved_points.json',dict(UTC=utc(),cases=cases,dependencies=dependencies,
          seconds=time.perf_counter()-tick,Optimize=0,solver_imports=0))
    write(OUT/'start_receipt.json',dict(UTC=utc(),base=BASE,
          actual_main=git('rev-parse','origin/main').decode().strip(),R137_in_main=False,
          branch=git('branch','--show-current').decode().strip(),PR_base='codex/round137-gi-tbc-consolidation',
          policy='New assets under ExactEBRP-work; bounded current-round cleanup after public check',
          baseline=manifest,experiment_limit_seconds=86400,default_new_Seed=0,H_seed=20260626,
          protected_original='E:/codes/ExactEBRP',source_goal_SHA=sha(OUT/'goal.md')))
    print(json.dumps({k:{n:v[n] for n in ['G_aux','J','J_minus_Bg','L_saved','validated_U']} for k,v in cases.items()}))

if __name__=='__main__':main()
