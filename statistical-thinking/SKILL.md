---
name: statistical-thinking
description: 医学统计基础思维。描述性统计、推断性统计、正态性检验、P值解读、效应量与统计显著性的关系。适合帮用户判断该用哪种检验、如何解读统计结果。
triggers:
  - "描述性统计"
  - "推断性统计"
  - "正态性检验"
  - "P值"
  - "效应量"
  - "统计方法选择"
  - "Shapiro-Wilk"
input_check:
  required:
    - "数据类型（连续/分类/生存）"
    - "研究问题"
  optional:
    - "样本量"
    - "分组信息"
output:
  - "推荐统计方法"
  - "结果解读说明"
source_references:
  - helix_article: "5分钟学会描述性统计，医学生必备！"
  - helix_article: "推断性统计：3大方法解析与实战"
  - helix_article: "统计学意义为何重要？6分钟读懂"
  - helix_article: "Shapiro-Wilk 检验如何判断正态性？3步解析"
next_skill:
  - "clinical-prediction-model（建模前先明确统计基础）"
  - "biomedical-visualization（统计图制作）"
---

# Statistical Thinking

## 触发条件
用户问“该用什么统计方法”、“P值怎么解释”、“效应量是什么意思”。

## 输入
- 数据类型
- 研究问题
- 样本量/分组

## 执行步骤

### 1. 先分清楚：描述 vs 推断
- 描述性统计：均值、中位数、率、构成比
- 推断性统计：假设检验、置信区间、效应量

### 2. 正态性判断
- 小样本：Shapiro-Wilk
- 大样本：直方图 / Q-Q 图 / 偏度峰度
- 非正态：换非参检验（Mann-Whitney / Kruskal-Wallis）

### 3. P值 ≠ 一切
- P值反映“差异是否可能由随机造成”
- 不反映效应大小和临床意义
- 样本量足够时，微小变化也可 P < 0.05
- 医学论文中更推荐优先报告校正后 P 值（adj.P.Val / FDR）

### 4. 效应量优先
- 连续：Cohen's d / 标准化均值差
- 二分类：OR / RR
- 生存：HR
- 报告效应量 + 95%CI，不能只写 P

### 5. 多重比较校正
- 高通量/多组学：必须校正
- 常用 FDR（Benjamini-Hochberg）
- 正式结论优先用 adj.P.Val

## 常见统计图表选择

| 目的 | 推荐图表 |
|------|----------|
| 展示样本分布/基线 | 箱线图、小提琴图、直方图 |
| 两组比较 | 火山图（组学）、箱线图（临床） |
| 多组比较 | 热图、小提琴图、ANOVA + 事后检验 |
| 诊断效能 | ROC 曲线 + AUC |
| 不平衡数据 | PR 曲线 + F1 |
| 预测模型 | 校准曲线 + DCA |
| 预后分层 | KM 曲线 + log-rank |
| Meta 偏倚 | 漏斗图 + Egger/Begg |

## 输出
- 推荐统计方法
- 结果解读
- 配套图表建议

## 边界
不包含具体建模和绘图；只解决“选什么方法”和“怎么读懂结果”。
