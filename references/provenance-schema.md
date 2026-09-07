# Provenance Schema

> 所有分析运行必须输出 `provenance.json`，位于结果目录根。

```json
{
  "schema_version": "1.0",
  "generated_at": "",
  "study_type": "",
  "data_mode": "real | simulated | not_collected",
  "endpoint": "",
  "truth_source": "",
  "censoring_def": "",
  "input_files": [
    {
      "path": "",
      "sha256": "",
      "rows": 0,
      "cols": 0,
      "description": ""
    }
  ],
  "sample_flow": {
    "raw": 0,
    "after_qc": 0,
    "train": 0,
    "validation": 0,
    "test": 0,
    "external": 0
  },
  "code_deps": {
    "python": "",
    "r": "",
    "packages": {}
  },
  "random_seeds": [],
  "parameters": {},
  "artifacts": [],
  "warnings": [],
  "acceptance_tests": {
    "endpoint_indicator_match": true,
    "numbers_consistency": true,
    "censoring_encoding": true,
    "train_val_isolation": true,
    "no_fictional_external": true,
    "no_unsubstantiated_clinical_claims": true,
    "demo_watermark": true
  }
}
```

## 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| schema_version | 是 | 本 schema 版本号 |
| generated_at | 是 | ISO-8601 时间戳 |
| study_type | 是 | 来自路由表的唯一主类型 |
| data_mode | 是 | real / simulated / not_collected |
| endpoint | 是 | 预先定义的终点，禁止后验替换 |
| truth_source | 是 | 金标准变量名或真实结局字段 |
| censoring_def | 条件 | 仅生存/时间事件必填 |
| input_files | 是 | 每个输入文件的 hash、行列数 |
| sample_flow | 是 | 样本在各阶段的计数 |
| code_deps | 是 | 语言版本和关键包版本 |
| random_seeds | 是 | 所有 random.seed / set.seed / np.random.seed |
| parameters | 是 | 模型超参、阈值、FDR 方法 |
| artifacts | 是 | 产物清单（CSV/PDF/PNG/HTML） |
| warnings | 是 | 数据质量问题、假设违反、缺失值处理 |
| acceptance_tests | 是 | 自动化验收测试结果 |
