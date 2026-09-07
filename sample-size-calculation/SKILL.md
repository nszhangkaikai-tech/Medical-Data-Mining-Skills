---
name: sample-size-calculation
description: 样本量计算与把握度分析。RCT/队列/病例对照/横断面研究的样本量估算，支持二分类/连续/生存/诊断效能(AUC)终点。当用户需要计算样本量、评估把握度、确定组间样本分配、考虑脱落率时使用。
triggers:
  - "样本量计算"
  - "sample size"
  - "把握度"
  - "power"
  - "effect size"
input_check:
  required:
    - "研究设计类型"
    - "主要终点类型（二分类/连续/生存/AUC）"
  optional:
    - "预期效应量"
    - "α水平（通常0.05）"
    - "把握度（通常0.80/0.90）"
    - "脱落率"
output:
  - "样本量计算公式"
  - "各组样本分配"
  - "敏感性分析（不同效应量/把握度）"
source_references:
  - helix_article: "医学研究样本量计算，2种方法详解"
  - helix_article: "临床数据统计分析方法如何提升研究效率"
  - helix_article: "临床统计分析流程全攻略，科研效率翻倍的关键"
next_skill:
  - "clinical-research-design（研究设计审查）"
  - "statistical-thinking（统计方法匹配）"
---

# Sample Size Calculation

## 触发条件
用户提到“样本量”“sample size”“power”“把握度”。

## 输入
- 研究设计
- 主要终点类型
- 效应量/α/把握度（可选）
- 脱落率（可选）

## 执行步骤

### 1. 先明确终点类型
| 终点类型 | 常用指标 | 样本量公式基础 |
|----------|----------|----------------|
| 二分类 | 率/OR/RR | 两组比例比较 |
| 连续 | 均值差/SD | t检验/方差分析 |
| 生存 | HR/中位生存时间 | log-rank检验 |
| 诊断 | AUC/Sensitivity/Specificity | ROC曲线下面积比较 |

### 2. 核心参数确定
- α：通常 0.05（双侧）
- 把握度 1-β：通常 0.80 或 0.90
- 效应量：来自预试验/文献/最小临床意义值
- 脱落率：10-20%（临床试验更高）

### 3. 公式选择
**两组平行设计（连续终点）**
n = 2 * (Z_α + Z_β)^2 * σ^2 / δ^2

**两组平行设计（二分类终点）**
n = [ (Z_α * √(2p̄(1-p̄)) + Z_β * √(p1(1-p1) + p2(1-p2)) ) / (p1 - p2) ]^2

**生存分析（log-rank）**
n = (Z_α + Z_β)^2 / [ (log(HR))^2 * P_bar ]

**诊断效能（AUC）**
n = (Z_α + Z_β)^2 / [ 2 * (AUC - 0.5)^2 ]

### 4. 实用工具
- R：`pwr` / `powerMediation` / `survival` / `pROC`
- Python：`statsmodels.stats.power` / `scikit-survival`
- 在线工具：OpenEpi / PASS / G*Power

### 5. 分层/多中心调整
- 多中心：考虑中心间异质性，适当放大样本量
- 分层分析：各层按比例分配
- 匹配设计：配对公式，效应量减半

## 输出
- 总样本量 + 各组分配
- 参数敏感性表（不同效应量/把握度）
- 脱落率调整后最终招募数

## 边界
不包含具体统计建模；只解决“需要多少样本”。
