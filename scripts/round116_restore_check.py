"""Actual restored-root reconstruction; original root is comparison reference only.

The input/model/own fleets, all admitted identities and native audit evidence
are read solely from the restored root. Output-only routing prevents overwriting
the saved engineering/arithmetic receipts. No native or forward PROJ rerun.
"""
import argparse, json, time
from pathlib import Path
import round108_reader as core
import read_round116_reporting as reader
import round116_report as organizer
import round116_analysis as arithmetic
import round116_source_check as lineage
import round116_evidence_organize as evidence_organizer
from round116_final_review import patch_check

def compare_organized(expected,actual):
    names=[];timings=['load_own_evidence_seconds','reconciliation_and_reverse_order_check_seconds',
        'group_outer_engineering_seconds','actual_recheck_unix']
    for p in sorted(expected.iterdir()):
        if p.suffix not in ['.json','.csv']:continue
        q=actual/p.name;assert q.is_file(),('missing organized reconstruction',p.name)
        if p.name=='group_reconciliation_costs.csv':
            a=core.rows(p);b=core.rows(q)
            for rows in [a,b]:
                for row in rows:
                    for name in timings:row.pop(name)
            assert a==b
        elif p.name=='cohort_reconciliation.json':
            a=core.read(p);b=core.read(q)
            for rows in [a,b]:
                for row in rows:row.pop('actual_reconciliation_unix',None)
            assert a==b
        else:assert p.read_bytes()==q.read_bytes(),('organized core mismatch',p.name)
        names.append(p.name)
    return dict(all_current_core_equal=True,files=names,
        newly_measured_engineering_fields_excluded_only=dict(group_reconciliation_costs=timings,cohort_reconciliation=['actual_reconciliation_unix']))

def run(original,restored):
    tick=time.perf_counter();original=Path(original).resolve();root=Path(restored).resolve()
    assert original!=root
    out=root/reader.ROUND;prior=original/reader.ROUND
    receipt=core.read(prior/'public_restore_receipt.json')
    assert Path(receipt['root']).resolve()==root and receipt['fresh_empty_directory']
    work=out/'restore_validation01';work.mkdir(exist_ok=False)
    patch_check(root)
    rebuilt=reader.rebuild(root,work/'reconstructed')
    raw_comparison=reader.compare(prior/'reconstruction02',work/'reconstructed')
    old_write,old_table=core.write,core.table
    redirected=[]
    destinations={out/'engineering/report_organization_receipt.json':work/'report_organization_receipt.json',
        out/'objective_structure_analysis.json':work/'objective_structure_analysis.json',
        out/'objective_structure.csv':work/'objective_structure.csv',
        out/'own_objective_components.csv':work/'own_objective_components.csv'}
    destinations.update({out/n:work/n for n in ['physical_completion.json','formal_compact_Start.json',
        'current_source_qualification.json','severe_loss_summary.json']})
    destinations.update({out/'reports_final'/n:work/'organized'/n for n in ['group_reconciliation_costs.csv','native_coefficient_ranges.csv']})
    destinations[out/'engineering/evidence_organization_receipt.json']=work/'evidence_organization_receipt.json'
    def output(function,path,*args,**kwargs):
        path=Path(path)
        if path in destinations:
            redirected.append(dict(requested=str(path),actual=str(destinations[path])))
            path=destinations[path]
        return function(path,*args,**kwargs)
    try:
        core.write=lambda path,*args,**kwargs:output(old_write,path,*args,**kwargs)
        core.table=lambda path,*args,**kwargs:output(old_table,path,*args,**kwargs)
        organized=organizer.organize(root,work/'reconstructed',work/'organized')
        math_result=arithmetic.run(root)
        evidence_result=evidence_organizer.run(root)
    finally:core.write,core.table=old_write,old_table
    formal_comparison=compare_organized(prior/'reports_final',work/'organized')
    for n in ['physical_completion.json','formal_compact_Start.json','current_source_qualification.json','severe_loss_summary.json']:
        assert core.read(out/n)==core.read(work/n),('organized evidence summary mismatch',n)
    for n in ['objective_structure.csv','own_objective_components.csv']:
        assert (out/n).read_bytes()==(work/n).read_bytes(),('arithmetic mismatch',n)
    expected=core.read(out/'objective_structure_analysis.json');actual=core.read(work/'objective_structure_analysis.json')
    for value in [expected,actual]:value.pop('seconds')
    assert expected==actual
    source=lineage.check(root)
    old_write(work/'source_lineage_check.json',source)
    value=dict(all_current_core_equal=True,organized_current_core_equal=True,
        arithmetic_core_equal=True,source_lineage_generation_equal=True,
        actual_restored_reconstruction=True,original_root_fallback=False,
        original_root_used_only_as_equality_reference=True,restored_root=str(root),
        export_commit=receipt['commit'],raw_comparison=raw_comparison,formal_comparison=formal_comparison,
        reader_summary=rebuilt,organized_summary=organized,math_result=math_result,evidence_result=evidence_result,
        output_only_receipt_routing=redirected,forward_PROJ_rerun=False,
        reader_SHA=core.sha(root/'scripts/read_round116_reporting.py'),validator_SHA=core.sha(__file__),
        Optimize=0,native_starts=0,checked_unix=time.time(),engineering_seconds=time.perf_counter()-tick,
        scope='24 fixed positions,36 fixed pairs, qualification, clocks, current native/source reconciliation, same-H, exact inventory components and source-input lineage; blocked positions preserved')
    old_write(prior/'public_reconstruction_comparison.json',value)
    print(json.dumps({k:value[k] for k in ['all_current_core_equal','organized_current_core_equal','arithmetic_core_equal','source_lineage_generation_equal','restored_root','engineering_seconds']}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--original',required=True);parser.add_argument('--restored',required=True)
    a=parser.parse_args();run(a.original,a.restored)
