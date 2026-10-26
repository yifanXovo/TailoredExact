"""Immutable, zero-engine diagnosis of the one real Windows parser crash."""
from pathlib import Path
import argparse,hashlib,json,re,struct,subprocess,sys,time,traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';DEST=Path(args.out).resolve();assert DEST.is_relative_to(OUT/'review');DEST.mkdir(exist_ok=False)
tick=time.perf_counter();error=None;commands=[];reads={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p);b=p.read_bytes();reads[str(p)]=hashlib.sha256(b).hexdigest();return b
def obj(p):return json.loads(read(p))
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def command(label,argv):
    start=time.perf_counter();p=subprocess.run(argv,cwd=ROOT,capture_output=True);(DEST/(label+'.stdout')).write_bytes(p.stdout);(DEST/(label+'.stderr')).write_bytes(p.stderr)
    result=dict(label=label,argv=argv,cwd=str(ROOT),exit_code=p.returncode,engineering_seconds=time.perf_counter()-start,stdout_SHA=sha(DEST/(label+'.stdout')),stderr_SHA=sha(DEST/(label+'.stderr')),solver_launch=False)
    commands.append(result);save(DEST/(label+'.receipt.json'),result);assert p.returncode==0,(label,p.stderr);return p.stdout.decode('utf-8-sig',errors='replace')
