# Proof of the factory-domain child estimate

Let child interval `I=[L_I,U_I]` inherit a parent node whose LP relaxation was
solved optimally with objective `b_N`. Let the shared factory prove inventory
bounds `Y_i^- <= Y_i <= Y_i^+`. Define the minimum possible absolute target
deviation over that interval by

\[
e_i^- = \begin{cases}
1-Y_i^+/T_i,&Y_i^+<T_i,\\
Y_i^-/T_i-1,&Y_i^->T_i,\\
0,&Y_i^-\le T_i\le Y_i^+.
\end{cases}
\]

For every feasible original solution in `I`, its point also belongs to the
parent feasible region. Therefore its objective is at least `b_N`. Its Gini
value is at least `L_I`; the interval distance formula gives
`e_i(x) >= e_i^-` for every station. Since `w_i >= 0` and `lambda >= 0`,

\[
F(x)=G(x)+\lambda\sum_iw_ie_i(x)
\ge L_I+\lambda\sum_iw_ie_i^- = B_{domain}(I).
\]

Both lower bounds hold simultaneously, hence

\[
F(x)\ge \widehat B(I)=\max\{b_N,B_{domain}(I)\}.
\]

The implementation independently recomputes each piecewise deviation from the
factory inventory bounds and rejects nonfinite values, invalid targets or
weights, negative lambda, inconsistent domains, and estimates below the parent
relaxation. A factory domain marked infeasible is never converted to a large
numeric estimate: without a native contradiction it fails closed.
