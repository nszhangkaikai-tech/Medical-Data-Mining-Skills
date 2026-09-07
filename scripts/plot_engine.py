#!/usr/bin/env python3
"""
Reproducible biomedical plotting engine (matplotlib only).

Design constraints:
- no AI-generated statistical imagery
- explicit not-generated status when inputs are missing/unsupported
- never fabricate upstream analyses, CIs, P-values or networks
- colourblind-friendly palette (Okabe-Ito)
- >=300 dpi PNG + SVG/PDF exports
- consistent figure sizes, readable labels/units/legends
- captions include data-source/split/method/threshold
- DEMO watermark for simulated data
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import html
import numpy as np

# matplotlib with non-interactive backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import ListedColormap

# colourblind-friendly defaults (Okabe-Ito first 7)
_OKABE_ITO = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#000000"
]
plt.rcParams["axes.prop_cycle"] = plt.cycler(color=_OKABE_ITO)
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.size"] = 11
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["figure.figsize"] = (7.0, 5.2)
plt.rcParams["savefig.bbox"] = "tight"


def _demo_banner(ax: plt.Axes, data_mode: str) -> None:
    if data_mode == "simulated":
        ax.text(
            0.5, -0.18, "DEMO / simulated data - not for clinical/publication use",
            transform=ax.transAxes, ha="center", va="top", fontsize=9,
            color="#856404", bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd", ec="#ffc107", lw=1.2)
        )


def _caption(ax: plt.Axes, text: str) -> None:
    ax.set_xlabel(ax.get_xlabel() + "\n" + text, labelpad=8)


def _safe_array(x: Sequence[Union[int, float]]) -> np.ndarray:
    return np.asarray(x, dtype=float)


def _check_binary(y_true: Sequence[Union[int, float]]) -> bool:
    y = np.asarray(y_true, dtype=float)
    return bool(np.all((y == 0) | (y == 1)))


def _validate_probabilities(s: Sequence[float]) -> Optional[str]:
    """Check that probabilities are finite and in [0, 1]. Return reason or None."""
    arr = np.asarray(s, dtype=float)
    if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
        return "non-finite probabilities"
    if np.any(arr < 0) or np.any(arr > 1):
        return "probabilities outside [0, 1]"
    return None


def write_figure_manifest(
    figures: List[Dict[str, Any]],
    output_dir: Union[str, Path],
    filename: str = "figure_manifest.json",
) -> str:
    """Write a JSON manifest listing all generated figures with metadata."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "figure_count": len(figures),
        "figures": figures,
    }
    path = out_dir / filename
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def plot_roc(
    y_true: Sequence[Union[int, float]],
    y_prob: Sequence[float],
    *,
    threshold: Optional[float] = None,
    output_dir: Union[str, Path] = ".",
    filename: str = "roc_curve.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    split: str = "validation",
    source_hash: str = "",
    method: str = "empirical rank AUC (trapezoid)",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if y_true is None or y_prob is None or len(y_true) != len(y_prob) or len(y_true) == 0:
        reason = "missing y_true or y_prob"
    elif not _check_binary(y_true):
        reason = "y_true not binary"
    else:
        prob_reason = _validate_probabilities(y_prob)
        if prob_reason:
            reason = prob_reason
        else:
            y = _safe_array(y_true)
            s = _safe_array(y_prob)
            pos = s[y == 1]
            neg = s[y == 0]
            if len(pos) == 0 or len(neg) == 0:
                reason = "only one class present"
            else:
                # Monotone ROC: descending thresholds + inf endpoint.
                # Using -inf ensures the curve always starts at (0,0) and ends at (1,1)
                # without the non-monotonicity caused by appending fixed endpoints to
                # an ascending unique-score sequence.
                uniq = np.unique(s)
                cutoff = np.sort(uniq)[::-1]  # descending
                tpr = np.array([(pos >= t).mean() for t in cutoff])
                fpr = np.array([(neg >= t).mean() for t in cutoff])
                # Prepend (0,0) so degenerate cases (e.g. all ties) still yield AUC=0.5
                # and the curve is guaranteed monotone from the origin.
                tpr = np.concatenate([[0.0], tpr])
                fpr = np.concatenate([[0.0], fpr])
                # Trapezoid AUC on the monotone curve (0,0) -> ... -> (1,1)
                auc = float(np.trapezoid(tpr, fpr))

                fig, ax = plt.subplots()
                ax.plot(fpr, tpr, label=f"ROC (AUC = {auc:.3f})", color=_OKABE_ITO[0], lw=2)
                ax.plot([0, 1], [0, 1], ls="--", color="#999999", lw=1)
                if threshold is not None:
                    t = float(threshold)
                    tp = (pos >= t).mean()
                    fp = (neg >= t).mean()
                    ax.scatter([fp], [tp], color=_OKABE_ITO[1], zorder=5, label=f"threshold = {threshold:.3f}")
                ax.set_xlabel("1 - Specificity (False Positive Rate)")
                ax.set_ylabel("Sensitivity (True Positive Rate)")
                ax.set_title("Receiver Operating Characteristic")
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1.05)
                ax.legend(loc="lower right")
                _caption(ax, f"split={split} | method={method} | source_hash={source_hash[:12]}...")
                _demo_banner(ax, data_mode)
                base = out_dir / filename
                fig.savefig(base, dpi=300)
                paths["png"] = str(base)
                if svg:
                    p = base.with_suffix(".svg")
                    fig.savefig(p)
                    paths["svg"] = str(p)
                if pdf:
                    p = base.with_suffix(".pdf")
                    fig.savefig(p)
                    paths["pdf"] = str(p)
                plt.close(fig)
                status = "generated"
                meta = {
                    "auc": round(auc, 4),
                    "n": int(len(y)),
                    "n_pos": int(len(pos)),
                    "n_neg": int(len(neg)),
                    "method": method,
                    "figure_type": "roc",
                }

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "roc",
        "split": split,
        "data_mode": data_mode,
        "source_hash": source_hash,
        "method": method,
    }


