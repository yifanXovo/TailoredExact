# Mathematical K1-AMF gate

For the unchanged K1-AM child gains, `eta=min(g_L,g_R)`, `mu=(g_L+g_R)/2`, and `S_AM=eta*mu`. For each child, AMF computes equal-weight mean non-Gini domain contraction `phi_j`. It then uses `gtilde_L=g_L+phi_L max(g_R-g_L,0)`, its symmetric right counterpart, `eta_hat=min(gtilde_L,gtilde_R)`, and `S_AMF=mu*eta_hat`. The single decision is `S_AMF + epsilon_score >= 0.07915`.

Because each `phi_j` lies in `[0,1]`, `eta <= eta_hat <= max(g_L,g_R)` and `S_AMF >= S_AM`. Zero formulation credit or equal child gains reduces exactly to AM. This is a structural refinement gate, not a runtime predictor.
