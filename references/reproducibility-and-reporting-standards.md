# 可复现性与报告规范（强制前置门禁）

> 所有 `medical-data-mining` 技能运行前必须读取本文件。

## 1. 研究问题路由表（唯一主类型）

| 主类型 | 典型问题 | 预先定义终点 | 主规范 | 禁止混用 |
|--------|----------|--------------|--------|----------|
| 探索性生信 | 差异/通路/网络探索 | 无强制单一终点，但需声明主要目标 | MINSEQE/FAIR/期刊生信指南 | 不得声称临床决策价值 |
| 诊断分类 | 能否区分疾病/亚型 | AUC/灵敏度/特异度/NPV/PPV | STARD 2015 / TRIPOD+AI | 不得改用 OS/DFS 作为主要终点 |
| 预后研究 | 生存/复发/进展时间 | OS/DFS/RFS/PFS | STROBE / TRIPOD+AI | 不得仅用横断面数据做生存曲线 |
| 治疗效应 | 干预是否优于对照 | RD/RR/HR（时间事件或二分类） | CONSORT 2017（RCT）/ STROBE（观察性） | 不得将相关关系解释为因果关系 |
| 系统综述/Meta | 综合多研究证据 | PICO 明确效应量 | PRISMA 2020 | 不得省略研究质量评价 |

## 2. 数据状态声明（每次运行必填）

```yaml
data_mode: real | simulated | not_collected
data_path: ""
endpoint: ""  # 预先定义，禁止后验替换
truth_source: ""  # 金标准或真实结局变量名
censoring_def: ""  # 删失编码规则，仅生存/时间事件
train_val_test_split: ""  # 若适用，需说明分层变量和随机种子
external_validation_status: completed | pending | not_planned | unavailable
```

## 3. 报告规范前置清单

根据研究类型，自动生成并逐项填写：

### 3.1 诊断分类模型
- [ ] STARD 2015 检查表（目标人群、数据采集、模型开发、验证、临床效用）
- [ ] TRIPOD+AI 声明（AI 组件、训练数据、可解释性、公平性）
- [ ] PROBAST+AI 偏倚风险（参与者、预测因子、结局、分析）
- [ ] REMARK 注释（若为生物标志物）

### 3.2 预后/预测模型
- [ ] TRIPOD+AI 检查表（标题、摘要、导言、方法、结果、讨论）
- [ ] PROBAST+AI 偏倚风险评估
- [ ] STROBE 核心项（研究设计、参与者、变量、统计方法）
- [ ] 时间依赖性能指标声明（1年/3年/5年 AUC/C-index）
- [ ] 校准报告（校准曲线 + 斜率/截距 或 Hosmer-Lemeshow）
- [ ] 决策曲线（DCA）及阈值区间说明

### 3.3 治疗效应（RCT）
- [ ] CONSORT 2017 流程图的每个盒子有数据
- [ ] SPIRIT 计划书（方案注册号、主要/次要终点、分析人群）
- [ ] 盲法/分配隐藏/ITT 原则声明
- [ ]  harms 报告

### 3.3 治疗效应（观察性）
- [ ] STROBE 检查表
- [ ] STROBE-ME（中介分析）或 RECORD（常规数据）如适用
- [ ] 混杂控制层级说明
- [ ] 敏感性分析（如 E-value、PSM 平衡性、负对照暴露）

### 3.4 探索性生信
- [ ] 数据来源与版本（GEO 系列号、TCGA 版本、测序平台）
- [ ] 预处理流程（标准化、批次校正、过滤阈值）
- [ ] 多重比较校正方法（FDR BH / Bonferroni / q值）
- [ ] 验证策略（内部交叉验证 / 独立队列 / 实验验证）
- [ ] 基因/蛋白 ID 版本与注释数据库版本
- [ ] 富集分析背景基因集与数据库版本（GO BP/MF/CC, KEGG, Reactome）

### 3.5 系统综述/Meta
- [ ] PRISMA 2020 流程图（7 个节点均有数据）
- [ ] PICO 表
- [ ] 检索策略（数据库、日期、检索式）
- [ ] 研究质量/偏倚工具（Cochrane RoB 2 / NOS / QUADAS-2 / ROBINS-I）
- [ ] 效应量换算与合并模型选择依据
- [ ] 异质性检验（Q 检验、I²、tau²）
- [ ] 敏感性分析与亚组预设
- [ ] 发表偏倚评估（Egger/Begg，仅当研究数 ≥10 时报告漏斗图）

## 4. 数据一致性校验规则

### 4.1 删失编码
- 必须全局一致：0 = 删失（censor），1 = 事件（event）；或反之，但必须文档化
- 禁止同一数据集中混用编码
- 若使用 competing risk，必须声明 Fine-Gray 模型而非 Cox

### 4.2 预测模型终点
- 诊断模型：终点为二分类金标准，报告 AUC/灵敏度/特异度/NPV/PPV/PLR/NLR
- 预后模型：终点为时间至事件，报告 C-index / time-dependent AUC / 指定时间点 Brier / 校准曲线
- 禁止将诊断 AUC 直接套用到生存数据，或将生存 HR 包装为诊断性能

### 4.3 模拟数据规则
- 所有模拟值必须通过 `simulated` 标记
- 报告顶部必须出现不可移除的 DEMO 水印
- 结论栏必须出现“本结果基于模拟数据，不得用于临床决策或作为发表依据”
- 禁止出现“可用于临床决策”“建议临床采用”等措辞

