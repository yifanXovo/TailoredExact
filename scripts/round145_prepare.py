"""Bounded setup, diagnostic provenance and zero-Optimize metadata amendment."""
import gzip
from round145_lp import domain
from round145_common import *
configure()
def initial():
    configure();assert not (OUT/'start_receipt.json').exists()
    protected=Path('E:/codes/ExactEBRP')
    tracked=git('status','--porcelain=v1','--untracked-files=no',cwd=protected).decode()
    (OUT/'protected_original_tracked_status.txt').write_text(tracked,encoding='utf-8')
    write(OUT/'start_receipt.json',dict(UTC=utc(),branch=git('branch','--show-current').decode().strip(),
        base=BASE,main=git('rev-parse','origin/main').decode().strip(),R144_in_main=False,PR_base='codex/round144-rn-projection',
        predecessor_PR=dict(number=206,open=True,Draft=True,head=BASE),goal_SHA=sha(OUT/'goal.md'),
        protected_original=str(protected),protected_tracked_status_SHA=sha(OUT/'protected_original_tracked_status.txt'),
        preexisting_active_tree_untracked_are_old_round_assets=True,no_preexisting_solver_seen_at_initial_inspection=True,
        ceiling_seconds=28800,Gurobi_Seed=0,H_seed=20260626,threads=1,serial=True,affinity_mask=4,
        policy='All new build/raw/temp/restore under ExactEBRP-work; bounded post-PR current-round cleanup after evidence/public recovery',
        preliminary_attachments_available=False,preliminary_reconstruction='goal and verified fixed historical carriers; no old experiment rerun'))
    versions=OUT/'engineering/diagnostic_helpers';versions.mkdir(parents=True,exist_ok=True)
    lp=(ROOT/'scripts/round145_lp.py').read_text()
    original=lp.replace("baseline_check=residual(model,d['point']);assert max(baseline_check['constraints'],baseline_check['bounds'])<=1e-6 and abs(baseline_check['objective']-d['old']['L'])<1e-8", "check=residual(model,d['point']);assert max(check['constraints'],check['bounds'])<=1e-6 and abs(check['objective']-d['old']['L'])<1e-8").replace('baseline_residual=baseline_check,','baseline_residual=check,')
    (versions/'round145_lp_v1.py').write_text(original,encoding='utf-8',newline='\n')
    mathfile=(ROOT/'scripts/round145_math.py').read_text()
    originalmath=mathfile.replace("        # RN inventory equalities identify sum(rn_Y_i) with sum(y*w_iy).\n        terms={f'rn_Y_{i}':F(1) for i in support}", "        terms={f'rn_w_{i}_{y}':F(y) for i,ys in support.items() for y in ys if y}")
    (versions/'round145_math_v1.py').write_text(originalmath,encoding='utf-8',newline='\n')
    (versions/'round145_math_v2.py').write_text(mathfile,encoding='utf-8',newline='\n')
    changes=[]
    for path in sorted((OUT/'LP').glob('*/result.json')):
        result=read(path);assert result['writer_SHA']==sha(versions/'round145_lp_v1.py')
        assert result['math_SHA'] in (sha(versions/'round145_math_v1.py'),sha(versions/'round145_math_v2.py'))
        raw=json.loads(gzip.decompress((path.parent/'primal_dual_matrix.json.gz').read_bytes()));d=domain(result['role'])
        point=d['point'];added=set(read(path.parent/'new_rows.json')['actually_added'])
        high=0.
        for row in raw['rows']:
            if row['name'] in added:continue
            lhs=math.fsum(a*point[k] for k,a in row['terms'].items())
            v=max(0.,row['rhs']-lhs) if row['sense']=='>' else max(0.,lhs-row['rhs']) if row['sense']=='<' else abs(lhs-row['rhs'])
            high=max(high,v)
        check=dict(constraints=high,bounds=max(max(c['LB']-point[k],point[k]-c['UB'],0.) for k,c in raw['columns'].items()),
            objective=raw['ObjCon']+math.fsum(c['Obj']*point[k] for k,c in raw['columns'].items()))
        assert max(check['constraints'],check['bounds'])<=1e-6 and abs(check['objective']-result['inherited_RN_L'])<=1e-8
        changes.append(dict(path=str(path.relative_to(ROOT)),before_SHA=sha(path),previous_mislabeled_value=result['baseline_residual']))
        result['baseline_residual']=check;result['baseline_metadata_amended_without_Optimize']=True;write(path,result);changes[-1]['after_SHA']=sha(path)
    write(OUT/'engineering/diagnostic_metadata_amendment.json',dict(UTC=utc(),Optimize=0,Native_load=0,
        reason='Independent review: baseline_residual had been overwritten by final residual; recomputed from saved matrix/old point; objectives and actual scientific outcomes unchanged',changes=changes,
        preserved_helpers={p.name:sha(p) for p in versions.iterdir()}))
    print('Initial identities and diagnostic helper lineage recorded; metadata-only baseline repair, Optimize=0')
if __name__=='__main__':globals()[sys.argv[1]]()
