"""Static scientific endpoint figure from qualified sealed summaries only."""
from round141_common import *
from round141_analyze import require_idle
import math

def main():
    require_idle()
    os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib')
    sys.path.insert(0,str(WORK/'build-cache/round137/python-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    full=read(OUT/'reports/full.json')
    roles=['K-15-S','K-20-S','K-35-U','R-B35-S-T2']
    methods=['base','both','TC_STOCK','TC2_STOCK','D0','D1']
    labels=['GI-TBC','STOCK','TC+STOCK','TC2+STOCK','D0','D1']
    colors=['#6b7280','#9ca3af','#bc6c25','#9b5de5','#5a7895','#087f8c']
    all_rows=full['reused_arms']+full['new_arms']
    fig,axes=plt.subplots(2,2,figsize=(8.0,6.0),layout='constrained')
    records=[]
    for ax,role in zip(axes.flat,roles):
        data=[]
        for method,label,color in zip(methods,labels,colors):
            rows=[r for r in all_rows if r['role']==role and r['method']==method and r.get('seed',0)==0]
            if rows:data.append((rows[0],label,color))
        assert any(r['method']=='D1' for r,_,_ in data)
        for y,(r,label,color) in enumerate(data):
            ax.plot([r['L'],r['U']],[y,y],color=color,lw=3,solid_capstyle='butt')
            ax.scatter([r['L']],[y],marker='|',s=100,color=color,zorder=3)
            ax.scatter([r['U']],[y],marker='o',s=26,color=color,zorder=3)
            records.append(dict(role=role,method=r['method'],L=r['L'],U=r['U'],certificate=r['certificate']))
        values=[r[k] for r,_,_ in data for k in ['L','U']]
        width=max(values)-min(values);margin=max(width*.08,1e-3)
        ax.set_xlim(min(values)-margin,max(values)+margin)
        ax.set_yticks(range(len(data)),[label for _,label,_ in data],fontsize=11)
        ax.invert_yaxis();ax.set_ylim(len(data)-.45,-.55)
        ax.set_title(role,fontsize=12.5,loc='left',fontweight='bold')
        ax.grid(axis='x',color='#e5e7eb',lw=.7);ax.set_axisbelow(True)
        ax.set_xlabel('Objective F',fontsize=11)
        ax.tick_params(axis='x',labelsize=9.5)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Initial four-role pilot: supported L and verified U, Seed0',fontsize=14)
    dest=OUT/'figures';dest.mkdir(exist_ok=True)
    path=dest/'pilot_endpoints.png';fig.savefig(path,dpi=220,facecolor='white');plt.close(fig)
    write(OUT/'figure_manifest.json',dict(UTC=utc(),figure=path.relative_to(ROOT).as_posix(),SHA=sha(path),
        rows=records,scope='Initial four declared pilot roles; supported intervals, not confidence intervals. Historical source/PE identities retained.',
        matplotlib_version=matplotlib.__version__,plot_dependencies=str(WORK/'build-cache/round137/python-packages'),
        raw_trajectory_or_first_discovery_claim=False,Optimize=0))

if __name__=='__main__':main()
