# 医学数据挖掘技能仓库使用手册

> 适用场景：GEO/TCGA/Oncomine 差异分析、生存分析、临床预测模型、Meta分析、统计作图、论文写作

---

## 一、快速上手

### 1.1 按研究问题直接进入

| 你想做 | 直接说 | 自动匹配技能链 |
|--------|--------|----------------|
| 我有一组临床数据，不知道该怎么分析 | "帮我设计临床统计分析路线" | `clinical-research-design` → `statistical-thinking` → `clinical-data-engineering` → `biomedical-visualization` |
| 我要做 GEO/TCGA 差异表达分析 | "帮我做差异基因筛选" | `geo-online-analysis` 或 `geo-download-qc` → `differential-gene-screening` → `visualization` → `enrichment-analysis` |
| 我要做预后/预测模型 | "帮我构建预后预测模型" | `tcga-survival` → `clinical-prediction-model` → `biomedical-visualization` → `omics-integration-validation` |
| 我要做 Meta 分析 | "帮我做 Meta 分析" | `statistical-thinking` → `meta-analysis-bias` → `biomedical-visualization` → `paper-writing` |
| 我要算样本量 | "帮我计算样本量" | `sample-size-calculation` |
| 我要写论文/回复审稿 | "帮我把结果写成论文" | `paper-writing` → `biomedical-visualization` |
| 我要做免疫浸润 | "帮我做免疫浸润分析" | `clinical-data-engineering` → `immune-infiltration` → `biomedical-visualization` |

### 1.2 一句话调用示例

```
用户：帮我看看这个数据该用什么统计方法
→ 触发：statistical-thinking

用户：我要做 KM 生存曲线和 Cox 回归
→ 触发：tcga-survival

用户：帮我画发表级的 ROC 和校准曲线
→ 触发：biomedical-visualization

用户：我要把结果写成 SCI 论文
→ 触发：paper-writing
```

---

## 二、标准分析 SOP（6 阶段）

### 阶段 1：问题定义与设计
**目标**：把模糊想法变成可执行的研究方案

**必做**
1. 明确研究问题（差异/预后/诊断/预测/验证）
2. 选择研究设计（RCT/队列/病例对照/横断面）
3. 计算样本量
4. 制定入排标准与数据字典

**推荐技能**
- `clinical-research-design`
- `sample-size-calculation`

**输出物**
- 研究问题一句话描述
- 研究设计类型
- 样本量计算报告
- 入排标准清单

---

### 阶段 2：数据获取与质控
**目标**：获得干净、可分析的数据集

**必做**
1. 下载公共数据库（GEO/TCGA/Oncomine）
2. 临床数据清洗与编码
3. 批次效应/缺失值/离群值处理
4. 注释与 ID 转换

**推荐技能**
- `geo-download-qc` / `geo-online-analysis`
- `tcga-download`
- `clinical-data-engineering`
- `gene-annotation`

**输出物**
- 表达矩阵 / 临床宽表
- QC 报告（RLE、降解图、PCA）
- 数据字典

---

### 阶段 3：统计分析
**目标**：回答研究问题，得到统计结论

**必做**
1. 选择统计方法（参数/非参/回归）
2. 差异筛选（火山图阈值）
3. 生存分析（KM/Cox）
4. 预测模型（区分度/校准/临床效用）
5. 富集与互作网络

**推荐技能**
- `statistical-thinking`
- `differential-gene-screening`
- `geo-deg-analysis`
- `tcga-survival`
- `clinical-prediction-model`
- `enrichment-analysis`
- `ppi-network`

**输出物**
- 差异基因列表
- 独立预后因素
- 模型性能指标（AUC/C-index/DCA）
- 富集/网络结果表

---

### 阶段 4：结果表达
**目标**：把数字变成可发表的图

**必做**
1. 统计可视化（火山图/热图/ROC/KM/森林图/列线图）
2. 图片/截图识别与判读（如果用户给的是截图）
3. 结果解读与结论提炼

**推荐技能**
- `biomedical-visualization`
- `visualization`

**输出物**
- 可直接投稿的统计图（TIFF/PDF/SVG）
- 图注与统计量标注

---

### 阶段 5：验证与深化
**目标**：让结论更可信、更完整

**必做**
1. 独立队列/公共数据库验证
2. qPCR/Western/实验验证
3. 免疫浸润/多组学整合

**推荐技能**
- `omics-integration-validation`
- `oncomine-analysis`
- `immune-infiltration`
- `biomarker-discovery`

**输出物**
- 验证结果表
- 候选标志物证据链

---

