---
name: tcga-survival
description: TCGA 生存分析（可复现版）。必须声明 index date、随访方案、删失编码；执行 KM+风险表+log-rank、Cox 多变量、比例风险检验；预后模型需报告 time-dependent AUC/C-index、指定时间点 Brier、校准、bootstrap 或嵌套 CV。当用户需要做 TCGA 临床预后分析、生存曲线、Cox 回归、风险分层时使用。
triggers:
  - "生存分析"
  - "Kaplan-Meier"
  - "log-rank"
  - "Cox"
  - "生存曲线"
  - "HR"
  - "5年生存率"
input_check:
  required:
    - "基因表达矩阵"
    - "临床信息（时间、状态）"
    - "index date 定义"
    - "删失编码规则"
    - "数据状态（real/simulated/not_collected）"
  optional:
    - "分组变量"
    - "时间点"
output:
  - "KM 曲线 + 风险表 + log-rank P"
  - "Cox 单因素/多因素汇总（HR, 95% CI, P）"
  - "比例风险检验结果"
  - "time-dependent AUC / C-index（若为预后模型）"
  - "校准曲线 + Brier（若为预后模型）"
  - "provenance.json"
source_references:
  - video: "10.TCGA数据整理和基因注释"
  - video: "11.寻找差异基因和制作5年生存率"
  - helix_article: "临床科研统计方法如何在实战中提高论文录取率"
next_skill:
  - "clinical-prediction-model（预后模型评价）"
  - "visualization（结果美化）"
---

# TCGA Survival（可复现版）

## 前置门禁
1. 明确研究类型：预后研究（时间至事件）
2. 声明 `endpoint`（OS/DFS/RFS/PFS），禁止后验替换
3. 声明 `censoring_def`：0=删失, 1=事件（或反之，但必须全局一致）
4. 声明 `index date`：入组日期、确诊日期、手术日期、首次随访日期

## 执行步骤

### 1. 数据准备
- 整理临床时间、状态
- 检查缺失：删失信息缺失 > 5% 必须报告处理方式
- 离群随访时间检查：描述最大/最小随访，与临床实际对照

### 2. KM 曲线 + 风险表
- 按研究需要分组（如 Stage、基因高低表达、风险评分）
- 报告：中位生存时间、1年/3年/5年生存率、log-rank P
- 风险人数表（risk table）必须附在 KM 曲线下方

### 3. Cox 回归
- 单因素：每个候选变量单独做 Cox
- 多因素：纳入单因素 P < 0.05 或临床重要变量
- 报告：HR、95% CI、P 值
- 若为弹性网/惩罚 Cox：报告 lambda 选择过程和惩罚强度

### 4. 比例风险假设
- Schoenfeld residuals test（全局和逐个变量）
- 图示检查（log(-log(S)) 曲线 crossing）
- 若不满足：分层 Cox / 时间依赖系数 / 参数生存模型（Weibull / log-normal）

### 5. 预后模型额外要求
若目标为构建预后风险模型，必须补充：
- time-dependent AUC（1年/3年/5年）及 95% CI
- 指定时间点 Brier score
- 校准曲线 + 校准斜率/截距
- 内部验证：bootstrap（≥200）或嵌套 CV
- 外部验证状态声明

## 输出
- KM 曲线 + 风险表 + log-rank P
- Cox 汇总表
- 比例风险检验结果
- time-dependent AUC / C-index（若适用）
- 校准指标（若适用）
- provenance.json

## 边界
不包含数据下载和差异分析；专注生存分析与预后模型评价。
