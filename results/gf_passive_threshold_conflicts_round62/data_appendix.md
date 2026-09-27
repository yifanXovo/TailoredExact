# Round 62 完整数据附录

由 `scripts/report_round62.py` 从逐启动 ledger 与已完成结果生成。未认证的墙钟数值是预算使用量，不能当作求解时间。
固定 F0 证书与完整原问题证书分开；所有配对的构建、预算、作用域必须一致。

## 预算

计费 72/72；完成 72；未完成 0；native micro 2/4；内部优化器调用 199。
失败 []；watchdog []；超预算 []。全部详细启动及命令见 processes.jsonl、budget.csv。

排除性能归因的已计费记录：[54]，原因见 run_exclusions.json；下表仍完整保留其原始结果。

## 全部固定区间及完整算法运行

| 编号 | 角色 | 阶段 | 配置 | cap/s | wall/s | 证书 | UB | LB | 绝对 gap | 相对 gap | Work | nodes |
|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 11 | D1 | full_easy | Single-off-off | 120 | 0.468 | original yes | 0 | 0 | 0 | 0 | 0.2564007 | 10 |
| 12 | D1 | full_easy | Single-passive-cert-off | 120 | 0.078 | original yes | 0 | 0 | 0 | 0 | 0 | 0 |
| 13 | D3 | full_screen | Single-off-off | 120 | 117.063 | original no | 0.04500155 | 0.038629881 | 0.0063716693 | 0.14158777 | 186.3603 | 11054 |
| 14 | D3 | full_screen | Single-passive-observe-off | 120 | 117.047 | original no | 0.04500155 | 0.038629881 | 0.0063716693 | 0.14158777 | 186.52568 | 11060 |
| 15 | D3 | full_screen | Single-passive-cert-off | 120 | 117.063 | original no | 0.04500155 | 0.038629881 | 0.0063716693 | 0.14158777 | 186.28099 | 11050 |
| 23 | D4 | mip_v2 | off | 120 | 89.812 | fixed yes | 0.50634331 | 0.50634331 | 3.1921121e-10 | 6.3042447e-10 | 140.87268 | 19132 |
| 24 | D4 | mip_v2 | events | 120 | 94.843 | fixed yes | 0.50634331 | 0.50634331 | 0 | 0 | 148.47928 | 19993 |
| 25 | D4 | mip_v2 | conflicts | 120 | 90.938 | fixed yes | 0.50634331 | 0.5063433 | 4.7796705e-09 | 9.4395847e-09 | 139.07161 | 21877 |
| 26 | D4 | mip_v2 | projection | 120 | 54.891 | fixed yes | 0.50634331 | 0.50634331 | 2.1165347e-09 | 4.1800389e-09 | 85.830947 | 16033 |
| 27 | D4 | mip_v2 | service | 120 | 118.079 | fixed no | 0.50642279 | 0.45272457 | 0.053698217 | 0.10603436 | 195.10712 | 12160 |
| 28 | D4 | mip_v2 | service-conflicts | 120 | 100.890 | fixed yes | 0.50634331 | 0.50634331 | 2.126068e-09 | 4.1988666e-09 | 157.49094 | 21041 |
| 29 | D4 | mip_v2 | projection-rlt | 120 | 57.109 | fixed yes | 0.50634331 | 0.5063433 | 3.8503836e-09 | 7.6042944e-09 | 90.814309 | 14835 |
| 30 | D3 | mip_v2 | off | 120 | 118.079 | fixed no | 0.04500155 | 0.038721095 | 0.0062804547 | 0.13956085 | 188.8516 | 11131 |
| 31 | D3 | mip_v2 | projection | 120 | 118.094 | fixed no | 0.056604476 | 0.037480971 | 0.019123505 | 0.33784439 | 200.06491 | 10208 |
| 32 | D6 | full_medium_v2 | Single-off-off | 120 | 117.218 | original no | 0.18859121 | 0.1382121 | 0.050379115 | 0.26713395 | 252.81099 | 602 |
| 33 | D6 | full_medium_v2 | Single-off-projection | 120 | 117.078 | original no | 0.18859121 | 0.1382121 | 0.050379115 | 0.26713395 | 253.08434 | 602 |
| 34 | D6 | full_medium_v2 | Single-passive-cert-projection | 120 | 117.078 | original no | 0.15724118 | 0.1382121 | 0.01902908 | 0.12101843 | 247.5405 | 598 |
| 37 | D4 | full_D4_v2 | Single-off-off | 120 | 89.953 | original yes | 0.50634331 | 0.50634331 | 3.1921121e-10 | 6.3042447e-10 | 140.98719 | 19132 |
| 38 | D4 | full_D4_v2 | Single-passive-cert-off | 120 | 90.047 | original yes | 0.50634331 | 0.50634331 | 3.1921121e-10 | 6.3042447e-10 | 140.98719 | 19132 |
| 39 | D4 | full_D4_v2 | Single-off-projection | 120 | 55.125 | original yes | 0.50634331 | 0.50634331 | 2.1165347e-09 | 4.1800389e-09 | 85.95303 | 16033 |
| 40 | D4 | full_D4_v2 | Single-passive-cert-projection | 120 | 55.156 | original yes | 0.50634331 | 0.50634331 | 2.1165347e-09 | 4.1800389e-09 | 85.95303 | 16033 |
| 41 | D3 | long_v2 | Single-off-off | 600 | 314.703 | original yes | 0.04500155 | 0.04500155 | 3.6819295e-10 | 8.1817837e-09 | 523.33821 | 26739 |
| 42 | D3 | long_v2 | Single-passive-cert-off | 600 | 315.172 | original yes | 0.04500155 | 0.04500155 | 3.6819295e-10 | 8.1817837e-09 | 523.33821 | 26739 |
| 43 | C2 | long_v2 | Single-off-off | 600 | 551.625 | original yes | 0.82996341 | 0.82996341 | 1.8873791e-15 | 2.274051e-15 | 1145.1514 | 46980 |
| 44 | C2 | long_v2 | Single-passive-cert-off | 600 | 552.360 | original yes | 0.82996341 | 0.82996341 | 1.8873791e-15 | 2.274051e-15 | 1145.1514 | 46980 |
| 45 | D7 | long_v2 | Single-off-off | 600 | 597.125 | original no | 0.37189401 | 0.19556943 | 0.17632458 | 0.4741259 | 1507.0808 | 448 |
| 46 | D7 | long_v2 | Single-passive-cert-off | 600 | 597.109 | original no | 0.28285622 | 0.19556943 | 0.087286796 | 0.30859069 | 1493.3907 | 447 |
| 47 | D3 | long_v2 | Single-off-projection | 600 | 460.515 | original yes | 0.04500155 | 0.04500155 | 1.8735014e-16 | 4.1631929e-15 | 853.12064 | 31036 |
| 48 | C2 | long_v2 | Single-off-projection | 600 | 457.750 | original yes | 0.82996341 | 0.82996341 | 1.5543122e-15 | 1.8727479e-15 | 926.60059 | 48773 |
| 49 | C2 | k1_v2 | K1-off-off | 600 | 597.109 | original no | 0.82996341 | 0.8224407 | 0.0075227126 | 0.0090639087 | 1229.3378 | 57146 |
| 50 | D4 | screen_v3 | off | 120 | 90.109 | fixed yes | 0.50634331 | 0.50634331 | 3.1921121e-10 | 6.3042447e-10 | 140.87268 | 19132 |
| 51 | D4 | screen_v3 | projection | 120 | 55.359 | fixed yes | 0.50634331 | 0.50634331 | 2.1165347e-09 | 4.1800389e-09 | 85.830947 | 16033 |
| 52 | D4 | screen_v3 | projection-service | 120 | 78.344 | fixed yes | 0.50634331 | 0.50634331 | 0 | 0 | 120.71928 | 18170 |
| 53 | D3 | screen_v3 | off | 600 | 315.110 | fixed yes | 0.04500155 | 0.04500155 | 3.6819295e-10 | 8.1817837e-09 | 523.26554 | 26739 |
| 54 | D3 | screen_v3 | projection-service | 600 | 310.016 | fixed yes | 0.04500155 | 0.04500155 | 6.9388939e-18 | 1.5419233e-16 | 523.59191 | 43922 |
| 57 | D3 | screen_v3 | projection-service | 600 | 307.422 | fixed yes | 0.04500155 | 0.04500155 | 6.9388939e-18 | 1.5419233e-16 | 523.59191 | 43922 |
| 58 | C2 | k1_v3 | K1-off-off | 600 | 597.250 | original no | 0.82996341 | 0.82225916 | 0.0077042496 | 0.0092826377 | 1227.7534 | 57004 |
| 59 | C2 | k1_v3 | K1-passive-cert-off | 600 | 597.109 | original no | 0.82996341 | 0.82217221 | 0.0077912005 | 0.0093874024 | 1226.4249 | 56879 |
| 60 | C2 | k1_v3 | K1-off-projection | 600 | 475.171 | original yes | 0.82996341 | 0.82996341 | 0 | 0 | 953.71645 | 43623 |
| 61 | C2 | k1_v3 | K1-passive-cert-projection | 600 | 476.828 | original yes | 0.82996341 | 0.82996341 | 0 | 0 | 953.71645 | 43623 |
| 62 | C2 | references_v3 | P-GRB | 600 | 597.079 | original no | 0.82996341 | 0.78651485 | 0.043448567 | 0.052349978 | 1170.493 | 83321 |
| 63 | C2 | references_v3 | K1-H | 600 | 526.219 | original yes | 0.82996341 | 0.8299634 | 1.022209e-08 | 1.2316313e-08 | 1069.6367 | 44826 |
| 65 | C1 | confirmation_v3 | K1-off-off | 600 | 386.421 | original yes | 0.26181696 | 0.26181696 | 9.5384167e-10 | 3.6431622e-09 | 729.94328 | 92805 |
| 66 | C1 | confirmation_v3 | K1-passive-cert-off | 600 | 386.859 | original yes | 0.26181696 | 0.26181696 | 9.5384167e-10 | 3.6431622e-09 | 729.94328 | 92805 |
| 67 | C1 | confirmation_v3 | K1-off-projection | 600 | 296.750 | original yes | 0.26181696 | 0.26181696 | 7.2164497e-16 | 2.7562957e-15 | 547.27551 | 63481 |
| 68 | C1 | confirmation_v3 | K1-passive-cert-projection | 600 | 296.640 | original yes | 0.26181696 | 0.26181696 | 7.2164497e-16 | 2.7562957e-15 | 547.27551 | 63481 |
| 69 | C3 | confirmation_v3 | K1-off-off | 600 | 597.078 | original no | 0.81799554 | 0.7194677 | 0.098527844 | 0.12045034 | 1340.5644 | 6249 |
| 70 | C3 | confirmation_v3 | K1-passive-cert-off | 600 | 597.078 | original no | 0.81799554 | 0.7194677 | 0.098527844 | 0.12045034 | 1341.6678 | 6256 |
| 71 | C3 | confirmation_v3 | K1-off-projection | 600 | 597.063 | original no | 0.82308552 | 0.71731132 | 0.1057742 | 0.12850937 | 1323.0308 | 7230 |
| 72 | C3 | confirmation_v3 | K1-passive-cert-projection | 600 | 597.078 | original no | 0.82308552 | 0.71731132 | 0.1057742 | 0.12850937 | 1323.9842 | 7232 |

