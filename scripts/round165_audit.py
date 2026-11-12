"""Bounded read-only context and offline paper data; never imports a solver."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, io, json, os, subprocess, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round165'
PAPER = ROOT / 'results/unified_exact_round137'
TEMP = Path('E:/codes/ExactEBRP-work/temp/round165')
BASE = 'de01e8fb27a954d031abac5fe99442d6c8d29d44'
PYTHON = sys.executable

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p, v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd).decode('utf-8', errors='replace').strip()
def binding(p):
    p=Path(p)
    return dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, SHA256=sha(p))

def context():
    if (OUT/'entry_state.json').exists():
        print('Existing entry audit retained; not rediscovered.'); return
    protected=[]
    for root in ['E:/codes/ExactEBRP','E:/codes/ExactEBRP-work/worktrees/paper-current','E:/codes/ExactEBRP-work/worktrees/round164']:
        status=git('status','--porcelain=v1','-uno',cwd=root)
        files=[]
        for line in status.splitlines():
            rel=line[3:]; p=Path(root)/rel
            if p.is_file(): files.append(dict(path=rel,SHA256=sha(p)))
        protected.append(dict(root=root,HEAD=git('rev-parse','HEAD',cwd=root),status=status,dirty_tracked=files))
    write(OUT/'entry_state.json',dict(UTC=utc(),work_start_UTC='2026-11-12T20:05:40+00:00',
        initial_task_read_precedes_measured_goal_window=True,
        policy='WORKSPACE_POLICY.md; all new assets inside ExactEBRP-work; no old deletion',
        selected_base=BASE,remote_main='b2b940c1e517a72e226ec60fc49ff19651737632',
        predecessor_PR=dict(number=226,state='open',draft=True,merged=False,head=BASE),
        prior_R165_PR_search='none',
        workspace_decision='paper-current is dirty at R155; retain it and use isolated round165 from verified R164; same R137 component paths',
        protected=protected))
    originals=[binding(PAPER/n) for n in ['paper_body.md','model_and_algorithm_appendices.md','mathematical_analysis.md','supplement.md','references.bib','method_and_model_source.md','manuscript.md','manuscript.pdf','document_assembly.json','document_lineage.json','pdf_export.json']]
    write(OUT/'inherited_document_identity.json',dict(commit=BASE,files=originals))
    candidates=[]
    for folder in [Path('C:/Users/Administrator/Downloads'),Path('C:/Users/Administrator/Desktop')]:
        candidates += sorted(folder.rglob('*GI_TBC*.csv'))
    candidates += [ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv']
    tables=[]
    for p in dict.fromkeys(candidates):
        data=p.read_bytes()
        for enc in ['utf-8-sig','gb18030']:
            try: rows=list(csv.reader(io.StringIO(data.decode(enc))));break
            except UnicodeDecodeError: continue
        tables.append(dict(path=str(p),bytes=len(data),SHA256=sha(p),encoding=enc,
            UTF8_BOM=data.startswith(b'\xef\xbb\xbf'),rows=len(rows)-1,columns=len(rows[0]),header=rows[0],
            result_keys=[dict(zip(['input','T','lambda','seed','repeat','round','cap'],[r[i] for i in [0,7,8,10,11,12,13]])) for r in rows[1:]]))
    master=next(t for t in tables if t['path'].replace('\\','/').endswith('unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'))
    incr=ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_Round164_Increment.csv'
    inc=list(csv.reader(io.StringIO(incr.read_text(encoding='utf-8-sig'))))
    allrows=list(csv.reader(io.StringIO(Path(master['path']).read_bytes().decode(master['encoding']))))
    assert len(inc)-1==12 and all(r in allrows for r in inc[1:])
    full=[t for t in tables if t['rows']==106 and t['SHA256']=='8f39e3a23b3b6df621139cb39b4db813ca3e992da091e97251ab8337fd2b0022']
    write(OUT/'main_table_reconciliation.json',dict(UTC=utc(),tables=tables,
        full_106_exact_found=bool(full),R164_increment=binding(incr),R164_increment_pairs=12,
        all_12_already_present=True,missing_historical_rows=[] if full else [
            dict(round=138,input='R-B35-S-T2',seed=1,cap=2400),
            dict(round=155,input='N-B35-S',seed=0,cap=7200),
            dict(round=156,input='R-X35-S-T2',seed=0,cap=7200)],
        new_performance_rows=0,external_files_modified=False,
        reconstruction='No original 94-row/106-row source found; absent original descriptive/source fields are not fabricated. Keep existing 103-row working copy explicitly incomplete.'))
    p=Path('C:/Users/Administrator/Desktop/Research/docs/Paper Draft 2.docx')
    if p.exists():
        with zipfile.ZipFile(p) as z:
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs=[''.join(t.itertext()) for t in ET.fromstring(z.read('word/document.xml')).findall('.//w:t',ns)]
            core=ET.fromstring(z.read('docProps/core.xml'))
        # Identity and observed concepts only; no private source text is published.
        text=' '.join(paragraphs)
        write(OUT/'antecedent_check.json',dict(UTC=utc(),local_basename=p.name,bytes=p.stat().st_size,SHA256=sha(p),
            same_as_R135_checked_version=sha(p)=='aabf6fc3377dcca25e36409bcbfb3a371091fafee93e93ce769d1778cc81d870',
            visible_title='Equity-aware Bike Repositioning in Station-based Bike-sharing Systems',
            title_observed='Equity-aware Bike Repositioning' in text,
            HGA_TGBC_observed='HGA' in text and 'TGBC' in text,
            modified_metadata=next((e.text for e in core if e.tag.endswith('modified')),None),
            latest_version_claim=False,authors_or_publication_not_inferred=True,private_text_redistributed=False))
    # Exactly one normal direct-download attempt after web size-limit failure.
    url='https://research.unipd.it/retrieve/1ca1c54a-9e2b-4b68-91b7-612ed0aa2942/1-s2.0-S0968090X26001798-main.pdf'
    dest=TEMP/'literature/caggiani2026.pdf'; dest.parent.mkdir(parents=True,exist_ok=True)
    access=dict(UTC=utc(),URL=url,web_result='Content length too large: 11802795',attempts=1,certificate_verification='normal',foreign_text_published=False)
    try:
        with urllib.request.urlopen(url,timeout=30) as response:
            data=response.read(); assert data.startswith(b'%PDF'); dest.write_bytes(data)
        access.update(local_download=True,bytes=len(data),SHA256=sha(dest),local_path=str(dest))
    except Exception as error:
        access.update(local_download=False,error=str(error),configuration_changes=False)
    write(OUT/'literature_access.json',access)
    print(json.dumps(dict(protected_trees=len(protected),CSV=[(t['rows'],t['bytes']) for t in tables],full106=bool(full),Caggiani=access),ensure_ascii=False))

def evidence():
    pairs=read(ROOT/'results/unified_exact_round164/reports/three_seed_comparisons.json')
    arrivals=read(ROOT/'results/unified_exact_round164/reports/primal_target_arrival.json')
    summary=read(PAPER/'reports/summary.json')
    assert len(pairs)==18 and len(arrivals)==36
    assert summary['stages']['B1']['certificates']=={'S2':9,'PS':7,'P':7}
    assert summary['stages']['B2']['certificates']=={'S2':4}
    keys={(r['id'],r['gurobi_seed']) for r in pairs}; assert len(keys)==18
    for s in range(3):
        group=[r for r in pairs if r['gurobi_seed']==s]
        assert len(group)==6
        assert sum(r['B_state']=='CERT' for r in group)==3
        assert sum(r['P_state']=='CERT' for r in group)==1
        assert sum(r['joint_CERT'] for r in group)==1
    for r in pairs:
        assert abs(r['B_U']-r['P_U']-r['delta_U'])<1e-14
        assert abs(r['B_L']-r['P_L']-r['delta_L'])<1e-14
        if '35' in r['id']: assert r['B_state']==r['P_state']=='OPEN'
        if r['B_state']=='OPEN': assert r['B_T_cert'] is None
        if r['P_state']=='OPEN': assert r['P_T_cert'] is None
    c35=sorted([r for r in pairs if r['id']=='R163-C35-U'],key=lambda r:r['gurobi_seed'])
    assert [r['delta_U_sign'] for r in c35]==[1,-1,-1]
    assert all(r['delta_L_sign']==1 for r in c35)
    assert c35[0]['P_U'] < min(r['B_U'] for r in c35)
    roles=['R163-C20-S','R163-B20-B','R163-X20-S','R163-C35-U','R163-B35-S','R163-X35-S']
    analysis=[]; arrival_rows=[]
    for role in roles:
        for r in sorted([r for r in pairs if r['id']==role],key=lambda r:r['gurobi_seed']):
            for m in ['B','P']:
                analysis.append(dict(configuration=role,Seed=r['gurobi_seed'],source='R163 historical' if r['historical'] else 'R164 added',method=m,state=r[m+'_state'],U=r[m+'_U'],L=r[m+'_L'],T_cert=r[m+'_T_cert']))
        for m in ['B','P']:
            rows=sorted([r for r in arrivals if r['id']==role and r['method']==m],key=lambda r:r['gurobi_seed'])
            assert len(rows)==3
            arrival_rows.append('| '+' | '.join([role,m,format(rows[0]['u_ref'],'.10g'),*[('['+format(r['paid_clock_lower_seconds'],'.6g')+', '+format(r['paid_clock_upper_seconds'],'.6g')+']') if r['reached_observed'] else 'censored at '+format(r['window_end_T_produce'],'.6g') for r in rows]])+' |')
    folder=OUT/'analysis'; folder.mkdir(exist_ok=True)
    with (folder/'three_seed_endpoints.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(analysis[0]));writer.writeheader();writer.writerows(analysis)
    target_table='\n'.join(['| Configuration | Method | Frozen u_ref | Seed 0 (s) | Seed 1 (s) | Seed 2 (s) |','|---|---|---|---|---|---|',*arrival_rows])+'\n'
    (folder/'target_availability.md').write_text(target_table,encoding='utf-8')
    # Scientific figure from fixed qualified endpoints, not new measurements.
    os.environ['MPLCONFIGDIR']=str(TEMP/'matplotlib')
    local_plot_dependencies=Path('E:/codes/ExactEBRP-work/build-cache/round137/python-packages')
    if local_plot_dependencies.is_dir(): sys.path.insert(0,str(local_plot_dependencies))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
    fig,axes=plt.subplots(2,3,figsize=(10.4,6.6))
    for ax,role in zip(axes.flat,roles):
        for m,color,offset in [('B','#195a91',-.08),('P','#c05b28',.08)]:
            rows=[r for r in analysis if r['configuration']==role and r['method']==m]
            xs=[r['Seed']+offset for r in rows]
            ax.plot(xs,[r['U'] for r in rows],color=color,linewidth=1,alpha=.6)
            ax.plot(xs,[r['L'] for r in rows],color=color,linestyle='--',linewidth=1,alpha=.7)
            for x,r in zip(xs,rows):
                ax.plot([x,x],[r['L'],r['U']],color=color,alpha=.3)
                ax.plot(x,r['U'],'o',color=color,markerfacecolor=color if r['state']=='CERT' else 'white',markersize=5)
                ax.plot(x,r['L'],'^',color=color,markersize=4)
        ref=next(r['u_ref'] for r in arrivals if r['id']==role)
        ax.axhline(ref,color='#666666',linestyle=':',linewidth=1)
        ax.set_title(role.replace('R163-','')+(' (all OPEN)' if '35' in role else ''))
        endpoints=[r[v] for r in analysis if r['configuration']==role for v in ['U','L']]
        if max(endpoints)-min(endpoints)<.02:
            centre=(max(endpoints)+min(endpoints))/2
            ax.set_ylim(max(0,centre-.02),centre+.02)
        ax.ticklabel_format(axis='y',style='plain',useOffset=False)
        ax.set_xticks([0,1,2],['0 historical','1 added','2 added'],fontsize=8)
        ax.grid(axis='y',alpha=.18); ax.set_ylabel('Original objective F')
        ax.spines[['top','right']].set_visible(False)
    handles=[Line2D([0],[0],color='#195a91',label='B'),Line2D([0],[0],color='#c05b28',label='P'),Line2D([0],[0],marker='o',mfc='white',color='black',linestyle='-',label='Feasible U (filled: CERT)'),Line2D([0],[0],marker='^',color='black',linestyle='--',label='Qualified L'),Line2D([0],[0],color='#666666',linestyle=':',label='Frozen offline u_ref')]
    fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.002))
    fig.tight_layout(rect=(0,.105,1,1),h_pad=2)
    figure=PAPER/'figures/three_seed_endpoints.png'; fig.savefig(figure,dpi=220);plt.close(fig)
    e=read(ROOT/'results/unified_exact_round163/reports/summary.json')
    assert e['pairs']['Eplus_vs_B']['higher_proof_L']==1
    write(OUT/'evidence_checks.json',dict(UTC=utc(),passed=True,new_Optimize=0,new_performance_arms=0,
        six_inputs=6,pairs=18,method_observations=36,new_in_R164=24,Eplus_Seed0_observations=6,
        R137_breadth=[9,7,7],R137_resource=[4,0,0],B_CERT_per_Seed=[3,3,3],P_CERT_per_Seed=[1,1,1],
        C35_absolute_P_Seed0_better_than_all_B=True,C35_relative_U_signs=[1,-1,-1],
        arrival_records=36,arrival_exact_first_find=False,Eplus_new_Seed_robustness=False,
        plotting=dict(matplotlib_version=matplotlib.__version__,Python=sys.version,minimum_B20_axis_span=.04,offset_axis_disabled=True,raw_endpoints_unchanged=True),
        inputs=[binding(ROOT/'results'/p) for p in ['unified_exact_round164/reports/three_seed_comparisons.json','unified_exact_round164/reports/primal_target_arrival.json','unified_exact_round137/reports/summary.json','unified_exact_round163/reports/summary.json']],
        outputs=[binding(folder/'three_seed_endpoints.csv'),binding(folder/'target_availability.md'),binding(figure)]))
    print('Offline checks PASS: 18 pairs / 36 observations; figure and all-target availability table generated.')

if __name__=='__main__': globals()[sys.argv[1]]()
