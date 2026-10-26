25 个只使用合成字典、模型和微型日志的有限检查通过，exit 0。审查绑定当前 reader SHA `61e5acec734139d82c984a457f620a991664500f45d5ac6078cad7e96642e5d9`。

终端 native log 的最终 bound 仅在同 call、leaf、model SHA、log path 和成功返回全部匹配后，在返回序列起可用。字节相同但不同调用日志路径、缺少/失败的返回和未来证据均拒绝。原共享行模式可只用 Bounds 编码 G 区间；改变 Bounds、objective cutoff、true-G cap/floor 仍拒绝。局部 bound 大于 cutoff 时只提供 min(bound, cutoff) 的无条件证据，保留原始发布 L 和 signed gap。

实际 33 个 native 调用的日志、模型和返回路径另由独立 raw 审计通过；此有限测试没有读取真实输入或实际模型，也没有加载 solver。最初合成 harness 漏掉 re 名字空间的失败源码/回执保留，修正后未改任何生产或性能证据。
