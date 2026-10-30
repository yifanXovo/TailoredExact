"""Rebind the accepted bounded nonexperimental child clock to this round."""
from round142_common import *
import round141_ordinary as old
import types
configure()

if __name__=='__main__':
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,budget=budget,environment=environment,read=read,write=write)
    types.FunctionType(old.main.__code__,ns,'main',old.main.__defaults__,old.main.__closure__)()
