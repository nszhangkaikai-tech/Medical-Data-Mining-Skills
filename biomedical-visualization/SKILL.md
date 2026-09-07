---
name: biomedical-visualization
description: 生物医学统计可视化。火山图、热图、ROC、PR、校准曲线、DCA、KM、漏斗图、列线图。专注于科研发表级出图和指标解读。
triggers:
  - "火山图"
  - "ROC"
  - "PR曲线"
  - "校准曲线"
  - "DCA"
  - "漏斗图"
  - "列线图"
  - "发表级出图"
input_check:
  required:
    - "图表类型"
    - "数据格式或结果表"
  optional:
    - "投稿期刊风格要求"
    - "颜色/分辨率要求"
output:
  - "出版级统计图"
  - "指标解读说明"
source_references:
  - helix_article: "火山图制作全流程，避开差异基因分析陷阱"
  - helix_article: "火山图与热图联动：差异基因筛选实战指南"
  - helix_article: "从漏斗图到ROC曲线，科研统计图表制作指南"
  - helix_article: "蛋白质组火山图如何精准筛选关键差异基因"
  - helix_article: "RNA-seq火山图解读：p值与log2FC如何影响差异基因筛选"
next_skill:
  - "clinical-prediction-model（模型图与评价图统一输出）"
  - "visualization（基础热图/火山图）"
---

# Biomedical Visualization

## 触发条件
用户需要制作/解读科研统计图，或要求“发表级出图”。

## 输入
- 图表类型
- 数据表/结果表
- 期刊风格/分辨率要求

## 执行步骤

### 1. 火山图（RNA-seq / 蛋白组）
- 横轴 log2FC，纵轴 -log10(P) 或 -log10(adj.P.Val)
- 阈值常用 |log2FC| >= 1 + adj.P.Val < 0.05
- 红/蓝/灰分区
- 只标注关键基因（top log2FC 或文献已知标志物）
- 优先用 ggplot2 + ggrepel，导出 PDF/300dpi TIFF

### 2. 热图
- 行=基因，列=样本，颜色=z-score 标准化表达
- 目的：验证分组是否清晰、是否有离群样本
- top N 基因通常取 20/50/100

### 3. ROC / PR 曲线
- ROC：1-特异度 vs 灵敏度，报告 AUC
- PR：召回率 vs 精准率，适合不平衡数据
- 两者互补，不要只报一个

### 4. 校准曲线
- 预测概率 vs 真实发生率
- 配合 Hosmer-Lemeshow / Brier score

### 5. DCA（Decision Curve Analysis）
- 横轴阈值概率，纵轴净获益
- 比较模型 vs 全干预 vs 不干预

### 6. KM 生存曲线
- 高低风险分组
- 报告中位生存时间、log-rank P、风险人数

### 7. 漏斗图
- 用于 Meta 偏倚风险
- 样本量越大越集中，不对称提示发表偏倚
- 研究 <10 项时判断力有限

### 8. 列线图（Nomogram）
- 将多变量模型转成临床可操作评分
- 常用于预后模型最终展示

## 输出
- 出版级统计图
- 指标数值与图注文案

## 边界
不包含上游差异分析和建模；专注图与指标解读。
