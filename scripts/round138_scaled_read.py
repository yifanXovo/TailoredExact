"""Private V2 four-row transport adapter; all accepted V1 proof checks retained."""
from round138_common import *
import types
import round138_read as prior
from round138_repair import scaled_rows

class ArmModels(prior.ArmModels):
    def model_contract(self,root,p,path,arm):
        original=prior.ArmModels.model_contract
        run=types.FunctionType(original.__code__,dict(vars(prior),stock_rows=scaled_rows),
            closure=original.__closure__)
        fact,model=run(self,root,p,path,arm)
        fact['stock_RLT']['transport']='V2 exact positive power-of-two scaling for tiny nonzero slopes'
        return fact,model

def verify(launch,identity):
    run=types.FunctionType(prior.verify.__code__,dict(vars(prior),ArmModels=ArmModels))
    return run(launch,identity)