### 阶段 6：论文产出
**目标**：把分析结果整理成可投稿的论文

**必做**
1. 方法学报告（PRISMA/Tripod/STROBE）
2. 结果表述与图表排版
3. 审稿逻辑与回复

**推荐技能**
- `paper-writing`
- `meta-analysis-bias`

**输出物**
- 结构化论文初稿（IMRD）
- 审稿回复要点
- 图表合规检查表

---

## 三、技能详细说明

### 3.1 统计基础层

#### statistical-thinking（统计基础思维）
- **解决**：该用什么检验、怎么解读 P 值和效应量
- **触发词**：描述性统计、推断性统计、P值、效应量、正态性、方差齐性
- **输入**：数据类型、研究问题、样本量/分组
- **输出**：推荐统计方法 + 结果解读 + 配套图表建议
- **边界**：不包含具体建模和绘图；只解决“选什么方法”和“怎么读懂结果”

#### clinical-research-design（临床研究设计）
- **解决**：研究设计方案审查、偏倚控制、质量评价
- **触发词**：RCT、队列、病例对照、横断面、样本量、基线、混杂、偏倚、NOS
- **输入**：研究类型、主要结局、效应量/把握度/α（可选）
- **输出**：研究设计合理性评估 + 偏倚控制清单 + 质量评价工具选择
- **边界**：不包含具体统计建模和绘图；偏重于“研究是否可发表”的方法学审查

#### sample-size-calculation（样本量计算）
- **解决**：样本量估算与把握度分析
- **触发词**：sample size、power、把握度、effect size
- **输入**：研究设计、主要终点类型、效应量/α/把握度、脱落率
- **输出**：总样本量 + 各组分配 + 敏感性分析表
- **支持终点**：二分类/连续/生存/AUC

### 3.2 数据获取与质控层

#### geo-online-analysis（GEO 在线分析）
- **解决**：GEO2R 快速初筛，不需要下载原始数据
- **触发词**：GEO2R、在线分析、快速筛差异
- **边界**：仅做快速初筛；正式分析建议走 `geo-download-qc` + `geo-deg-analysis`

#### geo-download-qc（GEO 下载与 QC）
- **解决**：GEO 原始数据下载与芯片质量评估
- **触发词**：GEO下载、.CEL文件、芯片质量、RLE、降解图
- **输出**：原始数据 + QC 报告

#### tcga-download（TCGA 下载）
- **解决**：TCGA GDC 数据下载与整理
- **触发词**：TCGA下载、GDC、legacy、count/FPKM
- **输出**：表达矩阵 + 临床数据 + 数据字典

#### clinical-data-engineering（临床数据工程）
- **解决**：临床数据清洗与编码
- **触发词**：缺失值、离群值、哑变量、基线表、重复值、数据清洗
- **输出**：可直接建模的宽表 + 数据字典

#### gene-annotation（基因注释）
- **解决**：探针/Ensembl/别名转 gene symbol
- **触发词**：ID转换、探针注释、Ensembl、symbol

### 3.3 核心分析层

#### differential-gene-screening（差异基因筛选策略）
- **解决**：阈值设定、log2FC、padj、批次效应、meta 整合
- **触发词**：阈值设定、log2FC、padj、批次效应、meta整合
- **输出**：差异基因列表 + 阈值依据 + 上下调分层

#### geo-deg-analysis（Limma 差异分析）
- **解决**：已有表达矩阵上的正式 Limma 差异分析
- **触发词**：Limma、差异基因、topTable、annotation
- **输出**：topTable + 注释结果

#### tcga-survival（TCGA 生存分析）
- **解决**：TCGA 临床预后分析
- **触发词**：KM、Cox、log-rank、生存曲线、HR
- **输出**：KM 曲线 + 风险表 + 独立预后因素

#### clinical-prediction-model（临床预测模型）
- **解决**：预测模型构建与评价
- **触发词**：AUC、C-index、DCA、校准、外部验证、列线图
- **输出**：区分度/校准度/临床效用 + 可落地评分工具

#### enrichment-analysis（功能富集）
- **解决**：GO/KEGG/DAVID/clusterProfiler 功能富集
- **触发词**：GO、KEGG、通路、富集

#### ppi-network（蛋白互作网络）
- **解决**：STRING/Cytoscape/Bingo 蛋白互作网络构建
- **触发词**：蛋白互作、PPI、网络图、Cytoscape

#### oncomine-analysis（Oncomine 验证）
- **解决**：Oncomine 数据库差异验证/共表达
- **触发词**：Oncomine、共表达、差异验证

