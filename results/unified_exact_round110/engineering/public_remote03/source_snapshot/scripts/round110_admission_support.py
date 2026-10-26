"""Materialize current admission indexing from completed actual evidence; no native work."""
from round110_common import *
import struct


def bind(paths):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def main():
    q = OUT/'qualification'
    actual = budget()
    assert not actual['unclosed'] and actual['qualification_starts'] == 16
    assert not list((OUT/'campaign/raw').glob('*'))
    finite = read(q/'finite_regressions01/audit.json')
    finite['raw_bindings'].update(bind([q/'finite_regressions01/audit.json',
        *[p for p in (OUT/'engineering/finite_regressions01').rglob('*') if p.is_file()]]))
    write(q/'finite_regression_evidence.json', finite)
    policy = read(OUT/'evidence_policy.json')
    original = OUT/'engineering/admission_support01/initial_policy.json'
    original.write_bytes((OUT/'evidence_policy.json').read_bytes())
    policy['raw_bindings'] = bind([ROOT/n for n in policy['implementation']] + [
        q/'finite_regression_evidence.json', q/'finite_regressions01/audit.json',
        q/'parser_equivalence_receipt.json', q/'main_entry_receipt.json',
        OUT/'engineering/qualification_rebuild01/receipt.json'])
    policy['freeze_scope'] = 'Before formal arm1; 42-arm performance not observed under current PE.'
    (OUT/'evidence_policy.json').write_text(json.dumps(policy, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    repair = read(OUT/'production_identity.json')
    repair.update(changed_production_files=['src/Parser.cpp'], only_entry_engineering=True,
                  math_search_unchanged=True, compiler_flags_match_inherited=True,
                  equivalence='Same original regex prefix; iterative first closing bracket only. '
                              'All other production bytes are unchanged; same-toolchain C++ dumps are exact.')
    repair['raw_bindings'] = bind([ROOT/'src/Parser.cpp', OUT/'production_identity.json',
        OUT/'engineering/initialization01/old_Parser.cpp',
        *[p for label in ['configure01','build01','prepare02']
          for p in (OUT/'engineering'/label).rglob('*') if p.is_file()],
        *[p for p in (OUT/'engineering/initialization01').rglob('*') if p.is_file()],
        q/'parser_build_plan.json', q/'parser_equivalence_receipt.json'])
    write(OUT/'repair_evidence.json', repair)
    qualification = read(q/'plan.json')
    qualification.update(conservative_starts=16, outer_cap_seconds=2000,
        original_plan_preserved=True, original_plan_SHA=sha(q/'plan.json'),
        resumption='CSV reader expected phase instead of actual event; retain all original four '
                   'declared starts and bill three new starts for only two never-started groups.',
        completed_actual_budget=actual,
        raw_bindings=bind([q/'plan.json', q/'main_entry_resumption_plan.json',
            *[p for p in (OUT/'fees').rglob('*.json')]]))
    write(q/'admission_plan.json', qualification)
    exe = BUILD/'ExactEBRP.exe';data=exe.read_bytes();off=struct.unpack_from('<I', data, 0x3c)[0]
    reserve,commit=struct.unpack_from('<QQ', data, off+24+72)
    header=dict(magic=struct.unpack_from('<H',data,off+24)[0], machine=struct.unpack_from('<H',data,off+4)[0],
                stack_reserve=reserve,stack_commit=commit)
    refs = dict(qualification_plan=q/'admission_plan.json',
        parser_equivalence=q/'parser_equivalence_receipt.json',main_entry=q/'main_entry_receipt.json',
        finite_regressions=q/'finite_regression_evidence.json',evidence_policy=OUT/'evidence_policy.json',
        repair_evidence=OUT/'repair_evidence.json')
    write(OUT/'review/admission_request.json',dict(
        production_PE_path=exe.relative_to(ROOT).as_posix(),actual_PE_header=header,
        remaining_formal_overhead_seconds=1800,
        artifacts={k:dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p)) for k,p in refs.items()}))
    (OUT/'RESUME.md').write_text('''# Round110 resume

Dedicated worktree E:/codes/ExactEBRP-round110; original user root untouched.
R109 base 8977da23a0be50da0ab2fceb69ad3ee04e040855; production repair commit
382cbcddc00fad4b1ed44fe8e9d9862f77cf5fba. Final PE SHA256
c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411,
build/research/round110-entry-v1/ExactEBRP.exe; original 2MiB stack and toolchain.

Only Parser namedBracketPayload changed. All12 old/new C++ mathematical dumps
match byte for byte; all12 actual-main zero-solve entries returned normally;
five final-PE H100 functional CLIs closed normally; 57 bounded evidence
regressions passed. Qualification-only raw rebuild succeeded. Closed fee
budget:16 starts,437.90709255634248 seconds; no formal arm has started.
Recompute exact budget from fees rather than treating this note as authority.

Retain failed managed-worktree C-disk creation, preparation/freeze authoring
failures and main_entry01 CSV-reader error. Main native3600 completed there;
main_entry02 ran only never-started7200/18000 groups, billed all new starts.
Never rerun any completed native qualification or spend prepaid failed slots.

Next: independent review of admission_request.json; only signed ACCEPT in
review/performance_admission.json admits formal arm1. Original42 frozen argv
are campaign/identity.json, with15 serial groups and57 formal billed starts,
88200 nominal seconds plus1800 planned wrapper overhead. Run group1 arms1–3
with `python scripts/round110_campaign.py billed campaign 1 3 main01`, then
groups4–6,7–9,10–12,13–15,16–18,19–21,22–24,25–27,28–30,31–33,34–36,
37–38,39–40,41–42 in original order. On any real fault preserve original raw
and closed fees, pause for current separately signed proof, resume only
never-started arms with new fees. No heavy jobs during formal performance.

After42 normal endpoints: primary raw rebuild, independent raw/decision
review, complete report and unique stage decision, current-only public pack,
actual fresh export/restore and root-only equal rebuild, independent restored
root audit, publish English stacked Draft PR based on current verified R109.
No PE/DLL/license in public evidence; attach every created PR to this chat.
''',encoding='utf-8')
    print(json.dumps(dict(request_SHA=sha(OUT/'review/admission_request.json'),budget=actual)))


