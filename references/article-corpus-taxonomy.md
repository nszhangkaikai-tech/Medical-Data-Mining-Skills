# 解螺旋临床科研文章库 taxonomy

分类页：`https://info.helixlife.cn/articles/list/linchuangkeyan`

## 规模

- 截图确认总规模：31 页，共 619 篇
- 可枚举唯一 URL：613 篇（HTTP 200 可访问）
- 正文存储：`/tmp/helixlife_text/`（613 个 txt，每篇含 URL/Title/正文）
- 正文提取方式：requests + `article-text` div 正则抽取

## 主题聚类（基于 613 篇全量读取）

| 聚类 | 文章数 | 说明 |
|------|--------|------|
| 统计方法与检验 | 176 | t检验/方差分析/非参/卡方/秩和/相关/回归/多重比较/FDR |
| 临床研究设计 | 92 | RCT/队列/病例对照/横断面/样本量/基线/混杂/偏倚 |
| Meta分析 | 57 | PRISMA/森林图/漏斗图/异质性/敏感性分析/Egger/Begg |
| 生存分析 | 55 | KM/Cox/时依Cox/竞争风险/HR/截尾 |
| 富集与互作网络 | 41 | GO/KEGG/STRING/Cytoscape/WGCNA/ceRNA/PPI |
| 预测模型 | 36 | 列线图/AUC/C-index/DCA/校准/外部验证 |
| 数据工程与质控 | 28 | 缺失值/离群值/编码/标准化/批次效应/随访QC |
| 统计可视化 | 22 | 火山图/热图/PCA/ROC/KM/森林图/列线图/箱线图 |
| 论文写作与报告 | 17 | PRISMA/Tripod/方法学报告/审稿逻辑/图表合规 |
| AI辅助科研 | 10 | AI+Meta/AI+生存/AI+作图/自动化QC |
| 组学网络分析 | 8 | WGCNA/共表达/蛋白互作/ceRNA |
| 空间与单细胞组学 | 1 | 空间转录/单细胞测序 |
| 基因注释与ID转换 | 1 | 探针/Ensembl/symbol转换 |
| 生物标志物与诊断 | 1 | LASSO/随机森林/SVM/特征选择 |
| 其他/综合 | 68 | 跨类别综合/未明确归类 |

## 分类脑图

见 `references/corpus-brainmap.md`

## 技能仓库覆盖映射

| 脑图节点 | 对应技能 | 覆盖状态 |
|----------|----------|----------|
| 统计基础 | statistical-thinking | ✅ |
| 研究设计 | clinical-research-design | ✅ 已新增 |
| 差异筛选 | differential-gene-screening / geo-deg-analysis | ✅ |
| 生存分析 | tcga-survival | ✅ |
| 预测模型 | clinical-prediction-model | ✅ |
| 富集互作 | enrichment-analysis / ppi-network | ✅ |
| 免疫浸润 | immune-infiltration | ✅ 已新增 |
| 数据工程 | clinical-data-engineering | ✅ |
| 可视化 | biomedical-visualization / visualization | ✅ |
| 论文写作 | （待补充） | ⚠️ |
| 数据库调用 | references/databases-and-vision.md | ✅ |
| 图片识别 | references/databases-and-vision.md | ✅ |
| AI辅助 | ai-assisted-research | ✅ |
| Meta分析 | meta-analysis-bias | ✅ |
| 样本量计算 | sample-size-calculation | ✅ 已新增 |
| 偏倚控制 | bias-quality-control | ✅ 已新增 |

## 阅读策略

- 613 篇已全量读取并存储到 `/tmp/helixlife_text/`
- 按标题+正文 intro 做主题聚类
- 技能仓库扩展基于聚类缺口，不逐篇全读
