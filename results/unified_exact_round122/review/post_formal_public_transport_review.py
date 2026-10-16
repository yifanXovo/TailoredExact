"""Bounded independent source/manifest transport check; never exports/restores."""
from pathlib import Path
import ast,copy,datetime,hashlib,json,math,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt
from post_formal_independent import typed_equal as independent_equal

def dump(n):return ast.dump(n,include_attributes=False)
def functions(t):return {n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

def run():
    tick=time.perf_counter();current=ROOT/'scripts/round122_release.py';old=OUT/'engineering/release_before_manifest_newline_fix.py'
    revision_path=OUT/'engineering/read_only_delivery_revision07.json';revision=read(revision_path)
    diagnostic_path=OUT/'engineering/committed_manifest_newline_diagnostic.json';diagnostic=read(diagnostic_path)
    assert sha(current)==revision['after_SHA']=='451331633e340155a49149a0a218eb3cf421bb9974e91b54d122a6c3b6090d12'
    assert sha(old)==revision['before_SHA']=='8820e82b948fb321bfed45b7f6e9cdd883fb1b3f5016e5634b0599e07963552c'
    previous=ast.parse(old.read_text(encoding='utf-8-sig'));now=ast.parse(current.read_text(encoding='utf-8-sig'))
    before=functions(previous);after=functions(now)
    assert set(after)-set(before)=={'public_manifest_bytes'} and not set(before)-set(after)
    identical=[n for n in before if dump(before[n])==dump(after[n])]
    assert identical==revision['all_other_functions_AST_identical'] and set(before)-set(identical)=={'restore'}
    residual=lambda t:[dump(n) for n in t.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    assert residual(previous)==residual(now)
    modified=copy.deepcopy(after['restore']);original=before['restore']
    selected=[n for n in modified.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['local_manifest','expected_public_manifest'] for t in n.targets)]
    expected=ast.parse("local_manifest=(out/'compact_evidence/manifest.json').read_bytes()\nexpected_public_manifest=public_manifest_bytes(local_manifest)").body
    assert [dump(n) for n in selected]==[dump(n) for n in expected]
    modified.body=[n for n in modified.body if n not in selected]
    additions=[n for n in modified.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='public.update']
    assert len(additions)==1
    added=ast.parse("public.update(local_manifest_SHA=hashlib.sha256(local_manifest).hexdigest(),expected_public_manifest_SHA=hashlib.sha256(expected_public_manifest).hexdigest(),manifest_transport_normalization='Only CRLF formatting whitespace to Git LF; all typed fields/values retained')").body[0]
    assert dump(additions[0])==dump(added);modified.body.remove(additions[0])
    calls=[n for n in ast.walk(modified) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='public_carrier_export']
    originals=[n for n in ast.walk(original) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='public_carrier_export']
    assert len(calls)==len(originals)==1 and ast.unparse(calls[0].args[1])=='expected_public_manifest'
    calls[0].args[1]=copy.deepcopy(originals[0].args[1])
    assert dump(modified)==dump(original),'restore changed beyond manifest normalization/provenance'
    # Execute only the two pure actual functions, not release/module imports.
    predecessor=ast.parse((ROOT/'scripts/round121_release.py').read_text(encoding='utf-8-sig'))
    equal=next(n for n in predecessor.body if isinstance(n,ast.FunctionDef) and n.name=='typed_equal')
    ns=dict(json=json,math=math)
    for n in [equal,after['public_manifest_bytes']]:exec(compile(ast.Module(body=[copy.deepcopy(n)],type_ignores=[]),'independent bounded manifest transport fixture','exec'),ns)
    normalize=ns['public_manifest_bytes'];cases=[]
    fixtures=[('LF_identity',b'{\n"s":"a\\r\\nb", "float":-0.0, "int":0, "a":[1.0,true,null]}\n'),
        ('CRLF_exact_LF',b'{\r\n"s":"a\\r\\nb", "float":-0.0, "int":0, "a":[1.0,true,null]}\r\n')]
    for name,raw in fixtures:
        value=normalize(raw);assert value==raw.replace(b'\r\n',b'\n')
        independent_equal(json.loads(raw),json.loads(value));assert b'a\\r\\nb' in value
        cases.append(name)
    for name,raw in [('standalone_CR',b'{\r"x":1}'),('invalid_JSON',b'{"x":}'),('raw_string_CRLF',b'{"x":"a\r\nb"}'),('NaN',b'{"x":NaN}')]:
        try:normalize(raw)
        except (AssertionError,ValueError):cases.append(name+'_rejected')
        else:raise AssertionError('invalid invented transport accepted '+name)
    for a,b in [(0.,-0.),(1,1.),([1,2],[2,1]),({'x':1},{'x':1,'y':2})]:
        try:ns['typed_equal'](a,b)
        except AssertionError:cases.append('typed_meaning_change_rejected_'+str(len(cases)))
        else:raise AssertionError('meaningful typed normalization accepted')
    # Read the one actual local manifest; never rewrite it, export or rescan parts.
    manifest_path=OUT/'compact_evidence/manifest.json';manifest_bytes=manifest_path.read_bytes();normalized=normalize(manifest_bytes)
    assert hashlib.sha256(manifest_bytes).hexdigest()==diagnostic['original_manifest_SHA']==revision['original_local_manifest_SHA']
    assert hashlib.sha256(normalized).hexdigest()==diagnostic['public_Git_blob_SHA256']==revision['expected_public_manifest_SHA']
    assert len(manifest_bytes)==diagnostic['original_bytes'] and len(normalized)==diagnostic['public_Git_blob_bytes']
    independent_equal(json.loads(manifest_bytes),json.loads(normalized))
    manifest=json.loads(normalized);assert len(manifest['files'])==62310 and len(manifest['parts'])==6
    comparisons=diagnostic['all_six_committed_parts_byte_equal']
    assert manifest['parts']==[{k:q[k] for k in ['path','SHA','bytes']} for q in comparisons]
    assert all(q['committed_bytes_equal'] and (ROOT/q['path']).stat().st_size==q['bytes'] for q in comparisons)
    assert sum(p['bytes'] for p in manifest['parts'])==176750386
    assert diagnostic['scienceA']==revision['scienceA']=='9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'
    assert 'scripts/round122_release.py' not in read(OUT/'candidate_identity.json')['helpers']
    assert sha(manifest_path)==diagnostic['original_manifest_SHA']
    result=dict(decision='ACCEPT',scope='Actual bounded independent source/finite-fixture/local-manifest normalization review. Does not certify an unfinished public HTTPS export or empty-root replay.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        review_script_SHA=sha(__file__),release_helper_SHA=sha(current),previous_preserved_release_SHA=sha(old),
        revision07_SHA=sha(revision_path),committed_manifest_diagnostic_SHA=sha(diagnostic_path),scienceA=diagnostic['scienceA'],
        unchanged_function_AST=identical,strict_public_export_and_member_hash_checks_unchanged=True,
        strict_restored_check_32_48_stage_typed_boundary_AST_unchanged=True,
        restore_other_AST_reverse_identical=True,new_pure_function='Only raw CRLF bytes to LF, standalone CR rejected, typed JSON equality retained; no value serialization.',
        actual_local_manifest_SHA=sha(manifest_path),normalized_manifest_SHA=hashlib.sha256(normalized).hexdigest(),
        normalized_manifest_matches_diagnostic_committed_SHA=True,all_actual_manifest_types_fields_values_arrays_signed_zero_preserved=True,
        canonical_carrier_members=62310,canonical_carrier_parts=6,compressed_part_bytes=176750386,
        part_metadata_and_local_sizes_match_committed_diagnostic=True,parts_rehashed_or_decompressed_by_this_review=False,
        finite_cases=cases,actual_public_export='NOT_EXECUTED_BY_REVIEWER; parent actual strict HTTPS export and later replay require their own completed receipts',
        limits=['Committed-blob SHA provenance is read from the bounded parent diagnostic; this review independently reproduced its normalized SHA from the actual local manifest, without another Git/network export.',
            'The canonical carrier is unchanged; its embedded original replay checker is AST-identical to the current checker. Host transport helper is separately identified.'],
        network_requests=0,Git_commands=0,scientific_carrier_exports=0,scientific_restores=0,native_starts=0,Optimize=0,
        existing_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_public_transport_review.json',result)

if __name__=='__main__':run()
