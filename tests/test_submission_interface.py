import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cv2

import hybrid_drift_sense as h

ROOT = Path(__file__).resolve().parents[1]


class SubmissionInterfaceTests(unittest.TestCase):
    def test_generator_cli_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dram"
            proc = subprocess.run(
                [
                    sys.executable, str(ROOT / "generate_dataset.py"),
                    "--architecture", "dram",
                    "--num-pairs", "1",
                    "--output-dir", str(out),
                    "--seed", "42",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            manifest = out / "manifest.csv"
            self.assertTrue(manifest.exists())
            with manifest.open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertIn("gt_x", row)
            self.assertIn("gt_y", row)

    def test_infer_stdout_is_coordinate_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sample = h.generate_sample("smoke", "dram", seed=42, forced_rotation_deg=0, forced_scale=1.0)
            ref = tmp_path / "reference.png"
            search = tmp_path / "search.png"
            self.assertTrue(cv2.imwrite(str(ref), sample.reference))
            self.assertTrue(cv2.imwrite(str(search), sample.search))
            proc = subprocess.run(
                [
                    sys.executable, str(ROOT / "infer.py"),
                    "--reference", str(ref),
                    "--search", str(search),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            parts = proc.stdout.strip().split()
            self.assertEqual(len(parts), 2)
            float(parts[0]); float(parts[1])
            self.assertEqual(proc.stderr.strip(), "")


if __name__ == "__main__":
    unittest.main()
