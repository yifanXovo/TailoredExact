from round101_common import *
if __name__=='__main__':
    roles=read(OUT/'development_inputs.json')['roles'];p=dict(roles[0]);p['cap_seconds']=120
    p['method_order']=['FLEET-SHADOW','FLEET-SUBMIT'];p['question']='Actual original-column MIPNODE proof/violation/submit and initial cost; not full performance admission.'
    write(OUT/'native_protocol01.json',dict(roles=[p],phase='fleet qualification',reference_billing='one_finite_batch',maximum_optimize_calls_per_arm=8))
