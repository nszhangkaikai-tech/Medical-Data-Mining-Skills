# medical-data-mining Skill 功能自述

## 1. 定位
这是一个面向真实医学研究的可复现性 skill，不是演示玩具。它的核心目标是：把一次医学数据分析从“手工拼报告”变成“manifest 门禁 → 自动训练/验证 → 合规 HTML 报告”的可追溯流水线。

适用场景：
- 诊断分类模型（AUC / 敏感度 / 特异度 / Brier）
- 预后生存模型（C-index / time-dependent AUC / Brier / 校准）
- 治疗效应（HR / OR / RD / MD）
- Meta 分析（PRISMA 2020 / I² / 漏斗图警告）
- 探索性生信（DEG / 富集 / PPI）
- 论文写作与报告（STARD / REMARK / TRIPOD+AI / PROBAST+AI）

不适用场景：
- 需要完整 sklearn / lifelines 环境的复杂建模（当前仅提供诊断 logistic 最小实现）
- 真实数据库自动查询（STRING / DAVID / Cytoscape 需手工或后续接入）
- 自动 PROBAST+AI 人工条目评估（当前为半自动清单）

## 2. 目录结构
```
medical-data-mining/
├── README.md                       ← 快速开始 + 当前支持/未实现
├── SKILL.md                        ← 总入口：强制 manifest 门禁 + 研究类型路由
├── requirements.txt                 ← numpy>=1.24
├── templates/                      ← 标准化项目骨架
│   ├── diagnostic/                  ← 诊断分类模板
│   │   ├── manifest.json
│   │   ├── data.csv
│   │   ├── report.html
│   │   └── run_example.py
│   └── prognostic/                 ← 预后生存模板
│       ├── manifest.json
│       ├── data.csv
│       └── report.html
├── scripts/                        ← 可执行脚本
│   ├── setup_project.py             ← 交互式项目初始化
│   ├── run_workflow.py              ← 编排器：校验 → 验收 → 报告
│   ├── acceptance_tests.py          ← 9 项机械验收测试
│   ├── compliance_report.py         ← HTML 合规报告生成
│   ├── trainers/
│   │   └── diagnostic_logistic.py   ← 纯 numpy 逻辑回归训练器
│   ├── external_validation.py       ← 外部验证脚本
│   ├── enrichment.py                ← 富集占位实现
│   ├── ppi.py                       ← PPI 占位实现
│   └── probast_ai.py                ← PROBAST+AI 半自动评估
├── tests/                          ← 验收测试夹具
│   ├── test_acceptance.py           ← unittest 套件（10 tests）
│   └── fixtures/
│       ├── compliant_diagnostic/    ← 合规诊断夹具（必须 PASS）
│       └── violating_prognostic/    ← 违规预后夹具（必须 FAIL）
└── references/                     ← 规范与 schema
    ├── manifest-schema.md           ← manifest 严格字段定义
    ├── provenance-schema.md         ← provenance JSON 结构
    ├── report-template.md           ← 报告必须包含的章节
    ├── reproducibility-and-reporting-standards.md  ← 研究类型路由 + 合规清单
    ├── user-manual.md               ← 使用手册 / FAQ / skill chain 查找表
    ├── corpus-brainmap.md           ← 619 篇 Helixlife 文章分类脑图
    ├── databases-and-vision.md      ← 数据库调用 + 截图识别工作流
    ├── enrichment-ppi-schema.md     ← 富集/PPI JSON schema
    └── probast-ai-checklist.md      ← PROBAST+AI 条目清单
```

## 3. 核心工作流
```
用户数据 CSV
    ↓
setup_project.py --study-type diagnostic --output my_project --data data.csv --id-col id --outcome-col outcome
    ↓
生成 my_project/
    ├── manifest.json      ← 已填好列映射、SHA-256、行/列
    ├── data.csv
    └── run_example.py
    ↓
diagnostic_logistic.py --manifest my_project/manifest.json
    ↓
生成
    ├── metrics.json       ← 真实训练指标
    ├── report.html        ← 含 DEMO 水印的报告
    └── 回写 manifest.model_spec.coefficients / intercept
    ↓
run_workflow.py --manifest my_project/manifest.json
    ↓
生成
    ├── acceptance_results.json   ← 9 项测试布尔结果
    └── compliance_report.html    ← 可追溯合规报告
```

## 4. 研究类型路由
skill 根据 `manifest.study_type` 强制路由，禁止混用终点：

| study_type | 必填指标 | 必填字段 | 适用清单 |
|-----------|---------|---------|---------|
| diagnostic | auc + sensitivity/specificity | truth_source | STARD 2015 / TRIPOD+AI |
| prognostic | c_index 或 time_dependent_auc 或 hr | truth_source + censoring_def | REMARK / TRIPOD+AI |
| treatment_effect | hr 或 or 或 rd 或 md | censoring_def | CONSORT |
| systematic_review | i² | search_strategy / prisma_flow | PRISMA 2020 |

## 5. 脚本功能详述

### 5.1 setup_project.py
- 根据 `--study-type` 复制 `templates/<type>/` 到目标目录
- 支持 `--data` 自动计算 SHA-256、行数、列数
- 支持 `--id-col`、`--outcome-col`、`--time-col`、`--event-col`
- 输出可直接接 `run_workflow.py` 的 manifest.json