#### omics-integration-validation（多组学整合与验证）
- **解决**：独立队列/公共数据库/实验验证
- **触发词**：独立队列、qPCR、Western、实验验证、泛癌、免疫浸润
- **输出**：验证证据链 + 跨队列一致性评估

#### biomarker-discovery（生物标志物发现）
- **解决**：从差异分析到机器学习筛选及验证
- **触发词**：标志物、biomarker、LASSO、随机森林、SVM、特征选择
- **输出**：候选标志物列表 + 验证证据链

### 3.4 结果表达层

#### visualization（差异基因可视化）
- **解决**：热图、火山图、PCA、聚类
- **触发词**：热图、火山图、PCA、聚类

#### biomedical-visualization（发表级统计可视化）
- **解决**：火山图/ROC/校准曲线/DCA/KM/漏斗图/列线图
- **触发词**：ROC、校准曲线、DCA、KM、漏斗图、列线图、箱线图、气泡图
- **输出**：可直接投稿的图

#### meta-analysis-bias（Meta 偏倚评估）
- **解决**：漏斗图、Egger/Begg 检验、发表偏倚
- **触发词**：Meta分析、漏斗图、发表偏倚、Egger
- **输出**：森林图 + 偏倚评估报告

#### paper-writing（论文写作与报告）
- **解决**：从结果到论文的可执行写作框架
- **触发词**：论文写作、方法学报告、审稿回复、图表合规、PRISMA、Tripod
- **输出**：结构化论文初稿 + 审稿回复要点 + 图表检查清单

### 3.5 底座与增强层

#### ai-assisted-research（AI 辅助科研）
- **解决**：AI+Meta、AI+作图、AI+生存分析、自动化 QC
- **触发词**：AI助力、自动化、Meta全流程、QC自动化
- **原则**：AI 提效，但统计判断和临床解释必须人工校验

#### immune-infiltration（免疫浸润分析）
- **解决**：CIBERSORT/xCell/ssGSEA 免疫细胞亚群分析
- **触发词**：免疫浸润、CIBERSORT、xCell、ssGSEA
- **输出**：免疫评分 + 亚群-预后关联

#### references/databases-and-vision.md（数据库与图片识别底座）
- **覆盖**：9 个数据库/工具调用顺序、R 包依赖、图片/截图识别工作流、任务路由表
- **适用**：所有需要调用数据库或识别科研图表的场景

---

## 四、技能组合推荐（速查表）

| 研究类型 | 推荐技能组合 |
|----------|-------------|
| GEO 差异表达 | geo-online-analysis → differential-gene-screening → visualization → enrichment-analysis → ppi-network |
| TCGA 预后模型 | tcga-download → tcga-survival → clinical-prediction-model → biomedical-visualization → omics-integration-validation |
| 临床统计 | clinical-research-design → statistical-thinking → clinical-data-engineering → biomedical-visualization |
| Meta 分析 | statistical-thinking → meta-analysis-bias → biomedical-visualization → paper-writing |
| 标志物发现 | differential-gene-screening → biomarker-discovery → omics-integration-validation → clinical-prediction-model |
| 免疫浸润 | tcga-download → immune-infiltration → biomedical-visualization → clinical-prediction-model |
| 论文全流程 | clinical-research-design → statistical-thinking → biomedical-visualization → paper-writing |

---

## 五、常见问题 FAQ

**Q：我是临床医生，不会 R，能用这个 skill 吗？**
可以。skill 会给出完整代码模板和分析思路，你只需按步骤运行并解读结果。

**Q：我的数据不是肿瘤数据，能用吗？**
可以。TCGA/GEO 技能不限于肿瘤，只要是有表达矩阵和临床数据的研究都适用。

**Q：我要做单细胞/空间转录组，当前 skill 覆盖吗？**
当前已有基础框架（差异筛选、可视化、富集），但单细胞专属流程（降维/聚类/细胞注释）和空间转录组（去卷积/空间可变基因）是已知缺口，可以基于现有技能扩展。

**Q：AI 能帮我直接写论文吗？**
`ai-assisted-research` 可以辅助生成初稿、整理结果、生成代码，但最终统计判断、临床解释和论文逻辑需要人工完成。

**Q：技能之间可以串联使用吗？**
可以。顶层 SOP 已经把 6 个阶段和技能链固化了，建议按阶段顺序串接。

---

## 六、更新日志

- 2026-09-01：基于 613 篇文章全量读取，反推扩展技能仓库到 22 个技能
- 2026-09-01：新增 clinical-research-design / sample-size-calculation / immune-infiltration / paper-writing
- 2026-09-01：固化分类脑图和文章 taxonomy
