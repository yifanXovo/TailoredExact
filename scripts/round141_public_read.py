"""Accepted finite anonymous reader, bound only to Round141's new carriers."""
from round141_common import *
import inspect
import round138_public_read as old
from round141_delivery import INDEX,BANNED

def main():
    source=inspect.getsource(old.main).replace("own['round']==138","own['round']==141").replace('dict(round=138','dict(round=141')
    source=source.replace('Round138','Round141').replace('prior_R137_public_semantic_receipt_unchanged','prior_R137_R138_R139_R140_receipts_unchanged')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,WORK=WORK,DEST=WORK/'restore/round141-public',
        INDEX=INDEX,BANNED=BANNED,budget=budget,read=read,write=write,sha=sha)
    assert 'gurobipy' not in sys.modules
    exec(compile(source,__file__+'::accepted_bounded_byte_reader','exec'),ns);ns['main']()

if __name__=='__main__':main()
