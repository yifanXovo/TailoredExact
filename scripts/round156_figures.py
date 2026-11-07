"""Standalone scientific plot from the sealed paid oracle trajectories."""
from round156_common import *

def run():
    from round100_idle import ensure_idle
    configure();ensure_idle()
    cache=WORK/'temp/round156/matplotlib';cache.mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(cache)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report=read(OUT/'reports/oracle_comparison.json');end=max(r['outer_seconds'] for r in report['rows'])
    colors={'RN':'#156b9d','residual':'#b46a12','residual_U':'#7c4394'}
    names={'RN':'RN16384','residual':'Residual','residual_U':'Residual + inventory upper'}
    fig,axes=plt.subplots(1,2,figsize=(10.6,3.9),layout='constrained')
    for method in ['RN','residual','residual_U']:
        row=next(r for r in report['rows'] if r['method']==method)
        curve=load_gz(OUT/'reports/oracle_time_chains'/f'{method}.json.gz')
        x=[0.]+[r['available_no_later_than'] for r in curve]
        lows=[row['initial_lower']]+[r['lower'] for r in curve]
        widths=[row['initial_upper']-row['initial_lower']]+[r['gap'] for r in curve]
        for ax,values in zip(axes,[lows,widths]):
            ax.step(x,values,where='post',color=colors[method],label=names[method],linewidth=1.6)
            ax.plot([row['outer_seconds']],[values[-1]],'o',color=colors[method],markersize=4)
            if row['outer_seconds']<end:
                ax.plot([row['outer_seconds'],end],[values[-1]]*2,color=colors[method],linestyle=':',linewidth=1)
    axes[0].set_ylabel('Qualified original inventory lower')
    axes[0].set_ylim(.2215,.237)
    axes[0].ticklabel_format(axis='y',style='plain',useOffset=False)
    axes[1].set_ylabel('Qualified inventory interval width')
    axes[1].set_yscale('log');axes[1].set_ylim(5e-5,2e-2)
    axes[1].axhline(1e-4,color='#555555',linestyle='--',linewidth=.8,label='Original precision target')
    for ax in axes:
        ax.set_xlabel('Paid outer seconds (conservative availability)')
        ax.set_xlim(0,end*1.025);ax.grid(True,alpha=.16)
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=8,frameon=False)
    axes[1].text(end*.64,1.17e-4,'Original precision target',fontsize=8,color='#555555')
    fig.suptitle('RX35: same saved scope, interval and stocks; all rebuilding paid',fontsize=11)
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    for suffix in ['png','svg']:fig.savefig(folder/('oracle_paid_trajectories.'+suffix),dpi=180,metadata={'Creator':'Round156 sealed evidence plot'})
    plt.close(fig)
    write(folder/'oracle_paid_trajectories.json',dict(report_SHA=sha(OUT/'reports/oracle_comparison.json'),source_SHA=sha(__file__),
        files={suffix:sha(folder/('oracle_paid_trajectories.'+suffix)) for suffix in ['png','svg']},
        conservative_all_nonbody_overhead_prepaid=True,not_exact_callback_wall_timestamps=True,
        dots='Actual completed-arm outer endpoints',dotted_tails='Completed interval carried forward; no further solving or fee',
        original_price_target=1e-4,posthoc_verification_charged_separately=True))
    print(json.dumps(dict(figures=2,report_SHA=sha(OUT/'reports/oracle_comparison.json'))),flush=True)

if __name__=='__main__':run()