save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0));(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    identity=obj(OUT/'campaign/identity.json');candidate=obj(OUT/'candidate_identity.json');launch=identity['launches'][24];assert (launch['number'],launch['id'],launch['arm'])==(25,'G100-C1','M-B')
    d=Path(launch['destination']);rawlaunch=obj(d/'launch.json');completion=obj(d/'completion.json');audit=obj(d/'audit.json');obs=obj(d/'observations.json')
    assert rawlaunch['command']==launch['command'] and rawlaunch['panel']==launch['panel'] and completion['returncode']==0xC00000FD and completion['stop_reason']=='abnormal_process_exit' and completion['committed_events']==0 and obs==[]
    assert audit['passed'] is False and audit['endpoint'] is None and not (d/'result.json').exists() and not (d/'native.log').exists() and not (d/'whole_arm_receipt.json').exists()
    assert not read(d/'stdout.log') and not read(d/'stderr.log');phases=read(d/'phases.csv').decode();assert re.findall(r'"(process_entry|instance_parsing_start)"',phases)==['process_entry','instance_parsing_start'] and phases.count('\n')==3
    sample=json.loads(read(d/'samples.jsonl').splitlines()[0]);assert sample['observed_events']==0 and sample['provisional_U'] is None and sample['formal_endpoint'] is False
    for l in identity['launches'][25:]:assert not Path(l['destination']).exists()
    pe=Path(launch['command'][0]);blob=read(pe);assert hashlib.sha256(blob).hexdigest()==candidate['production_PE_SHA']=='4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
    at=struct.unpack_from('<I',blob,0x3c)[0];assert blob[:2]==b'MZ' and blob[at:at+4]==b'PE\0\0';optional=at+24;assert struct.unpack_from('<H',blob,optional)[0]==0x20b
    base=struct.unpack_from('<Q',blob,optional+24)[0];reserve,commit=struct.unpack_from('<QQ',blob,optional+72);timestamp=struct.unpack_from('<I',blob,at+8)[0]
    assert (base,reserve,commit,timestamp)==(0x140000000,0x200000,0x1000,0x6ac719da)
    address=base+0x4e2693
    disassembly=command('fault_offset_disassembly',['D:/msys64/ucrt64/bin/objdump.exe','-d','-C','--start-address='+hex(address-0x13),'--stop-address='+hex(address+0x1d),str(pe)])
    assert '1404e2693:' in disassembly and '_CharMatcher' in disassembly and '_M_access' in disassembly
    headers=command('PE_private_headers',['D:/msys64/ucrt64/bin/objdump.exe','-p',str(pe)])
    imports=re.findall(r'DLL Name:\s*(\S+)',headers);assert not any('stdc++' in n.lower() for n in imports)
    eventcommand="$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); $events=Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001; StartTime=[datetime]'2026-10-09T12:35:00'; EndTime=[datetime]'2026-10-09T12:43:00'} -ErrorAction Stop; $events | Where-Object { $_.Message -like '*ExactEBRP.exe*' } | ForEach-Object { $_.ToXml() }"
    windows=command('windows_application_events',['powershell','-NoProfile','-Command',eventcommand]);assert 'c00000fd' in windows.lower() and '004e2693' in windows.lower() and '0x976c' in windows.lower() and str(pe).replace('/','\\') in windows
    active=command('no_active_PE',['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"name = 'ExactEBRP.exe'\" | Select-Object ProcessId,ParentProcessId,ExecutablePath | ConvertTo-Json -Compress"]);assert not active.strip()
    parser=read(ROOT/'src/Parser.cpp').decode();main=read(ROOT/'src/main.cpp').decode();assert 'std::regex_search(text, m, re)' in parser and '([\\s\\S]*?)' in parser and 'instance_parsing_start' in main
    for rel,digest in candidate['source_bindings'].items():assert sha(ROOT/rel)==digest
    inputblob=read(ROOT/launch['panel']['input_path']);assert hashlib.sha256(inputblob).hexdigest()==launch['panel']['input_sha256']
    inputtext=inputblob.decode();payload_lengths={name:len(re.search(name+r'\s*=\s*\[([\s\S]*?)\]',inputtext)[1]) for name in ['capacities','initial','target','weights','min_ratio','points']}
    for source in ['src/Parser.cpp','src/main.cpp','CMakeLists.txt','scripts/round109_prepaid_wrapper.py','scripts/round109_main06_recovery.py']:
        target=DEST/'source_snapshot'/source;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(read(ROOT/source))
    preserved=DEST/'original_failure_snapshot';preserved.mkdir()
    for name in ['launch.json','completion.json','audit.json','observations.json','phases.csv','samples.jsonl','stdout.log','stderr.log','affinity.json','process_start_marker.json']:(preserved/name).write_bytes(read(d/name))
    fees=[]
    for path in sorted((OUT/'fees').glob('*/receipt.json')):
        r=obj(path);l=obj(path.parent/'launch.json');assert r['conservative_process_starts']==l['conservative_process_starts'];fees.append(dict(label=path.parent.name,receipt_SHA=sha(path),launch_SHA=sha(path.parent/'launch.json'),**r))
    starts=sum(r['conservative_process_starts'] for r in fees);seconds=sum(r['outer_seconds'] for r in fees);failed=next(r for r in fees if r['label']=='main09');assert starts==51 and failed['exit_code']==1 and failed['conservative_process_starts']==4 and failed['actual_native_children_with_launch']==1
    for name in ['launch.json','receipt.json','failure.txt']:(preserved/('main09_'+name)).write_bytes(read(OUT/'fees/main09'/name))
    remaining=72-starts;nominal=sum(l['cap_seconds'] for l in identity['launches']);assert nominal==88200 and remaining==21 and starts+42>72 and seconds+nominal>100000
    value=dict(decision='BLOCKED_UNRESOLVED_SAME_PE_ENVIRONMENT_FAULT',resumption_allowed=False,actual_diagnosis=True,Optimize=0,native_environment=0,production_or_signed_source_edits=0,
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),production_PE_SHA=sha(pe),unchanged_all42_native_argv=[l['command'] for l in identity['launches']],
        native_failure=dict(number=25,id='G100-C1',arm='M-B',exit_code=completion['returncode'],exit_code_hex='0xC00000FD',legacy_seconds=completion['fully_observed_end_to_end_seconds'],process_seconds=completion['process_wall_seconds'],legal_scientific_endpoint=False,committed_events=0,stdout_empty=True,stderr_empty=True,result_missing=True,native_log_missing=True,whole_arm_receipt_missing=True,phase_boundary='instance_parsing_start; no subsequent committed process phase'),
        windows_evidence=dict(actual_event1000_and1001=True,pid=38764,fault_RVA='0x4e2693',fault_address=hex(address),PE_timestamp=hex(timestamp),fault_symbol='std::_Any_data::_M_access<std::__detail::_CharMatcher<std::__cxx11::regex_traits<char>, false, false>>',disassembly_SHA=sha(DEST/'fault_offset_disassembly.stdout'),events_SHA=sha(DEST/'windows_application_events.stdout')),
        PE_stack=dict(reserve_bytes=reserve,commit_bytes=commit,main_thread_default_bound_in_exact_PE_header=True,imports=imports,libstdcpp_regex_linked_into_exact_PE=True),
        cause=dict(confirmed='Windows stack-overflow exception during input parsing, fault inside linked C++ regex matcher',probable='Recursive libstdc++ DFS matching Parser.cpp namedBracketPayload multi-character payload; large V100 input exhausts fixed2MiB main-thread stack',specific_named_payload_not_proved=True,full_crash_dump_call_stack_unavailable=True,global_OOM_not_established=True,sampled_available_memory_bytes=sample['available_memory_bytes'],payload_character_lengths=payload_lengths),
        environment_only_resolution=dict(validated_samePE_sameentry_fix=None,reason='Documented executable default stack is PE reserve. Parent Python/thread/ulimit stack does not provide a documented CreateProcess child main-thread stack override. SetThreadStackGuarantee handles overflow within reserve; it does not enlarge reserve. Re-entering on injected/replacement thread changes entry/runtime and requires a new contract, not a proved environment-only fix.'),
        production_PE_change_boundary=dict(any_header_patch_changes_PE_SHA=True,user_requires_all42_same_final_PE=True,minimum_new_native_children_for_newPE=42,remaining_conservative_starts=remaining,absolute_lower_total_starts_excluding_wrappers_and_qualification=starts+42,minimum_all42_nominal_seconds=nominal,paid_plus_newPE_all42_nominal_seconds=seconds+nominal,prepaid26_27_not_coupons_for_changedPE=True),
        paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=remaining,valid_formal_arms_before_fault=24,failed_formal_arm=25,never_started_numbers=list(range(26,43)),original_main09_two_prepaid_unused_slots=[26,27],
        conditional_samePE_budget_only=dict(native_children_to_complete_with_retry25=18,unpaid_native_children_after_exact26_27_coupons=16,max_new_wrappers_without_extra_driver=5,resumption_allowed=False,requires_actual_validated_samePE_environment_fix_and_new_admission=True,wrapper_group_merging_never_solves_current_crash=True),
        resource_contract='Keep failed25/fee intact; cannot promote an absent endpoint or erase the failure. Without a verified samePE sameentry environment repair, freeze campaign and deliver BLOCKED with24valid/1failed/17unstarted; PE change requires42 reruns that hard starts and nominal outer budget cannot admit.',
        documentation=[dict(url='https://learn.microsoft.com/en-us/windows/win32/procthread/thread-stack-size',claim='Executable header specifies default reserve/commit; stack change API applies new thread/fiber creation'),dict(url='https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setthreadstackguarantee',claim='Guarantee cannot exceed already reserved stack')],paid_fees=fees,raw_read_bindings=reads,actual_engineering_commands=commands)
    save(DEST/'audit.json',value);print(json.dumps(dict(decision=value['decision'],paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=remaining,fault_address=hex(address),reserve_bytes=reserve)),flush=True)
except Exception:
    error=traceback.format_exc();save(DEST/'audit.json',dict(decision='HOLD_DIAGNOSIS_FAILED',error=error,Optimize=0,native_environment=0));print(error,file=sys.stderr,flush=True)
save(DEST/'receipt.json',dict(exit_code=int(error is not None),engineering_elapsed_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),audit_SHA=sha(DEST/'audit.json'),engineering=True,Optimize=0,native_environment=0))
if error:sys.exit(1)
