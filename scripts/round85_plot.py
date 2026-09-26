"""Five proof/protection plots from completed audited checkpoints only; no optimizer."""
import hashlib
import json
import math
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round85'


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started=time.perf_counter();campaign=OUT/'campaign'
    assert not (campaign/'active_run.lock').exists()
    for name in ['audit.json','mechanism_audit.json','replication_audit.json']:
        assert read(campaign/name)['all_checks_passed']
    destination=OUT/'figures'
    assert not destination.exists(), 'Never overwrite a completed plot namespace'
    points=read(campaign/'checkpoints.json');endpoints=read(campaign/'endpoint_checks.json')
    panel={p['id']:p for p in read(OUT/'protocol.json')['panel']}
    assert len(points)==84 and set(panel)=={'E7','S12','D3','C2','C6','C8','D6'}
    protocol=read(OUT/'protocol.json')
    for row in points:
        assert math.isfinite(row['L'])
        if row['available']:assert all(math.isfinite(row[k]) for k in ['U','L','gap'])
        else:assert row['U'] is None and row['gap'] is None
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
        'svg.fonttype':'none','svg.hashsalt':'round85-frozen-checkpoints'})
    colors={'P-GRB':'#575E68','ENS-C':'#009E73','K1-R':'#2267A5'}
    destination.mkdir();outputs=[]
    for identity in ['D3','C2','C6','C8','D6']:
        cap=panel[identity]['cap']; ticks=protocol['checkpoints'][str(cap)]
        fig,axes=plt.subplots(1,3,figsize=(15,5.4))
        for axis,metric,title in zip(axes,['U','L','gap'],
            ['Verified original upper bound U','Qualified whole-domain lower bound L','Absolute gap U - L']):
            values=[]
            for arm,color in colors.items():
                rows=sorted([r for r in points if r['id']==identity and r['arm']==arm],key=lambda r:r['seconds'])
                assert [r['seconds'] for r in rows]==ticks
                x=[r['seconds'] for r in rows]
                y=[r[metric] if metric=='L' or r['available'] else math.nan for r in rows]
                values.extend(v for v in y if math.isfinite(v))
                axis.plot(x,y,color=color,label=arm,marker='o',markersize=4,linewidth=1.5,linestyle='--')
                end=next(r for r in endpoints if r['id']==identity and r['arm']==arm)
                if end['stop_reason']!='normal_return' and rows[-1]['available']:
                    axis.scatter([cap],[y[-1]],s=85,marker='s',facecolors='none',edgecolors=color,linewidths=1.5,zorder=5)
            axis.set(title=title,xlabel='Whole-run elapsed time (seconds)',ylabel=metric)
            axis.set_xticks(ticks);axis.tick_params(axis='x',labelrotation=35)
            axis.set_xlim(max(0,ticks[0]-cap/30),cap+cap/30)
            if values:
                low=min(values);high=max(values);padding=max((high-low)*.10,abs(high)*.025,1e-8)
                axis.set_ylim(min(0,low-padding) if metric=='gap' else max(0,low-padding),high+padding)
            axis.grid(axis='y',color='#DFE3E8',linewidth=.7)
            axis.spines[['top','right']].set_visible(False)
            axis.ticklabel_format(axis='y',style='plain',useOffset=False)
        handles,labels=axes[0].get_legend_handles_labels()
        fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.52,.928),ncol=3,frameon=False,handlelength=2.3,columnspacing=1.8)
        fig.suptitle(f'Round85: {identity} comparison at a common {cap}-second cap',fontsize=14,y=.98)
        fig.subplots_adjust(left=.075,right=.985,top=.82,bottom=.29,wspace=.30)
        p=panel[identity]
        fig.text(.075,.11,
            'Markers are audited checkpoints; dashed lines only guide the eye. Missing U leaves U/gap blank; L is recorded.\n'
            'Whole time includes startup, every native call and exit. An outlined square marks a valid hard-stop endpoint if present.\n'
            f'{identity}: V{p["V"]}/M{p["M"]}/Q{p["Q"]}, mathematical T{p["T_seconds"]}; exposed protection/repetition. U/L axes use their observed range.',
            fontsize=9,va='top',linespacing=1.5)
        for extension in ['svg','png']:
            path=destination/f'{identity.lower()}_bounds_and_gap.{extension}'
            if extension=='svg':fig.savefig(path,metadata={'Date':None})
            else:fig.savefig(path,dpi=180)
            outputs.append(path)
        plt.close(fig)
    data=destination/'plotted_checkpoints.json'
    data.write_text(json.dumps(points,indent=2)+'\n',encoding='utf-8');outputs.append(data)
    receipt=dict(layout_revision=1,roles=['D3','C2','C6','C8','D6'],data_source='completed_audited_original_campaign',
        optimizer_calls=0,wall_seconds=time.perf_counter()-started,matplotlib_version=matplotlib.__version__,
        script_sha256=sha(Path(__file__)),checkpoint_sha256=sha(campaign/'checkpoints.json'),
        endpoint_sha256=sha(campaign/'endpoint_checks.json'),output_sha256={p.name:sha(p) for p in outputs},
        scope='Current audited observations only. Axis ranges are presentation choices, not altered endpoints or extra time samples.')
    (destination/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
