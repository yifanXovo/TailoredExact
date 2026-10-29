"""Use the accepted bounded anonymous byte/member reader for new carriers only."""
from round139_common import *
import inspect
import round138_public_read as old
from round139_delivery import INDEX,BANNED

def main():
    source=inspect.getsource(old.main)
    source=source.replace("own['round']==138","own['round']==139").replace('dict(round=138','dict(round=139')
    source=source.replace('Round138','Round139').replace('prior_R137_public_semantic_receipt_unchanged','prior_R137_R138_receipts_unchanged')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,WORK=WORK,DEST=WORK/'restore/round139-public',INDEX=INDEX,BANNED=BANNED,
        budget=budget,read=read,write=write,sha=sha)
    exec(compile(source,__file__+'::accepted_finite_byte_reader','exec'),ns);ns['main']()

if __name__=='__main__':main()
