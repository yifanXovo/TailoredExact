# Adaptive residual-mass gate

For finite complete child LP bounds, `G_p=max(U-B_p,epsilon_cert)`, clipped
gains are `g_j=clip((B_j-B_p)/G_p,0,1)`, `eta=min(g_L,g_R)`, and
`mu=(g_L+g_R)/2`. The score is `S_AM=eta*mu`. Equivalently,
`rho_I=min(1,tau/max(mu,epsilon_mass))` and the split tests
`S_AM>=tau` and `eta>=rho_I` agree up to the documented score tolerance.
The gate changes only split timing: below tau the existing native parent
target is `min(B_L,B_R)`, and without strict improvement exact parent closure
is retained. It launches no additional solve and is a structural proof-mass
gate, not a runtime predictor.
