\ Model round88_epigraph_B2_toy
\ LP format - for model browsing. Use MPS format to capture full model detail.
\ Signature: 0x5c1ab9bd61b53311
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
 otepi_rec_C_1_1: - state_1_0 + otepi_C_1_1 = 0
 otepi_rec_Q_1_1: - state_g_1_0 + otepi_Q_1_1 = 0
 otepi_rec_C_2_1: - state_2_0 + otepi_C_2_1 = 0
 otepi_rec_Q_2_1: - state_g_2_0 + otepi_Q_2_1 = 0
 otepi_u_pos_1_2_1: - otepi_C_1_1 + otepi_Q_1_1 + otepi_C_2_1 - otepi_Q_2_1
   + otepi_u_1_2_1 >= 0
 otepi_u_neg_1_2_1: otepi_C_1_1 - otepi_Q_1_1 - otepi_C_2_1 + otepi_Q_2_1
   + otepi_u_1_2_1 >= 0
 otepi_v_pos_1_2_1: - otepi_Q_1_1 + otepi_Q_2_1 + otepi_v_1_2_1 >= 0
 otepi_v_neg_1_2_1: otepi_Q_1_1 - otepi_Q_2_1 + otepi_v_1_2_1 >= 0
 otepi_sum_1_2: h_1_2 - otepi_u_1_2_1 - otepi_v_1_2_1 >= 0
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
