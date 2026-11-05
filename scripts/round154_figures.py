"""Static scientific endpoint plots; no intermediate trajectory qualification."""
from round154_common import *

def run():
    tick=time.perf_counter()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'svg.fonttype':'none','axes.grid':True,'grid.alpha':.16})
    pairs=read(OUT/'reports/complete_pairs.json')['pairs'];science=read(OUT/'reports/scientific_table.json')['rows']
    assert len(pairs)==4 and len(science)==3
    fig,axes=plt.subplots(1,2,figsize=(10.8,3.8),layout='constrained')
    labels={'N-B35-S':'NB35','K-35-U':'K35','R-B35-S-T1':'RB35-T1','N-C20-U':'NC20'}
    colors={'B':'#525967','E':'#176c9c','J':'#a85b21'}
    for i,row in enumerate(pairs):
        for method,shift in [('B',-.18),('E',0),('J',.18)]:
            if method+'_L' not in row:continue
            lo,hi=row[method+'_L'],row[method+'_U'];x=i+shift
            axes[0].plot([x,x],[lo,hi],color=colors[method],lw=2.2,label=method if i==0 else None)
            axes[0].scatter([x],[lo],marker='_',s=80,color=colors[method]);axes[0].scatter([x],[hi],s=24,color=colors[method],zorder=3)
    axes[0].set_xticks(range(4),[labels[r['role']] for r in pairs]);axes[0].set_ylabel('Physical objective: supported L to own feasible U')
    axes[0].set_title('Complete own-H methods, matched PE');axes[0].legend(frameon=False,ncol=3)
    selected=[r for r in science if r['role'] in ('K-35-U','N-C20-U')]
    for i,row in enumerate(selected):
        for shift,lo,hi,color,label in [(-.09,row['R153_lower'],row['R153_upper'],'#9a9da4','R153'),(.09,row['lower'],row['upper'],'#176c9c','R154')]:
            axes[1].plot([lo,hi],[i+shift,i+shift],color=color,lw=3,label=label if i==0 else None)
            axes[1].scatter([lo,hi],[i+shift]*2,color=color,s=18,zorder=3)
    axes[1].set_yticks(range(len(selected)),[labels[r['role']] for r in selected]);axes[1].set_xlabel('Complete inventory-hull LP value')
    axes[1].set_title('Same complete free Q; LP uppers are not fleets');axes[1].legend(frameon=False)
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    for suffix in ['svg','png']:fig.savefig(folder/('round154_endpoints.'+suffix),dpi=180)
    plt.close(fig)
    write(OUT/'figure_creation.json',dict(UTC=utc(),seconds=time.perf_counter()-tick,Native_Optimize=0,
        formatting_only=True,separately_reported=True,source_SHA=sha(__file__),
        sources={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'reports/complete_pairs.json',OUT/'reports/scientific_table.json']}))

if __name__=='__main__':run()