def refresh(label):
    d=OUT/'engineering'/label
    old_policy=OUT/'evidence_policy.json';old_request=OUT/'review/admission_request.json'
    (d/'superseded_policy.json').write_bytes(old_policy.read_bytes())
    (d/'superseded_request.json').write_bytes(old_request.read_bytes())
    finite=read(OUT/'qualification/finite_regressions02/audit.json')
    finite['raw_bindings'].update(bind([OUT/'qualification/finite_regressions02/audit.json',
        *[p for p in (OUT/'engineering/finite_regressions02').rglob('*') if p.is_file()]]))
    finite['supersedes']='qualification/finite_regression_evidence.json; before formal arm1 only'
    target=OUT/'qualification/finite_regression_evidence02.json';write(target,finite)
    policy=read(old_policy)
    policy['raw_bindings']=bind([ROOT/n for n in policy['implementation']] + [
        target,OUT/'qualification/finite_regressions02/audit.json',
        OUT/'qualification/parser_equivalence_receipt.json',OUT/'qualification/main_entry_receipt.json',
        OUT/'engineering/qualification_rebuild01/receipt.json'])
    policy['reader_assembly_correction']=('Before any formal arm: preserve rejected False field without duplicate keyword. '
        'Old source/finite01/request/policy/signature remain explicitly superseded; finite02 executes actual corrected statement.')
    old_policy.write_text(json.dumps(policy,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    request=read(old_request)
    request['artifacts']['finite_regressions']=dict(path=target.relative_to(ROOT).as_posix(),SHA=sha(target))
    request['artifacts']['evidence_policy']['SHA']=sha(old_policy)
    request['supersedes_request_SHA']=sha(d/'superseded_request.json')
    old_request.write_text(json.dumps(request,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    write(d/'correction.json',dict(before_formal=True,native_calls=0,production_or_performance_helpers_changed=False,
        old_reader_SHA=read(OUT/'qualification/finite_regressions01/audit.json')['raw_bindings']['scripts/round110_reader.py'],
        current_reader_SHA=sha(ROOT/'scripts/round110_reader.py'),actual_checks=finite['checks'],
        original_snapshot='results/unified_exact_round110/engineering/finite_regressions01/source_snapshot/scripts/round110_reader.py',
        request_SHA=sha(old_request),policy_SHA=sha(old_policy)))
    print(json.dumps(dict(request_SHA=sha(old_request),current_reader_SHA=sha(ROOT/'scripts/round110_reader.py'))))


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='refresh':refresh(sys.argv[2])
    else:main()
