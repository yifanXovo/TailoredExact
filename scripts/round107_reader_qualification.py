"""Zero-solver reader smoke on retained controls; no paired stage conclusion."""
from round107_common import *
import round107_reader as reader

def run(name):
    d=OUT/'reader_qualification'/name;d.mkdir(parents=True,exist_ok=False)
    ident=read(OUT/'development02/identity.json');checked=[]
    for launch in ident['launches'][:3]:
        folder=reader.portable(ROOT,launch['destination'])
        j=reader.journal(ROOT,launch['panel'],folder)
        ep=reader.endpoint(ROOT,launch,ident,folder,j)
        m=reader.mechanism(ROOT,launch,folder)
        checked.append(dict(number=launch['number'],arm=launch['arm'],journal_events=len(j['trace']),
            endpoint_checked=True,mechanism_events=len(m['events']),native_started=j['started'],
            layer='Retained superseded controls, engineering-only reader validation, no paired inference'))
    write(d/'result.json',dict(passed=True,checked=checked,reader_SHA=sha(ROOT/'scripts/round107_reader.py'),Optimize=0,IIS=0))
    print(json.dumps(dict(passed=True,retained_controls=len(checked),Optimize=0,IIS=0)))

if __name__=='__main__':run(sys.argv[1])
