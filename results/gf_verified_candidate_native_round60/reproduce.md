# Round 60 复现

Windows PowerShell，Gurobi 13.0.2 安装于 `D:/gurobi1302/win64`，MinGW UCRT64
位于 `D:/msys64/ucrt64`。以下命令均从仓库根目录运行；研究脚本检测已有成功
目录并跳过，不覆盖正式结果。

```powershell
cmake -S . -B build/round60-dev -G "MinGW Makefiles" `
  -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON `
  -DGUROBI_ROOT=D:/gurobi1302/win64
cmake --build build/round60-dev -j 4
ctest --test-dir build/round60-dev -j 4 --output-on-failure

D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py identity
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py fixed --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py hga --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py split --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py integration --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py partial-integration --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py product-route --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py product-time-relaxed --cap 60
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py long --cap 600
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py reference --cap 120
D:/msys64/ucrt64/bin/python.exe scripts/round60_research.py final-micro
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round60.py
```

`protocol.json` 必须在正式性能运行前存在；不要再次运行 `freeze` 覆盖它。
大体积模型、solver log 和逐变量快照留在忽略的 `local_raw/`；提交中的 compact
CSV/JSON 由最后一条命令从这些原始证据确定性生成。`processes.jsonl` 保存命令、
开始时间、二进制 hash 和计费序号，`budget_audit.json` 检查总进程数、原生微测
上限、看门狗和优化器并发。
