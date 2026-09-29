# Frozen finite route-order OFF/ON/P comparison — v1

Completed 9/12 arms; process cost 18258.671 s. Certified: {'P-GRB': 0, 'ENS-C': 1, 'ORDER-ON': 1}.

Every predeclared role is retained. A blank endpoint means uncompleted. Censored times are costs, not certificate times.

|Role|Arm|State|U|L|Absolute gap|Process seconds|
|---|---|---|---:|---:|---:|---:|
|F5|ENS-C|right_censored|0.3295041072|0.2814538063|0.04805030083|3597.25|
|F5|P-GRB|right_censored|0.4342358368|0.2682505969|0.1659852398|3597.172|
|F5|ORDER-ON|right_censored|0.320512227|0.2815237008|0.03898852627|3597.203|
|F2|ORDER-ON|certified|0.8659435203|0.8659435203|3.330669074e-16|587.984|
|F2|P-GRB|right_censored|0.8659435203|0.7559931056|0.1099504148|897.172|
|F2|ENS-C|certified|0.8659435203|0.8659435203|3.330669074e-16|590.359|
|V1|P-GRB|right_censored|0.1844137896|0.1524019912|0.03201179847|1797.234|
|V1|ORDER-ON|right_censored|0.179404638|0.1535547475|0.02584989049|1797.172|
|V1|ENS-C|right_censored|0.1715512347|0.1534048797|0.01814635496|1797.125|
|V2|ENS-C|not_completed|||||
|V2|ORDER-ON|not_completed|||||
|V2|P-GRB|not_completed|||||

Full numeric pairs and relative gaps: `pairs.csv` and `arms.csv`.

This evidence does not combine another arm's witness or lower bound into a certificate. Both-censored final-time ranking remains unknown.
