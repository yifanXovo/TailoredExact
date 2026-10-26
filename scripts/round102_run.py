"""Exclusive billed/engineering process receipt wrapper; no implicit retry."""
from round102_common import *
import argparse
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--cap',type=int,default=300);p.add_argument('--calls',type=int,default=0);p.add_argument('--engineering',action='store_true');p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args();cmd=a.command
    if cmd and cmd[0]=='--':cmd=cmd[1:]
    receipt(a.label,cmd,a.cap,a.calls,a.engineering)
