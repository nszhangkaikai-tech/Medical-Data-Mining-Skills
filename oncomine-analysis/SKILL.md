---
name: oncomine-analysis
description: Oncomine 数据库分析。用于差异基因在肿瘤 vs 正常中的表达验证、Meta 分析、共表达关系探索。
triggers:
  - "Oncomine"
  - "Meta分析"
  - "共表达"
  - "差异验证"
input_check:
  required:
    - "目标基因或基因列表"
    - "肿瘤类型"
  optional:
    - "分析类型（差异/共表达/Meta）"
    - "样本类型"
output:
  - "Oncomine 分析结果"
  - "差异验证结论"
source_references:
  - video: "12.Oncomine概述及Meta分析"
  - video: "13.Oncomine之差异分析及共表达分析"
  - transcript_time: "~15-35 min"
scripts: []
next_skill:
  - "tcga-survival（TCGA 中进一步验证预后）"
---

# Oncomine Analysis

## 触发条件
用户需要做公共数据验证、Meta 分析或共表达分析时。

## 输入
- 目标基因
- 肿瘤类型

## 执行步骤
1. 进入 Oncomine
2. 选择数据集
3. 差异分析或共表达分析
4. 导出结果

## 输出
- 差异验证结果
- 共表达网络
- Meta 结论

## 边界
不包含本地统计建模。
