# Independent local same-objective floor review

**PASS within the explicitly declared continuous cross-section.** The revised
`mathematical_analysis.md` and `round144_offline.py::local_floor` fix the
selector-one masses to (1, 1/2, 0), retain the stated old Gini/product,
stock, TC/TC2 and endpoint-pair blocks, and append an independent p>=0 with
the same objective g+p to both old and RN models. This specification avoids
treating 5/12 as a floor for an unspecified larger domain.

The old point is feasible: Y=(1,1/2,0), tau=3/2, H=2 and
q=((0,g),(0,g),(g,0)) give J=2g. At g=1/3 and at g=5/12, every station's q
has mass g and satisfies both lower and upper unit-box product bounds.
H<=3J, the four displayed stock inequalities, TC and TC2 all hold.
The explicit endpoint pair couplings have the required marginals and attain
the same pairwise absolute differences. Independently recomputing these
checks with Fraction succeeds at both g values.

In RN, the first and third fixed selectors force v1=t and v3=0;
normalization forces v2=1-t. The second site's zero-state product is 2t-1.
Its lower bound 1/4 gives t>=5/8, and the middle one-state lower bound
1/4 gives t<=3/4. Thus v1>=v2>=v3 and the normalized absolute-difference
sum is exactly 2t. Consequently g>=2t/3>=5/12. The stated t=5/8 and
w=((0,5/8),(1/4,3/8),(5/8,0)) attain equality, satisfy all RN mass/product
bounds and normalization, and extend the retained old rows at g=5/12.
With p=0 this proves the RN optimum of the same objective is exactly 5/12.

At the old g=1/3 point, choosing p=1/12 satisfies that very scalar objective
floor. The Rank-PC right side is 5/4, whereas 3g=1; its violation is 1/4.
Therefore the structural row excludes an old-domain point satisfying the
matched RN objective floor in this declared cross-section. The independent
penalty variable is essential to this particular floor-feasible witness.

No integer-feasible point is needed for a comparison of these continuous
relaxation cross-sections. Equally, this is not an exact witness in complete
routing P, a claim of universal floor dominance, a proof of full-search
benefit, or a substitute for a decision-relevant paid-floor experiment.
Those limits are correctly explicit in the revised text and certificate.

The certificate function was read without running its file-writing entry.
Independent Fraction arithmetic alone checked the old points, the RN
attainment, the objective equality and the PC violation. No Optimize,
commercial Native load, build or large artifact read was performed.
