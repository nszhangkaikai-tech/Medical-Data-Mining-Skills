# 解螺旋临床科研文章库分类脑图

基于 613 篇全量正文读取后的主题聚类结果。

## 聚类分布

| 聚类 | 文章数 | 说明 |
|------|--------|------|
| 统计方法与检验 | 176 | t检验/方差分析/非参/卡方/回归/相关/多重比较/FDR |
| 临床研究设计 | 92 | RCT/队列/病例对照/横断面/样本量/基线/混杂/偏倚 |
| Meta分析 | 57 | PRISMA/森林图/漏斗图/异质性/敏感性分析/Egger/Begg |
| 生存分析 | 55 | KM/Cox/时依Cox/竞争风险/HR/截尾 |
| 富集与互作网络 | 41 | GO/KEGG/STRING/Cytoscape/WGCNA/ceRNA/PPI |
| 预测模型 | 36 | 列线图/AUC/C-index/DCA/校准/外部验证 |
| 数据工程与质控 | 28 | 缺失值/离群值/编码/标准化/批次效应/随访QC |
| 统计可视化 | 22 | 火山图/热图/PCA/ROC/KM/森林图/列线图/箱线图 |
| 论文写作与报告 | 17 | PRISMA/Tripod/方法学报告/审稿回复/图表合规 |
| AI辅助科研 | 10 | AI+Meta/AI+生存/AI+作图/自动化QC |
| 组学网络分析 | 8 | WGCNA/共表达/蛋白互作/ceRNA |
| 空间与单细胞组学 | 1 | 空间转录/单细胞测序 |
| 基因注释与ID转换 | 1 | 探针/Ensembl/symbol转换 |
| 生物标志物与诊断 | 1 | LASSO/随机森林/SVM/特征选择 |
| 其他/综合 | 68 | 未明确归类或跨类别综合 |

## 知识脑图 DOT