def plot_pr(
    y_true: Sequence[Union[int, float]],
    y_prob: Sequence[float],
    *,
    output_dir: Union[str, Path] = ".",
    filename: str = "pr_curve.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    split: str = "validation",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if y_true is None or y_prob is None or len(y_true) != len(y_prob) or len(y_true) == 0:
        reason = "missing y_true or y_prob"
    elif not _check_binary(y_true):
        reason = "y_true not binary"
    else:
        prob_reason = _validate_probabilities(y_prob)
        if prob_reason:
            reason = prob_reason
        else:
            y = _safe_array(y_true)
            s = _safe_array(y_prob)
            pos = s[y == 1]
            neg = s[y == 0]
            if len(pos) == 0 or len(neg) == 0:
                reason = "only one class present"
            else:
                order = np.argsort(s)[::-1]
                y_sorted = y[order]
                s_sorted = s[order]
                recalls = []
                precisions = []
                tp = 0
                fp = 0
                n_pos = int((y == 1).sum())
                for yi, si in zip(y_sorted, s_sorted):
                    if yi == 1:
                        tp += 1
                    else:
                        fp += 1
                    recalls.append(tp / max(1, n_pos))
                    precisions.append(tp / max(1, tp + fp))
                # Append endpoints: (recall=0, precision=1) and (recall=1, precision=prevalence)
                recalls = [0.0] + recalls + [1.0]
                precisions = [1.0] + precisions + [n_pos / len(y)]
                # AP by trapezoid (approximate; for exact AP use sklearn.metrics.average_precision_score)
                ap = float(np.trapezoid(precisions, recalls))

                fig, ax = plt.subplots()
                ax.plot(recalls, precisions, label=f"PR (AP ≈ {ap:.3f})", color=_OKABE_ITO[1], lw=2)
                ax.set_xlabel("Recall (Sensitivity)")
                ax.set_ylabel("Precision (PPV)")
                ax.set_title("Precision-Recall Curve")
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1.05)
                ax.legend(loc="upper right")
                _caption(ax, f"split={split} | source_hash={source_hash[:12]}...")
                _demo_banner(ax, data_mode)
                base = out_dir / filename
                fig.savefig(base, dpi=300)
                paths["png"] = str(base)
                if svg:
                    p = base.with_suffix(".svg")
                    fig.savefig(p)
                    paths["svg"] = str(p)
                if pdf:
                    p = base.with_suffix(".pdf")
                    fig.savefig(p)
                    paths["pdf"] = str(p)
                plt.close(fig)
                status = "generated"
                meta = {
                    "ap": round(ap, 4),
                    "n": int(len(y)),
                    "n_pos": int(len(pos)),
                    "n_neg": int(len(neg)),
                    "figure_type": "pr",
                }

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "pr",
        "split": split,
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def plot_calibration(
    y_true: Sequence[Union[int, float]],
    y_prob: Sequence[float],
    *,
    n_bins: int = 10,
    output_dir: Union[str, Path] = ".",
    filename: str = "calibration_curve.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    split: str = "validation",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if y_true is None or y_prob is None or len(y_true) != len(y_prob) or len(y_true) == 0:
        reason = "missing y_true or y_prob"
    elif not _check_binary(y_true):
        reason = "y_true not binary"
    else:
        prob_reason = _validate_probabilities(y_prob)
        if prob_reason:
            reason = prob_reason
        else:
            y = _safe_array(y_true)
            p = _safe_array(y_prob)
            bins = np.linspace(0.0, 1.0, n_bins + 1)
            idx = np.digitize(p, bins[1:-1], right=True)
            bin_avg = []
            bin_obs = []
            bin_count = []
            for b in range(n_bins):
                mask = idx == b
                n = int(mask.sum())
                if n == 0:
                    bin_avg.append(np.nan)
                    bin_obs.append(np.nan)
                    bin_count.append(0)
                else:
                    bin_avg.append(float(p[mask].mean()))
                    bin_obs.append(float(y[mask].mean()))
                    bin_count.append(n)
            brier = float(np.mean((p - y) ** 2))

            fig, ax = plt.subplots()
            ax.plot([0, 1], [0, 1], ls="--", color="#999999", lw=1, label="perfect calibration")
            ax.plot(bin_avg, bin_obs, marker="o", lw=2, color=_OKABE_ITO[2], label="observed")
            ax.set_xlabel("Predicted probability")
            ax.set_ylabel("Observed proportion")
            ax.set_title(f"Calibration (Brier = {brier:.3f})")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1.05)
            ax.legend(loc="upper left")
            # annotate bin counts
            for x, y_, n in zip(bin_avg, bin_obs, bin_count):
                if n > 0 and not (np.isnan(x) or np.isnan(y_)):
                    ax.annotate(str(n), (x, y_), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
            _caption(ax, f"split={split} | bins={n_bins} | source_hash={source_hash[:12]}...")
            _demo_banner(ax, data_mode)
            base = out_dir / filename
            fig.savefig(base, dpi=300)
            paths["png"] = str(base)
            if svg:
                p = base.with_suffix(".svg")
                fig.savefig(p)
                paths["svg"] = str(p)
            if pdf:
                p = base.with_suffix(".pdf")
                fig.savefig(p)
                paths["pdf"] = str(p)
            plt.close(fig)
            status = "generated"
            meta = {"brier": round(brier, 4), "bins": n_bins, "n": int(len(y)), "figure_type": "calibration"}

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "calibration",
        "split": split,
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def render_figure_gallery(manifest_path: Union[str, Path], relative_to: Union[str, Path] = ".") -> str:
    """Return HTML string with an idempotent <img> gallery from a figure manifest."""
    p = Path(manifest_path)
    if not p.exists():
        return '<p>No figure manifest found. Run with --plots to generate figures.</p>'
    try:
        manifest = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        return f'<p>Figure manifest unreadable: {html.escape(str(e))}</p>'
    figures = manifest.get('figures', []) or []
    if not figures:
        return '<p>No figures generated.</p>'
    parts: List[str] = []
    for fig in figures:
        fig_type = fig.get('figure_type', '')
        split = fig.get('split', '')
        status = fig.get('status', '')
        paths = fig.get('paths', {}) or {}
        meta = fig.get('metadata', {}) or {}
        png_path = paths.get('png', '')
        if png_path and status == 'generated':
            rel = f"plots/{Path(png_path).name}"
            meta_str = ', '.join(f'{k}={v}' for k, v in meta.items() if k != 'figure_type')
            parts.append(
                f'<div style="margin:10px 0;padding:10px;border:1px solid #ddd;border-radius:6px">'
                f'<img src="{rel}" alt="{fig_type} ({split})" style="max-width:100%;height:auto">'
                f'<p style="font-size:12px;color:#555;margin-top:6px">{fig_type} | split={split} | {meta_str}</p>'
                f'</div>'
            )
        else:
            reason = fig.get('reason', 'unknown')
            parts.append(
                f'<div style="margin:10px 0;padding:10px;border:1px solid #ddd;border-radius:6px;background:#f8f9fa">'
                f'<p style="color:#856404;font-weight:bold">{fig_type} ({split}): NOT GENERATED</p>'
                f'<p style="font-size:12px;color:#856404">Reason: {html.escape(str(reason))}</p>'
                f'</div>'
            )
    return '\n'.join(parts)


def plot_km(
    times: Sequence[float],
    events: Sequence[int],
    risk_groups: Sequence[str],
    *,
    output_dir: Union[str, Path] = ".",
    filename: str = "km_curve.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    split: str = "validation",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if times is None or events is None or risk_groups is None:
        reason = "missing times/events/risk_groups"
    elif not (len(times) == len(events) == len(risk_groups)):
        reason = "length mismatch among times/events/risk_groups"
    elif len(times) == 0:
        reason = "empty survival arrays"
    else:
        t = _safe_array(times)
        e = np.asarray(events, dtype=int)
        groups = list(risk_groups)
        unique_groups = sorted(set(groups))
        if len(unique_groups) == 0:
            reason = "no risk groups provided"
        else:
            fig, ax = plt.subplots()
            if len(unique_groups) >= 3:
                plot_groups = unique_groups[:2]
                extra_note = f"; showing first 2 of {len(unique_groups)} groups"
            else:
                plot_groups = list(unique_groups)
                extra_note = " [single group]" if len(plot_groups) == 1 else ""

            km_curves = {}
            at_risk_tables = {}
            group_cens = {}

            for idx, g in enumerate(plot_groups):
                mask = np.array([r == g for r in groups], dtype=bool)
                gt = t[mask]
                ge = e[mask]
                order = np.argsort(gt)
                gt = gt[order]
                ge = ge[order]

                n_total = len(gt)
                surv = 1.0
                km_times = [0.0]
                km_surv = [1.0]
                at_risk = [n_total]
                unique_event_times = []
                event_counts = []

                for time_val in np.unique(gt):
                    n_at_risk = int(np.sum(gt >= time_val))
                    n_events = int(np.sum(ge[gt == time_val]))
                    if n_events > 0:
                        surv *= (1.0 - n_events / n_at_risk)
                        km_times.append(float(time_val))
                        km_surv.append(surv)
                        unique_event_times.append(float(time_val))
                        event_counts.append(n_events)
                        at_risk.append(n_at_risk)

                # extend to last followup time
                if len(gt) > 0:
                    last_time = float(np.max(gt))
                    if abs(km_times[-1] - last_time) > 1e-12:
                        km_times.append(last_time)
                        km_surv.append(surv)
                        at_risk.append(0)

                km_curves[g] = (np.array(km_times), np.array(km_surv))
                at_risk_tables[g] = {
                    "times": km_times,
                    "n_at_risk": [int(n) for n in at_risk],
                    "n_events": event_counts,
                }

                cens_times = gt[ge == 0]
                cens_surv = []
                for ct in cens_times:
                    idx = int(np.searchsorted(km_times, ct, side="right")) - 1
                    cens_surv.append(float(km_surv[idx]) if idx >= 0 else 1.0)
                group_cens[g] = (cens_times, np.array(cens_surv))

            for idx, g in enumerate(plot_groups):
                kt, ks = km_curves[g]
                label = f"{g} (n={int((np.array(groups)==g).sum())})"
                if len(plot_groups) == 1:
                    label += " [single group]"
                ax.step(kt, ks, where="post", label=label, color=_OKABE_ITO[idx % len(_OKABE_ITO)], lw=1.8)

            ax.set_xlabel("Time")
            ax.set_ylabel("Survival probability")
            ax.set_title("Kaplan-Meier curve" + extra_note)
            ax.set_ylim(0, 1.05)
            ax.legend(loc="upper right")

            for idx, g in enumerate(plot_groups):
                ct, cs = group_cens[g]
                if len(ct) > 0:
                    ax.scatter(ct, cs, marker="|", color=_OKABE_ITO[idx % len(_OKABE_ITO)], alpha=0.8, s=80, linewidths=1.5)

            # numbers-at-risk table
            all_times = np.concatenate([km_curves[g][0] for g in plot_groups])
            min_t = float(np.min(all_times)) if len(all_times) else 0.0
            max_t = float(np.max(all_times)) if len(all_times) else 0.0
            table_times = []
            if min_t > 0 or int(e.sum()) == 0:
                table_times.append(0.0)
            all_event_times = []
            for g in plot_groups:
                gt = t[np.array([r == g for r in groups], dtype=bool)]
                all_event_times.extend([float(x) for x in np.unique(gt)])
            all_event_times = sorted(set(all_event_times))
            table_times.extend(all_event_times)
            for i in range(len(all_event_times) - 1):
                mid = (all_event_times[i] + all_event_times[i + 1]) / 2.0
                table_times.append(mid)
            table_times = sorted(set(table_times))

            table_data = []
            for g in plot_groups:
                kt, ks = km_curves[g]
                at = at_risk_tables[g]["times"]
                nr = at_risk_tables[g]["n_at_risk"]
                row = []
                for tt in table_times:
                    idx = int(np.searchsorted(at, tt, side="right")) - 1
                    if idx >= 0:
                        row.append(str(nr[idx]))
                    elif nr:
                        row.append(str(nr[0]))
                    else:
                        row.append("0")
                table_data.append(row)

            if table_data and table_times:
                table = ax.table(
                    cellText=table_data,
                    rowLabels=[f"{g} n_at_risk" for g in plot_groups],
                    colLabels=[f"t={tt:.2f}" for tt in table_times],
                    loc="lower center",
                    bbox=[0.0, -0.35, 1.0, 0.18],
                )
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1.0, 1.6)

            group_display_times = {}
            for g in plot_groups:
                gt = t[np.array([r == g for r in groups], dtype=bool)]
                group_display_times[g] = gt

            displayed_risk_table = {
                "times": [round(float(tt), 2) for tt in table_times],
                "per_group": {
                    g: {
                        "n_at_risk": [
                            int(np.sum(gt >= tt))
                            for tt in table_times
                        ],
                    }
                    for g, gt in group_display_times.items()
                },
            }
            if not table_times:
                displayed_risk_table = {
                    "times": [],
                    "per_group": {
                        g: {"n_at_risk": []}
                        for g in plot_groups
                    },
                }
            _caption(ax, f"split={split} | source_hash={source_hash[:12]}...")
            _demo_banner(ax, data_mode)
            base = out_dir / filename
            fig.savefig(base, dpi=300)
            paths["png"] = str(base)
            if svg:
                p = base.with_suffix(".svg")
                fig.savefig(p)
                paths["svg"] = str(p)
            if pdf:
                p = base.with_suffix(".pdf")
                fig.savefig(p)
                paths["pdf"] = str(p)
            plt.close(fig)
            status = "generated"
            meta = {
                "group_counts": {g: int((np.array(groups) == g).sum()) for g in unique_groups},
                "n_events_total": int(e.sum()),
                "at_risk_table": at_risk_tables,
                "displayed_risk_table": displayed_risk_table,
                "plotted_groups": plot_groups,
                "is_single_group": len(plot_groups) == 1,
                "figure_type": "km",
            }

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "km",
        "split": split,
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def plot_forest(
    effect: Sequence[float],
    ci_lower: Sequence[float],
    ci_upper: Sequence[float],
    labels: Sequence[str],
    *,
    output_dir: Union[str, Path] = ".",
    filename: str = "forest_plot.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if not effect or not ci_lower or not ci_upper or not labels:
        reason = "missing effect/ci/labels"
    elif not (len(effect) == len(ci_lower) == len(ci_upper) == len(labels)):
        reason = "effect/ci/labels length mismatch"
    else:
        fig, ax = plt.subplots(figsize=(6.4, max(3.0, 0.45 * len(labels))))
        y_pos = np.arange(len(labels))
        ax.errorbar(
            effect, y_pos,
            xerr=[np.array(effect) - np.array(ci_lower), np.array(ci_upper) - np.array(effect)],
            fmt="o", color=_OKABE_ITO[3], ecolor="#999999", capsize=3, lw=1.5
        )
        ax.axvline(x=1.0 if all(v > 0 for v in effect) else 0, color="#999999", ls="--", lw=1)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Effect size (95% CI)")
        ax.set_title("Forest plot")
        _caption(ax, f"source_hash={source_hash[:12]}...")
        _demo_banner(ax, data_mode)
        base = out_dir / filename
        fig.savefig(base, dpi=300)
        paths["png"] = str(base)
        if svg:
            p = base.with_suffix(".svg")
            fig.savefig(p)
            paths["svg"] = str(p)
        if pdf:
            p = base.with_suffix(".pdf")
            fig.savefig(p)
            paths["pdf"] = str(p)
        plt.close(fig)
        status = "generated"
        meta = {"n_terms": len(labels), "figure_type": "forest"}

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "forest",
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def plot_volcano(
    log2fc: Sequence[float],
    p_value: Sequence[float],
    *,
    p_col: str = "p_value",
    output_dir: Union[str, Path] = ".",
    filename: str = "volcano_plot.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if log2fc is None or p_value is None or len(log2fc) != len(p_value) or len(log2fc) == 0:
        reason = "missing log2fc or p_value"
    else:
        fc = _safe_array(log2fc)
        p = _safe_array(p_value)
        if np.any(np.isnan(fc)) or np.any(np.isnan(p)) or np.any(np.isinf(fc)) or np.any(np.isinf(p)):
            reason = "non-finite values in log2fc or p_value"
        else:
            neg_log10_p = -np.log10(p + 1e-300)
            fig, ax = plt.subplots()
            ax.scatter(fc, neg_log10_p, s=12, alpha=0.7, color=_OKABE_ITO[4])
            ax.set_xlabel("log2 fold change")
            ax.set_ylabel(f"-log10({p_col})")
            ax.set_title("Volcano plot")
            _caption(ax, f"source_hash={source_hash[:12]}...")
            _demo_banner(ax, data_mode)
            base = out_dir / filename
            fig.savefig(base, dpi=300)
            paths["png"] = str(base)
            if svg:
                p = base.with_suffix(".svg")
                fig.savefig(p)
                paths["svg"] = str(p)
            if pdf:
                p = base.with_suffix(".pdf")
                fig.savefig(p)
                paths["pdf"] = str(p)
            plt.close(fig)
            status = "generated"
            meta = {"n_features": int(len(fc)), "figure_type": "volcano"}

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "volcano",
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def plot_heatmap(
    matrix: Sequence[Sequence[float]],
    *,
    row_labels: Optional[Sequence[str]] = None,
    col_labels: Optional[Sequence[str]] = None,
    scale: str = "zscore",
    output_dir: Union[str, Path] = ".",
    filename: str = "heatmap.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if matrix is None or len(matrix) == 0 or len(matrix[0]) == 0:
        reason = "empty matrix"
    else:
        mat = np.asarray(matrix, dtype=float)
        if np.any(np.isnan(mat)) or np.any(np.isinf(mat)):
            reason = "non-finite values in matrix"
        else:
            if scale == "zscore":
                row_mean = mat.mean(axis=1, keepdims=True)
                row_std = mat.std(axis=1, keepdims=True)
                row_std[row_std == 0] = 1.0
                mat = (mat - row_mean) / row_std
            elif scale == "row_max":
                row_max = np.abs(mat).max(axis=1, keepdims=True)
                row_max[row_max == 0] = 1.0
                mat = mat / row_max
            # else: raw

            fig, ax = plt.subplots(figsize=(max(4.0, 0.35 * mat.shape[1]), max(3.0, 0.35 * mat.shape[0])))
            im = ax.imshow(mat, aspect="auto", cmap=plt.cm.viridis)
            fig.colorbar(im, ax=ax, label="value")
            if row_labels is not None:
                ax.set_yticks(np.arange(mat.shape[0]))
                ax.set_yticklabels(row_labels, fontsize=8)
            if col_labels is not None:
                ax.set_xticks(np.arange(mat.shape[1]))
                ax.set_xticklabels(col_labels, rotation=90, fontsize=8)
            ax.set_title("Heatmap")
            _caption(ax, f"scale={scale} | source_hash={source_hash[:12]}...")
            _demo_banner(ax, data_mode)
            base = out_dir / filename
            fig.savefig(base, dpi=300)
            paths["png"] = str(base)
            if svg:
                p = base.with_suffix(".svg")
                fig.savefig(p)
                paths["svg"] = str(p)
            if pdf:
                p = base.with_suffix(".pdf")
                fig.savefig(p)
                paths["pdf"] = str(p)
            plt.close(fig)
            status = "generated"
            meta = {"rows": int(mat.shape[0]), "cols": int(mat.shape[1]), "scale": scale, "figure_type": "heatmap"}

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "heatmap",
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def plot_enrichment_dot(
    terms: Sequence[str],
    gene_ratio: Sequence[float],
    p_adjust: Sequence[float],
    *,
    output_dir: Union[str, Path] = ".",
    filename: str = "enrichment_dot.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if not terms or not gene_ratio or not p_adjust:
        reason = "missing terms/gene_ratio/p_adjust"
    elif not (len(terms) == len(gene_ratio) == len(p_adjust)):
        reason = "terms/gene_ratio/p_adjust length mismatch"
    else:
        gr = _safe_array(gene_ratio)
        p = _safe_array(p_adjust)
        if np.any(np.isnan(gr)) or np.any(np.isnan(p)) or np.any((gr <= 0) | (p <= 0)):
            reason = "non-positive or non-finite gene_ratio/p_adjust"
        else:
            order = np.argsort(p)[:min(len(terms), 30)]
            terms_s = [terms[i] for i in order]
            gr_s = gr[order]
            p_s = p[order]
            fig, ax = plt.subplots(figsize=(max(5.0, 0.6 * len(terms_s)), max(3.0, 0.5 * len(terms_s))))
            sc = ax.scatter(gr_s, np.arange(len(terms_s)), c=-np.log10(p_s + 1e-300), cmap=plt.cm.viridis)
            ax.set_yticks(np.arange(len(terms_s)))
            ax.set_yticklabels(terms_s, fontsize=8)
            ax.set_xlabel("Gene ratio")
            ax.set_title("Enrichment dot plot")
            ax.invert_yaxis()
            fig.colorbar(sc, ax=ax, label="-log10(p_adjust)")
            _caption(ax, f"source_hash={source_hash[:12]}...")
            _demo_banner(ax, data_mode)
            base = out_dir / filename
            fig.savefig(base, dpi=300)
            paths["png"] = str(base)
            if svg:
                p = base.with_suffix(".svg")
                fig.savefig(p)
                paths["svg"] = str(p)
            if pdf:
                p = base.with_suffix(".pdf")
                fig.savefig(p)
                paths["pdf"] = str(p)
            plt.close(fig)
            status = "generated"
            meta = {"n_terms": int(len(terms_s)), "figure_type": "enrichment_dot"}

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "enrichment_dot",
        "data_mode": data_mode,
        "source_hash": source_hash,
    }


def plot_ppi_network(
    edges: Sequence[Tuple[str, str]],
    scores: Sequence[float],
    *,
    output_dir: Union[str, Path] = ".",
    filename: str = "ppi_network.png",
    svg: bool = True,
    pdf: bool = True,
    data_mode: str = "real",
    source_hash: str = "",
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    status = "not_generated"
    reason: Optional[str] = None
    paths: Dict[str, str] = {}
    meta: Dict[str, Any] = {}

    if not edges or not scores or len(edges) != len(scores):
        reason = "missing edges/scores or length mismatch"
    else:
        import networkx as nx
        g = nx.Graph()
        for (a, b), s in zip(edges, scores):
            g.add_edge(a, b, weight=float(s))
        fig, ax = plt.subplots(figsize=(max(5.0, 0.6 * max(g.number_of_nodes(), 3)), max(4.0, 0.5 * max(g.number_of_nodes(), 3))))
        pos = nx.spring_layout(g, k=0.6, seed=42)
        weights = [d.get("weight", 0.0) for _, _, d in g.edges(data=True)]
        if weights:
            wmax = max(weights)
            weights = [1.0 if wmax == 0 else w / wmax for w in weights]
        nx.draw_networkx_edges(g, pos, alpha=0.4, width=[1.0 + 3.0 * w for w in weights], ax=ax)
        nx.draw_networkx_nodes(g, pos, node_color=_OKABE_ITO[0], node_size=300, ax=ax)
        nx.draw_networkx_labels(g, pos, font_size=8, ax=ax)
        ax.set_title("PPI network")
        ax.axis("off")
        _demo_banner(ax, data_mode)
        base = out_dir / filename
        fig.savefig(base, dpi=300)
        paths["png"] = str(base)
        if svg:
            p = base.with_suffix(".svg")
            fig.savefig(p)
            paths["svg"] = str(p)
        if pdf:
            p = base.with_suffix(".pdf")
            fig.savefig(p)
            paths["pdf"] = str(p)
        plt.close(fig)
        status = "generated"
        meta = {"nodes": g.number_of_nodes(), "edges": g.number_of_edges(), "figure_type": "ppi"}

    return {
        "status": status,
        "reason": reason,
        "paths": paths,
        "metadata": meta,
        "figure_type": "ppi",
        "data_mode": data_mode,
        "source_hash": source_hash,
    }
