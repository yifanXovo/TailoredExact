"""Static scientific figures; run only outside timed native computation."""
from round138_common import *

def main():
    assert not budget()['unclosed'] and read(OUT/'reports/full.json')['complete']
    os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib')
    sys.path.insert(0,str(WORK/'build-cache/round137/python-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    tick=time.perf_counter();dest=OUT/'figures';dest.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'savefig.facecolor':'white'})
    rows=read(OUT/'reports/LP.json')['rows'];by={(r['role'],r['variant']):r for r in rows}
    pairs=read(OUT/'reports/full.json')['core_pairs']
    fig,axes=plt.subplots(2,1,figsize=(6.8,7.6),layout='constrained')
    roles=['K-35-U','R-X20-S-T1','R-X35-S-T2','K-20-S'];x=np.arange(4);w=.34
    axes[0].bar(x-w/2,[by[r,'stock']['delta_new_base'] for r in roles],w,label='Stock RLT',color='#2675ad')
    axes[0].bar(x+w/2,[by[r,'tc_stock']['delta_new_base'] for r in roles],w,label='TC + stock RLT',color='#dc8b2a',hatch='//')
    axes[0].set_xticks(x,['K35','RX20-T1','RX35-T2','K20']);axes[0].set_ylabel('Original-objective LP bound increment')
    axes[0].set_title('(a) Same-domain root LPs');axes[0].legend(frameon=False);axes[0].grid(axis='y',alpha=.18)
    x=np.arange(len(pairs))
    axes[1].bar(x-w/2,[r['base_signed_gap'] for r in pairs],w,label='GI-TBC (matched R137)',color='#777d83')
    axes[1].bar(x+w/2,[r['stock_signed_gap'] for r in pairs],w,label='GI-TBC + stock RLT (V1)',color='#2675ad',hatch='//')
    labels={'K-15-S':'K15','R-X20-S-T1':'RX20','K-20-S':'K20','K-35-U':'K35',
            'R-B35-S-T1':'RB35-T1','R-B35-S-T2':'RB35-T2','R-X35-S-T1':'RX35-T1','R-X35-S-T2':'RX35-T2'}
    axes[1].set_xticks(x,[labels[r['role']] for r in pairs],rotation=40,ha='right')
    axes[1].set_ylabel('Signed endpoint gap U - L');axes[1].set_title('(b) Complete-method endpoints, Seed 0')
    axes[1].legend(frameon=False,fontsize=8);axes[1].grid(axis='y',alpha=.18)
    fig.savefig(dest/'paired_evidence.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.8,5.4),layout='constrained')
    ax.fill([0,1,0],[0,0,1],color='#dceaf5',label='Inventory budget: Y1 + Y2 <= 1')
    ax.plot([0,1],[2,0],'--',color='#666666',lw=1.7,label='Ratio bound: Y1 + Y2/2 <= 1')
    ax.plot([.5,0],[0,1.5],color='#bd6e38',lw=1.6)
    ax.scatter([.5,0,.25],[0,1.5,.75],s=[55,70,70],color=['#2675ad','#b3483e','#222222'],zorder=4)
    box=dict(facecolor='white',edgecolor='none',pad=1.5)
    ax.annotate('alpha endpoint\ng = 0, stock = 1/2',(.5,0),(.65,.18),arrowprops={'arrowstyle':'-','color':'#555555'},bbox=box)
    ax.annotate('beta endpoint\ng = 1/2, stock = 3/2',(0,1.5),(.25,1.48),arrowprops={'arrowstyle':'-','color':'#555555'},bbox=box)
    ax.annotate('Observed average\nY = (1/4, 3/4)',(.25,.75),(.55,.85),arrowprops={'arrowstyle':'-','color':'#555555'},bbox=box)
    ax.set_xlim(-.07,1.25);ax.set_ylim(-.07,2.12);ax.set_xlabel('Y1');ax.set_ylabel('Y2')
    ax.set_title('A ratio-consistent product mixture can violate stock consistency')
    ax.legend(loc='upper right',frameon=False,fontsize=8);ax.grid(alpha=.15)
    fig.savefig(dest/'heterogeneous_product.png',dpi=180);plt.close(fig)
    write(OUT/'figure_manifest.json',dict(UTC=utc(),seconds=time.perf_counter()-tick,
        files={p.name:dict(SHA256=sha(p),bytes=p.stat().st_size) for p in dest.glob('*.png')},
        root_deltas_are_not_complete_method_gains=True,
        counterexample_scope='Pure continuous product block; endpoint states are fractional distributions, not BRP fleets',Optimize=0))
    print('Two static scientific figures generated; visual review remains required')

if __name__=='__main__':main()