```dot
digraph 医学科研知识脑图 {
  rankdir=LR;
  node [shape=box, style=rounded, fontname="Microsoft YaHei", fontsize=11];
  edge [fontname="Microsoft YaHei", fontsize=9];

  数据层 [label="数据层\n临床数据/组学矩阵/公共数据库", fillcolor="#E3F2FD", style=filled];
  统计基础 [label="统计基础\n描述/推断统计、P值/效应量、正态性、方差齐性\n分布类型、多重比较、FDR、假设检验前提核查", fillcolor="#F3E5F5", style=filled];
  研究设计 [label="研究设计\nRCT/队列/病例对照/横断面\n样本量计算、入排标准、基线均衡\n混杂控制、偏倚识别、质量评价(NOS/Oxford)", fillcolor="#F3E5F5", style=filled];
  差异筛选 [label="差异筛选\n火山图阈值(log2FC/padj)、热图验证\nRNA-seq/蛋白质组/芯片/单细胞", fillcolor="#E8F5E9", style=filled];
  生存分析 [label="生存分析\nKM曲线、Cox/时依Cox/竞争风险\nHR解释、比例风险假定、截尾处理", fillcolor="#E8F5E9", style=filled];
  预测模型 [label="预测模型\nLogistic/Cox、AUC/C-index\n校准曲线、DCA、Hosmer-Lemeshow\n过拟合控制、外部验证、多中心验证", fillcolor="#E8F5E9", style=filled];
  富集互作 [label="富集与互作网络\nGO/KEGG/DO\nSTRING/Cytoscape/Bingo\nWGCNA/ceRNA/蛋白互作", fillcolor="#E8F5E9", style=filled];
  免疫浸润 [label="免疫浸润分析\nCIBERSORT/xCell/ssGSEA\n免疫细胞亚群与预后关联", fillcolor="#E8F5E9", style=filled];
  数据工程 [label="数据工程与质控\n缺失值/离群值/重复值\n编码转换/格式标准化\n批次效应/随访质量控制", fillcolor="#E8F5E9", style=filled];
  可视化 [label="统计可视化\n火山图/热图/PCA/聚类\nROC/PR/DCA/KM\n森林图/漏斗图/列线图\n箱线图/气泡图/棒棒糖图", fillcolor="#FFF3E0", style=filled];
  论文写作 [label="论文写作与报告\n方法学报告(PRISMA/Tripod)\n结果表述、审稿逻辑\n图表合规、回复审稿意见", fillcolor="#FFF3E0", style=filled];
  数据库调用 [label="数据库调用\nGEO/GEO2R、TCGA GDC\nDAVID、STRING\nCytoscape+Bingo\nOncomine、UCSC Xena\nGEPIA2、R 本地链路", fillcolor="#ECEFF1", style=filled];
  图片识别 [label="图片/截图识别\n火山图判读\nKM/ROC/森林图判读\n论文配图反推分析链路", fillcolor="#ECEFF1", style=filled];
  AI辅助 [label="AI辅助科研\nAI+Meta分析\nAI+生存分析\nAI+统计作图\n自动化QC与数据清洗\n论文初稿生成", fillcolor="#ECEFF1", style=filled];

  数据层 -> 数据工程;
  统计基础 -> 研究设计;
  统计基础 -> 差异筛选;
  统计基础 -> 生存分析;
  统计基础 -> 预测模型;
  研究设计 -> 预测模型;
  研究设计 -> Meta分析;
  数据工程 -> 差异筛选;
  数据工程 -> 生存分析;
  数据工程 -> 预测模型;
  数据库调用 -> 差异筛选;
  数据库调用 -> 生存分析;
  数据库调用 -> 可视化;
  差异筛选 -> 可视化;
  差异筛选 -> 富集互作;
  差异筛选 -> 免疫浸润;
  生存分析 -> 预测模型;
  生存分析 -> 可视化;
  富集互作 -> 可视化;
  免疫浸润 -> 预测模型;
  预测模型 -> 可视化;
  预测模型 -> 论文写作;
  可视化 -> 论文写作;
  可视化 -> 图片识别;
  图片识别 -> 可视化;
  图片识别 -> 差异筛选;
  AI辅助 -> 统计基础;
  AI辅助 -> 可视化;
  AI辅助 -> 论文写作;
  AI辅助 -> 数据工程;
  统计基础 -> Meta分析;
  研究设计 -> Meta分析;
  可视化 -> Meta分析;
  Meta分析 -> 论文写作;
}
```

## 技能仓库映射

当前 `medical-data-mining` 技能仓库覆盖情况：

| 脑图节点 | 对应技能 | 覆盖状态 |
|----------|----------|----------|
| 统计基础 | statistical-thinking | ✅ 已覆盖 |
| 研究设计 | clinical-prediction-model / meta-analysis-bias | ✅ 已覆盖 |
| 差异筛选 | differential-gene-screening / geo-deg-analysis | ✅ 已覆盖 |
| 生存分析 | tcga-survival | ✅ 已覆盖 |
| 预测模型 | clinical-prediction-model | ✅ 已覆盖 |
| 富集互作 | enrichment-analysis / ppi-network | ✅ 已覆盖 |
| 免疫浸润 | （待补充） | ⚠️ 部分覆盖 |
| 数据工程 | clinical-data-engineering | ✅ 已覆盖 |
| 可视化 | biomedical-visualization / visualization | ✅ 已覆盖 |
| 论文写作 | （待补充） | ⚠️ 部分覆盖 |
| 数据库调用 | references/databases-and-vision.md | ✅ 底座已覆盖 |
| 图片识别 | references/databases-and-vision.md | ✅ 底座已覆盖 |
| AI辅助 | ai-assisted-research | ✅ 已覆盖 |

## 建议扩展

基于 613 篇文章聚类，建议新增：
1. `sample-size-calculation` — 样本量计算与把握度（58篇）
2. `bias-quality-control` — 偏倚控制与质量评价（6篇+Meta质量评价）
3. `immune-infiltration` — 免疫浸润分析（CIBERSORT/xCell/ssGSEA）
