---
name: tcga-download
description: TCGA 数据下载与整理。通过 GDC 网页或命令行下载 count/FPKM/甲基化/SNV 数据，整理成表达矩阵。
triggers:
  - "TCGA下载"
  - "GDC"
  - "count"
  - "FPKM"
input_check:
  required:
    - "肿瘤类型（如 PAAD、LUAD）"
    - "数据类型（count/FPKM/甲基化/SNV）"
  optional:
    - "样本过滤条件（性别、种族、分期、生存状态）"
output:
  - "表达矩阵"
  - "样本元数据"
source_references:
  - video: "9.TCGA数据下载"
  - transcript_time: "~15-30 min"
scripts:
  - "../../课程脚本代码/TCGA.txt"
next_skill:
  - "tcga-survival（临床预后分析）"
  - "geo-deg-analysis（寻找差异基因）"
---

# TCGA Download

## 触发条件
用户需要下载 TCGA 数据时。

## 输入
- 肿瘤类型
- 数据类型

## 执行步骤
1. 进入 TCGA GDC
2. 选择肿瘤类型和文件类型
3. 加入 Cart 并下载
4. 整理成表达矩阵

## 输出
- 表达矩阵
- 样本元数据

## 边界
不包含差异分析和生存分析。
