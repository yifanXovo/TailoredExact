"""Seal zero-native packaging-only review; all original scientific bytes kept."""
import argparse, hashlib, json, sys, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args()
root=Path(a.root).resolve();out=root/'results/unified_exact_round108';review=out/'review';dest=review/'packaging_exact_parts_finalize01';dest.mkdir(exist_ok=False)
tick=time.perf_counter();reads={}
def sha(path):
    path=Path(path).resolve();assert path.is_relative_to(root);h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(1024*1024):h.update(b)
    reads[path.relative_to(root).as_posix()]=h.hexdigest();return h.hexdigest()
def obj(path):
    sha(path);return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,v):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
source=sha(Path(__file__));command=[sys.executable,*sys.argv];write(dest/'launch.json',dict(actual_command=command,explicit_read_root=str(root),source_SHA=source,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
candidate='c35f285d76dbfba1ca16e4d73bd670de603b868337095b563eeda3e0f5786ce3';assert sha(root/'scripts/round108_public.py')==candidate
f=obj(review/'packaging_parts_finite01/checks.json');receipt=obj(review/'packaging_parts_finite01/receipt.json')
assert f['decision']=='ACCEPT' and receipt['exit_code']==0 and f['case_count']==49 and f['links_cleaned']==3 and receipt['candidate_source_SHA']==candidate
assert sha(review/'packaging_parts_finite_audit01.py')==receipt['source_SHA'] and sha(review/'packaging_parts_finite01/candidate_at_execution.py')==candidate
probe=obj(review/'packaging_boundary_probe01/receipt.json');assert probe['exit_code']==1 and probe['actual']=='accepted' and probe['decision']=='HOLD'
assert sha(review/'packaging_boundary_probe01/candidate_at_execution.py')=='62333f124a980e1abe07adda886f389aecc872fde67d89ada5483c0a58be636d'
preserved=obj(out/'engineering/pack_oversize01/failed_carrier_member_manifest.json');pr=obj(out/'engineering/pack_oversize01/receipt.json')
archive=out/'compact_evidence_failed01/evidence.tar.gz'
assert archive.stat().st_size==150926168 and sha(archive)=='135ecdc4769cc9c8beaa237a9eb42778ce243e91e73e96ef45ab33e46e2c1556'
assert pr['member_count']==len(preserved['files'])==79111 and len({x['path'] for x in preserved['files']})==79111
assert pr['failed_archive_SHA']==preserved['failed_archive_SHA']==sha(archive) and sha(out/'engineering/pack_oversize01/failed_carrier_member_manifest.json')==pr['member_manifest_SHA']
c=obj(out/'candidate_identity.json')
for name,digest in c['source_bindings'].items():assert sha(root/name)==digest
for name,digest in c['helpers'].items():assert sha(root/name)==digest
unchanged={name:sha(root/name) for name in ['scripts/round108_reader.py','scripts/round108_decisions.py','results/unified_exact_round108/review/campaign_raw_audit01.py','results/unified_exact_round108/review/final_local_review01.json','results/unified_exact_round108/review/final_local_review01.md']}
expected=['52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1','9a827d2fccd9b37483c2d3a5f8aa5877abb5c2db434554d18abed28d13c63c46','47cb299f4a8844ca668fab0117b035076f760041fb44ba6c4be0cd751af15adc','70fa0f323c088b68a05169b5eca22444703154b2524bb843ca8717f939a8f636','3ff12e3729a94951cc693cfc56e3428baf31573e22634822fb44a045eabef73e']
assert list(unchanged.values())==expected
record=dict(schema='round108-independent-exact-parts-packaging-review-v1',decision='ACCEPT',reviewer='independent_admission',explicit_read_root=str(root),candidate_source_SHA=candidate,finite_source_SHA=receipt['source_SHA'],finite_checks_SHA=sha(review/'packaging_parts_finite01/checks.json'),finite_receipt_SHA=sha(review/'packaging_parts_finite01/receipt.json'),finite_cases=49,finite_accept_cases=9,finite_refusal_cases=40,actual_link_cases=3,links_cleaned=True,actual_finite_exit_code=0,actual_finite_engineering_seconds=receipt['seconds'],
    authorizing_user_instruction='第10节：必要时使用已验证的分片/精确换行模式；小包无需人为分片。',
    preservation=dict(original_size_gate_failure_source_SHA=sha(out/'engineering/pack_oversize01/failed_round108_public.py'),actual_original_pack_receipt_SHA=sha(out/'engineering/public_pack01/receipt.json'),original_combined_local_archive_SHA=sha(archive),original_combined_bytes=archive.stat().st_size,exact_old_member_manifest_SHA=sha(out/'engineering/pack_oversize01/failed_carrier_member_manifest.json'),exact_old_member_count=79111,
        first_parts_source_SHA=probe['candidate_source_SHA'],actual_boundary_probe_receipt_SHA=sha(review/'packaging_boundary_probe01/receipt.json'),boundary_probe_expected='reject',boundary_probe_actual='accepted',boundary_probe_retained=True),
    acceptance_basis=['Only a real compressed archive >=strict95MiB is split; each normal part is90MiB and small carriers stay single.', 'Parts copy contiguous exact compressed bytes once, with canonical index/name/offset/size, per-partSHA and concatenated wholeSHA; no part recompression or member filtering.', 'Export transfers the manifest and validated logical blob list, omitting the oversized combined local archive.', 'Actual synthetic export/restoration executes the exact exported script copy and restores identical compressed/member bytes and CRLF.', 'Missing/extra/reordered/overlapping/gapped/escaped/corrupt parts, incorrect sizes/per-part/whole hashes, artificial small split, existing destinations and old-root fallback are rejected.', 'The actual formerly accepted dependency path escape is now rejected before extraction; dependency paths, aliases, symlinks, size/SHA/uniqueness and package/manifest/root boundaries are checked.', 'Restore binds actual public scripts/round108_public.py to manifest sourceSHA and restored reader to manifest readerSHA; plain member type/hash/size/name/complete coverage checked.'],
    source_review=dict(default_cli_single_blob_limit=95*1024*1024,default_cli_part_bytes=90*1024*1024,small_test_limits_API_only=True,strict95_equal_boundary_splits=True,inside_lexical_equals_resolved_and_root_containment=True,fresh_destination_exclusive=True,no_original_workspace_fallback=True,source_and_reader_bound=True,dependency_checked_before_extraction=True),
    scientifically_unchanged=dict(source_binding_count=len(c['source_bindings']),frozen_helper_binding_count=len(c['helpers']),all_bound_bytes_unchanged=True,exact_existing_readers_and_sealed_local_review=unchanged,current_PE_identity=c['production_PE_SHA'],current_DLL_identity=c['DLL_SHA'],performance_identity_and_all_raw_evidence_unchanged=True,no_native_rerun=True,solver_fees_unchanged=True),
    scope='Packaging-only implementation and finite tests, not completed real campaign export/restoration or independent all21 public mathematical recovery.',full_actual_repack_still_required=True,full_actual_public_recovery_still_required=True,independent_all21_public_math_review_still_required=True,
    operations=dict(Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,actual_campaign_pack=0,production_edits=0,frozen_helper_edits=0,decision_rule_edits=0))
write(review/'packaging_exact_parts_review01.json',record)
md=f'''包装修正版独立审查 ACCEPT，候选源码 `{candidate}`。此结论仅接受分片/恢复实现和有限测试；实际全量重新打包、公共导出/恢复及独立全部 21 臂数学重建仍须执行。

第一次实际 150,926,168 字节压缩包超过严格 95 MiB 门槛，其源码/命令/exit1/67.6488424 工程秒/原始输出保留；本次独立重哈希原 local combined SHA `{record['preservation']['original_combined_local_archive_SHA']}`，并绑定 79,111 项精确 member manifest。现只有 actual>=95MiB 才分为90MiB连续压缩字节片，不按片重压缩，不移除任何 raw member；小包不拆。公共导出只含manifest和验证后的逻辑blob列表，不复制超限combined文件。

首个分片候选 62333f… 的实际小反例曾接受 `reference/../../outside.txt`，错误声称public-only；独立 probe exit1/HOLD、完整源码/命令/回执保留。当前修正以 lexical==resolved/plain/no-symlink/root-containment 阻止 package/manifest/依赖/目标逃逸，依赖 SHA/size/唯一性在解包前验证；实际执行源码必须是公共根脚本且匹配manifest，恢复reader也核SHA。该旧反例现已实际拒绝。

49 个实际小合成 API 案例全部通过（9接受/40拒绝），exit0，{receipt['seconds']:.9f} 工程秒，checks `{record['finite_checks_SHA']}`。成功路径真正split/export并从public脚本副本执行fresh restore，combined/member/CRLF字节精确恢复；unsplit成功。拒绝覆盖阈值/小包人工拆片、missing/extras/index/reorder/path/gap/overlap/size/per-part/whole SHA、已存在目标、public缺片时不回退原fixture、source/reader身份、member缺失/多余/重复/链接/逃逸与依赖路径/hash/size。3个实际OS链接（part/依赖/package目录）被候选拒绝并已清理。CLI95/90常量未调，只有测试API使用小值。

重新核对 205 生产源和20冻结helpers全SHA未变；主reader52cad…、decision9a827…、standalone47cb…及原封存本地final review70fa…字节未变。无solver/native/compiler/生产/性能helper/decision规则改变或重跑。新独立包装记录可入carrier，原科学审查不重写。随后全量恢复应使用真实新public根和恢复根，仅从拟公开文件及精确公共依赖执行；当前不声称已完成实际公共全量复算。
'''
with (review/'packaging_exact_parts_review01.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
write(dest/'receipt.json',dict(actual_command=command,explicit_read_root=str(root),source_SHA=source,exit_code=0,decision='ACCEPT',seconds=time.perf_counter()-tick,review_SHA=sha(review/'packaging_exact_parts_review01.json'),review_MD_SHA=sha(review/'packaging_exact_parts_review01.md'),read_bindings=reads,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision='ACCEPT',review_SHA=sha(review/'packaging_exact_parts_review01.json'),candidate_SHA=candidate,cases=49,production_bindings=len(c['source_bindings']),frozen_helpers=len(c['helpers']))))
