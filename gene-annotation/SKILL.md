---
name: gene-annotation
description: 基因 ID 转换与注释。将探针 ID、Ensembl ID、RNA-seq ID 转换为 gene symbol，支持 KNN 缺失值填补。
triggers:
  - "基因注释"
  - "探针ID"
  - "Ensembl"
  - "symbol"
  - "ID转换"
input_check:
  required:
    - "表达矩阵（探针/Ensembl 为行名）"
  optional:
    - "平台注释文件"
    - "缺失值处理方式"
output:
  - "注释后的 symbol 表达矩阵"
source_references:
  - video: "4.原始数据预处理"
  - video: "5.寻找差异基因及制作热图和火山图"
  - transcript_time: "~10-20 min"
scripts:
  - "../../课程脚本代码/perl/ensemblToSymbol.pl"
next_skill:
  - "geo-deg-analysis（注释后做差异分析）"
---

# Gene Annotation

## 触发条件
用户需要把探针/Ensembl ID 转成 gene symbol 时。

## 输入
- 表达矩阵
- 平台注释文件

## 执行步骤
1. 匹配探针 ID 与 gene ID
2. 多探针取平均/中位数
3. 转换为 gene symbol
4. 可选：KNN 填补缺失值

## 输出
- symbol 表达矩阵

## 边界
不包含差异分析和功能富集。
