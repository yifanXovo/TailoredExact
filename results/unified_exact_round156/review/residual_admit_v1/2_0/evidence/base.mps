* Signature: 0xc87ca1f2b49133b1
NAME 
ROWS
 N  OBJ
 E  onehot_1
 E  inventory_1
 E  ratio_1 
 E  product_mass_1
 G  product_lx_1_0
 L  product_ux_1_0
 G  product_Su_1_0
 L  product_Sl_1_0
 G  product_lx_1_1
 L  product_ux_1_1
 G  product_Su_1_1
 L  product_Sl_1_1
 G  product_lx_1_2
 L  product_ux_1_2
 G  product_Su_1_2
 L  product_Sl_1_2
 E  onehot_2
 E  inventory_2
 E  ratio_2 
 E  product_mass_2
 G  product_lx_2_0
 L  product_ux_2_0
 G  product_Su_2_0
 L  product_Sl_2_0
 G  product_lx_2_1
 L  product_ux_2_1
 G  product_Su_2_1
 L  product_Sl_2_1
 G  product_lx_2_2
 L  product_ux_2_2
 G  product_Su_2_2
 L  product_Sl_2_2
 E  denominator
 G  hard_lower
 L  hard_upper
 G  abs_p_1_2
 G  abs_m_1_2
 L  physical_G_upper_outward
 G  total_product_lower
 L  total_product_upper
 G  conditional_Sx_lower_1_0
 L  conditional_Sx_upper_1_0
 G  conditional_complement_lower_1_0
 L  conditional_complement_upper_1_0
 G  conditional_Sx_lower_1_1
 L  conditional_Sx_upper_1_1
 G  conditional_complement_lower_1_1
 L  conditional_complement_upper_1_1
 G  conditional_Sx_lower_1_2
 L  conditional_Sx_upper_1_2
 G  conditional_complement_lower_1_2
 L  conditional_complement_upper_1_2
 G  conditional_Sx_lower_2_0
 L  conditional_Sx_upper_2_0
 G  conditional_complement_lower_2_0
 L  conditional_complement_upper_2_0
 G  conditional_Sx_lower_2_1
 L  conditional_Sx_upper_2_1
 G  conditional_complement_lower_2_1
 L  conditional_complement_upper_2_1
 G  conditional_Sx_lower_2_2
 L  conditional_Sx_upper_2_2
 G  conditional_complement_lower_2_2
 L  conditional_complement_upper_2_2
 E  hard_cost_D_definition
 E  hard_cost_W_definition
 G  tight_DP_cost_product_ll
 G  tight_DP_cost_product_uu
 L  tight_DP_cost_product_ul
 L  tight_DP_cost_product_lu
 G  floor_residual
 G  G_residual