## 5. Provenance 规范

见 `references/provenance-schema.md`。

## 6. 基线表标准

- 必须报告全部关键协变量（年龄、性别、分期、合并症、主要治疗）
- 连续变量：均值 ± SD 或 中位数（IQR），附检验方法（t / Mann-Whitney / KS）
- 分类变量：频数（百分比），附检验方法（卡方 / Fisher）
- 报告标准化均值差异（SMD）或标准化差异，|SMD| < 0.1 视为小差异
- 禁止仅凭 P > 0.05 断言“基线可比”；大样本下 P 值易显著，应以 SMD 为主

## 7. 差异分析标准

- 必须声明输入尺度：raw counts / TPM / FPKM / log2CPM / normalized expression
- QC 步骤：离群样本检测、PCA/聚类检查、批次效应评估
- 批次/混杂校正：ComBat / limma removeBatchEffect / 协变量纳入设计矩阵
- 设计矩阵：明确 ~ condition + batch + covariates
- FDR 方法：Benjamini-Hochberg（默认）或 Bonferroni，禁止 raw P 冒充 adj.P.Val

## 8. 生存分析标准

- 必须声明：index date（入组/确诊/手术/首次随访）、follow-up schema（active vs passive）、censoring rule（删失定义）
- KM + risk table + log-rank 是基础 trio
- Cox 多变量必须包含单因素中 P < 0.05 或临床重要的变量
- 比例风险假设：Schoenfeld residuals test + 图示检查
- 若比例风险不满足：分层 Cox / 时间依赖系数 / 参数生存模型

## 9. 预测模型标准

### 9.1 开发
- 完整模型公示：变量名、系数/截距、预处理步骤、阈值
- 事件数/变量比（EPV）≥ 10–20
- 缺失值处理：多重插补或完整案例分析，禁止中位数填充后声称模型可用

### 9.2 内部验证
- Bootstrap（optimism correction, ≥ 200 replicates）
- 或 嵌套交叉验证（outer CV for performance, inner CV for tuning）
- 禁止使用测试集做特征选择或阈值优化

### 9.3 外部验证
- 必须声明：外部队列来源、时间窗口、平台/中心差异、样本量
- 若未完成：必须写“外部验证尚未完成，当前性能仅为开发队列表现”
- 禁止用同一数据集的不同随机拆分冒充外部验证

## 10. Meta 分析标准

- 检索式必须可复现：数据库、日期、语言限制、检索字段
- 筛选流程：PRISMA 流程图，含重复筛选一致性（kappa）
- 数据提取：双人独立提取 +  dispute resolution
- 效应量换算：统一指标（OR/RR/HR/SMD），注明换算公式
- 异质性：Q 检验 p 值、I²、tau²
- 模型选择：I² < 50% 且 Q 不显著时可考虑固定效应；否则随机效应
- 敏感性：剔除小样本/低质量研究后的合并值变化
- 亚组：必须预先注册，避免数据驱动分亚组
- 发表偏倚：Egger/Begg 仅在研究数 ≥ 10 时报告；漏斗图仅作辅助

## 11. PPI/富集标准

- 背景基因集：必须声明（例如全基因组 / 表达基因 / 差异基因输入集）
- 注释数据库：版本号、物种、发布时间
- 富集方法：超几何检验 / 过表征分析 / GSEA / clusterProfiler
- 多重校正：FDR BH（默认）或 Bonferroni
- 若为模拟数据：必须在图注和正文中标注“模拟网络，不做生物学实证解读”

## 12. 验收测试清单

```
tests:
  endpoint_indicator_match:
    description: "诊断模型不能报 OS HR；预后模型不能只报 AUC"
    required: true
  numbers_consistency:
    description: "所有表格数字必须与源结果对象（DataFrame/JSON）一致"
    required: true
  censoring_encoding:
    description: "删失编码全局一致，且与数据字典匹配"
    required: true
  train_val_isolation:
    description: "训练/验证/测试严格隔离，无信息泄漏"
    required: true
  no_fictional_external:
    description: "未完成的外部验证必须明确标注，不得模拟数值"
    required: true
  no_unsubstantiated_clinical_claims:
    description: "禁止出现可用于临床决策等未经验证的表述"
    required: true
  demo_watermark:
    description: "模拟数据报告必须包含不可移除的 DEMO 水印"
    required_when: "data_mode == 'simulated'"
```

## 13. 禁止项清单

- [ ] 禁止 raw P 值冒充 padj/adj.P.Val
- [ ] 禁止将相关关系解释为因果关系（观察性数据）
- [ ] 禁止同一数据集随机拆分后称“外部验证”
- [ ] 禁止研究数 < 10 时声称漏斗图证明无发表偏倚
- [ ] 禁止用 AUC 评估纯生存数据（应使用 C-index / time-dependent AUC）
- [ ] 禁止基线表仅报告 P 值，忽略 SMD/效应量
- [ ] 禁止删除删失数据后做完整病例分析并声称无偏
- [ ] 禁止模拟数据使用“证据强度高”“建议临床采用”等措辞
- [ ] 禁止 PPI/富集随机生成数值后做确定性生物学结论
- [ ] 禁止未说明 train/test 流程就报告验证指标
