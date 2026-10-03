"""Serial explicitly numbered arms; stop on the first failure, no retries."""
import sys
from round101_campaign import run
if __name__=='__main__':
    for number in map(int,sys.argv[2:]):run(sys.argv[1],number)
