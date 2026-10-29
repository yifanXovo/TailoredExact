"""Compact scientific plots from sealed summaries only, outside native timing."""
from round139_common import *

def main():
    assert not budget()['unclosed'] and read(OUT/'reports/full.json')['complete']
    os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib')
    sys.path.insert(0,str(WORK/'build-cache/round137/python-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    full=read(OUT/'reports/full.json');decision=read(OUT/'candidate_decision.json');candidate=decision.get('selected_uniform_candidate')
    dest=OUT/'figures';dest.mkdir(exist_ok=True)
    if candidate and candidate not in ['base','both']:
        rows=[r for r in full['new_arms'] if r['method']==candidate and r['seed']==0]
        base={r['role']:r for r in full['reused_arms'] if r['method']=='base'}
        both={r['role']:r for r in full['reused_arms'] if r['method']=='both'}
        fig,axes=plt.subplots(2,1,figsize=(7.1,6.4),layout='constrained');x=np.arange(len(rows));width=.36
        for ax,key,title in zip(axes,['U','L'],['(a) Verified upper bound change (positive is worse)','(b) Supported lower bound change (positive is stronger)']):
            ax.bar(x-width/2,[r[key]-base[r['role']][key] for r in rows],width,label=candidate+' vs BASE',color='#2675ad')
            ax.bar(x+width/2,[both[r['role']][key]-base[r['role']][key] for r in rows],width,label='BOTH vs BASE (reused)',color='#dc8b2a',hatch='//')
            ax.axhline(0,color='#454545',linewidth=.7);ax.set_title(title);ax.set_xticks(x,[r['role'].replace('R-','').replace('-S','').replace('-U','') for r in rows],rotation=30,ha='right');ax.grid(axis='y',alpha=.18);ax.legend(frameon=False,fontsize=8)
        fig.savefig(dest/'placement_endpoints.png',dpi=180);plt.close(fig)
    else:
        roles=['K-15-S','K-20-S','R-B35-S-T2'];allrows=full['reused_arms']+full['new_arms']
        by={(r['role'],r['method']):r for r in allrows if r['seed']==0};x=np.arange(3);w=.24
        fig,axes=plt.subplots(2,1,figsize=(7.1,6.0),layout='constrained')
        for ax,key,title in zip(axes,['U','L'],['(a) Verified upper bound change (positive is worse)','(b) Supported lower bound change (positive is stronger)']):
            for j,(method,color) in enumerate([('both','#dc8b2a'),('lp-only','#2675ad'),('mip-only','#3c9965')]):
                ax.bar(x+(j-1)*w,[by[r,method][key]-by[r,'base'][key] for r in roles],w,color=color,label=method+' (R138 reused)' if method=='both' else method)
            ax.axhline(0,color='#454545',linewidth=.7);ax.set_xticks(x,['K15','K20','RB35-T2']);ax.set_title(title);ax.grid(axis='y',alpha=.18);ax.legend(frameon=False,fontsize=8)
        fig.savefig(dest/'placement_endpoints.png',dpi=180);plt.close(fig)
    trajectories=read(OUT/'reports/native_trajectories_and_witnesses.json')['positions']
    roles=['K-20-S','R-B35-S-T2'];fig,axes=plt.subplots(2,1,figsize=(7.1,6.6),layout='constrained')
    colors={'base':'#777d83','both':'#dc8b2a','lp-only':'#2675ad','mip-only':'#3c9965'}
    for ax,role in zip(axes,roles):
        for item in trajectories:
            if item['role']!=role or item['seed']!=0:continue
            logs=[log for log in item['native'] if log['terminal']]
            if len(logs)!=1:continue
            log=logs[0];events=[e for e in log['events'] if e['approx_native_seconds'] is not None and e['rounded_native_incumbent'] is not None]
            times=[e['approx_native_seconds'] for e in events];values=[e['rounded_native_incumbent'] for e in events]
            if log['native_initial_submitted_Start_objective'] is not None:
                times.insert(0,0.);values.insert(0,log['native_initial_submitted_Start_objective'])
            if log['native_final_logged_objective'] is not None:
                times.append(max(log['native_solver_seconds'],times[-1] if times else 0.));values.append(log['native_final_logged_objective'])
            if not times:continue
            ax.step(times,values,where='post',color=colors[item['method']],label=item['method'])
        ax.set_title(role+' - terminal native incumbent diagnostics, Seed0');ax.set_xlabel('Rounded native solve time (s)');ax.set_ylabel('Rounded native model objective');ax.grid(alpha=.18);ax.legend(frameon=False,fontsize=8)
    fig.savefig(dest/'native_search.png',dpi=180);plt.close(fig)
    write(OUT/'figure_manifest.json',dict(UTC=utc(),figures={p.relative_to(ROOT).as_posix():sha(p) for p in dest.glob('*.png')},
        physical_endpoints_source=sha(OUT/'reports/full.json'),native_diagnostics_source=sha(OUT/'reports/native_trajectories_and_witnesses.json'),
        native_clocks_not_formal_certificate_or_exact_discovery_clocks=True,Optimize=0))

if __name__=='__main__':main()
