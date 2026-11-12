# Final 17-page CMC manuscript alignment — change log (2026-11-12)

## 核心目的

仅对齐投稿前 17 页 `CMC_Condensed_Illustrated_Graphs.pdf`，而不是较早的 23 页 DOCX；原始数据不可凭主观判断改写。

## 已修改的内容

1. **唯一论文版本**：保留正式 17 页 PDF 和 SHA-256；移除不再对应终稿的 23 页 DOCX 和两张旧图截图。PDF 文件仅作私下核对版本，公开仓库应确认版权。
2. **去除非实测图**：删除原文件夹 `data/illustrative/` 的人工曲线与 `figures/illustrative_*`，绘图脚本只读取 `data/empirical/full_run/` 的真实 CSV。
3. **对齐定理/表格编号**：Q 的规范化四色案例属于终稿 **Table 2**，删边四色证书属于 **Table 3**，六顶点证书属于 **Table 4**；证书的 JSON 字段和源代码常量同步更名，实际图论证书本身未被篡改。
4. **对齐实验编号**：终稿 **Table 5** 是 649 项一致性，**Figure 6** 展示 60 项/阶的状态、时间和内存曲线；重写全部中英文复现文档、原有错指旧图号的索引和数值对照。
5. **保留原始记录**：649 项图输入、649 项着色证书、649 份 SP 分解树、13,629 条逐次计时、72,980 项节点记录及 15 行汇总保持为真实归档观测；不因重跑新机器出现不同数值而重写论文记录。
6. **补齐 Figure 8 算法证据**：根据第 15 页编号图人工转录 71 顶点/76 边拓扑，计算并验证**另一个有效的**无环四时隙边着色；不宣称转录得到原绘图文件或与图面逐边颜色完全一致。
7. **新增一致性门禁**：`scripts/verify_paper_alignment.py` 对逐个证书、原始计时与聚合值、Figure 6、Figure 8、表 2–5 和最终 PDF 哈希进行复核；`scripts/verify_release.py` 对压缩包内全部分发文件进行 SHA-256 完整性检查。
8. **安全信息披露**：保留原始 Linux 运行清单，不擅自添加论文声称的 i9-14900HX / 32 GB；在 `docs/PAPER_RESULT_COMPARISON.md` 说明该硬件的日志来源尚无法从打包材料验证。

## 未进行的改动

- 没有强行将真实计时调成更快。
- 没有把旧 339/656 数字混入终稿。
- 没有改变核心 DP 数学规则及原 649 项观测记录。
- 没有向 GitHub 自动上传：这是一个可下载、可自行发布的完整归档文件。

## 审计顺序

```bash
python -m pip install -e '.[plot,test]'
python -m pytest -q
python scripts/verify_paper_alignment.py
python scripts/verify_figure8.py
python scripts/verify_release.py
```

**注意：** 图 8 的原始绘图脚本/颜色记录、论文中具体实验设备的日志，如果期刊特别要求，仍需作者原始资料。不能用新合成数据冒充。
