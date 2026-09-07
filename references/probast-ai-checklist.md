# PROBAST+AI 半自动评估清单（草案）

适用：诊断分类 / 预后生存 / 治疗效应 / 预测模型（含 AI/ML 模型）。

- 所有条目均需在报告中逐项给出状态：`Yes` / `No` / `Unclear` / `NA` + 证据来源。
- `automatic` 标记的条目可被 `scripts/probast_ai.py` 自动判定；`manual` 条目需人工填写。

## 1. Participants / Index（研究人群与入组）
1.1 目标人群明确定义（ICD/纳排标准）
1.2 入组时间窗（index date range）
1.3 入组来源（单中心/多中心/数据库/注册）
automatic

## 2. Outcomes / Truth Source（终点与真值）
2.1 终点定义（疾病状态/生存时间/删失/事件）
2.2 真值来源（病理/随访/电子病历/标准化评估）
2.3 终点盲法评估（ assessor blinded ）
automatic

## 3. Analysis / Model Specification（分析与模型）
3.1 特征定义与预处理（编码/标准化/缺失值规则）
3.2 模型类型（logistic/cox/RSF/GBDT/NN）
3.3 超参数选择方式（开发集/嵌套CV/独立验证集）
3.4 阈值选择（预测模型必须说明阈值来源）
automatic

## 4. Data Handling（数据处理）
4.1 缺失值处理（删除/插补/指示变量）
4.2 离群值处理（Winsorize / 截断 / 保留）
4.3 多重比较校正（FDR / Bonferroni）
automatic

## 5. Cointerventions / Competitors（共干预/对照）
5.1 是否记录共干预（用药/手术/其他治疗）
5.2 对照/竞争风险说明
manual

## 6. Dropouts / Missing（失访/缺失）
6.1 失访率及原因
6.2 缺失机制假设（MCAR/MAR/MNAR）
automatic

## 7. Sample Size / Cost（样本量/成本）
7.1 样本量计算或理由
7.2 事件/每变量数（events per variable, EPV）
automatic

## 8. External Validation（外部验证）
8.1 是否完成真正外部验证（独立机构/时间/设备）
8.2 外部集 ID 与开发集无重叠
8.3 外部集有相同终点编码与列映射
automatic

## 9. Reporting（报告）
9.1 提供完整模型 specification（变量/系数/截距/预处理/阈值）
9.2 报告校准（calibration slope/intercept / Brier / 校准图）
9.3 报告区分度（AUC / C-index / 时点 AUC 及 95%CI）
9.4 报告决策曲线/临床效用（DCA/召回率）
automatic
