"""Round158 serial outer accounting; historical dependencies are read only."""
from round153_common import *

OUT = ROOT/'results/unified_exact_round158'
OLD157 = ROOT/'results/unified_exact_round157'
BASE = '7f9f0d31ee6963e58c620b029469c90c2d92a6cc'
SCIENCE157 = '9889473a9b64c749ea8841bac1d38fec8be21d96'
TOTAL = 259200.

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round158'
    meter.LIMITS = dict(research=TOTAL, verification=TOTAL, native=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure();return meter.budget()

def run(label,seconds,script,args,kind='research'):
    configure();snapshot={}
    for source in sorted((ROOT/'scripts').glob('round158*.py')):
        digest=sha(source);dest=OUT/'engineering/source_bytes'/f'{digest}.txt'
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(source.read_bytes())
        snapshot[source.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',dict(UTC=utc(),files=snapshot,dependency_base=BASE))
    supervisor=meter.metered
    if float(seconds)>28800:
        from round158_supervisor import metered
        supervisor=metered
    rc=supervisor(label,kind,[PYTHON,'-B',ROOT/'scripts'/script,*args],float(seconds),float(seconds),cwd=ROOT)
    assert rc==0,(label,rc)

class Durable:
    """Persist a few complete integer events and honor a normal stop request.

    The request file is an explicit research interface, never a production
    timer-based mechanism. A supervisor watchdog remains a last resort.
    """
    def __init__(self,folder):
        self.folder=Path(folder);self.tick=time.perf_counter();self.events=[];self.errors=[];self.stopped=False;self.best=math.inf
    def observe(self,model,where):
        from round100_gurobi_runtime import gp
        try:
            if where==gp.GRB.Callback.MIPSOL:
                no=len(self.events);objective=model.cbGet(gp.GRB.Callback.MIPSOL_OBJ)
                if objective<self.best:
                    variables=model.getVars();values=model.cbGetSolution(variables)
                    dest=self.folder/'incumbent_best.json.gz'
                    save_gz(dest,dict(zip((v.VarName for v in variables),values)))
                    self.best=objective
                    write(self.folder/'incumbent_best.json',dict(UTC=utc(),seconds=time.perf_counter()-self.tick,
                        objective=objective,point=dest.name,SHA256=sha(dest)))
                if no<16:
                    variables=model.getVars();values=model.cbGetSolution(variables)
                    dest=self.folder/f'incumbent_{no:02d}.json.gz'
                    save_gz(dest,dict(zip((v.VarName for v in variables),values)))
                    self.events.append(dict(UTC=utc(),seconds=time.perf_counter()-self.tick,
                        objective=objective,point=dest.name,SHA256=sha(dest)))
                    write(self.folder/'incumbents.json',self.events)
            if (self.folder/'TERMINATE.json').exists():
                self.stopped=True;model.terminate()
        except BaseException as error:
            self.errors.append(dict(type=type(error).__name__,message=str(error)))
            write(self.folder/'callback_errors.json',self.errors);model.terminate()

if __name__=='__main__':
    if len(sys.argv)==1:print(json.dumps(budget(),indent=2))
    else:run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
