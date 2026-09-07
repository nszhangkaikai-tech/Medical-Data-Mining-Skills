---
name: omics-integration-validation
description: 多组学整合与独立验证。将差异基因/蛋白在独立队列、公共数据库或实验层面做交叉验证，形成证据链闭环。
triggers:
  - "验证"
  - "qPCR"
  - "Western blot"
  - "IHC"
  - "独立队列"
  - "GEO验证"
  - "TCGA验证"
  - "Oncomine验证"
  - "实验验证"
input_check:
  required:
    - "候选分子列表"
    - "验证数据来源"
  optional:
    - "实验方法（蛋白/RNA/细胞/动物）"
output:
  - "验证结果表"
  - "证据链强度评估"
source_references:
  - helix_article: "外部验证队列构建：临床研究选题的黄金法则"
  - helix_article: "蛋白质组火山图如何精准筛选关键差异基因"
  - transcript: "5.寻找差异基因及制作热图和火山图"
  - transcript: "11.寻找差异基因和制作5年生存率"
next_skill:
  - "clinical-prediction-model（验证后进入模型）"
  - "tcga-survival（TCGA 独立预后验证）"
---

# Omics Integration & Validation

## 触发条件
用户拿到候选基因/蛋白后，需要跨数据库、跨队列或实验验证。

## 输入
- 候选分子列表
- 验证数据来源

## 验证层级

### 1. 公共数据库验证
- TCGA：独立肿瘤队列预后验证
- GEO：另一批次的表达验证
- Oncomine：肿瘤 vs 正常差异验证
- GEPIA2：快速 TCGA/GTEx 差异验证

### 2. 临床队列验证
- 外部验证队列要独立于训练集
- 不同中心 / 不同时间段 / 不同平台
- 不参与变量筛选和阈值优化

### 3. 实验验证
- RNA 水平：qPCR
- 蛋白水平：Western blot / PRM / IHC
- 功能：细胞增殖/凋亡/迁移

## 执行步骤

### 1. 先数据库，后实验
- 先用 TCGA/GEO/Oncomine 证明“公共数据里也这样”
- 再选 1-3 个关键分子做实验验证

### 2. 验证指标
- 差异方向是否一致
- 效应量是否同向
- 预后相关性是否保留

### 3. 证据链闭环
- 生物信息学筛选
- 公共数据验证
- 实验验证
- 功能机制（可选）

## 输出
- 验证结果表
- 证据链强度评估

## 边界
不包含实验protocol细节；聚焦验证策略和证据层级。
