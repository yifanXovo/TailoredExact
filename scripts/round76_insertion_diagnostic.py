"""Two bounded fixed-witness insertion closures, never a formal solver arm."""
import copy
import csv
import json
import os
from pathlib import Path
import subprocess
import time
import analyze_round61 as physical
import round70_affinity as affinity
from round75_startup import normalize,route_hash
from round75_qualify import ROOT,read,write,sha
OUT=ROOT/'results/unified_exact_round76'
DIAG=OUT/'diagnostic'
BUILD=ROOT/'build/round76/diagnostic'

SOURCE=r'''#include "Parser.hpp"
#include "Evaluator.hpp"
#include "Round73JointInsertion.hpp"
#include "Round61Candidates.hpp"
#include "ProcessPhaseLedger.hpp"
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
int main(int argc,char** argv) {
 try {
    SolveOptions opt;opt.process_start_time_valid=true;
    opt.process_start_time=std::chrono::steady_clock::now();
    opt.process_wall_time_limit=30;opt.process_shutdown_margin_seconds=1;
    if(argc!=3)throw std::runtime_error("diagnostic requires role and fresh output directory");
    Instance in;std::vector<RoutePlan> routes;
    @CASES@
    else throw std::runtime_error("undeclared diagnostic role");
    std::filesystem::path out(argv[2]);
    auto verification=verifySolution(in,routes,opt.lambda);
    if(!verification.feasible||!verification.errors.empty())throw std::runtime_error("invalid diagnostic input");
    const double initial=verification.objective;
    auto snapshot=[&](const char* name) {
        VerifiedCandidateStore store;
        if(!store.consider(in,opt.lambda,routes,"round76_fixed_witness_diagnosis","original_problem"))
            throw std::runtime_error("diagnostic snapshot verification failed");
        writeRound61Witness(out/name,in,opt.lambda,store.best());
    };
    snapshot("initial.json");
    Round73InsertionStats stats;
    std::ofstream trace(out/"trace.csv");
    trace<<"step,process_seconds,vehicle,pickup,drop,quantity,pickup_leg,drop_leg,travel_delta,added_duration,F,G,P,placements,quantity_evaluations,status\n"<<std::setprecision(17);
    auto record=[&](const Round73InsertionChoice& c,const char* status) {
        trace<<stats.accepted<<','<<processElapsedSeconds(opt)<<','<<c.vehicle<<','<<c.pickup<<','<<c.drop<<','<<c.quantity<<','
             <<c.pickup_leg<<','<<c.drop_leg<<','<<c.travel_delta<<','<<c.added_duration<<','<<verification.objective<<','
             <<verification.G<<','<<verification.P<<','<<stats.placements<<','<<stats.quantity_evaluations<<','<<status<<'\n';
        trace.flush();if(!trace)throw std::runtime_error("diagnostic trace failure");
    };
    record({},"initial_verified");
    for(;;) {
        auto c=bestRound73Insertion(in,routes,opt.lambda,stats,&opt);
        if(stats.deadline_reached){record({},"whole_run_deadline");break;}
        if(!c.found){stats.exhausted=true;record({},"motif_exhausted");break;}
        auto next=applyRound73Insertion(routes,c);auto checked=verifySolution(in,next,opt.lambda);
        if(!checked.feasible||!checked.errors.empty()||std::abs(checked.objective-c.objective)>1e-10||
            !(verification.objective-checked.objective>1e-12))throw std::runtime_error("diagnostic physical/objective disagreement");
        routes=std::move(next);verification=std::move(checked);++stats.accepted;
        if(stats.accepted>in.V)throw std::runtime_error("diagnostic finite-visit invariant failed");
        record(c,"accepted_verified");
    }
    snapshot("witness.json");
    std::ofstream result(out/"result.json");result<<std::setprecision(17)
        <<"{\"initial_F\":"<<initial<<",\"final_F\":"<<verification.objective
        <<",\"accepted\":"<<stats.accepted<<",\"passes\":"<<stats.passes
        <<",\"placements\":"<<stats.placements<<",\"quantity_evaluations\":"<<stats.quantity_evaluations
        <<",\"exhausted\":"<<(stats.exhausted?"true":"false")
        <<",\"deadline_reached\":"<<(stats.deadline_reached?"true":"false")
        <<",\"optimizer_calls\":0,\"scope\":\"fixed_witness_diagnosis_only\"}\n";
    result.flush();if(!result)throw std::runtime_error("diagnostic result write failure");
    return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
'''

