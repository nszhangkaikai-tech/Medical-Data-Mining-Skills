---
name: biomarker-discovery
description: 生物标志物发现与验证。从差异分析到机器学习筛选，再到公共数据库验证和实验验证的完整链路。
triggers:
  - "标志物"
  - "biomarker"
  - "诊断标志物"
  - "预后标志物"
  - "特征筛选"
  - "LASSO"
  - "随机森林"
input_check:
  required:
    - "研究目标（诊断/预后/疗效预测）"
    - "候选分子或组学数据"
  optional:
    - "验证策略（公共数据库/实验）"
output:
  - "候选标志物列表"
  - "验证结论"
source_references:
  - helix_article: "蛋白质组火山图如何精准筛选关键差异基因"
  - helix_article: "RNA-seq火山图解读：p值与log2FC如何影响差异基因筛选"
  - helix_article: "外部验证队列构建：临床研究选题的黄金法则"
  - transcript: "11.寻找差异基因和制作5年生存率"
next_skill:
  - "omics-integration-validation（验证）"
  - "clinical-prediction-model（转模型）"
---

# Biomarker Discovery

## 触发条件
用户明确要找诊断标志物、预后标志物、疗效预测分子。

## 输入
- 研究目标
- 组学数据或候选分子

## 执行步骤

### 1. 初筛
- 火山图 + 阈值筛选
- 效应量 + 显著性双重过滤

### 2. 精筛
- LASSO 回归压缩特征
- 随机森林 / SVM 做重要性排序
- 多因素回归确认独立性

### 3. 验证
- 公共数据库：TCGA / GEO / Oncomine
- 独立队列
- 实验：qPCR / Western / IHC / PRM

### 4. 临床实用性检查
- 是否容易检测
- 是否成本可控
- 是否比现有标志物更优

## 输出
- 候选标志物列表
- 验证证据链

## 边界
不包含实验protocol；聚焦筛选策略和验证设计。
