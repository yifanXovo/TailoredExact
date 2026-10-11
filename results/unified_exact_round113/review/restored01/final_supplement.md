# Round113 恢复复核的最终发布补充

决定：**接受实际公共恢复及已观察的 science A 发布；科学结论保持 BLOCKED。** [最终补充 JSON](E:/codes/ExactEBRP-round113/results/unified_exact_round113/review/restored01/final_supplement.json) 关闭初签 [report.json](E:/codes/ExactEBRP-round113/results/unified_exact_round113/review/restored01/report.json) 的两个明确待核项，初签文件和此前两份科学审查没有改写。本次只做静态源码及字节核验，用时 1.481900000013411 秒；未重复 reader、旧 LP、资格或 native 执行。

旧 publisher 原型 SHA `05ef67218a484d379599d93db6a6e2327ca4fd806ae2570e43796fc3bd959acd`，实际公共版本 SHA `4b89a153246b5c63b5dfe26fd2f165f5e2dcdfe1807d341bd3cef7b73e099a98`。旧源是逆转实际四处编辑并命中冻结 SHA 的重建字节，不是当时额外保存的原始快照。独立验证了完整 diff 和精确逆变换；只有 `pack` 函数变化，其他函数、导出/恢复胶合和 import 的 AST 相同。四处编辑为：

1. 顶层 `public_/remote_/pr_` 排除保留 `public_readme.md` 和嵌套当前证据。
2. 显式加入并核对旧 clock manifest 指定的 146 份有限权威文件。
3. 将 `scripts/.gitattributes` 加入打包；两份新 R113 路径的 `-text` 属性保护签名字节。
4. 将旧 identity 路径改为 `inherited_r112/authoritative/campaign`。

先前“只有两处”的描述不完整，已明确纠正。publisher 和属性属于发布工程，未进入 42 项性能闭包或 206 项生产源码。除 publisher 原型这一处外，whole-goal 绑定均与恢复字节一致。实际 manifest SHA `e2998e98164cb80b63e3afb9e96f1775a5b03ace86831c0f365d341465a15348`、archive SHA `990207810f40a0cdd46f40caaa1925d89e19103d82292d8fba143d4698e9bfbb` 与初签一致。

实际远端 verifier 曾把历史冻结 CRLF 原始字节当作已有 LF Git blob，第一次失败已保留。科学载体内 verifier SHA `2f11bd97…` 没有替换；实际发布工具 SHA `0ee2a1f1…` 的精确补丁只分开“Git 提交对象”与“冻结 raw/manifest”核验。raw SHA/大小仍必须与 candidate 和 manifest 完全相同；历史 Git 差异只允许精确 CRLF→LF，载体仍要求工作字节与提交字节的大小/SHA 完全一致。唯一额外工作文件差异限于明确披露的 verifier 自身。

[实际 science A 远端收据](F:/ExactEBRP-round113-public01/engineering/remote_publication_A.json) 观察 [PR175](https://github.com/yifanXovo/TailoredExact/pull/175) 为 OPEN、Draft，base commit 为 `9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4`，scientific head 为 `8dd38b790a4584f17aa75094f9451519e07bcdbe`。审查员从两份 F 根证据独立重建了全部 **361 个 Git blob 的 OID、SHA256 和大小**，包括明确列出的五个历史换行差异；206 源码与 42 helper 的冻结 raw 身份均匹配。缺于科学载体的实际 pack receipt 通过后续 F 根补充核对，其字节和 Git blob 也匹配。

这些工程补充不属于原始四文件导出或 6,095 个科学载体成员，未重包或增加载体。此次签署核阅已经实际完成的父代理远端观察，未主动发起 live Git/GitHub 查询，未验证随后包含 receipts 的提交或未来 final head。

新 3 合格、cold P 正常返回但缺正式 whole/端点、4 个 G100 未启动、21/30 配对、两个 backend 不完整归因、15 启动/6,112.501114845276 秒、branch3 与 STOP 全部保持。source-derived 零 Optimize 夹具仍属 synthetic，没有声称实际 CLI 取消分支已经曝光；没有改变阈值、时钟、必要 runtime audit 或科学数值。
