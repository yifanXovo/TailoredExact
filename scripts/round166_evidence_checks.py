"""Current-artifact consistency checks, distinct from independent final reviews."""
from round166_common import *
from fractions import Fraction
import csv,re

def checks():
    tick=time.perf_counter();s=read(OUT/'reports/summary.json');assert s['complete']
    arms=read(OUT/'reports/complete_arms.json');pairs=read(OUT/'reports/pairs.json')
    matrix=read(OUT/'matrix_frozen.json');candidate=read(OUT/'candidate_manifest.json');qualification=read(OUT/'qualification.json')
    assert len(arms)==12 and len(pairs)==6 and [a['position'] for a in arms]==list(range(1,13))
    assert {a['method'] for a in arms}=={'B','C166'} and all(a['seed']==0 for a in arms)
    assert all(a['numbers_qualified'] and a['implementation_qualified'] and a['performance_eligible'] and a['H_complete'] for a in arms)
    assert sum(g['launch']['cap_seconds'] for g in matrix['groups'])==21600
    assert qualification['PASS'] and qualification['actual_Optimize']==96<=120 and qualification['diagnostic_window_seconds']<=3600
    assert read(OUT/'preformal_admission.json')['remaining_science_seconds']>=32400
    source_hashes=0
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name;source_hashes+=1
    for name,digest in matrix['helper_hashes'].items():assert sha(ROOT/name)==digest,name
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA']==matrix['PE_SHA']
    assert sha(candidate['DLL'])==candidate['DLL_SHA']==matrix['DLL_SHA']
    assert all(a['source_commit']==candidate['source_commit'] and a['PE_SHA']==matrix['PE_SHA'] and a['DLL_SHA']==matrix['DLL_SHA'] for a in arms)
    assert all((a['T_cert'] is not None)==a['certificate'] for a in arms)
    for g,a in zip(matrix['groups'],arms):
        assert a['id']==g['input_id'] and a['method']==g['method'] and a['input_SHA']==g['launch']['panel']['input_sha256']
        argv=g['launch']['command'];assert argv[argv.index('--gurobi-seed')+1]=='0'
        assert argv[argv.index('--round166-breakpoint')+1]==('on' if a['method']=='C166' else 'off')
        assert not any('data_physical_archive' in token or 'qualification/parents' in token.replace('\\','/') for token in argv)
        assert a['T_produce']<=g['launch']['cap_seconds'] and a['not_holdout']
        assert sha(ROOT/a['endpoint']['path'])==a['endpoint']['SHA256']
    for name in ['config/gi_tbc_round137.json','scripts/paper_s2.py','config/paper_s2.json']:
        original=__import__('subprocess').check_output(['git','show',BASE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==original,name
    lp=read(OUT/'qualification/LP_pairs.json');assert len(lp)==8
    max_delta=max(abs(q['signed_LP_delta']) for q in lp);assert max_delta<=1e-12
    archive=read(OUT/'review/data_physical_archive.json');assert len(archive['records'])==50
    param=[r for r in archive['records'] if r['parameter_analysis']];assert len(param)==32 and all(r['lower_qualified'] for r in param)
    for family in {r['family'] for r in param}:
        assert len({r['physical_SHA'] for r in param if r['family']==family})==1
    analysis=read(OUT/'analysis/analysis_receipt.json');assert analysis['Optimize']==0 and sha(OUT/'review/data_physical_archive.json')==analysis['archive']['SHA256']
    envelope=read(OUT/'analysis/parameter_envelopes.json');assert len(envelope['families'])==4
    for family in envelope['families']:
        assert family['records']==sum(r['family']==family['family'] for r in param)
        assert all(Fraction(p['gap']['exact'])>=0 for p in family['critical_points'])
        assert Fraction(family['worst_gap']['gap']['exact'])==max(Fraction(p['gap']['exact']) for p in family['critical_points'])
    resources=read(OUT/'analysis/resource_intervals.json');assert len(resources)==4
    assert all(r['safe_lower']>0 and r['safe_upper']>=r['safe_lower'] for r in resources)
    csv_state=read(OUT/'CSV_reconciliation.json');assert csv_state['independent_increment']['rows']==6
    assert not csv_state['requested_master']['found'] and csv_state['independent_increment']['new_B_P_pairs']==0
    csv_qa=read(OUT/'CSV_QA.json');assert csv_qa['PASS'] and csv_qa['read_only']
    assert csv_qa['source_CSV_SHA256']==csv_state['independent_increment']['SHA256']
    figure=read(OUT/'analysis/figure_manifest.json')
    for binding in figure['outputs']+[figure['data'],figure['archive']]:assert sha(ROOT/binding['path'])==binding['SHA256']
    for family in envelope['families']:
        assert Fraction(figure['displayed_regret_upper_bounds'][family['family']])>=Fraction(family['worst_gap']['gap']['exact'])
    body=(ROOT/'results/unified_exact_round137/paper_body.md').read_text(encoding='utf-8-sig')
    assert re.findall(r'^\*\*Table (\d+)\.',body,re.M)==[str(i) for i in range(1,17)]
    from round166_documents import typeset
    expected=['0.2822618761','0.2822620892','0.2105292995','0.2105295021','0.1112611656','0.3725317852','0.0600858983','0.3813035291']
    for name,supp in [('paper_body.md',False),('supplement.md',True)]:
        raw=(ROOT/'results/unified_exact_round137'/name).read_text(encoding='utf-8-sig');_,text=typeset(raw,supp)
        assert all(number in text for number in expected),name
    value=dict(UTC=utc(),PASS=True,operation='current scientific-artifact consistency; document QA and independent reviews recorded separately',Optimize=0,
        complete_positions=12,paired_inputs=6,source_hashes_verified=source_hashes,helper_hashes_verified=len(matrix['helper_hashes']),
        actual_same_PE_and_DLL=True,actual_mode_and_Seed_flags=True,all_own_H_complete=True,no_offline_start_information=True,
        B_configs_and_existing_entry_byte_unchanged=True,integer_and_LP_scope='mathematical proofs plus independent preformal admission; this data check does not substitute for the final mathematical review',
        qualification_Optimize=96,LP_pairs=8,max_absolute_LP_delta=max_delta,physical_archive_records=50,parameter_records=32,
        continuous_intersections_nonnegative=True,resource_pairs=4,resource_improvement_lowers_positive=True,
        CSV_master_not_overwritten=True,separate_B_controls=6,C166_variant_records=6,new_strict_B_P_pairs=0,
        new_independent_benchmark_inputs=0,new_Seed_values=0,outward_decimals_preserved_in_PDF_input=True,
        summary=bind(OUT/'reports/summary.json'),matrix=bind(OUT/'matrix_frozen.json'),analysis=bind(OUT/'analysis/analysis_receipt.json'),
        generator=bind(Path(__file__)),seconds=time.perf_counter()-tick)
    write(OUT/'evidence_checks.json',value);print('Current scientific artifacts PASS; independent final reviews remain separate.')

if __name__=='__main__':checks()
