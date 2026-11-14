"""Standalone scientific parameter bands from exact finite knots; no optimizer."""
from round166_common import *
from round166_result_text import upper_bound
from decimal import Decimal
import os
def figures():
    start=time.perf_counter();temp=WORK/'temp/round166/figures';temp.mkdir(parents=True,exist_ok=True)
    os.environ.update(MPLCONFIGDIR=str(temp/'mpl'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    packages=WORK/'build-cache/round137/python-packages'
    if packages.is_dir():sys.path.insert(0,str(packages))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    data=read(OUT/'analysis/parameter_envelopes.json');archive=read(OUT/'review/data_physical_archive.json')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.6,'axes.titlesize':9.2})
    fig,axes=plt.subplots(2,2,figsize=(7.0,5.5));displayed={}
    for ax,family in zip(axes.flat,data['families']):
        low,high=[r['value'] for r in family['rho_range']]
        xs=[p['rho']['value'] for p in family['critical_points']]
        us=[p['U_safe']['value'] for p in family['critical_points']]
        ls=[p['L_safe']['value'] for p in family['critical_points']]
        for p in family['plans']:
            ax.plot([low,high],[p['a']['value']+low*p['b']['value'],p['a']['value']+high*p['b']['value']],color='#aab3be',lw=.8,alpha=.5,zorder=1)
        ax.fill_between(xs,ls,us,color='#9cc9ec',alpha=.5,zorder=2)
        ax.plot(xs,us,color='#17679b',lw=2,zorder=4)
        ax.plot(xs,ls,color='#20272e',lw=1.5,linestyle='--',zorder=3)
        for a in family['anchors']:ax.scatter(a['x']['value'],a['L']['value'],s=27,marker='v',color='#20272e',zorder=6)
        seen=set()
        for r in archive['records']:
            if r['family']!=family['family'] or not r['parameter_analysis']:continue
            x=r['verified']['rho_binary64'];y=r['verified']['F'];key=(x,y)
            if key not in seen:ax.scatter(x,y,s=24,facecolor='white',edgecolor='#a64d2a',linewidth=.9,zorder=5);seen.add(key)
        ax.set_title(family['family'].replace('R134:','').replace('R137:',''))
        bound=upper_bound(family['worst_gap']['gap']['exact'],5)
        if Decimal(bound)<Decimal('0.0001'):bound=format(Decimal(bound),'.4E').replace('E','e')
        displayed[family['family']]=bound
        ax.text(.03,.94,'Whole-range regret ≤ '+bound,transform=ax.transAxes,va='top',fontsize=7.3,
            bbox=dict(boxstyle='round,pad=.22',fc='white',ec='#d5dbe0',alpha=.95))
        ax.set_xlabel(r'Effective weight $\rho$');ax.set_ylabel('Original objective')
        ax.set_xlim(low-.035*(high-low),high+.035*(high-low));ax.grid(alpha=.18)
        ax.spines[['top','right']].set_visible(False);ax.ticklabel_format(useOffset=False,style='plain')
    handles=[Line2D([0],[0],color='#17679b',lw=2,label='Best verified archive upper'),
        Line2D([0],[0],color='#20272e',lw=1.5,ls='--',marker='v',markersize=4,label='Applicable lower chords / anchors'),
        Line2D([0],[0],color='#a64d2a',marker='o',mfc='white',ls='',label='Original run incumbent'),
        Patch(facecolor='#9cc9ec',alpha=.5,label='Remaining quality band')]
    fig.legend(handles=handles,loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.5,.0),fontsize=7.6)
    fig.tight_layout(rect=(0,.10,1,1),h_pad=1.5,w_pad=1.5)
    png=ROOT/'results/unified_exact_round137/figures/parameter_quality_bands.png'
    pdf=OUT/'analysis/parameter_quality_bands.pdf';fig.savefig(png,dpi=220);fig.savefig(pdf);plt.close(fig)
    write(OUT/'analysis/figure_manifest.json',dict(UTC=utc(),Optimize=0,exact_finite_knot_plot=True,grid_optimization=False,
        data=bind(OUT/'analysis/parameter_envelopes.json'),archive=bind(OUT/'review/data_physical_archive.json'),
        outputs=[bind(png),bind(pdf)],generator=bind(Path(__file__)),Matplotlib=matplotlib.__version__,seconds=time.perf_counter()-start))
    receipt=read(OUT/'analysis/figure_manifest.json');receipt.update(displayed_regret_upper_bounds=displayed,
        annotation_rounding='upward to five significant digits using exact rational source',
        rounding_helper=bind(ROOT/'scripts/round166_result_text.py'));write(OUT/'analysis/figure_manifest.json',receipt)
    print('Exact-knot four-panel parameter figure saved.')
if __name__=='__main__':figures()
