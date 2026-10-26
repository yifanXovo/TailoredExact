"""Explicit serial never-started arms; no retry after failure."""
from round103_campaign import run
import sys
if __name__=='__main__':
    for n in map(int,sys.argv[2:]):run(sys.argv[1],n)
