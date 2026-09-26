\ Model round88_epigraph_B1_toy
\ LP format - for model browsing. Use MPS format to capture full model detail.
\ Signature: 0x1f34d5952daceab3
Minimize
  h_1_2
Subject To
 onehot_1: state_1_0 + state_1_1 = 1
 qsum_1: state_g_1_0 + state_g_1_1 - G = 0
 perspective_upper_1_0: - state_1_0 + state_g_1_0 <= 0
 perspective_upper_1_1: - state_1_1 + state_g_1_1 <= 0
 onehot_2: state_2_0 + state_2_1 = 1
 qsum_2: state_g_2_0 + state_g_2_1 - G = 0
 perspective_upper_2_0: - state_2_0 + state_g_2_0 <= 0
 perspective_upper_2_1: - state_2_1 + state_g_2_1 <= 0
Bounds
 state_1_0 = 0.5
 state_1_1 = 0.5
 state_2_0 = 0.5
 state_2_1 = 0.5
 state_g_1_0 = 0
 state_g_1_1 = 0.5
 state_g_2_0 = 0.5
 state_g_2_1 = 0
 G = 0.5
 h_1_2 <= 2
End
