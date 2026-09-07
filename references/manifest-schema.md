# Manifest Schema (strict)

```json
{
  "study_type": "diagnostic | prognostic | treatment_effect | systematic_review",
  "data_mode": "simulated | real",
  "endpoint": "string",
  "truth_source": "string",
  "censoring_def": "string (required for prognostic/treatment_effect)",
  "input_files": [
    {
      "path": "relative or absolute path",
      "sha256": "hex string",
      "rows": 10,
      "cols": 5,
      "description": "string"
    }
  ],
  "column_map": {
    "id": "id",
    "time": "time (prognostic)",
    "event": "event (prognostic)",
    "outcome": "outcome (diagnostic)"
  },
  "split_manifest": {
    "train": [],
    "validation": [],
    "test": [],
    "external": []
  },
  "model_spec": {
    "type": "logistic_regression | cox | ...",
    "features": [],
    "preprocessing": {
      "standardize": true,
      "mean": [],
      "std": [],
      "missing": "omit"
    },
    "coefficients": [],
    "intercept": 0.0,
    "threshold": 0.5
  },
  "metrics": {
    "auc": null,
    "sensitivity": null,
    "specificity": null,
    "c_index": null,
    "time_dependent_auc": {},
    "brier": null,
    "calibration_slope": null,
    "calibration_intercept": null,
    "hr": null,
    "or": null,
    "i2": null
  },
  "sample_flow": {
    "raw": 10,
    "after_qc": 10,
    "train": 5,
    "validation": 5,
    "test": 0,
    "external": 0
  },
  "code_deps": {
    "python": "3.12",
    "r": "N/A",
    "packages": {}
  },
  "random_seeds": [42],
  "parameters": {},
  "artifacts": ["report.html"],
  "warnings": [],
  "external_validation": {
    "status": "unavailable | pending | completed | failed",
    "external_data_path": "",
    "external_ids": [],
    "external_metrics": {}
  },
  "compliance_checklist": {},
  "human_sign_off": false,
  "acceptance_tests": {}
}
```
