"""Run the Drift-Sense hybrid ablation matrix and generate figures."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import hybrid_drift_sense as h


def _rows_by_method(rows: list[h.EvaluationRow]) -> dict[str, list[h.EvaluationRow]]:
    result: dict[str, list[h.EvaluationRow]] = defaultdict(list)
    for row in rows:
        result[row.method].append(row)
    return result


def make_plots(rows: list[h.EvaluationRow], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped = _rows_by_method(rows)

    # Precision-recall curves at a 5-pixel correctness radius.
    plt.figure(figsize=(8, 5))
    for method, method_rows in grouped.items():
        curve = h.precision_recall_curve(method_rows, correctness_threshold_px=5.0)
        if not curve:
            continue
        recall = [item[2] for item in curve]
        precision = [item[1] for item in curve]
        plt.plot(recall, precision, marker="o", linewidth=1.2, markersize=3, label=method)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–Recall at 5 px Localization Threshold")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "precision_recall.png", dpi=160)
    plt.close()

    # Localization-error CDF.
    plt.figure(figsize=(8, 5))
    for method, method_rows in grouped.items():
        errors = np.array([row.error_px for row in method_rows if row.error_px is not None], dtype=float)
        if len(errors) == 0:
            continue
        errors.sort()
        cdf = np.arange(1, len(errors) + 1) / len(errors)
        plt.plot(errors, cdf, linewidth=1.6, label=method)
    plt.xlabel("Localization error (px)")
    plt.ylabel("Cumulative fraction")
    plt.title("Localization Error CDF")
    plt.xlim(left=0)
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "error_cdf.png", dpi=160)
    plt.close()

    # IoU distribution.
    data = []
    labels = []
    for method, method_rows in grouped.items():
        values = [row.iou for row in method_rows if row.iou is not None]
        if values:
            data.append(values)
            labels.append(method)
    if data:
        plt.figure(figsize=(9, 5))
        plt.boxplot(data, tick_labels=labels, showmeans=True)
        plt.ylabel("Polygon IoU")
        plt.title("Localization IoU Distribution")
        plt.grid(True, axis="y", alpha=0.25)
        plt.tight_layout()
        plt.savefig(output_dir / "iou_boxplot.png", dpi=160)
        plt.close()

    # Angular error distribution where available.
    data = []
    labels = []
    for method, method_rows in grouped.items():
        values = [row.angular_error_deg for row in method_rows if row.angular_error_deg is not None]
        if values:
            data.append(values)
            labels.append(method)
    if data:
        plt.figure(figsize=(9, 5))
        plt.boxplot(data, tick_labels=labels, showmeans=True)
        plt.ylabel("Angular error (degrees)")
        plt.title("Estimated Orientation Error")
        plt.grid(True, axis="y", alpha=0.25)
        plt.tight_layout()
        plt.savefig(output_dir / "angular_error_boxplot.png", dpi=160)
        plt.close()

    # Relative scale-ratio error distribution.
    data = []
    labels = []
    for method, method_rows in grouped.items():
        values = [row.scale_ratio_error for row in method_rows if row.scale_ratio_error is not None]
        if values:
            data.append(values)
            labels.append(method)
    if data:
        plt.figure(figsize=(9, 5))
        plt.boxplot(data, tick_labels=labels, showmeans=True)
        plt.ylabel("Relative scale-ratio error")
        plt.title("Estimated Scale Error")
        plt.grid(True, axis="y", alpha=0.25)
        plt.tight_layout()
        plt.savefig(output_dir / "scale_error_boxplot.png", dpi=160)
        plt.close()

    # Runtime comparison.
    methods = []
    runtimes = []
    for method, method_rows in grouped.items():
        if method_rows:
            methods.append(method)
            runtimes.append(np.mean([row.runtime_ms for row in method_rows]))
    if methods:
        plt.figure(figsize=(9, 5))
        plt.bar(methods, runtimes)
        plt.ylabel("Mean runtime (ms/sample)")
        plt.title("Inference Runtime")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(output_dir / "runtime_bar.png", dpi=160)
        plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full Drift-Sense ablation experiments.")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--samples-per-architecture", type=int, default=1)
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 29, 47])
    args = parser.parse_args()
    if args.samples_per_architecture < 1:
        parser.error("--samples-per-architecture must be >= 1")

    summary = h.run_ablation_suite(
        args.output_dir,
        seeds=tuple(args.seeds),
        n_per_architecture=args.samples_per_architecture,
    )
    rows = []
    csv_path = args.output_dir / "all_evaluation_rows.csv"
    with csv_path.open(encoding="utf-8", newline="") as handle:
        import csv
        reader = csv.DictReader(handle)
        for item in reader:
            rows.append(
                h.EvaluationRow(
                    scenario=item["scenario"],
                    sample_id=item["sample_id"],
                    architecture=item["architecture"],
                    method=item["method"],
                    status=item["status"],
                    error_px=float(item["error_px"]) if item["error_px"] not in ("", "None") else None,
                    iou=float(item["iou"]) if item["iou"] not in ("", "None") else None,
                    angular_error_deg=float(item["angular_error_deg"]) if item["angular_error_deg"] not in ("", "None") else None,
                    scale_ratio_error=float(item["scale_ratio_error"]) if item["scale_ratio_error"] not in ("", "None") else None,
                    runtime_ms=float(item["runtime_ms"]),
                    score=float(item["score"]) if item["score"] not in ("", "None") else None,
                    failure_mode=item["failure_mode"],
                )
            )
    make_plots(rows, args.output_dir / "figures")
    print(json.dumps(summary["stress"], indent=2))
    print(f"Results: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