## 同构建配对及冻结双门槛

证书增减单列；均认证时需要 10 秒及 10%；均未认证时需要绝对 gap 0.001 及 5%。负值表示回退。

| 角色 | 阶段 | 编号 | 对照 → 候选 | 判定 | 认证秒数节省 | 未认证绝对 gap 节省 |
|---|---|---|---|---|---:|---:|
| D1 | full_easy | 11→12 | Single-off-off → Single-passive-cert-off | below_time_threshold | 0.39 | — |
| D3 | full_screen | 13→14 | Single-off-off → Single-passive-observe-off | below_gap_threshold | — | 0 |
| D3 | full_screen | 13→15 | Single-off-off → Single-passive-cert-off | below_gap_threshold | — | 0 |
| D4 | mip_v2 | 23→24 | off → events | below_time_threshold | -5.031 | — |
| D4 | mip_v2 | 23→25 | off → conflicts | below_time_threshold | -1.126 | — |
| D4 | mip_v2 | 24→25 | events → conflicts | below_time_threshold | 3.905 | — |
| D4 | mip_v2 | 23→26 | off → projection | time_gain | 34.921 | — |
| D4 | mip_v2 | 23→27 | off → service | certificate_loss | — | — |
| D4 | mip_v2 | 23→28 | off → service-conflicts | time_loss | -11.078 | — |
| D4 | mip_v2 | 27→28 | service → service-conflicts | certificate_gain | — | — |
| D4 | mip_v2 | 23→29 | off → projection-rlt | time_gain | 32.703 | — |
| D4 | mip_v2 | 26→29 | projection → projection-rlt | below_time_threshold | -2.218 | — |
| D3 | mip_v2 | 30→31 | off → projection | gap_loss | — | -0.01284305 |
| D6 | full_medium_v2 | 32→33 | Single-off-off → Single-off-projection | below_gap_threshold | — | 0 |
| D6 | full_medium_v2 | 32→34 | Single-off-off → Single-passive-cert-projection | gap_gain | — | 0.031350034 |
| D6 | full_medium_v2 | 33→34 | Single-off-projection → Single-passive-cert-projection | gap_gain | — | 0.031350034 |
| D4 | full_D4_v2 | 37→38 | Single-off-off → Single-passive-cert-off | below_time_threshold | -0.094 | — |
| D4 | full_D4_v2 | 37→39 | Single-off-off → Single-off-projection | time_gain | 34.828 | — |
| D4 | full_D4_v2 | 37→40 | Single-off-off → Single-passive-cert-projection | time_gain | 34.797 | — |
| D4 | full_D4_v2 | 39→40 | Single-off-projection → Single-passive-cert-projection | below_time_threshold | -0.031 | — |
| D4 | full_D4_v2 | 38→40 | Single-passive-cert-off → Single-passive-cert-projection | time_gain | 34.891 | — |
| D3 | long_v2 | 41→42 | Single-off-off → Single-passive-cert-off | below_time_threshold | -0.469 | — |
| D3 | long_v2 | 41→47 | Single-off-off → Single-off-projection | time_loss | -145.812 | — |
| C2 | long_v2 | 43→44 | Single-off-off → Single-passive-cert-off | below_time_threshold | -0.735 | — |
| C2 | long_v2 | 43→48 | Single-off-off → Single-off-projection | time_gain | 93.875 | — |
| D7 | long_v2 | 45→46 | Single-off-off → Single-passive-cert-off | gap_gain | — | 0.089037787 |
| D4 | screen_v3 | 50→51 | off → projection | time_gain | 34.75 | — |
| D4 | screen_v3 | 50→52 | off → projection-service | time_gain | 11.765 | — |
| D4 | screen_v3 | 51→52 | projection → projection-service | time_loss | -22.985 | — |
| D3 | screen_v3 | 53→57 | off → projection-service | below_time_threshold | 7.688 | — |
| C2 | k1_v3 | 58→59 | K1-off-off → K1-passive-cert-off | below_gap_threshold | — | -8.6950871e-05 |
| C2 | k1_v3 | 58→60 | K1-off-off → K1-off-projection | certificate_gain | — | — |
| C2 | k1_v3 | 58→61 | K1-off-off → K1-passive-cert-projection | certificate_gain | — | — |
| C2 | k1_v3 | 60→61 | K1-off-projection → K1-passive-cert-projection | below_time_threshold | -1.657 | — |
| C2 | k1_v3 | 59→61 | K1-passive-cert-off → K1-passive-cert-projection | certificate_gain | — | — |
| C1 | confirmation_v3 | 65→66 | K1-off-off → K1-passive-cert-off | below_time_threshold | -0.438 | — |
| C1 | confirmation_v3 | 65→67 | K1-off-off → K1-off-projection | time_gain | 89.671 | — |
| C1 | confirmation_v3 | 65→68 | K1-off-off → K1-passive-cert-projection | time_gain | 89.781 | — |
| C1 | confirmation_v3 | 67→68 | K1-off-projection → K1-passive-cert-projection | below_time_threshold | 0.11 | — |
| C1 | confirmation_v3 | 66→68 | K1-passive-cert-off → K1-passive-cert-projection | time_gain | 90.219 | — |
| C3 | confirmation_v3 | 69→70 | K1-off-off → K1-passive-cert-off | below_gap_threshold | — | 0 |
| C3 | confirmation_v3 | 69→71 | K1-off-off → K1-off-projection | gap_loss | — | -0.0072463603 |
| C3 | confirmation_v3 | 69→72 | K1-off-off → K1-passive-cert-projection | gap_loss | — | -0.0072463603 |
| C3 | confirmation_v3 | 71→72 | K1-off-projection → K1-passive-cert-projection | below_gap_threshold | — | 0 |
| C3 | confirmation_v3 | 70→72 | K1-passive-cert-off → K1-passive-cert-projection | gap_loss | — | -0.0072463603 |
| C2 | references_v3 -> k1_v3 | 62→58 | P-GRB → K1-off-off | gap_gain | — | 0.035744317 |
| C2 | references_v3 -> k1_v3 | 62→59 | P-GRB → K1-passive-cert-off | gap_gain | — | 0.035657366 |
| C2 | references_v3 -> k1_v3 | 62→60 | P-GRB → K1-off-projection | certificate_gain | — | — |
| C2 | references_v3 -> k1_v3 | 62→61 | P-GRB → K1-passive-cert-projection | certificate_gain | — | — |
| C2 | references_v3 -> k1_v3 | 63→58 | K1-H → K1-off-off | certificate_loss | — | — |
| C2 | references_v3 -> k1_v3 | 63→59 | K1-H → K1-passive-cert-off | certificate_loss | — | — |
| C2 | references_v3 -> k1_v3 | 63→60 | K1-H → K1-off-projection | below_time_threshold | 51.048 | — |
| C2 | references_v3 -> k1_v3 | 63→61 | K1-H → K1-passive-cert-projection | below_time_threshold | 49.391 | — |
| C2 | references_v3 | 62→63 | P-GRB → K1-H | certificate_gain | — | — |

