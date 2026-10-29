"""Accepted bounded anonymous byte/member reader, retargeted to new carriers only."""
from round140_common import *
import inspect
import round138_public_read as old
from round140_delivery import INDEX,BANNED

def main():
    source=inspect.getsource(old.main).replace("own['round']==138","own['round']==140").replace('dict(round=138','dict(round=140')
    source=source.replace('Round138','Round140').replace('prior_R137_public_semantic_receipt_unchanged','prior_R137_R138_R139_receipts_unchanged')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,WORK=WORK,DEST=WORK/'restore/round140-public',INDEX=INDEX,BANNED=BANNED,
        budget=budget,read=read,write=write,sha=sha)
    exec(compile(source,__file__+'::accepted_finite_byte_reader','exec'),ns);ns['main']()

if __name__=='__main__':main()
