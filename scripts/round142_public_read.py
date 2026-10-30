"""Accepted bounded anonymous archive/member reader, limited to Round142."""
from round142_common import *
import inspect
import round138_public_read as old
from round142_delivery import INDEX,BANNED
configure()

def main():
    source=inspect.getsource(old.main).replace("own['round']==138","own['round']==142").replace('dict(round=138','dict(round=142')
    source=source.replace('Round138','Round142')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,WORK=WORK,DEST=WORK/'restore/round142-public',
        INDEX=INDEX,BANNED=BANNED,budget=budget,read=read,write=write,sha=sha)
    assert 'gurobipy' not in sys.modules
    exec(compile(source,__file__+'::bounded_byte_reader','exec'),ns);ns['main']()

if __name__=='__main__':main()
