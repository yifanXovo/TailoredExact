# Recorded tiny column use during the K35 continuation

This is a lightweight observation of saved running-phase records, not the
post-run independent arithmetic or primal readback. The serial Native
continuation remains active. No new optimization or numerical checker was
launched to make this observation.

At iteration152 (the153rd completed feedback step) of
K-35-U_bounded_remaining_v1, the saved usage record contains14 tracked
Round155-origin columns above the fixed1e-10 reporting threshold. Five
originate in bounded_deep_v1 and nine in bounded_remaining_v1. Their
recorded total weight is3.967706312819521e-09. Individual saved weights
range from1.3015914618248303e-10 to6.445603339705698e-10.
The observed iteration154 record again reports zero tracked use.
These observations do not establish zero use in every intervening or
future solve, and the later all-phase usage reconciliation is still pending.

The retained numerical RMP upper changed from.2873261633037888 to
.287326162801573, approximately5.02e-10 downward; the lower remained
.2828596948801708. This is not a material full-hull improvement at the
unchanged1e-4 study target. The actual saved RMP return has Status2 and
passes the inherited numerical qualification: mass.999999998770559,
negative mass8.172351452145745e-09, full marginal mismatch
1.7580486924880099e-09, original-row residual1.6738232184731183e-09
and true completion slack1.000002756070564e-08. These are numerical
qualification observations, not a rational primal certificate. Do not
upgrade the tiny upper change or tiny positive weights into a mathematical
improvement claim.

The saved full sparse primal allows the subsequent independent reader to
check this particular usage projection against the actual point. Its
observed evidence hashes are:

- iter000152/result.json:
  26c650ce5ccee47b0069544380fbe1e08eb59d65f5ebcacfbd237b77d907ba60
- iter000152/new_column_usage.json.gz:
  cecbd3b29d5e73f16f40105d0857d75e9eda35ed6b85949a546509474731d4b0
- iter000152/primal.json.gz:
  0eabe558f0dc67812f5d87ebf7b4b2218956cd9b1ffd4dfdb9336eeac681f5a8

Earlier matched-screen/deep-phase nonuse statements describe observations
within those completed phases. The final whole-branch account must include
this later tiny use of five older columns and must not claim that every
Round155 column remained below1e-10 in every later primal.
