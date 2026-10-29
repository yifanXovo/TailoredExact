"""Finite guarded controller U/L traces, preserving their native process clock."""
from round138_common import *
import csv,io,zipfile
from round138_analyze import csv_write

def main():
    assert not budget()['unclosed'] and read(OUT/'reports/full.json')['complete']
    selection=read(OUT/'seed1_selection.json');roles=selection['roles'];rows=[];dependencies=[]
    reuse={r['role']:r for r in read(OUT/'baseline_reuse.json')['baselines']}
    matrix=read(OUT/'matrix_frozen.json')
    def collect(role,method,text,audit,endpoint,origin):
        assert not audit['source_rejections'] and endpoint['native_proof_qualified'] and endpoint['performance_eligible']
        values=list(csv.DictReader(io.StringIO(text)));assert values
        for r in values:
            t=float(r['process_elapsed_seconds']);U=float(r['verified_global_upper_bound']);L=float(r['valid_global_lower_bound'])
            assert math.isfinite(t) and math.isfinite(U) and math.isfinite(L)
            rows.append(dict(role=role,method=method,seed=0,process_elapsed_seconds=t,U=U,L=L,
                event=r['event_type'],source=r['event_source'],origin=origin,
                clock='Recorded native process elapsed; not the complete certificate clock'))
        last=values[-1]
        assert abs(float(last['valid_global_lower_bound'])-endpoint['L'])<1e-7
        assert abs(float(last['verified_global_upper_bound'])-endpoint['U'])<1e-7
    for role in roles:
        old=reuse[role];position=old['position'];archive=ROOT/'results/unified_exact_round137/artifacts'/f'campaign_{position:03}.zip'
        members=[]
        with zipfile.ZipFile(archive) as z:
            def get(suffix):
                name=next(n for n in z.namelist() if n.endswith('/'+suffix));raw=z.read(name)
                members.append(dict(member=name,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
                return raw
            text=get('external/global_bound_trace.csv').decode('utf-8')
            audit=json.loads(get('audit.json'));endpoint=json.loads(get('round135_endpoint.json'))
            collect(role,'BASE',text,audit,endpoint,'R137 fixed accepted baseline')
        dependencies.append(dict(role=role,commit='e735c3447eb1443713c700942d873de1783a4a26',
            archive=archive.relative_to(ROOT).as_posix(),SHA256=sha(archive),members=members))
        launch=next(g['launch'] for g in matrix['groups'] if g['launch']['id']==role and g['launch']['method']=='STOCK')
        d=Path(launch['destination'])
        collect(role,'STOCK',(d/'external/global_bound_trace.csv').read_text(),read(d/'audit.json'),read(d/'round135_endpoint.json'),'R138 independent complete run')
    csv_write(OUT/'reports/trajectories.csv',rows)
    write(OUT/'reports/trajectory_scope.json',dict(UTC=utc(),roles=roles,selection_rationale=selection['rationale'],
        dependencies=dependencies,rows=len(rows),Optimize=0,
        scope='Actual guarded controller valid_global_lower_bound and verified_global_upper_bound; each sealed run has no source revocation and its final trace agrees with the qualified endpoint',
        clock='Native process elapsed; formal T_produce/T_cert remain their independently complete clocks',
        no_raw_node_bound_substitution=True))
    os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib')
    sys.path.insert(0,str(WORK/'build-cache/round137/python-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(len(roles),1,figsize=(6.8,3.8*len(roles)),squeeze=False,layout='constrained')
    for ax,role in zip(axes[:,0],roles):
        for method,color,label in [('BASE','#777d83','GI-TBC (R137 Seed0)'),('STOCK','#2675ad','Stock RLT (V1 Seed0)')]:
            rr=[r for r in rows if r['role']==role and r['method']==method]
            ax.step([r['process_elapsed_seconds'] for r in rr],[r['U'] for r in rr],where='post',color=color,label=label+' U')
            ax.step([r['process_elapsed_seconds'] for r in rr],[r['L'] for r in rr],where='post',color=color,linestyle='--',label=label+' L')
        ax.set_title(role);ax.set_xlabel('Native process elapsed (s)');ax.set_ylabel('Objective value');ax.grid(alpha=.18);ax.legend(frameon=False,fontsize=8)
    (OUT/'figures').mkdir(exist_ok=True);fig.savefig(OUT/'figures/bound_trajectories.png',dpi=180);plt.close(fig)
    print(f'{len(rows)} guarded diagnostic U/L trace rows, {len(roles)} explicitly selected known roles')

if __name__=='__main__':main()