def routes_cpp(witness):
    parts=[]
    for route in witness['routes']:
        nodes=','.join(str(int(i)) for i in route['nodes'])
        operations=','.join('{'+','.join(str(int(op[k])) for k in ['station','pickup','drop'])+'}' for op in route['operations'])
        parts.append('{'+str(int(route['vehicle']))+',{'+nodes+'},{'+operations+'}}')
    return '{'+','.join(parts)+'}'

def replay(p,dest,original):
    began=time.perf_counter();initial=normalize(read(dest/'initial.json'));final=normalize(read(dest/'witness.json'))
    assert route_hash(initial)==route_hash(original)
    physical.physical(p,initial);routes=copy.deepcopy(initial['routes'])
    rows=list(csv.DictReader((dest/'trace.csv').open(encoding='utf-8')))
    assert rows[0]['status']=='initial_verified' and rows[-1]['status']=='motif_exhausted'
    prior=initial['F'];last_time=-1;accepted=0
    for row in rows:
        now=float(row['process_seconds']);assert now>=last_time;last_time=now
        if row['status']!='accepted_verified':continue
        k,pick,drop,q,a,b=[int(row[key]) for key in ['vehicle','pickup','drop','quantity','pickup_leg','drop_leg']]
        used={i for route in routes for i in route['nodes']}
        assert q>0 and (pick or drop) and (not pick or pick not in used) and (not drop or drop not in used)
        route=next((route for route in routes if route['vehicle']==k),None)
        if route is None:route=dict(vehicle=k,nodes=[0,0],operations=[]);routes.append(route)
        if drop:route['nodes'].insert(b+1,drop);route['operations'].append(dict(station=drop,pickup=0,drop=q))
        if pick:route['nodes'].insert(a+1,pick);route['operations'].append(dict(station=pick,pickup=q,drop=0))
        checked=physical.physical(p,dict(routes=routes,F=float(row['F'])))
        assert checked['original_T_feasible'] and prior-checked['F']>1e-12
        prior=checked['F'];accepted+=1;assert int(row['step'])==accepted
    assert route_hash(dict(routes=routes))==route_hash(final)
    checked=physical.physical(p,final);assert checked['original_T_feasible']
    result=read(dest/'result.json');assert result['accepted']==accepted and result['exhausted'] and not result['deadline_reached']
    assert abs(result['final_F']-checked['F'])<1e-10 and result['optimizer_calls']==0
    return dict(result=result,physical=checked,initial_physical=physical.physical(p,initial),
        independently_verified_witnesses=accepted+2,route_sha256=route_hash(final),offline_replay_seconds=time.perf_counter()-began)

