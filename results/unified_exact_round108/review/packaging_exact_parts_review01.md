包装修正版独立审查 ACCEPT，候选源码 `c35f285d76dbfba1ca16e4d73bd670de603b868337095b563eeda3e0f5786ce3`。此结论仅接受分片/恢复实现和有限测试；实际全量重新打包、公共导出/恢复及独立全部 21 臂数学重建仍须执行。

第一次实际 150,926,168 字节压缩包超过严格 95 MiB 门槛，其源码/命令/exit1/67.6488424 工程秒/原始输出保留；本次独立重哈希原 local combined SHA `135ecdc4769cc9c8beaa237a9eb42778ce243e91e73e96ef45ab33e46e2c1556`，并绑定 79,111 项精确 member manifest。现只有 actual>=95MiB 才分为90MiB连续压缩字节片，不按片重压缩，不移除任何 raw member；小包不拆。公共导出只含manifest和验证后的逻辑blob列表，不复制超限combined文件。

首个分片候选 62333f… 的实际小反例曾接受 `reference/../../outside.txt`，错误声称public-only；独立 probe exit1/HOLD、完整源码/命令/回执保留。当前修正以 lexical==resolved/plain/no-symlink/root-containment 阻止 package/manifest/依赖/目标逃逸，依赖 SHA/size/唯一性在解包前验证；实际执行源码必须是公共根脚本且匹配manifest，恢复reader也核SHA。该旧反例现已实际拒绝。

49 个实际小合成 API 案例全部通过（9接受/40拒绝），exit0，5.611692000 工程秒，checks `f41395c1f726fc9d203271f61f18f52c7a00349fa6be499d4af67a7d858051a8`。成功路径真正split/export并从public脚本副本执行fresh restore，combined/member/CRLF字节精确恢复；unsplit成功。拒绝覆盖阈值/小包人工拆片、missing/extras/index/reorder/path/gap/overlap/size/per-part/whole SHA、已存在目标、public缺片时不回退原fixture、source/reader身份、member缺失/多余/重复/链接/逃逸与依赖路径/hash/size。3个实际OS链接（part/依赖/package目录）被候选拒绝并已清理。CLI95/90常量未调，只有测试API使用小值。

重新核对 205 生产源和20冻结helpers全SHA未变；主reader52cad…、decision9a827…、standalone47cb…及原封存本地final review70fa…字节未变。无solver/native/compiler/生产/性能helper/decision规则改变或重跑。新独立包装记录可入carrier，原科学审查不重写。随后全量恢复应使用真实新public根和恢复根，仅从拟公开文件及精确公共依赖执行；当前不声称已完成实际公共全量复算。
