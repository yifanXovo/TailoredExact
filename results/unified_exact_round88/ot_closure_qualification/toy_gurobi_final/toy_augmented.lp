\ Model round88_ot_closure_toy
\ LP format - for model browsing. Use MPS format to capture full model detail.
\ Signature: 0xd56a2af40e4defcd
Minimize
  0 state_g_1_0 + 0 state_1_1 + 0 state_g_1_1 + 0 state_g_2_0 + 0 state_2_1
   + 0 state_g_2_1 + h_1_2
Subject To
 toy_ot_b1: - state_1_0 + state_2_0 + h_1_2 >= 0
Bounds
 state_1_0 = 1
 state_g_1_0 = 0.5
 state_1_1 = 0
 state_g_1_1 = 0
 state_2_0 = 0
 state_g_2_0 = 0
 state_2_1 = 1
 state_g_2_1 = 0.5
End
