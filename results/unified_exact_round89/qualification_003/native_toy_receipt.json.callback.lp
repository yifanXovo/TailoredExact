\ Model round89_native_B1_toy
\ LP format - for model browsing. Use MPS format to capture full model detail.
\ Signature: 0x42d63da67e370e96
Minimize
  h_1_2
Subject To
 R0: state_1_0 + state_1_1 + state_1_2 + state_1_3 + state_1_4 + state_1_5
   = 1
 R1: Y_1 - state_1_1 - 2 state_1_2 - 3 state_1_3 - 4 state_1_4
   - 5 state_1_5 = 0
 R2: - G + state_g_1_0 + state_g_1_1 + state_g_1_2 + state_g_1_3
   + state_g_1_4 + state_g_1_5 = 0
 R3: - Y_1 + r_1 = 0
 R4: state_2_0 + state_2_1 + state_2_2 + state_2_3 + state_2_4 + state_2_5
   = 1
 R5: Y_2 - state_2_1 - 2 state_2_2 - 3 state_2_3 - 4 state_2_4
   - 5 state_2_5 = 0
 R6: - G + state_g_2_0 + state_g_2_1 + state_g_2_2 + state_g_2_3
   + state_g_2_4 + state_g_2_5 = 0
 R7: - Y_2 + r_2 = 0
 R8: - r_1 + r_2 + h_1_2 >= 0
 R9: r_1 - r_2 + h_1_2 >= 0
Bounds
 G = 0
 Y_1 <= 5
 Y_2 <= 5
 r_1 <= 10
 r_2 <= 10
 h_1_2 <= 10
 state_1_1 = 0
 state_1_3 = 0
 state_1_5 = 0
 state_2_0 = 0
 state_2_2 = 0
 state_2_4 = 0
 state_g_1_0 = 0
 state_g_1_1 = 0
 state_g_1_2 = 0
 state_g_1_3 = 0
 state_g_1_4 = 0
 state_g_1_5 = 0
 state_g_2_0 = 0
 state_g_2_1 = 0
 state_g_2_2 = 0
 state_g_2_3 = 0
 state_g_2_4 = 0
 state_g_2_5 = 0
Binaries
 state_1_0 state_1_1 state_1_2 state_1_3 state_1_4 state_1_5 state_2_0
 state_2_1 state_2_2 state_2_3 state_2_4 state_2_5
Generals
 Y_1 Y_2
End
