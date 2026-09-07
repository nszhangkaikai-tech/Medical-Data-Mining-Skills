---
name: differential-gene-screening
description: 差异基因筛选策略（可复现版）。必须声明输入尺度、QC、批次/混杂校正、设计矩阵、FDR 方法；禁止 raw P 冒充 padj。当用户拿到差异分析结果需要筛基因、定阈值、解释筛选逻辑时使用。
triggers:
  - "差异基因筛选"
  - "阈值设定"
  - "log2FC"
  - "adj.P.Val"
  - "padj"
  - "批次效应"
  - "meta整合"
input_check:
  required:
    - "差异分析结果表"
    - "输入数据尺度说明"
    - "FDR 方法"
  optional:
    - "研究目的（探索/标志物/验证）"
    - "样本量"
    - "批次信息"
output:
  - "分层差异基因列表"
  - "筛选阈值说明"
  - "QC 报告"
  - "provenance.json"
source_references:
  - helix_article: "火山图制作全流程，避开差异基因分析陷阱"
  - helix_article: "火山图与热图联动：差异基因筛选实战指南"
  - helix_article: "火山图阈值设定：影响所有差异基因结果"
  - helix_article: "蛋白质组火山图如何精准筛选关键差异基因"
  - helix_article: "RNA-seq火山图解读：p值与log2FC如何影响差异基因筛选"
next_skill:
  - "visualization（热图/火山图验证）"
  - "enrichment-analysis（功能解释）"
---

# Differential Gene Screening（可复现版）

## 前置门禁
1. 声明 `input_scale`：raw counts / TPM / FPKM / log2CPM / normalized expression
2. 声明 `qc_passed`：离群样本检测、PCA/聚类检查、批次效应评估结果
3. 声明 `batch_correction`：ComBat / limma removeBatchEffect / 协变量纳入设计矩阵 / 无
4. 声明 `design_matrix`：~ condition + batch + covariates
5. 声明 `fdr_method`：Benjamini-Hochberg（默认） / Bonferroni / qvalue
6. 禁止 raw P 值冒充 adj.P.Val / padj

## 执行步骤

### 1. 数据 QC
- 低表达过滤：保留在 >75% 样本中表达量大于 0 或 cpm > 1 的基因
- 离群样本：PCA 距离 > 3 SD 或 hierarchical clustering 明显异常
- 批次效应：PCA 按批次分离 > 设计矩阵必须纳入批次

### 2. 差异分析
- 工具：limma（芯片/RNA-seq 均可） / DESeq2（raw counts） / edgeR
- 设计矩阵必须显式写出
- 提取：log2FC、aveExpr、t、P、adj.P.Val（不可省略）

### 3. 阈值设定
- 初筛：|log2FC| >= 1 且 adj.P.Val < 0.05
- 严格：|log2FC| >= 2 且 adj.P.Val < 0.001
- 低表达过滤：保留在 >75% 样本中表达量大于 0 的基因
- 阈值必须在论文 Methods 中明确写出，禁止后验调整以获得显著结果

### 4. 分层
- 第一层：高 log2FC + 高显著性（强候选）
- 第二层：显著但效应略弱（中等候选）
- 第三层：接近阈值（观察性）

### 5. 火山图 + 热图联动
- 火山图负责“筛”
- 热图负责“验”
- 如果热图分组混乱，回查阈值/批次/分组标签

### 6. 上下调分开分析
- 上调：通路激活、应激反应
- 下调：抑制通路、代谢改变
- 两者同等重要

### 7. 多数据集整合
- 荟萃分析可减少偶然性
- 平台不同时需统一 ID 类型和标准化方式
- 跨数据集 meta 需报告异质性

## 输出
- 上调/下调/NS 三层基因列表
- QC 报告（PCA 图、离群样本清单、批次效应评估）
- 阈值设定说明（适合写入论文 Methods）
- provenance.json

## 边界
不包含功能富集和蛋白互作；聚焦“如何筛得准”。
