# Timing mechanism definition

The selected uniform rule is `old_C6_split AND Gamma_sum >= 0.012`, where
`Gamma_sum = (|I|[t-L_E]+ - |I-|[t-L-]+ - |I+|[t-L+]+)/M0`. The tolerance is
`epsilon_gamma = 1e-7/max(M0,1e-7)`. It uses K0=4, frontier-d2 lookahead,
all valid parent-scope envelope facets, no MIP starts, and midpoint locations.
The rule produced both split and retain actions on the frozen development and
complex atlases. No-adaptive remained an ineligible reference.
