# Station-state projection mapping

| Direction | Original quantities | Extended assignment | Preserved relation |
|---|---|---|---|
| original to VD-P | integer (Y_i=y^*), (G), (Z_i=GY_i) | (s_{iy^*}=1), (q_{iy^*}=G); all others zero | selector, inventory, G, product |
| VD-P to original | unique selected (y^*) | project (Y_i=y^*), (G=\sum q), (Z_i=\sum yq) | (Z_i=GY_i) |
| original optimum to VD-J | above plus (r_i=Y_i/D_i), minimum (e_i) | same state assignment | exact ratio and absolute penalty |
| VD-J to original | unique selected (y^*) | project original variables | same decision feasibility and optimum |

The old product-only bit and (G\)-times-bit variables are absent in VD-P and
VD-J.  Original variables needed outside that product block remain and are
linked exactly.  Unreachable values are absent because selectors are created
only for the propagated domain.  No size-dependent representation is chosen.
