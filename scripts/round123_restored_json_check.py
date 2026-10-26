"""Delivery-only strict saved-JSON check of the already public A payload.

The A reader returns some internal tuples but writes JSON arrays. Compare the
actual saved JSON, never coerce comparison types or remove fields. This helper
is an explicit addition beside immutable A members, published with delivery B.
"""
from pathlib import Path
import argparse,csv,hashlib,json,os,sys,time

def run(root):
    tick=time.perf_counter();root=Path(root).resolve()
    assert root==Path(__file__).resolve().parents[1],'Execute the copy inside the recovered root'
    runtime=Path(sys.base_prefix).resolve();opened=set()
    def boundary(event,args):
        if event in ['subprocess.Popen','socket.connect','os.system','os.posix_spawn']:
            raise AssertionError(('No process/network in restored checker',event))
        if event=='ctypes.dlopen' and args and any(v in str(args[0]).lower() for v in ['gurobi','cplex']):
            raise AssertionError('No solver library in restored checker')
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve()
        assert p.is_relative_to(root) or p.is_relative_to(runtime),('External recovered-root read',str(p))
        if p.is_relative_to(root):opened.add(p.relative_to(root).as_posix())
    sys.addaudithook(boundary);csv.field_size_limit(64*1024*1024)
    import round123_common as c
    from round121_release import normalize,typed_equal
    import read_round123 as reader
    import round123_history_fixture as history
    assert c.ROOT==root
    out=root/'results/unified_exact_round123';origin=c.read(root/'public_restore_origin.json');manifest=origin['manifest']
    measured=c.read(out/'initialization_receipt.json')['workspace']['execution']
    def members():
        for name,e in manifest['files'].items():
            p=(root/name).resolve();assert p.is_relative_to(root) and p.is_file()
            assert p.stat().st_size==e['bytes'] and c.sha(p)==e['SHA'],('Modified public payload member',name)
    members()
    dest=out/'restored_reconstruction_json_checked';assert not dest.exists()
    reader.rebuild(root,dest)
    actual=c.read(dest/'current_core.json');expected=c.read(out/'reconstruction/final/current_core.json')
    typed_equal(normalize(actual,[root,measured]),normalize(expected,[root,measured]))
    first=out/'restored_reconstruction/current_core.json'
    assert first.exists();typed_equal(actual,c.read(first))
    regression=history.check(root,write_receipt=False);members()
    modules=[]
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        p=Path(filename).resolve()
        assert p.is_relative_to(root) or p.is_relative_to(runtime),('External imported helper',name,str(p))
        if p.is_relative_to(root):modules.append(dict(module=name,path=p.relative_to(root).as_posix()))
    added=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in manifest['files'])
    receipt=dict(passed=True,scientific_commit=origin['scientific_commit'],formal_arms=3,pairs=3,
        research_disposition=actual['decision']['research_disposition'],
        typed_JSON_all_fields_arrays_types_values_and_signed_zero_equal=True,
        comparison='Both operands read from actually saved JSON; internal Python tuples are not a JSON type',
        normalization='Only complete measured/restored root prefixes; no field dropped, rounded or type-coerced',
        first_public_reader_saved_core_identical=True,first_reader_failure='A post-check compared internal tuples with stored JSON lists; reconstruction itself had completed',
        original_public_export_count=1,original_fresh_empty_root_count=1,read_only_core_rebuilds=2,
        repaired_delivery_harness=str(Path(__file__).relative_to(root)),delivery_harness_SHA=c.sha(__file__),
        A_payload_reader_SHA=c.sha(root/'scripts/read_round123.py'),
        reconstructed_core_SHA=c.sha(dest/'current_core.json'),expected_A_core_SHA=c.sha(out/'reconstruction/final/current_core.json'),
        initial_unpack_hash_equality_distinct_from_reconstruction=True,compared_manifest_members_byte_unchanged=True,
        regenerated_derived_sidecars=[],additional_paths_excluding_this_receipt=added,
        no_claim_that_all_expanded_and_newly_generated_files_are_identical=True,
        portable_history_regression=regression,actual_local_modules=modules,opened_inside_root=sorted(opened),
        no_original_raw_helper_or_runtime_binary_fallback=True,no_solver_DLL_or_Optimize=True,Optimize=0,native_starts=0,
        boundary='Actual Python file/process/network/library and imported-module audit; standard runtime allowed, not an OS sandbox',
        seconds=time.perf_counter()-tick,UTC=c.utc())
    c.write(root/'restored_check_receipt.json',receipt)
    print(json.dumps(dict(passed=True,arms=3,pairs=3,stage=actual['decision']['research_disposition'],saved_JSON_types_strictly_compared=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));args=parser.parse_args();run(args.root)
