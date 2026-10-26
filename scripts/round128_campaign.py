"""Serial independent arms under inherited complete producer clock."""
from round128_common import *
import copy,types,traceback,collections
from round122_prepare import command as original_command,COMMON
import round90_lp_g_g3 as supervisor
import round115_campaign as producer
from round121_campaign import finish_producer
from round126_run import child_creation
from round115_common import process_origin
from round113_progress import OptionalPublisher
from round128_evidence import verify,extension
import read_round118 as reader
import read_round116 as base_reader
import round108_reader as core

def prepare_group(name,layer,p,methods,seed,repeat=1,config=None):
    p=copy.deepcopy(p);p.update(gurobi_seed=seed,instance_path=p['input_path'],panel_kind=name.split('/')[0])
    camp=OUT/name;camp.mkdir(parents=True,exist_ok=False)
    ref=OUT/'qualification/references'/p['id']
    if not (ref/'build.json').exists():
        rc=metered('reference_'+p['id'],'qualification',[BUILD/'Round128ExportE2.exe',ROOT/p['input_path'],p['T_seconds'],0,0,0,'p',ref])
        assert rc==0
    p['reference']=read(ref/'build.json')
    target=camp/'reference'/p['id'];target.mkdir(parents=True)
    for n in ['original.lp','build.json']:(target/n).hardlink_to(ref/n)
    pe=E1 if layer=='E1' else E2;pe_sha=sha(pe);launches=[]
    for position,method in enumerate(methods,1):
        arm='P-GRB' if method in ['P','PT'] else 'M-B';d=camp/'raw'/f'{position:02d}_{p["id"]}_S{seed}_R{repeat}_{method}'
        arm_config=config if config is not None and (method=='PT' or name.startswith('training/')) else None
        cmd=original_command(p,arm,d);cmd[0]=str(pe)
        if layer in ['E1','E2']:
            cmd += ['--round128-mode','md-r'] if method=='MD-R' else ['--round127-mode','p' if arm=='P-GRB' else method.lower()]
            if arm_config is not None:cmd+=['--round127-p-parameters',str(OUT/'tuning_manifest'/(arm_config['id']+'.prm'))]
        launches.append(dict(number=position,group_number=1,id=p['id'],arm=arm,method=method,seed=seed,repeat=repeat,
            binary_layer=layer,panel=copy.deepcopy(p),panel_kind=p['panel_kind'],destination=str(d),cap_seconds=p['cap_seconds'],
            hard_stop_seconds=p['cap_seconds']-2,command=cmd,configuration=arm_config if arm_config else dict(id='q0',MIPFocus=0,Cuts=-1)))
    i=dict(prereg=dict(common=dict(COMMON,gurobi_seed=seed),candidate_binary=str(pe),candidate_binary_sha256=pe_sha),
        prereg_sha256=sha(OUT/'experiment_manifest.json'),runner_sha256=sha(__file__),candidate_binary_sha256=pe_sha,dll_sha256=DLL_SHA,
        source_hashes=read(ROOT/'results/unified_exact_round127/E1_frozen.json')['source_bindings'] if layer=='E1' else read(OUT/'E2_build.json')['source_bindings'],
        measured_source_commit=SOURCE if layer=='E0' else git('rev-parse','HEAD').decode().strip(),
        delivery_base_commit=BASE,launches=launches,references={p['id']:p['reference']},
        source_tree=str(PREVIOUS) if layer=='E1' else str(ROOT),
        no_cross_arm_information=True,configuration=config)
    write(camp/'identity.json',i);return i
def supervised(l,i,tick):
    d=Path(l['destination']);publisher=OptionalPublisher(l)
    production_check=types.FunctionType(producer.production_check.__code__,dict(vars(producer),ROOT=ROOT))
    def popen(*args,**kwargs):
        child=subprocess.Popen(*args,**kwargs)
        write(d/'child_process_origin.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=child_creation(child),
            command=l['command'],seed=l['seed'],source_commit=i['measured_source_commit'],PE_SHA=i['candidate_binary_sha256'],creation_from_live_OS_handle=True))
        return child
    process_api=types.SimpleNamespace(**dict(vars(subprocess),Popen=popen))
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=d.parents[1],atomic_status=publisher,_arm_tick=tick,
        production_check=production_check,subprocess=process_api)
    try:return producer.supervisor_function(namespace)(l,i['prereg'],i)
    finally:
        if d.is_dir():write(d/'progress_publication_receipt.json',dict(publisher.receipt(),necessary_write_before_production=True,global_namespace_modified=False))
def reconstruct(camp):
    i=read(camp/'identity.json');recs=collections.defaultdict(list);core.start_reader.ROOT=ROOT
    with extension():
        items=[reader.item(ROOT,l,i,recs) for l in i['launches']]
        # The inherited algebra reader calls each diagnostic representation
        # M-B. Reconcile each arm's native IDs separately; cross-arm witnesses
        # may refute a false bound, never supply a performance proof/solution.
        witnesses=[dict(q,arm=v['l']['method']) for v in items if v['complete'] for q in v['ind']['witnesses']]
        local=[base_reader.reconcile(v.get('claims',[]),witnesses) for v in items]
        final=base_reader.reconcile([dict(q,arm=v['l']['method']) for v in items if v['complete'] for q in v['claims']],witnesses)
        arms=[reader.finalize(ROOT,v,f,recs) for v,f in zip(items,local)]
    for a,l in zip(arms,i['launches']):
        a.update(method=l['method'],seed=l['seed'],repeat=l['repeat'],binary_layer=l['binary_layer'],configuration=l.get('configuration'),
            T_cert=a['T_produce'] if a.get('certificate') and a.get('formal_protocol_qualified') else None,
            destination=l['destination'],input_SHA=l['panel']['input_sha256'])
    write(camp/'reconstructed.json',dict(arms=arms,adjudication=final,per_arm_adjudication=local,
        inherited_representation_labels_not_used_as_cross_arm_call_IDs=True))
    tables=camp/'tables';tables.mkdir(exist_ok=True)
    for n,rows in recs.items():
        path=tables/(n+'.csv')
        if rows and not path.exists():core.table(path,rows)
    return arms
def execute(name):
    wrapper_tick,wrapper_creation=process_origin()
    camp=OUT/name;i=read(camp/'identity.json')
    if (camp/'reconstructed.json').exists():return read(camp/'reconstructed.json')['arms']
    for l in i['launches']:
        d=Path(l['destination'])
        if (d/'arm_total_receipt.json').exists():continue
        if not d.exists():
            tick=wrapper_tick if l['number']==1 else time.perf_counter()
            unix=wrapper_creation if l['number']==1 else time.time()
            assert sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            assert sha(l['command'][0])==i['candidate_binary_sha256'] and sha(DLL)==i['dll_sha256']
            supervised(l,i,tick);finish_producer(l,tick,unix)
        else:
            # Recovery only reads a complete sealed producer; no Optimize retry.
            assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'unsealed production needs explicit engineering decision'
        verify(l,i)
        write(OUT/'runtime_status.json',dict(UTC=utc(),last_sealed=l['destination'],group=name,next_method=l['number']+1))
        (OUT/'RESUME.md').write_text(f'Round128 active.\n\nLast sealed: `{l["destination"]}`.\nNext position in `{name}`: {l["number"]+1}.\nCheck fees/PID and native processes before resuming. Never overwrite a sealed arm.\n',encoding='utf-8')
    return reconstruct(camp)

if __name__=="__main__":execute(sys.argv[1])
