# AMF exactness and termination

AMF reads bounds from the already-generated parent and midpoint-child canonical models after the existing K1-AM LP calls. It launches no LP or MIP. A rescue changes only the existing finite-child split/retain disposition; native-target, exact-parent closure, strict child infeasibility, atomic coverage replacement, and the external-tree certificate remain unchanged. Every split is a midpoint split of a finite interval, so the pre-existing finite tree/deadline termination argument applies. Invalid profiles receive zero credit and exactly reproduce AM.
