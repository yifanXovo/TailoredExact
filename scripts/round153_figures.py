"""Format already audited value ranges as publication figures; no solver."""
from round153_common import *
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING


def label(value,upper=False):
    return str(Decimal.from_float(value).quantize(Decimal('.00000001'),
        rounding=ROUND_CEILING if upper else ROUND_FLOOR))


def run():
    configure();assert not budget()['unclosed']
    source=OUT/'reports/scientific_table.json';rows=read(source)['rows']
    assert len(rows)==3 and read(OUT/'candidate_decision.json')['study_complete']
    tick=time.perf_counter()
    temp=WORK/'temp/round153/figures';temp.mkdir(parents=True,exist_ok=True)
    os.environ['TEMP']=os.environ['TMP']=str(temp)
    os.environ['MPLCONFIGDIR']=str(WORK/'temp/round153/matplotlib')
    dependencies=WORK/'build-cache/round137/python-packages'
    assert dependencies.is_dir();sys.path.insert(0,str(dependencies))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    target=OUT/'figures';target.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#ccd1d8',
        'text.color':'#192c3c','axes.labelcolor':'#192c3c','xtick.color':'#516271','ytick.color':'#192c3c'})
    fig,ax=plt.subplots(figsize=(7.4,4.4));color='#087e8b'
    largest=max(r['coupled_U']-r['direct_U'] for r in rows)
    for j,r in enumerate(rows):
        y=len(rows)-1-j;lo=r['coupled_L']-r['direct_U'];hi=r['coupled_U']-r['direct_U']
        assert all(math.isfinite(v) for v in (lo,hi)) and lo<=hi
        ax.plot([lo,hi],[y,y],color=color,linewidth=3,solid_capstyle='round')
        ax.scatter([lo],[y],s=52,color=color,zorder=3)
        ax.scatter([hi],[y],s=52,facecolor='white',edgecolor=color,linewidth=1.5,zorder=4)
        ax.annotate(f"[{label(r['coupled_L'])}, {label(r['coupled_U'],True)}]  |  width ≈ {r['interval_width']:.3g}",
            (0,y),xytext=(0,-21),textcoords='offset points',fontsize=9,color='#516271')
    ax.set_yticks(list(range(len(rows)-1,-1,-1)),[r['role'] for r in rows])
    ax.set_ylim(-.55,len(rows)-.45);ax.set_xlim(0,largest*1.1)
    ax.set_xlabel("LP value minus the domain's numerical reference upper",labelpad=10)
    ax.xaxis.grid(True,color='#e5e9ed',linewidth=.7);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0,pad=12)
    ax.scatter([],[],s=45,color=color,label='Qualified lower')
    ax.scatter([],[],s=45,facecolor='white',edgecolor=color,label='Numerical primal upper')
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.22),frameon=False,ncols=2,fontsize=9)
    fig.suptitle('Value of the complete inventory objective hull',x=.16,y=.96,ha='left',fontsize=14,fontweight='bold')
    fig.text(.08,.025,'Bounds on the strengthened LP value; upper endpoints are numerical LP uppers, not routing incumbents.',
        fontsize=8,color='#516271')
    fig.subplots_adjust(left=.16,right=.97,top=.77,bottom=.19)
    products=[]
    for extension in ('svg','png'):
        path=target/('coupled_value_intervals.'+extension)
        fig.savefig(path,dpi=260,facecolor='white')
        products.append(dict(path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),bytes=path.stat().st_size))
    plt.close(fig)
    write(OUT/'figure_creation.json',dict(UTC=utc(),kind='documentation_formatting',
        source=source.relative_to(ROOT).as_posix(),source_SHA=sha(source),products=products,
        separately_reported_seconds=time.perf_counter()-tick,Native_Optimize=0,
        Python=sys.executable,matplotlib_version=matplotlib.__version__,existing_plot_dependencies=str(dependencies),
        decimal_endpoint_labels_rounded_outward=True,
        horizontal_offsets_use_fixed_numerical_reference_uppers=True,
        horizontal_offsets_are_not_complete_gain_intervals=True,
        reference_offsets=[dict(role=r['role'],direct_U=r['direct_U']) for r in rows],
        no_producer_or_numerical_claim_recalculation=True,visual_inspection_separate=True))
    print(json.dumps(read(OUT/'figure_creation.json')),flush=True)


if __name__=='__main__':run()
