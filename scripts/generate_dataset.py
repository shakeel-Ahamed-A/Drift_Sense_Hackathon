"""Standalone Drift-Sense challenge-style dataset generator.

Usage:
    python generate_dataset.py --architecture dram --num-pairs 30 --output-dir data/dram
    python generate_dataset.py --architecture finfet --num-pairs 30 --output-dir data/finfet

The generator records exact ground-truth center coordinates and the applied
rotation/scale values in ``manifest.csv``.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2

import hybrid_drift_sense as h


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Drift-Sense image pairs.")
    parser.add_argument("--architecture", choices=("dram", "finfet"), required=True)
    parser.add_argument("--num-pairs", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.num_pairs < 1:
        parser.error("--num-pairs must be >= 1")

    ref_dir = args.output_dir / "reference"
    search_dir = args.output_dir / "search"
    ref_dir.mkdir(parents=True, exist_ok=True)
    search_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = args.output_dir / "manifest.csv"
    fields = [
        "sample_id", "architecture", "reference_file", "search_file",
        "gt_x", "gt_y", "rotation_deg", "scale_ratio"
    ]

    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()

        for index in range(args.num_pairs):
            sample_id = f"{args.architecture}_{index:04d}"
            sample = h.generate_sample(
                sample_id,
                args.architecture,
                seed=args.seed + index,
            )

            ref_path = ref_dir / f"{sample_id}.png"
            search_path = search_dir / f"{sample_id}.png"
            if not cv2.imwrite(str(ref_path), sample.reference):
                raise OSError(f"Failed to write reference image: {ref_path}")
            if not cv2.imwrite(str(search_path), sample.search):
                raise OSError(f"Failed to write search image: {search_path}")

            writer.writerow({
                "sample_id": sample.sample_id,
                "architecture": sample.architecture,
                "reference_file": str(ref_path.relative_to(args.output_dir)),
                "search_file": str(search_path.relative_to(args.output_dir)),
                "gt_x": f"{sample.gt_center[0]:.10f}",
                "gt_y": f"{sample.gt_center[1]:.10f}",
                "rotation_deg": f"{sample.rotation_deg:.10f}",
                "scale_ratio": f"{sample.scale_ratio:.10f}",
            })

    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