COLUMNS
    MARKER    'MARKER'                 'INTORG'
    x[1,0]    onehot_1  1
    x[1,0]    product_lx_1_0  -0.5
    x[1,0]    product_ux_1_0  -2.5
    x[1,0]    product_Su_1_0  -2.5
    x[1,0]    product_Sl_1_0  -0.5
    x[1,0]    conditional_Sx_lower_1_0  -0.5
    x[1,0]    conditional_Sx_upper_1_0  -1
    x[1,0]    conditional_complement_lower_1_0  1
    x[1,0]    conditional_complement_upper_1_0  2.5
    x[1,1]    onehot_1  1
    x[1,1]    inventory_1  -1
    x[1,1]    product_lx_1_1  -0.5
    x[1,1]    product_ux_1_1  -2.5
    x[1,1]    product_Su_1_1  -2.5
    x[1,1]    product_Sl_1_1  -0.5
    x[1,1]    conditional_Sx_lower_1_1  -1
    x[1,1]    conditional_Sx_upper_1_1  -2
    x[1,1]    conditional_complement_lower_1_1  0.5
    x[1,1]    conditional_complement_upper_1_1  2.5
    x[1,2]    onehot_1  1
    x[1,2]    inventory_1  -2
    x[1,2]    product_lx_1_2  -0.5
    x[1,2]    product_ux_1_2  -2.5
    x[1,2]    product_Su_1_2  -2.5
    x[1,2]    product_Sl_1_2  -0.5
    x[1,2]    conditional_Sx_lower_1_2  -2
    x[1,2]    conditional_Sx_upper_1_2  -2.5
    x[1,2]    conditional_complement_lower_1_2  0.5
    x[1,2]    conditional_complement_upper_1_2  2
    x[2,0]    onehot_2  1
    x[2,0]    product_lx_2_0  -0.5
    x[2,0]    product_ux_2_0  -2.5
    x[2,0]    product_Su_2_0  -2.5
    x[2,0]    product_Sl_2_0  -0.5
    x[2,0]    conditional_Sx_lower_2_0  -1
    x[2,0]    conditional_Sx_upper_2_0  -2
    x[2,0]    conditional_complement_lower_2_0  0.5
    x[2,0]    conditional_complement_upper_2_0  2.5
    x[2,0]    hard_cost_D_definition  -0.02125
    x[2,1]    onehot_2  1
    x[2,1]    inventory_2  -1
    x[2,1]    product_lx_2_1  -0.5
    x[2,1]    product_ux_2_1  -2.5
    x[2,1]    product_Su_2_1  -2.5
    x[2,1]    product_Sl_2_1  -0.5
    x[2,1]    conditional_Sx_lower_2_1  -0.5
    x[2,1]    conditional_Sx_upper_2_1  -2.5
    x[2,1]    conditional_complement_lower_2_1  0.5
    x[2,1]    conditional_complement_upper_2_1  2.5
    x[2,2]    onehot_2  1
    x[2,2]    inventory_2  -2
    x[2,2]    product_lx_2_2  -0.5
    x[2,2]    product_ux_2_2  -2.5
    x[2,2]    product_Su_2_2  -2.5
    x[2,2]    product_Sl_2_2  -0.5
    x[2,2]    conditional_Sx_lower_2_2  -1
    x[2,2]    conditional_Sx_upper_2_2  -2
    x[2,2]    conditional_complement_lower_2_2  0.5
    x[2,2]    conditional_complement_upper_2_2  2.5
    x[2,2]    hard_cost_D_definition  0.02125
    MARKER    'MARKER'                 'INTEND'
    Sx[1,0]   product_mass_1  1
    Sx[1,0]   product_lx_1_0  1
    Sx[1,0]   product_ux_1_0  1
    Sx[1,0]   product_Su_1_0  1
    Sx[1,0]   product_Sl_1_0  1
    Sx[1,0]   conditional_Sx_lower_1_0  1
    Sx[1,0]   conditional_Sx_upper_1_0  1
    Sx[1,0]   conditional_complement_lower_1_0  -1
    Sx[1,0]   conditional_complement_upper_1_0  -1
    Sx[1,1]   product_mass_1  1
    Sx[1,1]   product_lx_1_1  1
    Sx[1,1]   product_ux_1_1  1
    Sx[1,1]   product_Su_1_1  1
    Sx[1,1]   product_Sl_1_1  1
    Sx[1,1]   total_product_lower  1
    Sx[1,1]   total_product_upper  1
    Sx[1,1]   conditional_Sx_lower_1_1  1
    Sx[1,1]   conditional_Sx_upper_1_1  1
    Sx[1,1]   conditional_complement_lower_1_1  -1
    Sx[1,1]   conditional_complement_upper_1_1  -1
    Sx[1,2]   product_mass_1  1
    Sx[1,2]   product_lx_1_2  1
    Sx[1,2]   product_ux_1_2  1
    Sx[1,2]   product_Su_1_2  1
    Sx[1,2]   product_Sl_1_2  1
    Sx[1,2]   total_product_lower  2
    Sx[1,2]   total_product_upper  2
    Sx[1,2]   conditional_Sx_lower_1_2  1
    Sx[1,2]   conditional_Sx_upper_1_2  1
    Sx[1,2]   conditional_complement_lower_1_2  -1
    Sx[1,2]   conditional_complement_upper_1_2  -1
    Sx[2,0]   product_mass_2  1
    Sx[2,0]   product_lx_2_0  1
    Sx[2,0]   product_ux_2_0  1
    Sx[2,0]   product_Su_2_0  1
    Sx[2,0]   product_Sl_2_0  1
    Sx[2,0]   conditional_Sx_lower_2_0  1
    Sx[2,0]   conditional_Sx_upper_2_0  1
    Sx[2,0]   conditional_complement_lower_2_0  -1
    Sx[2,0]   conditional_complement_upper_2_0  -1
    Sx[2,0]   hard_cost_W_definition  -0.02125
    Sx[2,0]   floor_residual  -0.02125
    Sx[2,0]   G_residual  -0.02125
    Sx[2,1]   product_mass_2  1
    Sx[2,1]   product_lx_2_1  1
    Sx[2,1]   product_ux_2_1  1
    Sx[2,1]   product_Su_2_1  1
    Sx[2,1]   product_Sl_2_1  1
    Sx[2,1]   total_product_lower  1
    Sx[2,1]   total_product_upper  1
    Sx[2,1]   conditional_Sx_lower_2_1  1
    Sx[2,1]   conditional_Sx_upper_2_1  1
    Sx[2,1]   conditional_complement_lower_2_1  -1
    Sx[2,1]   conditional_complement_upper_2_1  -1
    Sx[2,2]   product_mass_2  1
    Sx[2,2]   product_lx_2_2  1
    Sx[2,2]   product_ux_2_2  1
    Sx[2,2]   product_Su_2_2  1
    Sx[2,2]   product_Sl_2_2  1
    Sx[2,2]   total_product_lower  2
    Sx[2,2]   total_product_upper  2
    Sx[2,2]   conditional_Sx_lower_2_2  1
    Sx[2,2]   conditional_Sx_upper_2_2  1
    Sx[2,2]   conditional_complement_lower_2_2  -1
    Sx[2,2]   conditional_complement_upper_2_2  -1
    Sx[2,2]   hard_cost_W_definition  0.02125
    Sx[2,2]   floor_residual  0.02125
    Sx[2,2]   G_residual  0.02125
    S         product_mass_1  -1
    S         product_Su_1_0  -1
    S         product_Sl_1_0  -1
    S         product_Su_1_1  -1
    S         product_Sl_1_1  -1
    S         product_Su_1_2  -1
    S         product_Sl_1_2  -1
    S         product_mass_2  -1
    S         product_Su_2_0  -1
    S         product_Sl_2_0  -1
    S         product_Su_2_1  -1
    S         product_Sl_2_1  -1
    S         product_Su_2_2  -1
    S         product_Sl_2_2  -1
    S         denominator  1
    S         physical_G_upper_outward  -2
    S         total_product_lower  -1
    S         total_product_upper  -3
    S         conditional_complement_lower_1_0  1
    S         conditional_complement_upper_1_0  1
    S         conditional_complement_lower_1_1  1
    S         conditional_complement_upper_1_1  1
    S         conditional_complement_lower_1_2  1
    S         conditional_complement_upper_1_2  1
    S         conditional_complement_lower_2_0  1
    S         conditional_complement_upper_2_0  1
    S         conditional_complement_lower_2_1  1
    S         conditional_complement_upper_2_1  1
    S         conditional_complement_lower_2_2  1
    S         conditional_complement_upper_2_2  1
    S         tight_DP_cost_product_ll  0.02125
    S         tight_DP_cost_product_uu  -0.02125
    S         tight_DP_cost_product_ul  0.02125
    S         tight_DP_cost_product_lu  -0.02125
    S         floor_residual  -2.6250000000000055e-02
    S         G_residual  -2.6250000000000055e-02
    Y[1]      inventory_1  1
    Y[1]      ratio_1   -1
    Y[1]      hard_lower  1
    Y[1]      hard_upper  1
    Y[2]      inventory_2  1
    Y[2]      ratio_2   -0.5
    Y[2]      hard_lower  1
    Y[2]      hard_upper  1
    r[1]      ratio_1   1
    r[1]      denominator  -1
    r[1]      abs_p_1_2  -1
    r[1]      abs_m_1_2  1
    r[2]      ratio_2   1
    r[2]      denominator  -1
    r[2]      abs_p_1_2  1
    r[2]      abs_m_1_2  -1
    abs[1,2]  abs_p_1_2  1
    abs[1,2]  abs_m_1_2  1
    abs[1,2]  physical_G_upper_outward  1
    abs[1,2]  G_residual  -0.125
    residual_scaled  OBJ       1
    residual_scaled  floor_residual  1
    residual_scaled  G_residual  1
    hard_cost_D  hard_cost_D_definition  1
    hard_cost_D  tight_DP_cost_product_ll  -0.5
    hard_cost_D  tight_DP_cost_product_uu  -2.5
    hard_cost_D  tight_DP_cost_product_ul  -2.5
    hard_cost_D  tight_DP_cost_product_lu  -0.5
    hard_cost_W  hard_cost_W_definition  1
    hard_cost_W  tight_DP_cost_product_ll  1
    hard_cost_W  tight_DP_cost_product_uu  1
    hard_cost_W  tight_DP_cost_product_ul  1
    hard_cost_W  tight_DP_cost_product_lu  1
