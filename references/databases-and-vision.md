# 数据库调用与图片识别

本仓库的“需求底座”由两部分组成：可调用的外部数据库/工具链，以及对图片/截图的识别与反推能力。

---

## 1. 数据库调用

### 1.1 数据库与工具清单

| 数据库/工具 | 主要用途 | 调用方式 | 涉及技能 |
|-------------|----------|----------|----------|
| GEO / GEO2R | 在线差异基因初筛、热图 | 网页操作 / GEO2R | geo-online-analysis |
| DAVID | GO/KEGG 富集、ID 转换 | 网页提交基因列表 | enrichment-analysis |
| STRING | 蛋白互作网络 | 网页 API / Cytoscape 插件 | ppi-network |
| Cytoscape + Bingo | GO 有向无环图、PPI 可视化 | 桌面软件 | ppi-network / enrichment-analysis |
| TCGA GDC | 下载 count/FPKM/甲基化/SNV | 网页 / GDC Data Transfer Tool | tcga-download |
| Oncomine | 差异验证、Meta、共表达 | 网页 | oncomine-analysis |
| UCSC Xena | TCGA 整理好的临床/表达数据 | 网页下载 | tcga-survival |
| GEPIA2 | TCGA/GTEx 差异表达快速验证 | 网页 | oncomine-analysis / tcga-survival |
| R (limma/clusterProfiler/ggplot2/survival) | 本地差异分析、富集、绘图、生存 | 命令行 R | geo-deg-analysis / visualization / enrichment-analysis / tcga-survival |

### 1.2 调用顺序与依赖

典型分析链路：

1. 数据获取
   - GEO → 表达矩阵 / .CEL
   - TCGA → count 或 FPKM + clinical

2. 质控与预处理
   - GEO: affy/limma 做 RLE、降解图、标准化
   - TCGA: 通常不需要严格 QC（三级数据已整理）

3. 差异分析
   - GEO: limma（芯片）/ DESeq2（RNA-seq）
   - TCGA: limma 或 DESeq2

4. 注释与筛选
   - 探针/Ensembl → gene symbol
   - 阈值：|log2FC| > 1 且 adj.P.Val < 0.05（初筛）

5. 可视化
   - 火山图、热图、PCA
   - ggplot2 / pheatmap

6. 功能解释
   - DAVID / clusterProfiler 做 GO/KEGG
   - Cytoscape + Bingo 画有向无环图

7. 互作网络
   - STRING 构建 PPI
   - Cytoscape 可视化 + MCode 找模块

8. 临床验证（TCGA）
   - 整理临床信息
   - Kaplan-Meier + log-rank
   - 5 年生存率或时间依赖 ROC

### 1.3 R 环境依赖

建议最小包集合：

```r
# 基础与差异
library(limma)
library(DESeq2)
library(edgeR)

# 可视化
library(ggplot2)
library(pheatmap)
library(ggrepel)
library(ggplot2)
library(ggpubr)

# 富集
library(clusterProfiler)
library(org.Hs.eg.db)
library(enrichplot)
library(DOSE)

# 生存
library(survival)
library(survminer)

# 质控
library(affy)
library(genefilter)
library(sva)          # 批次效应
```

### 1.4 调用边界与限制

- **在线工具（GEO2R/DAVID/STRING/Oncomine/GEPIA2）**：依赖网络，适合快速验证和探索，不适合大样本批量自动化。
- **TCGA 大文件**：优先用 GDC Data Transfer Tool 命令行下载；网页下载适合小文件。
- **Cytoscape**：桌面软件，不能在无头服务器自动调用；PPI 网络可用 STRING 网页版替代初筛。
- **R 版本**：建议 R >= 4.2，部分包（如 enrichplot）对 R 版本有要求。

---

## 2. 图片/截图识别

### 2.1 适用场景分类

| 场景 | 输入 | 目标 |
|------|------|------|
| 数据库界面截图 | NCBI/GEO/TCGA/DAVID/STRING 页面 | 指导下一步点击或参数填写 |
| 分析结果图 | RLE、降解图、热图、火山图、KM 曲线、ROC、PPI、GO 图 | 解读统计指标、判断质量、提取关键数值 |
| 论文配图 | 方法流程图、结果组合图 | 反推分析流程、工具链、阈值设定 |

### 2.2 识别工作流

#### A. 数据库界面截图
1. 确认数据库类型：GEO / TCGA / DAVID / STRING / Oncomine
2. 定位关键区域：搜索框、分组按钮、Submit/Continue/Download
3. 输出操作路径，必要时给出点击坐标或文本指令

#### B. 分析结果图
1. 识别图型：
   - 火山图 → 读 log2FC 阈值、显著点颜色分区、top 基因标签
   - 热图 → 看样本聚类、离群样本、颜色梯度
   - KM 曲线 → 读中位生存时间、log-rank P 值、风险表
   - ROC → 读 AUC、最佳截断值、灵敏度/特异度
   - PPI → 看 degree/hub 基因、置信度边
   - GO 有向无环图 → 读富集层级、颜色深度、基因数
2. 提取关键数值
3. 判断结果质量（批次效应、阈值合理性、分组是否清晰）

#### C. 论文配图
1. 识别是方法图还是结果图
2. 反推上游数据库和工具
3. 还原统计方法（limma/DESeq2/Cox/Logistic）
4. 输出可复现的分析链路

### 2.3 常见图型的识别要点

**火山图**
- 横轴：log2FC
- 纵轴：-log10(P) 或 -log10(adj.P.Val)
- 典型阈值：|log2FC| >= 1, adj.P.Val < 0.05
- 红/蓝/灰分区 = 上调/下调/不显著

**热图**
- 行 = 基因，列 = 样本
- 颜色 = 标准化后表达量（通常 z-score）
- 目的：验证分组是否清晰、是否有离群样本

**KM 生存曲线**
- 需报告：中位生存时间、log-rank P 值、风险人数
- 常用于 TCGA 预后验证

**ROC 曲线**
- AUC 解释：0.5 随机，0.7-0.8 可用，0.8-0.9 良好，>0.9 优秀
- 需报告最佳截断值及对应灵敏/特异度

**PPI 网络**
- 边颜色 = 证据类型（实验/共表达/数据库/共注释）
- 节点大小/颜色 = degree 或富集程度
- 目标：找 hub 基因和关键模块

**GO 有向无环图**
- 颜色深度 = 富集程度
- 节点大小 = 包含基因数
- 层级 = 从具体到泛化的功能聚类

### 2.4 当前环境限制与 fallback

- 若当前模型无原生视觉能力，优先让用户提供：
  - 图注/caption
  - 关键数值（P 值、logFC、AUC、HR）
  - 作者声称使用的数据库/工具
- 复杂多子图建议拆成单张图分别识别
- 对论文配图，优先反推方法链路，而不是追求像素级复现

---

## 3. 典型任务路由

| 用户意图 | 首选技能 | 是否需要数据库/图片 |
|----------|----------|---------------------|
| “帮我看看这张火山图” | visualization | 图片识别 |
| “GSEXXXXX 找差异基因” | geo-online-analysis → geo-deg-analysis | 数据库调用 |
| “TCGA 某肿瘤 5 年生存率” | tcga-download → tcga-survival | 数据库调用 |
| “这些基因做什么功能” | enrichment-analysis | 数据库调用 |
| “蛋白互作网络怎么做” | ppi-network | 数据库调用 + 桌面软件 |
| “Oncomine 验证这个基因” | oncomine-analysis | 数据库调用 |
| “反推这篇论文的分析流程” | 组合多个技能 | 图片识别 + 数据库知识 |
