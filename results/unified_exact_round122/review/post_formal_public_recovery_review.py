"""Bounded actual public-root corroboration after completed replay.

Reads eight reconstructed/stored cores and six declared changed sidecars.
Does not rerun the reader, scan all members, export, network or optimize.
"""
from pathlib import Path,PurePosixPath,PureWindowsPath
import ast,copy,datetime,hashlib,json,math,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt
from post_formal_independent import normalize,typed_equal,independent_pair,independent_stage,editorial_arm,PAIRS

COMMIT='9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'
RECEIPT_SHA='d5374e3af5033318bd63d2e42bf7d31ae9bc518da436a1bd47062a9f1487586d'
USED={}
def rd(p):USED[str(p)]=sha(p);return read(p)
def node(p,name):return next(n for n in ast.parse(p.read_text(encoding='utf-8-sig')).body if isinstance(n,ast.FunctionDef) and n.name==name)
def exact(a,b,roots,path='',differences=None):
    """Typed comparison with path normalization on string leaves only.

    Avoids making two more copies of the largest 40MB core. Full dictionary
    keys, arrays/order, numeric values and float zero signs remain mandatory.
    """
    assert type(a) is type(b),('type changed',path)
    if isinstance(a,dict):
        assert a.keys()==b.keys(),('keys changed',path)
        for k in a:exact(a[k],b[k],roots,path+'/'+k,differences)
    elif isinstance(a,list):
        assert len(a)==len(b),('array length changed',path)
        for j,(x,y) in enumerate(zip(a,b)):exact(x,y,roots,path+'/'+str(j),differences)
    elif isinstance(a,str):
        typed_equal(normalize(a,roots),normalize(b,roots),path)
        if differences is not None and a!=b:differences.append(dict(field=path,restored=a,canonical=b))
    else:typed_equal(a,b,path)

