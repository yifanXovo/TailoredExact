"""One finite, zero-Optimize all-row audit of two completed production arms."""
from round98_start_audit import run
if __name__=='__main__':
    run('results/unified_exact_round98/revision01/raw/01_R97-C3_R3','revision_R3_starts')
    run('results/unified_exact_round98/revision01/raw/04_R97-C3_R2','revision_R2_starts')
