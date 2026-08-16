"""Evaluate a saved Drift-Sense manifest with the finalized hybrid pipeline.

Expected CSV columns:
    sample_id,architecture,reference_file,search_file,gt_x,gt_y

Paths are resolved relative to the manifest's directory. Additional columns are
ignored so the script can ingest richer exports from a synthetic-data generator.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import hybrid_drift_sense as h


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a Drift-Sense image manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--method", type=h._parse_method, default=h.Method.HYBRID_CONFIDENCE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.manifest.parent
    rows = []
    with args.manifest.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"sample_id", "architecture", "reference_file", "search_file", "gt_x", "gt_y"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Manifest is missing required columns: {sorted(missing)}")
        for record in reader:
            reference = h.load_grayscale(root / record["reference_file"])
            search = h.load_grayscale(root / record["search_file"])
            prediction = h.hybrid_localize(reference, search, method=args.method)
            gt = (float(record["gt_x"]), float(record["gt_y"]))
            error = h.euclidean_error(prediction.center, gt)
            rows.append({
                "sample_id": record["sample_id"],
                "architecture": record["architecture"],
                "method": prediction.method,
                "gt_x": gt[0],
                "gt_y": gt[1],
                "pred_x": "" if prediction.center is None else prediction.center[0],
                "pred_y": "" if prediction.center is None else prediction.center[1],
                "error_px": "" if error is None else error,
                "score": "" if prediction.score is None else prediction.score,
                "runtime_ms": prediction.runtime_ms,
                "status": prediction.status,
            })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["sample_id"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
