"""Standalone scientific trajectory artifact from existing receipts only."""
from round161_common import *
from round161_analyze import events,label_for
import csv

def plot():
    dependencies=WORK/'temp/round161_plot_deps'
    if dependencies.exists():sys.path.insert(0,str(dependencies))
    os.environ['MPLCONFIGDIR']=str(WORK/'temp/round161_plot_config')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report=read(OUT/'reports/bridge.json');fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    colors={'OLD':'#145da0','RN':'#df6d17','RN-P':'#32825f'}
    for row,role in enumerate(('R-X35-S-T2','N-B35-S')):
        for form in ('OLD','RN','RN-P'):
            samples=[x for x in report['samples'] if x['role']==role and x['formulation']==form and x['mode']=='MIP']
            if not samples:continue
            sample=samples[0];folder=OUT/'runs'/label_for(role,form,'MIP');es=events(folder)
            start=next(x['outer_observation_seconds'] for x in es if x['kind']=='call')
            progress=list(csv.DictReader((folder/'progress.csv').open()))
            values=[p for p in progress if p['available']=='1' and -1<float(p['raw_lower'])<1]
            axes[row,0].step([0]+[x['time'] for x in sample['trajectory']]+[sample['T_cpp']],
                [sample['trajectory'][0]['J']]+[x['J'] for x in sample['trajectory']]+[sample['physical_U']],where='post',color=colors[form],label=form+' physical U')
            axes[row,0].step([float(p['time'])+start for p in values],[min(float(p['raw_lower']),next(x['cutoff'] for x in es if x['kind']=='call')) for p in values],
                where='post',color=colors[form],linestyle='--',label=form+' qualified L')
            axes[row,1].step([float(p['work']) for p in values],[float(p['raw_lower']) for p in values],where='post',color=colors[form],linestyle='--',label=form+' qualified L')
            inc=[p for p in progress if 0<=float(p['native_upper'])<10]
            axes[row,1].step([float(p['work']) for p in inc],[float(p['native_upper']) for p in inc],where='post',color=colors[form],label=form+' native incumbent objective')
        axes[row,0].set_title(role+' / observed physical U and qualified L')
        axes[row,1].set_title(role+' / Native Work observations')
        axes[row,0].set_xlabel('Outer seconds (bound timestamps offset from Native Runtime)');axes[row,1].set_xlabel('Native Work')
        for ax in axes[row]:ax.set_ylabel('Original objective units');ax.grid(alpha=.2);ax.legend(fontsize=7)
    target=OUT/'reports/trajectories.png';fig.savefig(target,dpi=160);plt.close(fig)
    write(OUT/'reports/trajectory_plot.json',dict(Optimize=0,path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),
        time='physical U uses journal close observation; lower uses Native Runtime plus pre-opt call receipt offset',
        Work='native incumbent objective is a raw model observation, not substituted for verified physical U',
        qualification='lower curves are retrospectively qualified by each final source state',reused_OLD_controls_for_RN_P=True))

if __name__=='__main__':plot()
