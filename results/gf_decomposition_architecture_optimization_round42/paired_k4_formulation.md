# Family B: paired K4 blocks

Let the frozen C6 quarters be `I1,I2,I3,I4`. Family B always creates the two
structurally adjacent blocks `(I1,I2)` and `(I3,I4)`. Each block is one
generalized `ST-K2-P-Core` model with the original quarter-width row packs. The
complete proof therefore has exactly two independent native integer jobs when
both blocks optimize, versus four or more terminal jobs in external C6 and one
job in full static K4.

The global cover is accepted only when both component geometries are exact and
gap-free. Its valid lower bound is the minimum component native bound. A
higher-G component may retain a verified route whose recomputed original
objective belongs to a lower-G component, so that component does not issue an
original-problem certificate in isolation. The complete union is strict only
when every native component closes exactly, the minimum native block bound
matches a verified original-space union objective, and the original verifier
passes. This is the same minimum-over-cover certificate semantics used by the
external C6 tree.

The required refinement applies the same exact common-row factoring uniformly
inside both blocks. Pairing and solve membership never depend on instance
outcomes or runtime information.
