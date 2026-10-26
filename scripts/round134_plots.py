"""Publication plots from all fixed points; run only after native timing ends."""
from round134_common import *
def main():
    assert read(OUT/'sequence_driver_status.json')['state']=='COMPLETE_C_D_E_NATIVE' and not budget()['unclosed']
    # Optional task-local plotting packages leave the shared runtime unchanged.
    sys.path.insert(0,str(BUILD/'document-packages'))
    os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    points=read(OUT/'reports/D/six_points.json');assert len(points)==6
    target=OUT/'figures';target.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.18,'savefig.facecolor':'white'})
    fig,axes=plt.subplots(2,1,figsize=(6.8,6.5),layout='constrained')
    colors=['#205b91','#b65e18']
    for ax,role in zip(axes,('K-15-S','UC-B20-B')):
        rows=sorted([p for p in points if p['role']==role],key=lambda r:r['lambda_value'])
        x=[p['lambda_value'] for p in rows]
        for key,label,color,marker in zip(('G','P_avg'),('Ratio-Gini','Average relative deviation'),colors,('o','s')):
            y=[p[key] for p in rows]
            ax.plot(x,y,'--',color=color,alpha=.65,linewidth=1,label=label)
            for p in rows:
                ax.scatter([p['lambda_value']],[p[key]],s=60,marker=marker,edgecolor=color,
                    facecolor=color if p['certificate'] else 'white',linewidth=1.5,zorder=4)
        ax.set_xticks(x,[f"{p['lambda_value']:.3f}\nrho={p['rho']:.4f}" for p in rows])
        ax.set_xlim(.05,.325)
        top=max(p[key] for p in rows for key in ('G','P_avg'))
        ax.set_ylim(0,max(.05,top*1.35))
        ax.set_xlabel('Penalty weight lambda (effective rho below)')
        ax.set_ylabel('Objective component')
        ax.set_title(role+f"  (Omega={rows[0]['Omega']:.4f})",fontsize=11)
        ax.legend(frameon=False,fontsize=9,loc='upper center',ncol=2)
    fig.savefig(target/'weight_tradeoff.png',dpi=300);plt.close(fig)
    roots=read(OUT/'reports/roots.json');tiny=read(OUT/'math/tiny_exact.json')
    fig,axes=plt.subplots(2,1,figsize=(6.8,6.6),layout='constrained')
    axes[0].bar([0,1,2],[.15,.3375,.4],color=['#8fa4b2','#205b91','#4f8b65'],width=.6)
    axes[0].set_xticks([0,1,2],['Old full reference','Old + TC','Integer optimum'],rotation=12)
    axes[0].set_ylabel('Original objective')
    axes[0].set_ylim(0,.5)
    axes[0].set_title('J2/J3 exact tiny comparison',fontsize=11)
    axes[0].text(.5,.92,'Increment 3/16; remaining gap 1/16',ha='center',transform=axes[0].transAxes,fontsize=8)
    positions=np.arange(len(roots));width=.23
    for j,(key,label,color) in enumerate([('L0','S2 LP','#b6c3cc'),('L_old','+ old state penalty','#205b91'),('L_old_TC','+ TC','#b65e18')]):
        axes[1].bar(positions+(j-1)*width,[r[key] for r in roots],width,label=label,color=color)
    axes[1].set_xticks(positions,[r['role'] for r in roots]);axes[1].set_ylabel('Numerical root LP bound')
    axes[1].set_title('Fixed real roots: no TC increment',fontsize=11)
    axes[1].set_ylim(0,max(r[key] for r in roots for key in ('L0','L_old','L_old_TC'))*1.5)
    axes[1].legend(frameon=False,fontsize=9,loc='upper center',ncol=3)
    fig.savefig(target/'count_bound_scope.png',dpi=300);plt.close(fig)
    write(OUT/'figure_metadata.json',dict(UTC=utc(),matplotlib_version=matplotlib.__version__,
        numpy_version=np.__version__,Python=sys.executable,plot_script_SHA=sha(Path(__file__)),
        D_points_SHA=sha(OUT/'reports/D/six_points.json'),root_results_SHA=sha(OUT/'reports/roots.json'),
        tiny_SHA=sha(OUT/'math/tiny_exact.json'),figures={p.name:sha(p) for p in target.glob('*.png')},
        all_six_points_used=True,filled_certified_open_uncertified=True,lines_are_visual_guides_not_frontier_interpolation=True))
    print('Two static research figures created from all fixed observations')
if __name__=='__main__':main()
