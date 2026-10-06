"""R105 configuration of the existing exclusive self-paid receipt recorder."""
import round104_common as inherited
from round104_common import ROOT, CMAKE, NINJA, PYTHON, sha, read, write, bindings, env
import sys
OUT = ROOT / 'results/unified_exact_round105'
BUILD = ROOT / 'build/research/round105-decomposition-v1'
inherited.OUT = OUT
inherited.BUILD = BUILD
receipt = inherited.receipt
if __name__ == '__main__':
    receipt(sys.argv[1],sys.argv[4:],float(sys.argv[2]),sys.argv[3]=='engineering')