## 固定 F0 原生根处理及表示成本

| 编号 | 配置 | rows | cols | nonzeros | build/s | root LP | 根割后 bound | root Work | root/s |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 23 | D4 off | 4136 | 1404 | 19373 | 0.0308342 | 0.1078381 | 0.36524073 | 3.0705362 | 2.1166647 |
| 24 | D4 events | 4236 | 1440 | 19573 | 0.0386254 | 0.1088436 | 0.36098296 | 2.2854814 | 1.5394722 |
| 25 | D4 conflicts | 4268 | 1440 | 19701 | 0.0392044 | 0.1090024 | 0.36126673 | 2.1674117 | 1.5266448 |
| 26 | D4 projection | 4168 | 1404 | 19501 | 0.0377843 | 0.107838 | 0.36557772 | 2.7263809 | 1.9182676 |
| 27 | D4 service | 4344 | 1440 | 20005 | 0.0400711 | 0.1132938 | 0.3675775 | 2.9779571 | 2.0673806 |
| 28 | D4 service-conflicts | 4376 | 1440 | 20133 | 0.0396026 | 0.1132873 | 0.36534452 | 3.0220838 | 2.1024308 |
| 29 | D4 projection-rlt | 4232 | 1404 | 19949 | 0.0385745 | 0.107871 | 0.3667135 | 3.6318685 | 2.5939533 |
| 30 | D3 off | 4143 | 1406 | 20074 | 0.0356533 | 0.03081566 | 0.032479287 | 2.6768713 | 2.1180071 |
| 31 | D3 projection | 4175 | 1406 | 20202 | 0.0426095 | 0.03081566 | 0.032547066 | 2.5533771 | 2.1926383 |
| 50 | D4 off | 4136 | 1404 | 19373 | 0.0347062 | 0.1078381 | 0.36524073 | 3.0705362 | 2.1365186 |
| 51 | D4 projection | 4168 | 1404 | 19501 | 0.041302 | 0.107838 | 0.36557772 | 2.7263809 | 1.9222103 |
| 52 | D4 projection-service | 4168 | 1404 | 19757 | 0.0402219 | 0.1078365 | 0.36562108 | 2.6603666 | 1.8721441 |
| 53 | D3 off | 4143 | 1406 | 20074 | 0.0378274 | 0.03081566 | 0.032479287 | 2.6768713 | 2.1203908 |
| 54 | D3 projection-service | 4175 | 1406 | 20458 | 0.0448028 | 0.03081566 | 0.032185555 | 2.3864902 | 1.8542074 |
| 57 | D3 projection-service | 4175 | 1406 | 20458 | 0.0476894 | 0.03081566 | 0.032185555 | 2.3864902 | 1.859259 |

