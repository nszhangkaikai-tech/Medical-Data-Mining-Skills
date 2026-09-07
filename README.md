<div align="center">

# 🧬 Medical Data Mining Skills

### 面向医学研究与生物信息分析的 AI Skills 工具箱

从研究问题、数据准备到模型训练、结果可视化与研究报告，
让每一步都有明确输入、可检查的结果和可追溯的依据。

**研究设计 · 临床预测 · GEO / TCGA · 统计绘图 · 可复现报告**

[快速开始](#快速开始) · [选择入口](#第一次使用从哪个入口开始) · [使用示例](#典型使用场景) · [能力与边界](#当前实现与使用边界) · [参与贡献](#参与贡献)

</div>

---

## 这个项目能帮你做什么？

医学研究往往涉及多个环节：明确终点、整理数据、选择分析方法、训练模型、验证结果，再把图表和文字组织成报告。

本项目把这些环节整理成可供 AI 助手读取的研究技能，并为**诊断分类和预后生存分析**提供可运行的 Python 工作流。你可以从当前研究问题切入，也可以直接运行示例，查看数据、模型、指标和报告如何连接起来。

适合医学研究者、生物信息分析人员，以及希望扩展医学分析工具的开发者。使用真实研究数据前，仍需具备相应的统计判断与数据使用权限。

## 第一次使用：从哪个入口开始？

| 你现在需要做的事 | 建议入口 | 重点产出 |
| --- | --- | --- |
| 有研究想法，还没明确设计和终点 | [clinical-research-design](clinical-research-design/SKILL.md)、[statistical-thinking](statistical-thinking/SKILL.md) | 研究问题、设计思路、分析注意事项 |
| 准备样本量估算或清理临床数据 | [sample-size-calculation](sample-size-calculation/SKILL.md)、[clinical-data-engineering](clinical-data-engineering/SKILL.md) | 估算假设、字段与数据质量检查 |
| 用临床变量构建预测模型 | [clinical-prediction-model](clinical-prediction-model/SKILL.md) | 建模方案、训练与验证结果 |
| 从 GEO 数据开始做差异分析 | [geo-download-qc](geo-download-qc/SKILL.md)、[geo-deg-analysis](geo-deg-analysis/SKILL.md) | 数据准备、质控与差异分析指引 |
| 获取 TCGA 数据并开展生存分析 | [tcga-download](tcga-download/SKILL.md)、[tcga-survival](tcga-survival/SKILL.md) | 数据获取与生存分析指引 |
| 解释候选基因的功能与互作 | [enrichment-analysis](enrichment-analysis/SKILL.md)、[ppi-network](ppi-network/SKILL.md) | 富集结果、互作网络分析 |
| 把已有结果整理成科研图表 | [biomedical-visualization](biomedical-visualization/SKILL.md) | 图表、图注与数据来源说明 |
| 整理证据、写作或规划后续验证 | [paper-writing](paper-writing/SKILL.md)、[omics-integration-validation](omics-integration-validation/SKILL.md) | 写作结构、验证方案与待补证据 |

这些入口包含研究方法指导；**并非每个入口都对应独立、全自动的分析程序**。当前可直接执行的主流程见下文。

## 快速开始

### 1. 准备运行环境

下载本仓库，在仓库根目录执行。建议使用独立 Python 虚拟环境；项目曾在 Python 3.12 环境中进行测试。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

主要依赖为 NumPy、Matplotlib 和 NetworkX。完整版本要求见 [requirements.txt](requirements.txt)。演示脚本使用 Bash，适用于 macOS / Linux；Windows 用户可在 WSL 中运行。

### 2. 跑通一个完整示例

```bash
bash scripts/demo_end_to_end.sh
```

脚本会创建独立临时目录，准备模拟数据，并依次执行诊断模型训练、预后模型训练、图表生成、预后外部验证和测试。终端中的 `TEST_DIR` 是本次产物目录。

> 示例用于理解工具链。模拟数据中的指标和图表不代表真实队列上的研究结果；图表模块仍在持续验收，已知限制见下文。

### 3. 让 AI 助手按技能协作

把仓库放在 AI 助手可读取的位置，指定总入口 [SKILL.md](SKILL.md) 或某个子技能文件，并提供你的研究目标和输入数据说明。例如：

```text
请读取本仓库 SKILL.md 和 clinical-prediction-model/SKILL.md。
我想研究患者的预后风险。先检查终点、随访时间、事件编码、
缺失值和训练/验证划分，再说明适用的建模流程。
不要把没有计算的指标写进报告。
```

当前文档提供文件读取和 Python CLI 两种使用方式；不假设所有助手都已支持一键插件安装或同名斜杠命令。

## 典型使用场景

### 🩺 临床预测：从数据到训练与验证

```text
请使用 clinical-prediction-model 技能检查我的诊断分类数据。
结局列是 outcome，1 表示阳性，0 表示阴性。
请先核对字段、数据来源与样本划分，训练逻辑回归模型，
输出验证集指标，并说明哪些结果还需要外部验证。
```

已经准备好 CSV 时，可以直接初始化项目：

```bash
python scripts/setup_project.py \
  --study-type diagnostic \
  --output work/diagnostic-study \
  --data /absolute/path/cohort.csv \
  --id-col id \
  --outcome-col outcome

python scripts/run_workflow.py \
  --manifest work/diagnostic-study/manifest.json \
  --train --plots
```

`--output` 必须指向尚未存在的项目目录。运行真实研究前，请检查生成的 `manifest.json`，确认数据模式、终点、字段映射、预测变量与样本划分符合研究方案。

预后分析使用 `--study-type prognostic`，并通过 `--time-col` 和 `--event-col` 指定随访时间与事件字段。当前训练器采用 Cox PH 模型。

### 🧪 功能探索：从候选基因到富集与互作

```text
请使用 enrichment-analysis 和 ppi-network 技能。
我的候选基因列表已经准备好，请先核对物种和基因标识，
说明富集背景及筛选参数，再查询数据库并保存来源信息。
请区分统计关联、功能注释与机制证据。
```

已有基因列表时，可分别调用接口脚本：

```bash
python scripts/enrichment.py --help
python scripts/ppi.py --help
```

g:Profiler 和 STRING 客户端默认不联网。显式添加 `--allow-network` 才会发起查询；离线模式记录“未执行”，不会生成替代的数据库结果。联网前应确认提交的基因列表可以发送到相应外部服务。

### 📊 结果表达：生成与分析数据一致的图表

```text
请使用 biomedical-visualization 技能整理本次分析结果。
诊断模型展示 ROC、PR 和校准曲线；预后模型展示 KM 曲线。
请注明数据集、分组规则、坐标含义和样本量，
导出高清 PNG 与矢量图；缺少依据的统计量请明确标记未计算。
```

已有预测产物时，可单独运行：

```bash
python scripts/run_workflow.py \
  --manifest work/diagnostic-study/manifest.json \
  --plots
```

当前绘图模块包含 ROC、PR、校准与 KM，并提供森林图、火山图、热图、富集点图和 PPI 网络图函数。后五类需提供对应的上游结果，不能仅凭研究类型自动生成；它们与主流程的接入程度也不同。

## 一次运行会留下什么？

| 产物 | 用途 |
| --- | --- |
| `manifest.json` | 记录研究设置、输入来源、样本划分与模型信息 |
| `metrics.json` | 保存模型评估指标 |
| `predictions.json` | 保存验证集预测，供结果复核和绘图使用 |
| `predictions_train.json` | 单独保存训练集预测，避免与验证结果混用 |
| `report.html` | 展示模型结果及图表 |
| `compliance_report.html` | 展示项目检查结果与待补信息 |
| `acceptance_results.json` | 保存机器检查结果 |
| `plots/figure_manifest.json` | 记录图表文件、状态及来源信息 |
| `plots/` | 保存 PNG、SVG / PDF 图表 |
| `external_metrics.json` | 执行外部验证后保存外部指标 |

具体文件取决于启用的步骤。分享 HTML 报告时，请同时保留其引用的 `plots/` 目录。预测记录即使不含直接身份标识，也应按研究数据管理，不能默认作为公开仓库素材。

## 当前实现与使用边界

| 能力 | 当前状态 |
| --- | --- |
| 诊断分类 | 已有逻辑回归训练与二分类指标计算 |
| 预后生存 | 已有 Cox PH、C-index 与系数对应的 HR |
| 外部验证 | 已接入主流程，检查 ID 交叠并复用开发集预处理参数；需预先配置外部数据及状态 |
| 报告绘图 | 已有生成模块及报告嵌图；KM 风险人数实际渲染与元数据一致性仍有待完成的验收项 |
| 富集 / PPI | 已有真实 API 客户端；本轮工程验收未完成实网结果核验 |
| PROBAST+AI | 提供机器辅助检查，不替代完整的人工风险偏倚评估 |
| 指标冲突处理 | 支持严格检查、来源优先与有限的二分类指标重算；不支持任意指标自动修复 |
| 生存时间依赖 AUC / Brier | 删失校正估计尚未实现，当前返回 `null` 并说明原因 |
| Meta 与组学完整流水线 | 有方法技能和部分图函数，不应视为已完成全自动上游分析 |

二分类 Brier 衡量概率预测的总体误差，不能单独证明模型校准良好。测试通过说明相应工程行为得到检查，不等于研究设计、统计假设或临床有效性已得到认证。

## 项目结构

```text
medical-data-mining/
├── SKILL.md                   # 总入口与研究流程导航
├── clinical-prediction-model/ # 临床预测模型技能
├── biomedical-visualization/  # 科研可视化技能
├── geo-deg-analysis/          # GEO差异分析技能
├── tcga-survival/             # TCGA生存分析技能
├── …                         # 研究设计、数据工程、富集、写作等技能
├── scripts/
│   ├── setup_project.py      # 建立研究项目
│   ├── run_workflow.py       # 编排训练、验证、绘图与报告
│   ├── trainers/             # 诊断和预后训练器
│   ├── plot_engine.py        # 统计图表函数
│   └── demo_end_to_end.sh    # 完整模拟示例
├── templates/                # 项目模板
├── references/               # 方法、数据格式与使用说明
├── tests/                    # 数值与工作流测试
└── requirements.txt          # 运行依赖
```

## 参与贡献

欢迎通过问题反馈、可复现样例、方法修正和代码改进参与建设。

提交问题时，请提供运行命令、环境版本、预期行为和实际错误；如需数据，请使用最小化的合成或可公开样例，避免提交患者资料、凭证和未经授权的数据。

涉及统计计算或绘图的修改，请附上可手工核对的数值用例；涉及报告的修改，请附上渲染结果。运行测试：

```bash
python -B -m unittest discover -s tests -v
```

后续重点包括删失校正的生存评价指标、图表数值与视觉回归、更多外部验证场景，以及真实 API 的可复现测试。

## 许可证

当前发布准备版本尚未提供独立的 `LICENSE` 文件，许可证待维护者确定。引用的第三方代码、资料和数据分别遵循其原有授权条件。