def run():
    tick=time.perf_counter();receipt_path=OUT/'delivery/restored_check_receipt.json'
    receipt=rd(receipt_path);root=Path(receipt['fresh_empty_root']);restored_out=root/'results/unified_exact_round122'
    expected_root=Path('E:/codes/ExactEBRP-work/restore/round122-9ed88cf9da87')
    assert root==expected_root and receipt['scientific_commit']==COMMIT and receipt['passed']
    for p in [receipt_path,root/'restored_check_receipt.json',Path('E:/codes/ExactEBRP-work/evidence/round122/restored_check_receipt.json')]:assert sha(p)==RECEIPT_SHA
    summary=rd(OUT/'delivery/restored_check_summary.json')
    assert summary['full_receipt_SHA']==RECEIPT_SHA and summary['actual_checker_exit_code']==0 and summary['full_receipt_bytes']==receipt_path.stat().st_size==6566378
    assert receipt['formal_arms']==32 and receipt['pairs']==48 and receipt['stage']=='BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION'
    assert receipt['Optimize']==receipt['native_starts']==0 and receipt['typed_JSON_all_fields_values_arrays_and_signed_zero_equal']
    assert receipt['all_other_carrier_members_byte_unchanged'] and receipt['no_original_raw_helper_or_runtime_binary_fallback']
    assert receipt['normalization']=='only complete measured/restored root path component prefixes; no rounding/field removal'
    boundary='Python open/module/process/network audit; not an OS sandbox; standard runtime prefix allowed'
    assert receipt['boundary']==boundary and receipt['engineering_seconds']==782.8252536999935
    export=rd(OUT/'delivery/public_export_restore_receipt.json');assert export['scientific_commit']==COMMIT and Path(export['fresh_empty_root'])==root and export['members']==62310
    manifest=rd(OUT/'compact_evidence/manifest.json');assert len(manifest['files'])==62310
    origin=rd(root/'public_restore_origin.json')
    typed_equal(origin['manifest'],manifest)
    assert origin['scientific_commit']==COMMIT and Path(origin['fresh_empty_root'])==root and origin['all_member_hashes_equal'] and origin['no_original_raw_fallback']
    assert origin['published_manifest_SHA']==export['public_HTTP_export']['expected_public_manifest_SHA']=='0bc5561235ce9419452a647c7c8d1e50c735a59e956a41f344638438ea777746'
    checker=root/'scripts/round122_release.py';checker_SHA=sha(checker)
    assert checker_SHA==summary['checker_source_SHA']==manifest['files']['scripts/round122_release.py']['SHA']=='8820e82b948fb321bfed45b7f6e9cdd883fb1b3f5016e5634b0599e07963552c'
    actual_checker=node(checker,'restored_check');host_checker=node(ROOT/'scripts/round122_release.py','restored_check')
    assert ast.dump(actual_checker,include_attributes=False)==ast.dump(host_checker,include_attributes=False)
    checker_source=ast.unparse(actual_checker)
    for expected in ["['subprocess.Popen', 'socket.connect']",'path.is_relative_to(root) or path.is_relative_to(runtime)',
        'sys.addaudithook(boundary)','range(1, 9)','typed_equal(normalize(actual, [root, measured]), normalize(expected, [root, measured]))',
        "path.name == 'round120_event_contract.json'","all_other_carrier_members_byte_unchanged=True"]:assert expected in checker_source
    paths=receipt['opened_inside_root'];assert len(paths)==len(set(paths))==summary['opened_inside_root_count']==62550
    assert paths==sorted(paths)
    for path in paths:
        assert isinstance(path,str) and not PureWindowsPath(path).is_absolute() and not PurePosixPath(path).is_absolute()
        assert '..' not in PurePosixPath(path.replace('\\','/')).parts and ':' not in path and not path.startswith(('\\','/'))
    assert 'scripts/round122_release.py' in paths
    measured=Path(rd(restored_out/'initialization_receipt.json')['workspace']['execution']);assert measured==ROOT
    roots=[root,measured];groups=[];independent_pairs=[];annotated=[];core_facts=[];sidecar_facts=[];proof_risk=False
    ind=rd(REVIEW/'post_formal_independent.json');assert ind['decision']=='ACCEPT'
    canonical_pairs=rd(OUT/'all48_pairs.json');typed_equal(canonical_pairs,ind['independent_pairs'])
    canonical_arms=rd(OUT/'all32_arms.json')
    for n in range(1,9):
        relative=f'results/unified_exact_round122/reconstruction/group{n:02d}/current_core.json'
        stored_path=root/relative;original_path=ROOT/relative;actual_path=restored_out/f'restored_reconstruction/group{n:02d}/current_core.json'
        assert sha(stored_path)==sha(original_path)==manifest['files'][relative]['SHA']
        stored=rd(stored_path);actual=rd(actual_path)
        exact(actual,stored,roots)
        g=actual['group'];by={a['arm']:a for a in actual['arms']};recomputed=[]
        for c,p in PAIRS:
            a,b=by[c],by[p];p0=independent_pair(a,b)
            dU=a['U']-b['U'];dL=a['L']-b['L'];dgap=a['gap']-b['gap']
            assert abs(dgap-(dU-dL))<=1e-12
            recomputed.append(dict(id=g['id'],group_number=n,seed=g['seed'],**p0,dU=dU,dL=dL,dgap=dgap,identity_dgap_equals_dU_minus_dL=True,causal_shares=False))
        typed_equal(recomputed,actual['pairs']);independent_pairs.extend(recomputed)
        annotated.extend(editorial_arm(a,g) for a in actual['arms'])
        proof_risk=proof_risk or bool(actual['adjudication']['rejections'])
        groups.append(dict(group=g,arms=actual['arms'],pairs=recomputed,mechanism=actual['mechanism']))
        core_facts.append(dict(group=n,canonical_SHA=sha(stored_path),restored_reconstructed_SHA=sha(actual_path),all_fields_typed_root_only_equal=True))
        del stored,actual
    typed_equal(independent_pairs,ind['independent_pairs'])
    typed_equal(independent_pairs,rd(restored_out/'all48_pairs.json'))
    exact(annotated,canonical_arms,roots);exact(annotated,rd(restored_out/'all32_arms.json'),roots)
    blockers=[dict(group=g['group']['number'],arm=a['arm'],reason='unqualified necessary protocol/numbers') for g in groups for a in g['arms'] if not a['formal_protocol_qualified'] or not a['numbers_qualified']]
    decision=independent_stage(groups,True,proof_risk,blockers)
    typed_equal(decision,ind['independent_stage']);typed_equal(decision,rd(restored_out/'stage_decision.json'))
    sidecars=receipt['regenerated_derived_sidecars'];assert len(sidecars)==6
    assert {int(q['path'].split('/campaign/group')[1][:2]) for q in sidecars}=={1,2,3,4,6,7}
    for q in sidecars:
        rel=q['path'];n=int(rel.split('/campaign/group')[1][:2]);target=root/rel;original=ROOT/rel
        assert rel.endswith('_MB-D1/round120_event_contract.json') and q['only_normalized_root_paths_differ']
        assert q['unpacked_SHA']==manifest['files'][rel]['SHA']==sha(original)
        assert q['reconstructed_SHA']==sha(target) and q['reconstructed_SHA']!=q['unpacked_SHA']
        a,b=rd(target),rd(original);diff=[];exact(a,b,roots,differences=diff);assert diff
        saved=next(e for e in groups[n-1]['mechanism'] if e['arm']=='MB-D1')
        saved={k:v for k,v in saved.items() if k!='arm'};exact(a,saved,roots)
        sidecar_facts.append(dict(group=n,path=rel,unpacked_SHA=q['unpacked_SHA'],reconstructed_SHA=q['reconstructed_SHA'],only_root_string_differences=diff))
    for n in [5,8]:
        identity=rd(restored_out/f'campaign/group{n:02d}/identity.json');l=next(l for l in identity['launches'] if l['arm']=='MB-D1')
        rel=Path(l['destination']).relative_to(ROOT).as_posix()+'/round120_event_contract.json'
        assert sha(root/rel)==manifest['files'][rel]['SHA']
    assert all(sha(path)==digest for path,digest in USED.items())
    result=dict(decision='ACCEPT',scope='Actual bounded independent completed public-root receipt/source/boundary, eight reconstructed cores,48 pairs/stage and six root-only sidecar corroboration. Separate prior full scientific review remains its own authority.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_script_SHA=sha(__file__),scienceA=COMMIT,
        actual_replay_receipt_SHA=RECEIPT_SHA,all_three_receipt_copies_byte_identical=True,actual_replay_exit_code=0,
        actual_replay_seconds=receipt['engineering_seconds'],actual_checker_source_SHA=checker_SHA,checker_source_matches_actual_carrier_member=True,
        boundary=boundary,opened_inside_root_relative_paths_checked=62550,no_absolute_or_parent_traversal_paths_in_record=True,
        no_original_measured_root_access_corroborated_by_original_boundary_and_success=True,
        actual8_reconstructed_cores_vs_stored_canonical=core_facts,exact_typed_normalization='Only complete measured/restored root component prefixes in string leaves; no rounding, removed fields, array reorder, numeric/type/signed-zero change.',
        independent_48_recomputed_from_restored_endpoints_equal_to_prior_review=True,independent_stage=decision,
        complete32_editorial_arms_typed_equal=True,six_allowed_sidecars_checked=sidecar_facts,both_unexposed_sidecars_byte_unchanged=True,
        earlier_full_mathematical_review_SHA=sha(REVIEW/'post_formal_independent.json'),
        distinction='Prior independent full32/48 physical/model/Start/proof review: ACCEPT. This later public-root corroboration compares sealed typed outputs/source/root effects; no second mathematical raw replay was performed.',
        all_other62310_member_hash_status='Actual original checker independently looped and recorded unchanged except six declared derived sidecars; this bounded corroboration did not repeat all-member hashing.',
        actual_public_export_review_SHA=sha(REVIEW/'post_formal_https_hardening_and_export_review.json'),
        reviewed_targeted_evidence_files=len(USED),all_reviewed_targeted_bytes_unchanged=True,
        limitations=['The original checker boundary is a Python audit boundary allowing its standard runtime prefix, not an OS sandbox.',
            'No full62310-member rehash, archive scan/decompression, complete reader replay, network/export or native solve was repeated by this reviewer. Cleanup remains a separately gated later action.'],
        native_starts=0,Optimize=0,network_requests=0,Git_commands=0,exports=0,full_replays=0,full_member_scans=0,
        existing_source_or_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_public_recovery_review.json',result)

if __name__=='__main__':run()