def main():
    driver_started=time.perf_counter()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round76-physical-route-closure'
    assert not DIAG.exists() and not BUILD.exists(),'Never overwrite a diagnostic or compile attempt'
    assert not (ROOT/'results/unified_exact_round75/startup/active_run.lock').exists()
    assert not (ROOT/'results/unified_exact_round75/qualification_active.lock').exists()
    qualification=read(ROOT/'results/unified_exact_round75/qualification_v2.json')
    assert len(qualification['attempts'])==3 and all(r['returncode']==0 for r in qualification['attempts'])
    for name,digest in qualification['identity']['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'CMakeLists.txt')==qualification['identity']['cmake_sha256']
    panel={p['id']:p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    witnesses={};cases=[];sources=[];physical.ROOT=ROOT
    for key in ['D6','D7']:
        p=panel[key];assert sha(ROOT/p['instance_path'])==p['input_sha256']
        wp=ROOT/'results/unified_exact_round75/startup/local_raw'/key/'JDS-X/result.json'
        witness=normalize(read(wp));physical.physical(p,witness);witnesses[key]=witness
        clause='if' if not cases else 'else if'
        cases.append(f'{clause}(std::string(argv[1])=={json.dumps(key)}) {{in=parseInstanceFile({json.dumps(str(ROOT/p["instance_path"]))},{p["T_seconds"]},{p["pickup_seconds"]},{p["drop_seconds"]});opt.lambda={p["lambda"]};routes={routes_cpp(witness)};}}')
        sources.append(dict(id=key,input=p,witness_path=str(wp.relative_to(ROOT)),witness_sha256=sha(wp),route_sha256=route_hash(witness)))
    DIAG.mkdir(parents=True);BUILD.mkdir(parents=True)
    source=DIAG/'fixed_witness_harness.cpp';source.write_text(SOURCE.replace('@CASES@','\n    '.join(cases)),encoding='utf-8')
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe');library=ROOT/'build/round75/v2/libexact_ebrp_core.a';exe=BUILD/'insertion_diagnostic.exe'
    command=list(map(str,[compiler,'-O3','-DNDEBUG','-std=c++17','-DEXACT_EBRP_ENABLE_GUROBI=1','-I',ROOT/'include',source,library,'-o',exe,
        '-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']))
    launches=[dict(id=key,command=[str(exe),key,str(DIAG/'local_raw'/key)],cap_seconds=30,hard_deadline=29.8,
        destination=str((DIAG/'local_raw'/key).relative_to(ROOT))) for key in ['D6','D7']]
    identity=dict(plan_sha256=sha(OUT/'plan.md'),driver_sha256=sha(__file__),generated_source_sha256=sha(source),
        compiler=str(compiler),compiler_sha256=sha(compiler),library=str(library.relative_to(ROOT)),library_sha256=sha(library),
        qualified_core_source=qualification['identity']['source_commit'],qualified_core_identity_sha256=sha(ROOT/'results/unified_exact_round75/qualification_v2.json'),
        physical_reader_sha256=sha(physical.__file__),sources=sources,compile_command=command,compile_cap_seconds=60,
        launches=launches,expected_optimize_calls=0,scope='Fixed-witness diagnosis; no production configuration change')
    write(DIAG/'identity.json',identity)
    lock=DIAG/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    records=[];compile_record=None;failure=None
    try:
        start=time.perf_counter()
        compile_timeout=False
        with (BUILD/'compile.log').open('w') as stream:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
            try:process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                compile_timeout=True
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                process.wait()
        compile_record=dict(returncode=process.returncode,whole_tree_timeout=compile_timeout,
            wall_seconds=time.perf_counter()-start,log_sha256=sha(BUILD/'compile.log'))
        write(DIAG/'compile.json',compile_record);assert process.returncode==0 and not compile_timeout
        identity['binary_sha256']=sha(exe);write(DIAG/'identity.json',identity)
        for launch in launches:
            dest=ROOT/launch['destination'];dest.mkdir(parents=True)
            write(dest/'launch.json',dict(launch,identity_sha256=sha(DIAG/'identity.json'),started_unix=time.time()))
            start=time.monotonic();watchdog=False
            with affinity.inherited_core() as binding:
                with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                    proc=subprocess.Popen(launch['command'],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                    child=affinity.read_masks(proc.pid);assert child['process_mask']==4
                    write(dest/'affinity.json',dict(binding=binding,child=child,child_pid=proc.pid))
                    try: code=proc.wait(timeout=max(.001,29.8-(time.monotonic()-start)))
                    except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;watchdog=True
            completion=dict(returncode=code,wall_seconds=time.monotonic()-start,watchdog=watchdog,restored=affinity.read_masks())
            write(dest/'completion.json',completion);record=dict(id=launch['id'],completion=completion,valid=False);records.append(record)
            write(DIAG/'summary.json',dict(compile=compile_record,records=records))
            assert code==0 and not watchdog and completion['wall_seconds']<=30 and completion['restored']==binding['before']
            for name in ['stdout.log','stderr.log']:assert 'Optimize a model' not in (dest/name).read_text(encoding='utf-8',errors='replace')
            record.update(valid=True,audit=replay(panel[launch['id']],dest,witnesses[launch['id']]))
            write(dest/'audit.json',record);write(DIAG/'summary.json',dict(compile=compile_record,records=records))
            print(json.dumps(record),flush=True)
    except Exception as error:
        failure=repr(error);raise
    finally:
        write(DIAG/'summary.json',dict(compile=compile_record,records=records,failure=failure,
            total_driver_wall_seconds=time.perf_counter()-driver_started,optimizer_calls=0))
        lock.unlink()

if __name__=='__main__':main()
