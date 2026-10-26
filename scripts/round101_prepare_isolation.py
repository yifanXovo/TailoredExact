"""Pre-register one complete four-mode role; P and root execution diagnosis added explicitly."""
from round101_common import *
if __name__=='__main__':
    p=dict(read(OUT/'development_inputs.json')['roles'][0]);p['cap_seconds']=1200
    p['method_order']=['ENS-C','FLEET-SHELL','FLEET-SHADOW','FLEET-SUBMIT','FLEET-ROOT','P-GRB']
    p['question']='Nonzero complete certification protection; OFF/SHELL shared PreCrush effect, SHELL/SHADOW separation, SHADOW/SUBMIT net native effect; root/tree execution diagnosis if tree regresses. P is main benchmark.'
    write(OUT/'isolation_protocol01.json',dict(roles=[p],phase='fleet isolation',reference_billing='one_finite_batch',
        maximum_optimize_calls_per_arm=8,source_stage='postqualification cost revision; no change in finite mathematical rows on four saved raw points',
        ordering='Declared once. Root arm is a distinct execution strength and remains development, not an independent confirmation.'))