## 完整算法生命周期

| 编号 | 角色 / 配置 | 调用数 | 末叶数 | 分裂数 | PREFIX/s | 外部停止 | 外部证书 | native statuses |
|---:|---|---:|---:|---:|---:|---|---|---|
| 11 | D1 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 12 | D1 Single-passive-cert-off | 0 | 1 | 0 | 0.0343735 | True | True | no native optimize |
| 13 | D3 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 14 | D3 Single-passive-observe-off | 2 | 1 | 0 | 0.0433281 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 15 | D3 Single-passive-cert-off | 2 | 1 | 0 | 0.0444889 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 32 | D6 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 33 | D6 Single-off-projection | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 34 | D6 Single-passive-cert-projection | 2 | 1 | 0 | 2.9968955 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 37 | D4 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 38 | D4 Single-passive-cert-off | 2 | 1 | 0 | 0.0295549 | False | True | LP:OPTIMAL; MIP:OPTIMAL |
| 39 | D4 Single-off-projection | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 40 | D4 Single-passive-cert-projection | 2 | 1 | 0 | 0.0294249 | False | True | LP:OPTIMAL; MIP:OPTIMAL |
| 41 | D3 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 42 | D3 Single-passive-cert-off | 2 | 1 | 0 | 0.0432281 | False | True | LP:OPTIMAL; MIP:OPTIMAL |
| 43 | C2 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 44 | C2 Single-passive-cert-off | 2 | 1 | 0 | 0.0228903 | False | True | LP:OPTIMAL; MIP:OPTIMAL |
| 45 | D7 Single-off-off | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 46 | D7 Single-passive-cert-off | 2 | 1 | 0 | 4.2979488 | False | False | LP:OPTIMAL; MIP:TIME_LIMIT |
| 47 | D3 Single-off-projection | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 48 | C2 Single-off-projection | 2 | 1 | 0 | 0 | False | False | LP:OPTIMAL; MIP:OPTIMAL |
| 49 | C2 K1-off-off | 5 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; CHILD_BOUND_TARGET_MIP:INTERRUPTED; MIP:TIME_LIMIT |
| 58 | C2 K1-off-off | 5 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; CHILD_BOUND_TARGET_MIP:INTERRUPTED; MIP:TIME_LIMIT |
| 59 | C2 K1-passive-cert-off | 5 | 1 | 0 | 0.0238804 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; CHILD_BOUND_TARGET_MIP:INTERRUPTED; MIP:TIME_LIMIT |
| 60 | C2 K1-off-projection | 5 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; CHILD_BOUND_TARGET_MIP:INTERRUPTED; MIP:OPTIMAL |
| 61 | C2 K1-passive-cert-projection | 5 | 1 | 0 | 0.0232838 | False | True | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; CHILD_BOUND_TARGET_MIP:INTERRUPTED; MIP:OPTIMAL |
| 62 | C2 P-GRB | 1 | 0 | 0 | 0 | False | False | TIME_LIMIT |
| 63 | C2 K1-H | 7 | 2 | 1 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:INFEASIBLE; LP:OPTIMAL; LP:OPTIMAL; CHILD_BOUND_TARGET_MIP:INTERRUPTED; MIP:OPTIMAL |
| 65 | C1 K1-off-off | 4 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:OPTIMAL |
| 66 | C1 K1-passive-cert-off | 4 | 1 | 0 | 0.0935876 | False | True | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:OPTIMAL |
| 67 | C1 K1-off-projection | 4 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:OPTIMAL |
| 68 | C1 K1-passive-cert-projection | 4 | 1 | 0 | 0.0932289 | False | True | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:OPTIMAL |
| 69 | C3 K1-off-off | 4 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:TIME_LIMIT |
| 70 | C3 K1-passive-cert-off | 4 | 1 | 0 | 0.0321249 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:TIME_LIMIT |
| 71 | C3 K1-off-projection | 4 | 1 | 0 | 0 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:TIME_LIMIT |
| 72 | C3 K1-passive-cert-projection | 4 | 1 | 0 | 0.0321535 | False | False | LP:OPTIMAL; LP:OPTIMAL; LP:OPTIMAL; MIP:TIME_LIMIT |