### 5.2 trainers/diagnostic_logistic.py
- 纯 numpy 实现，不依赖 sklearn
- 自动推断特征列（排除 id/time/event）
- 内置标准化
- 输出 metrics.json（auc/sensitivity/specificity/ppv/npv/brier）
- 回写 manifest.model_spec.features / coefficients / intercept / preprocessing
- 写 report.html（含 DEMO 水印）

### 5.3 external_validation.py
- 读取开发集 manifest 和外部 CSV
- 校验 ID 与 train/validation/test 无交叠
- 用开发集模型参数计算外部指标
- 输出 external_metrics.json
- 更新 manifest.external_validation.status = completed

### 5.4 enrichment.py / ppi.py
- 占位实现，不调用真实 API
- 校验输入基因列表非空
- 输出固定 schema 的 JSON
- 可用于 skill 流水线测试和后续替换为真实 API

### 5.5 probast_ai.py
- 读取 manifest，自动评估可计算项：
  - 缺失率（sample_flow.raw vs after_qc）
  - EPV（train / feature 数）
  - 外部验证状态
  - 模型完整披露（features + coefficients + intercept）
- 输出 probast_ai.json，含 automatic_items 和 manual_items

### 5.6 acceptance_tests.py
9 项验收，全部从 manifest + 数据文件 + 产物文件独立计算，无默认 True：

1. required_fields：必填字段 + 空字符串/空列表检查
2. input_integrity：SHA-256 + CSV 行/列
3. sample_flow_non_empty：raw/after_qc/train/validation/test/external 全非空
4. endpoint_indicator_match：diagnostic 必须有 auc，prognostic 必须有 c_index 或 hr
5. numbers_consistency：sample_flow 逻辑 + HTML 与 metrics.json 数值逐项比对
6. censoring_encoding：删失值域校验（0/1/0.0/1.0）
7. train_val_isolation：split 集合两两无交叠
8. no_fictional_external：external_validation completed 时必须 external_data_path 存在 + external_ids 非空 + external_metrics 非空 + ID 无交叠
9. no_unsubstantiated_clinical_claims：模拟数据必须有 DEMO 横幅，禁止临床决策措辞

支持 `--metrics-policy strict|manifest_wins|disk_wins` 解决 metrics.json 与 manifest.metrics 冲突。

### 5.7 run_workflow.py
编排器，不实现分析算法，只做：
1. manifest 必填字段 + sample_flow + artifacts + model_spec 长度校验
2. 调用 acceptance_tests.py，输出 acceptance_results.json
3. 调用 compliance_report.py，生成 compliance_report.html

### 5.8 compliance_report.py
读取 manifest + acceptance_results.json，输出 HTML：
- Provenance Summary
- Compliance Checklist
- Warnings / Missing Items
- Acceptance Tests（真实验收结果，非 manifest 空对象）

## 6. 当前支持的分析类型
- 诊断分类（自动：逻辑回归 + AUC/敏感度/特异度/Brier）
- 预后生存（手工：需提供 metrics.json）
- 治疗效应（手工）
- Meta 分析（手工，提供 PRISMA 2020 清单）
- 探索性生信（手工，提供 DEG/富集/PPI 框架）
- 论文写作（手工，提供 STARD/REMARK/TRIPOD+AI/PROBAST+AI 模板）

## 7. 未实现 / 待补全
- 预后模型自动训练（需要 lifelines / scikit-survival）
- 富集/PPI 真实数据库 API 接入（当前为占位）
- 外部验证脚本未集成进 run_workflow.py 主流程
- PROBAST+AI 人工条目仍需专家勾选
- metrics.json 与 manifest.metrics 不一致时的自动修复（当前策略是 strict FAIL 或按 policy 覆盖）

## 8. 使用示例
```bash
# 1. 初始化项目
python3 scripts/setup_project.py \
  --study-type diagnostic \
  --output ~/my_diagnostic_study \
  --data ~/real_data.csv \
  --id-col patient_id \
  --outcome-col disease_status

# 2. 训练模型
python3 scripts/trainers/diagnostic_logistic.py --manifest ~/my_diagnostic_study/manifest.json

# 3. 跑门禁 + 生成报告
python3 scripts/run_workflow.py --manifest ~/my_diagnostic_study/manifest.json

# 4. 单独跑验收
python3 scripts/acceptance_tests.py --manifest ~/my_diagnostic_study/manifest.json

# 5. 外部验证（可选）
python3 scripts/external_validation.py \
  --manifest ~/my_diagnostic_study/manifest.json \
  --external-data ~/external_cohort.csv
```

## 9. 设计原则
- manifest 是唯一真相源，所有产出必须回写或指向 manifest
- 所有路径解析基于 manifest 所在目录，禁止依赖当前工作目录
- 模拟数据必须有不可移除的 DEMO 水印
- 真实数据无 human_sign_off 不得声称可临床使用
- 外部验证必须证明 ID 无交叠、数据文件存在、指标非空
- 禁止临床决策/发表效力措辞出现在报告中
