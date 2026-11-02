"""Qualified physical-incumbent trajectories on actual producer clocks."""
import csv
from round145_common import *
def main():
    assert not budget()['unclosed'];full=read(OUT/'reports/full.json');records=[];curves={}
    for a in full['new_arms']:
        d=Path(a['destination']);assert read(d/'audit.json')['passed'] and read(d/'verification_closeout.json')['native_proof_qualified']
        observations=read(d/'observations.json');best=math.inf;points=[]
        for item in observations:
            e=item['payload']
            if e['kind']!='witness':continue
            u=float(e['objective']);t=float(item['effective_available_seconds'])
            if u>=best-1e-15:continue
            best=u;assert 0<=t<=a['T_produce']+.1
            row=dict(role=a['role'],method=a['method'],seed=a['seed'],producer_seconds=t,U=u,sequence=item['sequence'],
                committed_event_SHA=item['sha256'],source=e['source'],PE_SHA=a['PE_SHA'],
                raw_observation_SHA=sha(d/'observations.json'),clock='effective committed availability on the producer wall clock; not Native log time or T_total')
            records.append(row);points.append((t,u))
        assert points and abs(best-a['U'])<=1e-8,(a['role'],best,a['U'])
        points.append((a['T_produce'],a['U']));curves[(a['role'],a['method'],a['seed'],a['PE_SHA'])]=points
    target=OUT/'reports/verified_U_trajectories.csv'
    with target.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]) if records else []);w.writeheader();w.writerows(records)
    pairs=[p for p in full['pairs'] if p['role'] in ['K-35-U','R-B35-S-T2'] and p['seed']==0]
    if pairs:
        # Keep optional authoring dependencies and Matplotlib caches local to
        # this round; no global interpreter or app configuration is changed.
        local_deps=TEMP/'document-deps'
        if not local_deps.exists():local_deps=WORK/'temp/round144/document-deps'
        if local_deps.exists():sys.path.insert(0,str(local_deps))
        os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib-cache')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        figures=[]
        for pair in pairs:
            role=pair['role'];title,stem=('K35','K35') if role=='K-35-U' else ('RB35-T2','RB35_T2')
            arm=next(a for a in full['new_arms'] if a['role']==role and a['method']=='RNJP' and a['seed']==0)
            pe=arm['PE_SHA'];figure,ax=plt.subplots(figsize=(8.0,3.7),layout='constrained')
            for method,color,label in [('OFF','#305e8c','stable-off'),('RNJP','#bc572b','RN-JP'),('RNP','#387b53','RN-P bridge')]:
                key=(role,method,0,pe)
                if key not in curves:continue
                if method=='RNJP' and not arm.get('PC_emitted',False):label+=' (no PC)'
                values=curves[key];ax.step([t/60 for t,u in values],[u for t,u in values],where='post',color=color,lw=1.8,label=label)
            ax.set(xlabel='Producer wall time (minutes)',ylabel='Verified physical objective U',title=title+': same PE, Seed 0, independent own H')
            ax.grid(axis='y',alpha=.22);ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False)
            path=OUT/('figures/'+stem+'_verified_U.png');path.parent.mkdir(parents=True,exist_ok=True);figure.savefig(path,dpi=200);plt.close(figure)
            figures.append(dict(role=role,figure=str(path.relative_to(ROOT)),SHA256=sha(path),PC_emitted=arm.get('PC_emitted',False)))
        write(OUT/'figure_manifest.json',dict(PASS=True,figures=figures,data_SHA=sha(target),
            source='Postqualified original committed physical witnesses only; no LP primals, historical incumbents or Native log clock substitutions',
            T_verify_and_T_total_separate=True,Optimize=0,Native_load=0))
    print(json.dumps(dict(improvement_events=len(records),curves=len(curves),Optimize=0,Native_load=0)))
if __name__=='__main__':main()
