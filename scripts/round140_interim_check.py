"""Explicit nine-sealed-position subset of the final reader, before one new control."""
from round140_common import *
import types
import round140_delivery as delivery

def main():
    assert not budget()['unclosed']
    names=['qualification','primary','incremental']
    groups=[g for name in names for g in read(OUT/f'{name}_matrix.json')['groups']]
    assert len(groups)==9
    for g in groups:assert (Path(g['launch']['destination'])/'verification_closeout.json').exists()
    def scoped_write(path,value):
        if Path(path)==OUT/'local_semantic_check.json':
            value.update(interim=True,completed_matrices=names,
                not_covered='Registered attribution control; not yet run and not claimed complete')
            path=OUT/'qualification/interim_local_semantic.json'
        write(path,value)
    run=types.FunctionType(delivery.local_check.__code__,dict(vars(delivery),groups=lambda:groups,write=scoped_write))
    run()

if __name__=='__main__':main()
