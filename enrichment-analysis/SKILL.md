---
name: enrichment-analysis
description: GO/KEGG 功能富集分析。使用 DAVID、clusterProfiler 或 Bingo 对差异基因做功能注释与通路富集。
triggers:
  - "GO"
  - "KEGG"
  - "DAVID"
  - "clusterProfiler"
  - "Bingo"
input_check:
  required:
    - "差异基因列表（gene symbol）"
    - "背景基因列表（可选）"
  optional:
    - "物种（默认 human）"
    - "FDR 阈值（默认 0.05）"
output:
  - "GO BP/CC/MF 富集表"
  - "KEGG pathway 表"
  - "可视化图"
source_references:
  - video: "6.GO富集分析"
  - video: "7.KEGG分析(修复)"
  - transcript_time: "~20-45 min"
scripts:
  - "../../课程脚本代码/GEO.txt"
next_skill:
  - "ppi-network（蛋白互作验证）"
---

# Enrichment Analysis

## 触发条件
用户需要对差异基因做功能解释时。

## 输入
- 差异基因列表
- 可选：背景基因、物种

## 执行步骤
1. 基因 ID 统一为 symbol
2. GO 富集：BP / CC / MF
3. KEGG 通路分析
4. 可选：Cytoscape Bingo 可视化

## 输出
- 富集结果表
- 通路图

## 边界
不包含蛋白互作与生存分析。
