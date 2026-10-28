"""Standalone scientific figure from complete finite-budget endpoints."""
from round137_common import *

def main():
    assert not budget()['unclosed'] and read(OUT/'reports/summary.json')['completed']==120
    cache=TEMP/'matplotlib';cache.mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(cache)
    local_plot_dependencies=WORK/'build-cache/round137/python-packages'
    if local_plot_dependencies.is_dir():sys.path.insert(0,str(local_plot_dependencies))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    rows=[r for r in read(OUT/'reports/arms.json') if r['stage']=='B2']
    methods=['P','PS','S2'];colors=dict(P='#31688e',PS='#e1812c',S2='#26855b')
    names=dict(P='P',PS='PS',S2='GI-TBC')
    plt.rcParams.update({'font.size':10.5,'axes.titlesize':10.5,'xtick.labelsize':9,'ytick.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':200})
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.6),constrained_layout=True)
    for ax,base in zip(axes.flat,['R-B20-S','R-X20-S','R-B35-S','R-X35-S']):
        subset=[r for r in rows if r['base_id']==base]
        for method in methods:
            rr=sorted([r for r in subset if r['method']==method],key=lambda x:x['T'])
            xx=[r['T']/60 for r in rr]
            ax.plot(xx,[r['U'] for r in rr],color=colors[method],lw=1.7)
            ax.plot(xx,[r['L'] for r in rr],color=colors[method],lw=1.5,ls='--',marker='v',ms=4)
            for r,x in zip(rr,xx):
                ax.scatter([x],[r['U']],s=dict(P=80,PS=50,S2=28)[method],linewidths=1.05,edgecolors=colors[method],facecolors=colors[method] if r['certificate'] and r['performance_eligible'] else 'white',zorder=4)
        floor=subset[0]['offline_problem_floor'];ax.axhline(floor,color='#999999',lw=.8,ls=':')
        source='CABI' if '-B' in base else 'Divvy';n=subset[0]['n']
        ax.set(title=fr'{source}, $n={n}$, fixed $\rho=1$',xlabel=r'Physical route horizon $T$ (minutes)',ylabel=r'Original objective $F$')
        ax.set_xticks(sorted(set(r['T']/60 for r in subset)));ax.grid(axis='y',color='#dddddd',lw=.6)
        ax.set_ylim(bottom=0)
    handles=[Line2D([0],[0],color=colors[m],lw=1.7,label=names[m]) for m in methods]
    handles += [Line2D([0],[0],color='#555555',marker='o',mfc='white',label='Feasible $U$'),
                Line2D([0],[0],color='#555555',ls='--',marker='v',label='Qualified $L$'),
                Line2D([0],[0],color='#555555',ls='none',marker='o',mfc='#555555',label='Certified $U$'),
                Line2D([0],[0],color='#999999',ls=':',label='Analytic positive floor')]
    fig.legend(handles=handles,loc='outside lower center',ncol=4,frameon=False,fontsize=9)
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    fig.savefig(folder/'resource_endpoints.png',bbox_inches='tight');fig.savefig(folder/'resource_endpoints.svg',bbox_inches='tight')
    plt.close(fig)
    write(folder/'figure_source.json',dict(UTC=utc(),source_SHA=sha(OUT/'reports/arms.json'),
        rows=[r['position'] for r in rows],no_cap_imputation=True,filled_U_means_qualified_certificate=True,
        matplotlib_version=matplotlib.__version__,Python=sys.executable,local_plot_dependencies=str(local_plot_dependencies),
        design=dict(inches=list(fig.get_size_inches()),base_font_points=10.5,tick_and_legend_points=9),
        caption='Finite-budget U/L at the two physical T values; connecting lines do not assert exact optimal values or monotone search performance',
        outputs={n:sha(folder/n) for n in ['resource_endpoints.png','resource_endpoints.svg']}))

if __name__=='__main__':main()
