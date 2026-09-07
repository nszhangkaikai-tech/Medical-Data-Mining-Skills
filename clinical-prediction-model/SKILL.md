---
name: clinical-prediction-model
description: 临床预测模型构建与评价（可复现版）。区分度/校准度/临床效用三段式评价，明确分离诊断分类与预后生存终点，要求完整模型公示、数据泄漏防护、开发/内部验证/外部验证的独立数据流。当用户需要构建或评价临床预测模型、诊断模型、预后模型、风险评分时使用。
triggers:
  - "预测模型"
  - "诊断模型"
  - "预后模型"
  - "AUC"
  - "C-index"
  - "DCA"
  - "校准曲线"
  - "外部验证"
  - "风险评分"
input_check:
  required:
    - "研究类型（诊断分类 / 预后生存 / 风险分层）"
    - "临床结局类型（二分类诊断 / 时间生存 / 多分类）"
    - "候选预测变量"
    - "数据状态（real/simulated/not_collected）"
  optional:
    - "训练集 / 验证集划分"
    - "截断值 / 风险分层阈值"
output:
  - "完整模型公式（变量、系数、截距、预处理、阈值）"
  - "区分度指标（AUC 或 C-index/time-dependent AUC）"
  - "校准曲线 + 斜率/截距 或 Hosmer-Lemeshow"
  - "DCA 决策曲线"
  - "外部验证报告或‘未完成外部验证’声明"
  - "provenance.json"
source_references:
  - helix_article: "生物医学预测模型效能指标：如何选择与解读"
  - helix_article: "基于预测模型统计分析的临床研究设计要点"
  - helix_article: "外部验证队列构建：临床研究选题的黄金法则"
  - reference: "TRIPOD+AI 声明"
  - reference: "PROBAST+AI 偏倚风险评估"
next_skill:
  - "tcga-survival（预后模型 downstream）"
  - "biomedical-visualization（模型图统一输出）"
---

# Clinical Prediction Model（可复现版）

## 前置门禁（必须首先执行）

### 1. 终点分离
- **诊断分类模型**：金标准明确（有/无疾病），主要终点为 AUC/灵敏度/特异度/NPV/PPV。禁止改用 OS/DFS 作为主要终点。
- **预后模型**：时间至事件终点（OS/DFS/RFS/PFS），主要终点为 C-index / time-dependent AUC / 指定时间点 Brier / KM。禁止仅用横断面数据做生存分析。
- **风险分层**：基于连续评分分组（高/中/低），需报告 KM + log-rank + 风险表。

### 2. 数据状态声明
在 `provenance.json` 中必须声明：
- `data_mode`: `real` / `simulated` / `not_collected`
- `train_val_test_split`: 分层变量、随机种子、比例
- `external_validation_status`: `completed` / `pending` / `not_planned` / `unavailable`

### 3. 报告规范前置
- 预测模型：TRIPOD+AI + PROBAST+AI
- 诊断模型：STARD 2015 + TRIPOD+AI + PROBAST+AI
- 预后模型：TRIPOD+AI + STROBE

## 执行步骤

### 1. 问题定义与数据流
- 明确：诊断 / 预后 / 风险分层
- 绘制样本流：raw → QC → train → validation → test → external（若有）
- 若为模拟数据：在报告头部插入不可移除的 DEMO 水印

### 2. 变量筛选与数据泄漏防护
- 特征选择只能在训练集上执行
- 标准化/归一化参数（均值/SD）只能从训练集估计
- 缺失值处理：多重插补或完整案例分析，禁止中位数填充后直接建模
- EPV（事件数/变量比）≥ 10–20；若不满足，必须报告并考虑收缩/惩罚方法

### 3. 建模
- 二分类诊断：Logistic 回归（首选可解释模型）或 penalized logistic
- 预后：Cox 回归（先单因素再多因素）或 penalized Cox (LASSO/Ridge)
- 高风险维：随机森林/SVM/梯度提升仅作候选压缩，最终模型需公示系数

### 4. 区分度评价
- 诊断：ROC + AUC（95% CI）+ Youden 最佳截断值 + 灵敏度/特异度
- 预后：C-index（95% CI）+ time-dependent AUC（1年/3年/5年）
- 分类报告：Precision / Recall / F1（不平衡数据必须补充 PR 曲线）

### 5. 校准度评价
- 校准曲线（预测概率 vs 真实发生率）
- 校准斜率（calibration slope）和截距（calibration intercept）
- Hosmer-Lemeshow 检验（大样本下检验力过强，需谨慎解读）
- Brier score（0=完美，0.25=无信息）

### 6. 临床效用
- DCA（Decision Curve Analysis）
- 明确阈值概率区间：在该区间内模型净获益优于“全干预”和“全不干预”
- 若 DCA 显示全区间无获益，必须明确报告“未发现明确临床效用区间”

### 7. 风险分层（预后模型）
- 基于 risk score 中位数或 validated 截断值分组
- KM 曲线 + log-rank 检验 + 风险人数表
- 时间依赖 ROC

### 8. 验证
- **内部验证**：Bootstrap（optimism correction, ≥200 replicates）或 嵌套 CV（outer loop 性能估计，inner loop 调参）
- **外部验证**：独立中心/不同时间段/不同平台。外部队列不参与变量筛选和阈值优化。
- 若未完成外部验证：必须在结果和结论中明确写“外部验证尚未完成，当前性能仅为开发队列表现”

## 输出
- 完整模型公示：变量名、系数、截距、预处理步骤、阈值
- AUC / C-index / time-dependent AUC（95% CI）
- 校准曲线 + 斜率/截距 + Brier score
- DCA 曲线 + 阈值区间
- KM 曲线（预后）
- 外部验证一致性报告或“未完成”声明
- provenance.json

## 边界
不包含上游差异分析、富集、PPI；专注建模与评价。
