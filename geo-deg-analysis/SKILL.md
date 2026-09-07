---
name: geo-deg-analysis
description: GEO 差异基因分析。使用 Limma 对芯片表达矩阵做差异分析，输出 logFC、t、P、adj.P.Val，支持基因注释。
triggers:
  - "Limma"
  - "差异基因"
  - "topTable"
  - "annotation"
input_check:
  required:
    - "表达矩阵（探针 ID 为行名）"
    - "分组向量（如 normal/tumor）"
  optional:
    - "平台注释文件"
    - "FC 阈值（默认 1.0）"
    - "P 值阈值（默认 0.05）"
output:
  - "差异基因结果表"
  - "基因 symbol 注释矩阵"
source_references:
  - video: "4.原始数据预处理"
  - video: "5.寻找差异基因及制作热图和火山图"
  - transcript_time: "~15-35 min"
scripts:
  - "../../课程脚本代码/GEO.txt"
next_skill:
  - "visualization（画热图/火山图）"
  - "enrichment-analysis（功能富集）"
---

# GEO DEG Analysis

## 触发条件
用户已有表达矩阵，需要做正式差异分析时。

## 输入
- 表达矩阵
- 分组向量
- 可选：平台注释文件、阈值

## 执行步骤
1. 读取表达矩阵
2. 矩阵转置、去除 NA
3. 创建 design 矩阵
4. Limma 拟合
5. 提取 topTable
6. 可选：基因注释探针 ID → gene symbol

## 输出
- 差异基因表
- 注释后的基因 symbol 矩阵

## 边界
不包含下游富集和可视化。
