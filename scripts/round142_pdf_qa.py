"""Reuse the accepted Poppler page render; inspect every new appendix page."""
from round142_common import *
from round142_analyze import require_idle
import round138_pdf_qa as old
import types
configure()

def render():
    require_idle()
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,budget=budget,read=read,write=write,sha=sha,environment=environment)
    types.FunctionType(old.render.__code__,ns,'render',old.render.__defaults__,old.render.__closure__)()

if __name__=='__main__':render()
