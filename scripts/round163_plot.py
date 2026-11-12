"""One standalone scientific endpoint figure; no fabricated OPEN solve times."""
from round163_common import *

def prepare_environment():
    """Isolated plot-only dependencies; no production Python/PE change."""
    import ctypes
    k=ctypes.WinDLL('kernel32');k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    assert k.SetProcessAffinityMask(k.GetCurrentProcess(),1)
    target=TEMP/'plot-libs';assert not target.exists()
    target.mkdir(parents=True)
    command=[sys.executable,'-B','-m','pip','--disable-pip-version-check','--no-input','install',
             '--no-compile','--target',str(target),'matplotlib==3.10.8']
    tick=time.perf_counter()
    with (OUT/'infra/plot_dependency_install.log').open('wb') as log:
        r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    write(OUT/'infra/plot_dependency_install.json',dict(UTC=utc(),command=command,exit_code=r.returncode,
        ordinary_dependency_IO_seconds=time.perf_counter()-tick,affinity_mask=1,target=str(target),
        production_environment_changed=False,Optimize=0,scientific_seconds=0,
        intended_use='standalone plotting only, outside the measured implementation'))
    assert r.returncode==0

def run():
    sys.path.insert(0,str(TEMP/'plot-libs'))
    os.environ['MPLCONFIGDIR']=str(TEMP/'plot-mpl-config')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    arms=read(OUT/'reports/complete_arms.json');inputs=read(OUT/'input_manifest.json')['roles']
    assert len(arms)==18 and len(inputs)==6
    colors={'B':'#245787','Eplus':'#B96124','P':'#6B7280'};labels={'B':'B','Eplus':'E+','P':'P-GRB'}
    fig,axes=plt.subplots(3,2,figsize=(12,9),constrained_layout=True)
    for p,ax in zip(inputs,axes.flat):
        current={a['method']:a for a in arms if a['id']==p['id']}
        ticks=[]
        for y,m in zip([2,1,0],['B','Eplus','P']):
            a=current[m];c=colors[m]
            ax.plot([a['L'],a['U']],[y,y],color=c,lw=2.5,zorder=1)
            ax.scatter([a['L']],[y],marker='s',c=c,s=48,zorder=3)
            ax.scatter([a['U']],[y],marker='o',c=c,s=48,zorder=3)
            if abs(a['raw_search_L']-a['L'])>1e-7:ax.scatter([a['raw_search_L']],[y],marker='^',facecolors='none',edgecolors=c,s=55,zorder=4)
            ticks.append(labels[m]+'  '+a['state']+(f' ({a["T_cert"]:.1f}s)' if a['certificate'] else ''))
        values=[a[k] for a in current.values() for k in ['L','U']]
        span=max(values)-min(values);pad=max(.003,span*.08)
        ax.set_xlim(min(values)-pad,max(values)+pad);ax.set_ylim(-.5,2.5)
        ax.set_yticks([2,1,0],ticks,fontsize=9)
        ax.set_title(f'{p["id"]}  |  physical T={p["T_seconds"]}s',loc='left',fontsize=11,pad=10)
        ax.set_xlabel('Original objective',fontsize=9);ax.grid(axis='x',color='#E0E0E0',lw=.6)
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    fig.suptitle('Frozen complete methods on six prospective archived-source configurations',fontsize=14)
    handles=[Line2D([],[],color='#222222',marker='s',linestyle='',label='Final qualified proof L'),
             Line2D([],[],color='#222222',marker='o',linestyle='',label='Verified physical U'),
             Line2D([],[],color='#222222',marker='^',markerfacecolor='none',linestyle='',label='Raw search L when different')]
    fig.legend(handles=handles,loc='outside lower center',ncol=3,frameon=False,fontsize=9)
    dest=OUT/'figures/prospective_endpoints.png';dest.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(dest,dpi=220);plt.close(fig)
    write(OUT/'figures/figure_record.json',dict(UTC=utc(),path=dest.relative_to(ROOT).as_posix(),SHA256=sha(dest),
        source_SHA256=sha(OUT/'reports/complete_arms.json'),scope='all 18 arms, original endpoints; per-role axes',
        certificate_times_only_for_CERT=True,OPEN_times_not_substituted_by_cap=True,numerical_values_not_rounded_in_source=True))
    print(str(dest))

if __name__=='__main__':
    if len(sys.argv)>1:globals()[sys.argv[1]]()
    else:run()
