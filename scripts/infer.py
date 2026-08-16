"""Evaluator-facing standalone inference entry point for Drift-Sense.

Usage:
    python infer.py --reference reference.png --search search.png

The default configuration is HYBRID-CONFIDENCE. The evaluator-facing stdout
contains only the predicted ``x y`` coordinate pair. Optional diagnostics are
sent to stderr with ``--verbose`` so they do not contaminate machine parsing.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

import hybrid_drift_sense as h


def main() -> int:
    """Parse arguments, perform localization, and emit evaluator-safe output.

    Returns:
        0: localization succeeded.
        1: invalid input or runtime error.
        2: valid inputs but no localization could be produced.
    """
    parser = argparse.ArgumentParser(
        description="Locate the reference pattern in a Drift-Sense search image."
    )
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--search", type=Path, required=True)
    parser.add_argument(
        "--method",
        type=h._parse_method,
        default=h.Method.HYBRID_CONFIDENCE,
        help="NCC, ORB-RANSAC, HYBRID-EQUAL, or HYBRID-CONFIDENCE.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Write diagnostic information to stderr; stdout remains x y only.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        reference = h.load_grayscale(args.reference)
        search = h.load_grayscale(args.search)
        prediction = h.hybrid_localize(reference, search, method=args.method)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if prediction.center is None:
        if args.verbose:
            logging.error("Localization failed: %s", prediction.status)
        return 2

    x, y = prediction.center
    print(f"{x:.4f} {y:.4f}")

    if args.verbose:
        logging.info(
            "method=%s score=%s runtime_ms=%.3f status=%s",
            prediction.method,
            "none" if prediction.score is None else f"{prediction.score:.6f}",
            prediction.runtime_ms,
            prediction.status,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
