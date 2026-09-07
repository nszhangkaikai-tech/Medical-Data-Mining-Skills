---
name: ppi-network
description: 蛋白互作网络构建。使用 STRING 数据库和 Cytoscape 构建差异基因蛋白互作网络，并用 Bingo 做功能聚类。
triggers:
  - "蛋白互作"
  - "STRING"
  - "Cytoscape"
  - "Bingo"
input_check:
  required:
    - "差异基因列表（gene symbol）"
  optional:
    - "STRING 物种"
    - "置信度阈值"
output:
  - "PPI 网络图"
  - "核心基因列表"
source_references:
  - video: "8.蛋白互作网络"
  - transcript_time: "~20-40 min"
scripts:
  - "../../课程脚本代码/GEO.txt"
next_skill:
  - "enrichment-analysis（进一步解释功能）"
---

# PPI Network

## 触发条件
用户需要构建蛋白互作网络时。

## 输入
- 差异基因列表

## 执行步骤
1. 提交基因到 STRING
2. 下载 PPI 网络
3. Cytoscape 可视化
4. 可选：Bingo 功能聚类

## 输出
- PPI 网络
- 核心基因

## 边界
不包含差异分析和富集分析。
