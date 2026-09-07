---
name: meta-analysis-bias
description: Meta 分析偏倚评估与统计图（PRISMA 2020 版）。漏斗图、Egger/Begg 检验、发表偏倚、异质性评估。要求 PICO、检索策略、筛选流程、数据提取、质量/偏倚工具、效应量换算、异质性(Q/I²/tau²)、固定/随机效应选择依据、敏感性/亚组。研究数 < 10 时不得声称漏斗图证明无发表偏倚。当用户需要做 Meta 分析、系统综述、偏倚评估、森林图、漏斗图时使用。
triggers:
  - "Meta分析"
  - "漏斗图"
  - "发表偏倚"
  - "异质性"
  - "Egger"
  - "Begg"
  - "PRISMA"
  - "系统综述"
input_check:
  required:
    - "纳入研究列表"
    - "效应量（OR/RR/HR/SMD）"
    - "PICO 声明"
    - "检索策略/数据库/日期"
    - "数据状态（real/simulated/not_collected）"
  optional:
    - "标准误或样本量"
    - "研究质量评价结果"
output:
  - "PRISMA 流程图"
  - "森林图"
  - "异质性检验结果（Q/I²/tau²）"
  - "偏倚风险说明"
  - "provenance.json"
source_references:
  - helix_article: "从漏斗图到ROC曲线，科研统计图表制作指南"
  - helix_article: "一文掌握基础统计图形绘制：Meta分析与生信发文必备技能"
  - reference: "PRISMA 2020 声明"
  - reference: "AMSTAR 2 工具"
next_skill:
  - "biomedical-visualization（漏斗图/森林图统一出图）"
  - "paper-writing（方法学报告）"
---

# Meta Analysis & Bias（PRISMA 2020 版）

## 前置门禁
1. 明确研究类型：系统综述/Meta
2. 声明 PICO：
   - P（Population/ Participants）
   - I（Intervention / Exposure）
   - C（Comparator / Control）
   - O（Outcome）
3. 声明 `data_mode` 和检索信息（数据库、日期、语言限制）
4. 若研究数 < 10：在报告中显式标注“漏斗图判断力有限，不做发表偏倚结论”

## 执行步骤

### 1. 检索与筛选
- 检索式必须可复现：数据库、日期、检索字段、布尔逻辑
- 重复率（kappa）或双重独立筛选
- PRISMA 流程图：7 个节点（识别、去重、标题摘要筛选、全文评估、纳入、排除及原因）

### 2. 数据提取
- 双人独立提取 + dispute resolution
- 效应量统一指标：OR / RR / HR / SMD，注明换算公式
- 样本量、事件数、随访中位数

### 3. 质量/偏倚评价
- 根据研究类型选择工具：
  - RCT：Cochrane Risk of Bias 2
  - 队列：Newcastle-Ottawa Scale (NOS)
  - 诊断：QUADAS-2
- 结果必须表格化呈现，不得仅文字概括

### 4. 异质性先于合并
- Q 检验 p 值 + I² + tau²
- I² < 50% 且 Q 不显著：可考虑固定效应模型，但需说明理由
- I² ≥ 50%：必须使用随机效应模型
- 探索来源：预先指定的亚组分析 / Meta 回归

### 5. 合并效应量
- 固定效应：Mantel-Haenszel（分类）或 IV（连续）
- 随机效应：DerSimonian-Laird（默认）或 REML（若研究数少且异质性高）
- 报告合并效应量、95% CI、P 值

### 6. 敏感性分析
- 剔除低质量研究
- 剔除小样本研究
- 不同效应量模型切换（固定↔随机）
- 若结果稳健，报告“结论未受单项研究影响”

### 7. 发表偏倚
- 漏斗图：仅作辅助可视化，不能单独证明偏倚
- Egger 检验（连续结局）和 Begg 检验（秩相关）：仅当研究数 ≥ 10 时报告
- 若研究数 < 10：显式写“研究数不足，无法可靠评估发表偏倚”

## 输出
- PRISMA 流程图
- 森林图 + 异质性指标
- 偏倚风险表
- 敏感性/亚组分析结果
- provenance.json

## 边界
包含完整 Meta 分析流程；偏倚评估与统计图为其中一部分。
