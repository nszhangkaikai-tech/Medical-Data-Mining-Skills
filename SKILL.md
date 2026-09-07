# 医学数据挖掘技能仓库（可复现性与报告规范版）

> 强制前置门禁：所有分析必须先走 manifest → acceptance tests → compliance report。
> 详细规范见 `references/reproducibility-and-reporting-standards.md`。
> manifest schema 见 `references/manifest-schema.md`。

## 当前支持的分析类型

| 类型 | 主规范 | 核心指标 | 状态 |
|------|--------|----------|------|
| 诊断分类 | STARD 2015 / TRIPOD+AI | AUC / 灵敏度 / 特异度 / Brier | 可运行 |
| 预后生存 | STROBE / TRIPOD+AI | C-index / time-dependent AUC / Brier / 校准 / HR | 可运行 |
| 治疗效应（观察性） | STROBE | HR / OR / RD | 可运行 |
| 系统综述/Meta | PRISMA 2020 | I² / pooled effect / 森林图 | 可运行 |
| 探索性生信 | MINSEQE / FAIR | DEG / 火山图 / 热图 / 富集 | 可运行 |
| 外部验证 | TRIPOD+AI | 外部 AUC / sensitivity / specificity / Brier | 可运行 |
| PROBAST+AI | PROBAST+AI | 0-4 / low-high risk | 可运行 |

## 标准分析 SOP

### 阶段 0：Manifest 注册（强制）
1. 准备 `manifest.json`（见 `references/manifest-schema.md`）
2. 运行 `scripts/run_workflow.py --manifest <path> [--metrics-policy strict|manifest_wins|disk_wins|repair] [--train] [--external-validation] [--probast]`
3. 自动执行 acceptance tests + compliance report

### 阶段 1：问题定义与设计
→ `clinical-research-design`, `sample-size-calculation`

### 阶段 2：数据获取与质控
→ `geo-download-qc`, `tcga-download`, `clinical-data-engineering`, `gene-annotation`

### 阶段 3：统计分析
→ `statistical-thinking`, `differential-gene-screening`, `tcga-survival`, `clinical-prediction-model`
→ `scripts/trainers/diagnostic_logistic.py`：诊断 logistic 训练（numpy，无 sklearn）
→ `scripts/trainers/prognostic_cox.py`：预后 Cox PH 训练（numpy，无 lifelines）
→ `scripts/external_validation.py`：外部验证（ID 交叠校验 + metrics 输出）
→ `scripts/enrichment.py` / `scripts/ppi.py`：富集/PPI（g:Profiler + STRING，默认离线）
→ `scripts/probast_ai.py`：PROBAST+AI 自动机检清单
→ `scripts/metrics_repair.py`：metrics 冲突修复（--metrics-policy repair）

### 阶段 4：结果表达
→ `biomedical-visualization`, `visualization`

### 阶段 5：验证与深化
→ `omics-integration-validation`, `oncomine-analysis`

### 阶段 6：论文产出
→ `paper-writing`, `meta-analysis-bias`

## 关键参考

- `references/reproducibility-and-reporting-standards.md` — 强制门禁
- `references/manifest-schema.md` — typed manifest schema
- `references/provenance-schema.md` — provenance JSON 规范
- `references/report-template.md` — 合规报告模板
- `references/databases-and-vision.md` — 数据库调用底座

## 验证与测试

```bash
cd ~/.hermes/skills/medical-data-mining

# 诊断夹具
python3 scripts/run_workflow.py --manifest tests/fixtures/compliant_diagnostic/manifest.json --train

# 预后夹具
python3 scripts/run_workflow.py --manifest tests/fixtures/compliant_prognostic/manifest.json --train

# 全量 unittest
python3 -B -m unittest discover -s tests -v
```

## 知识源

- 解螺旋临床科研文章库：`https://info.helixlife.cn/articles/list/linchuangkeyan`
- 课程转录/脚本：`lineage-skill/.lineage/courses/medical-data-mining-geo-tcga-oncomine/`