原始的 native-target INTERRUPTED、TIME_LIMIT、OPTIMAL 分开保存；外部逻辑证书不重写这些状态。
LP 松弛及合法连续补全见 lp_comparison.csv、frozen_lp_completion.json；节点见 native_point_separation.json。
投影包含关系查询见 projection_containment_verification.json 和 projection_audit/；自动冲突与原路线独立复核见 proofs/、witnesses/ 及对应 verification 文件。


## 冻结面板

| 角色 | V | M | Q / Q向量 | T/s | lambda | pick/drop 秒 | 本轮角色 |
|---|---:|---:|---|---:|---:|---|---|
| D1 | 8 | 2 | [20,20] | 3600 | 0.15 | 60.0/60.0 | 开发/保护 |
| D3 | 12 | 3 | 30 | 2850 | 0.15 | 60/60 | 开发/保护 |
| D4 | 12 | 3 | 30 | 2400 | 0.15 | 60/60 | 开发/保护 |
| D6 | 30 | 3 | [30,30,30] | 18000 | 0.15 | 60.0/60.0 | 开发/保护 |
| D7 | 50 | 4 | [30,30,30,30] | 18000 | 0.15 | 60.0/60.0 | 开发/保护 |
| C2 | 20 | 2 | [30,30] | 1800 | 0.15 | 60.0/60.0 | 开发/保护 |
| C1 | 12 | 2 | [30,30] | 3600 | 0.15 | 60.0/60.0 | 未参与本轮选择的旧公开角色 |
| C3 | 30 | 3 | [30,30,30] | 1800 | 0.15 | 60.0/60.0 | 未参与本轮选择的旧公开角色 |

完整输入路径、SHA-256、manifest 来源和冻结规则见 protocol.json；D3 T=2850，D4 T=2400。
