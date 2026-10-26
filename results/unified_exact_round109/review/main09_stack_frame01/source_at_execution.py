"""Read-only PE prologue evidence; no process execution of the engine."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
root=Path(sys.argv[1]).resolve();dest=Path(sys.argv[2]).resolve();assert dest.is_relative_to(root/'results/unified_exact_round109/review');dest.mkdir(exist_ok=False);tick=time.perf_counter()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,value):
    with (dest/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
pe=root/'build/research/round109-inherited-mb-v1/ExactEBRP.exe';assert sha(pe)=='4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
write('launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0));(dest/'source_at_execution.py').write_bytes(Path(__file__).read_bytes());commands=[];outputs={}
for label,start,end in [('main_prologue',0x1400ba135,0x1400ba180),('Parser_prologue',0x1400e8c28,0x1400e8c80),('regex_DFS_prologue',0x1405cd780,0x1405cd7e0)]:
    argv=['D:/msys64/ucrt64/bin/objdump.exe','-d','-C','--start-address='+hex(start),'--stop-address='+hex(end),str(pe)];started=time.perf_counter();p=subprocess.run(argv,cwd=root,capture_output=True);(dest/(label+'.stdout')).write_bytes(p.stdout);(dest/(label+'.stderr')).write_bytes(p.stderr);assert p.returncode==0
    commands.append(dict(label=label,argv=argv,cwd=str(root),exit_code=p.returncode,engineering_seconds=time.perf_counter()-started,stdout_SHA=sha(dest/(label+'.stdout')),stderr_SHA=sha(dest/(label+'.stderr')),solver_launch=False));outputs[label]=p.stdout.decode()
assert '$0x159490,%eax' in outputs['main_prologue'] and '___chkstk_ms' in outputs['main_prologue'] and 'sub    %rax,%rsp' in outputs['main_prologue']
assert '$0x6b0,%rsp' in outputs['Parser_prologue'] and '$0x20,%rsp' in outputs['regex_DFS_prologue']
value=dict(decision='ACCEPT_ADDITIONAL_STATIC_STACK_FACTS',original_diag_SHA=sha(root/'results/unified_exact_round109/review/main09_stack_diagnosis03/audit.json'),original_PE_SHA=sha(pe),original_diagnosis_not_modified=True,
    confirmed_main_fixed_frame_allocation_bytes=0x159490,confirmed_parser_fixed_frame_allocation_bytes=0x6b0,confirmed_single_DFS_frame_explicit_stack_sub_bytes=0x20,reserved_main_thread_stack_bytes=0x200000,
    theoretical_space_after_main_fixed_frame_before_other_call_frames_bytes=0x200000-0x159490,
    additional_pushes_return_addresses_guard_pages_and_other_frames_reduce_theoretical_space=True,
    inference='Large fixed main frame consumes about1.35MiB of the2MiB reserve before parsing; the parser frame is only1712bytes, while recursive regex matching consumes the remaining stack. Exact failing regex depth/payload and attribution of main frame to individual local objects remain unproved without a crash stack/variable-layout audit.',
    samePE_sameentry_environment_fix_still_unqualified=True,stage='BLOCKED',resumption_allowed=False,actual_engineering_commands=commands,Optimize=0,native_environment=0,production_edits=0)
write('audit.json',value);write('receipt.json',dict(exit_code=0,engineering_elapsed_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),audit_SHA=sha(dest/'audit.json'),Optimize=0,native_environment=0));print(json.dumps(dict(decision=value['decision'],main_fixed_frame_bytes=0x159490,remaining_theoretical_bytes=0x200000-0x159490)))