RHS
    RHS1      onehot_1  1
    RHS1      product_Su_1_0  -2.5
    RHS1      product_Sl_1_0  -0.5
    RHS1      product_Su_1_1  -2.5
    RHS1      product_Sl_1_1  -0.5
    RHS1      product_Su_1_2  -2.5
    RHS1      product_Sl_1_2  -0.5
    RHS1      onehot_2  1
    RHS1      product_Su_2_0  -2.5
    RHS1      product_Sl_2_0  -0.5
    RHS1      product_Su_2_1  -2.5
    RHS1      product_Sl_2_1  -0.5
    RHS1      product_Su_2_2  -2.5
    RHS1      product_Sl_2_2  -0.5
    RHS1      hard_lower  1
    RHS1      hard_upper  3
    RHS1      conditional_complement_lower_1_0  1
    RHS1      conditional_complement_upper_1_0  2.5
    RHS1      conditional_complement_lower_1_1  0.5
    RHS1      conditional_complement_upper_1_1  2.5
    RHS1      conditional_complement_lower_1_2  0.5
    RHS1      conditional_complement_upper_1_2  2
    RHS1      conditional_complement_lower_2_0  0.5
    RHS1      conditional_complement_upper_2_0  2.5
    RHS1      conditional_complement_lower_2_1  0.5
    RHS1      conditional_complement_upper_2_1  2.5
    RHS1      conditional_complement_lower_2_2  0.5
    RHS1      conditional_complement_upper_2_2  2.5
    RHS1      tight_DP_cost_product_ll  0.010625
    RHS1      tight_DP_cost_product_uu  -5.3125000000000006e-02
    RHS1      tight_DP_cost_product_ul  5.3125000000000006e-02
    RHS1      tight_DP_cost_product_lu  -0.010625
BOUNDS
 BV BND1      x[1,0]  
 BV BND1      x[1,1]  
 BV BND1      x[1,2]  
 BV BND1      x[2,0]  
 BV BND1      x[2,1]  
 BV BND1      x[2,2]  
 UP BND1      Sx[1,0]   2.5
 UP BND1      Sx[1,1]   2.5
 UP BND1      Sx[1,2]   2.5
 UP BND1      Sx[2,0]   2.5
 UP BND1      Sx[2,1]   2.5
 UP BND1      Sx[2,2]   2.5
 LO BND1      S         0.5
 UP BND1      S         2.5
 FR BND1      residual_scaled
 LO BND1      hard_cost_D  -0.02125
 UP BND1      hard_cost_D  0.02125
 FR BND1      hard_cost_W
ENDATA
