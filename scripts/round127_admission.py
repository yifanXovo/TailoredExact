"""Read-only concentrated final qualification and explicit mode disposition."""
from round127_common import *
import collections,copy,math
import round108_reader as core
from round127_qualify import compare
from compare_round112_startup import reconstruct as H

def root_model(d):
    calls=[r['payload'] for r in read(d/'observations.json') if r['payload']['kind']=='call' and r['payload']['leaf']=='L0']
    assert calls
    c=calls[0];p=core.portable(ROOT,c['model_path']);assert sha(p)==c['model_sha256']
    return p,c
def run():
    q=OUT/'qualification';e0=read(q/'smoke_E0/identity.json');e1=read(q/'smoke_E1/identity.json')
    pt=read(q/'smoke_PT/reconstructed.json')['arms'][0]
    assert pt['formal_protocol_qualified'] and pt['numbers_qualified'] and pt['certificate_qualified']
    a0=read(q/'smoke_E0/reconstructed.json')['arms'];a1=read(q/'smoke_E1/reconstructed.json')['arms']
    assert all(a['formal_protocol_qualified'] and a['numbers_qualified'] and a['certificate_qualified'] for a in a0+a1)
    launches={l['method']:l for l in e1['launches']};p=launches['MB']['panel']
    control=H(ROOT,p,Path(launches['MB']['destination']));hchecks=[]
    for label,l in [('E0_MB',next(l for l in e0['launches'] if l['method']=='MB'))]+[(m,launches[m]) for m in ['MD','MR','MG','MS2']]:
        value=H(ROOT,p,Path(l['destination']))
        fields=dict(full_H_complete=value['complete'] and control['complete'],fleet_equal=value['fleet']==control['fleet'],
            actions_equal=value['semantic_traces']==control['semantic_traces'],final_inventory_equal=value['physical']['Y']==control['physical']['Y'])
        assert all(fields.values()),(label,fields)
        hchecks.append(dict(method=label,**fields))
    root,c=root_model(Path(launches['MB']['destination']));diffs=[]
    for mode in ['MR','MG','MS2']:
        path,call=root_model(Path(launches[mode]['destination']))
        assert (call['cutoff'],call['lower_g'],call['upper_g'])==(c['cutoff'],c['lower_g'],c['upper_g'])
        diffs.append(compare(root,path,mode.lower(),p['V'],p['M']))
    md=Path(launches['MD']['destination']);rows=core.rows(md/'external/paper_optimize_ledger.csv')
    assert [r['solve_kind'] for r in rows]==['LP','MIP'] and {r['leaf_id'] for r in rows}=={'L0'}
    assert rows[0]['model_sha256']==rows[1]['model_sha256'] and int(rows[0]['integer_domain_restored'])==1
    assert all(a['certificate'] for a in a1 if a['method']!='P')
    # Equal-capacity labels are physically interchangeable; heterogeneous
    # labels require the same permutation of Q and complete assigned routes.
    pp=copy.deepcopy(p);pp['Q_vector']=list(reversed(p['Q_vector']))
    lines=(ROOT/p['input_path']).read_text().splitlines();lines[0]=f'{p["V"]} {p["M"]} {json.dumps(pp["Q_vector"])}'
    path=TEMP/'vehicle_permutation.txt';path.write_text('\n'.join(lines)+'\n');pp['input_path']=str(path)
    w=read(Path(launches['MB']['destination'])/'hga.csv.exchange/final.json');w=copy.deepcopy(w)
    for r in w['routes']:r['vehicle']=p['M']-1-r['vehicle']
    permuted=core.full_fleet(ROOT,pp,w);assert permuted['F']==control['physical']['F'] and permuted['Y']==control['physical']['Y']
    boundary=read(q/'boundary_vectors.json');bad=[r for r in boundary['records'] if r['violations']]
    assert len(bad)==4 and {r['id'] for r in bad}=={'zero_S_duration60'}
    assert all(len(r['violations'])==1 and r['violations'][0]['terms']==[] and r['violations'][0]['rhs']==-1 for r in bad)
    summary=dict(UTC=utc(),zero_Optimize_SHA=sha(q/'zero_optimize.json'),actual_S12_root_differences=diffs,
        H_checks=hchecks,MD_S12_single_root_LP_MIP_functional=True,MD_general_mathematical_qualification=False,
        boundary_SHA=sha(q/'boundary_vectors.json'),vehicle_permutation_physical_equivalence=True,
        numerical_cutoff_closure_exception='R126 Appendix A.5.6/A.7 retained; not an inclusive-set infeasibility statement',
        qualified_methods=['P','PT','MB','MR','MG','MS2'],blocked_methods=['MD'],
        reviewer_source='review/preformal_source_review.md',reviewer_math='review/preformal_cutoff_boundary_review.md',
        scope='finite direct checks plus concentrated second-executor review; no third-party replication or full rational proof')
    write(q/'admission_summary.json',summary)
    frozen=read(OUT/'E1_build.json');assert sha(E1)==frozen['PE_SHA'] and source_bindings()==frozen['source_bindings']
    frozen.update(UTC_frozen=utc(),qualification_summary_SHA=sha(q/'admission_summary.json'),
        qualified_methods=summary['qualified_methods'],blocked_methods=['MD'],source_review_SHA=sha(OUT/summary['reviewer_source']),
        math_review_SHA=sha(OUT/summary['reviewer_math']),E0_unchanged_SHA=sha(E0))
    write(OUT/'E1_frozen.json',frozen)
    write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',qualified_methods=summary['qualified_methods'],blocked_methods=['MD'],
        E1_SHA=sha(E1),DLL_SHA=sha(DLL),E1_frozen_SHA=sha(OUT/'E1_frozen.json'),qualification_SHA=sha(q/'admission_summary.json'),
        MD_scope='blocked before any formal performance; numerical equality closure incompatible with required inclusive Start',
        no_evaluation_or_training_results_used=True))
    print(json.dumps(summary))
if __name__=='__main__':run()
