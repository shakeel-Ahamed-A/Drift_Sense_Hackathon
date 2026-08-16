"""Tests for the hybrid localization pipeline and challenge-aligned generator."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import hybrid_drift_sense as h  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_reference_and_search_have_expected_dimensions(self) -> None:
        sample = h.generate_sample("x", "dram", seed=1, forced_rotation_deg=45, forced_scale=1.1)
        self.assertEqual(sample.reference.shape, (1000, 1000))
        self.assertEqual(sample.search.shape, (1000, 1000))
        self.assertEqual(sample.gt_quad.shape, (4, 2))
        self.assertEqual(sample.gt_ref_to_search.shape, (2, 3))

    def test_generation_is_reproducible(self) -> None:
        a = h.generate_sample("x", "finfet", seed=99, forced_rotation_deg=137, forced_scale=0.8)
        b = h.generate_sample("x", "finfet", seed=99, forced_rotation_deg=137, forced_scale=0.8)
        self.assertTrue(np.array_equal(a.reference, b.reference))
        self.assertTrue(np.array_equal(a.search, b.search))
        self.assertTrue(np.allclose(a.gt_quad, b.gt_quad))
        self.assertEqual(a.gt_center, b.gt_center)

    def test_rotation_and_scale_are_recorded_exactly(self) -> None:
        sample = h.generate_sample("x", "dram", seed=7, forced_rotation_deg=123.456, forced_scale=0.73)
        self.assertAlmostEqual(sample.rotation_deg, 123.456)
        self.assertAlmostEqual(sample.scale_ratio, 0.73)

    def test_ground_truth_center_is_inside_image(self) -> None:
        for seed in (1, 2, 3, 4):
            sample = h.generate_sample("x", "dram", seed=seed)
            x, y = sample.gt_center
            self.assertGreaterEqual(x, 0)
            self.assertLess(x, 1000)
            self.assertGreaterEqual(y, 0)
            self.assertLess(y, 1000)


    def test_ground_truth_transform_reprojects_reference_center_exactly(self) -> None:
        for rotation, scale in ((0.0, 1.0), (37.5, 0.82), (271.2, 1.21)):
            sample = h.generate_sample(
                "x", "dram", seed=31, forced_rotation_deg=rotation, forced_scale=scale
            )
            center = np.array([[499.5, 499.5]], dtype=np.float64)
            projected = h._transform_points(sample.gt_ref_to_search, center)[0]
            self.assertTrue(np.allclose(projected, sample.gt_center, atol=1e-10))

    def test_ground_truth_transform_inverse_mapping_is_stable(self) -> None:
        sample = h.generate_sample("x", "finfet", seed=32, forced_rotation_deg=311.2, forced_scale=1.17)
        linear = sample.gt_ref_to_search[:, :2]
        inverse = np.linalg.inv(linear)
        reconstructed = (np.array(sample.gt_center) - sample.gt_ref_to_search[:, 2]) @ inverse.T
        self.assertTrue(np.allclose(reconstructed, [499.5, 499.5], atol=1e-8))

    def test_edge_brightening_changes_image_when_enabled(self) -> None:
        sample = h.generate_sample(
            "a", "dram", seed=5,
            config=h.GeneratorConfig(architecture="dram", edge_brightening=0.0),
            forced_rotation_deg=0,
            forced_scale=1.0,
        )
        bright = h.add_edge_brightening(sample.reference, 0.4)
        self.assertGreater(float(np.mean(np.abs(bright.astype(np.float32) - sample.reference))), 0.0)


class HybridTests(unittest.TestCase):
    def test_hybrid_recovers_nominal_dram(self) -> None:
        sample = h.generate_sample("x", "dram", seed=1, forced_rotation_deg=90, forced_scale=1.1)
        prediction = h.hybrid_localize(sample.reference, sample.search, method=h.Method.HYBRID_CONFIDENCE)
        error = h.euclidean_error(prediction.center, sample.gt_center)
        self.assertIsNotNone(error)
        self.assertLess(error, 5.0)
        self.assertGreaterEqual(prediction.inliers, 4)

    def test_hybrid_recovers_rotated_scaled_dram(self) -> None:
        sample = h.generate_sample("x", "dram", seed=1, forced_rotation_deg=90, forced_scale=1.1)
        prediction = h.hybrid_localize(sample.reference, sample.search, method=h.Method.HYBRID_CONFIDENCE)
        error = h.euclidean_error(prediction.center, sample.gt_center)
        self.assertIsNotNone(error)
        self.assertLess(error, 5.0)
        self.assertIsNotNone(prediction.predicted_mapping_angle_deg)
        self.assertIsNotNone(prediction.predicted_scale_ratio)

    def test_hybrid_recovers_finfet_extreme_rotation(self) -> None:
        sample = h.generate_sample("x", "finfet", seed=1, forced_rotation_deg=180, forced_scale=0.75)
        prediction = h.hybrid_localize(sample.reference, sample.search, method=h.Method.HYBRID_CONFIDENCE)
        error = h.euclidean_error(prediction.center, sample.gt_center)
        self.assertIsNotNone(error)
        self.assertLess(error, 5.0)

    def test_ncc_can_be_wrong_while_hybrid_recovers(self) -> None:
        sample = h.generate_sample("x", "dram", seed=1, forced_rotation_deg=90, forced_scale=1.1)
        ncc = h.hybrid_localize(sample.reference, sample.search, method=h.Method.NCC)
        hybrid = h.hybrid_localize(sample.reference, sample.search, method=h.Method.HYBRID_CONFIDENCE)
        ncc_error = h.euclidean_error(ncc.center, sample.gt_center)
        hybrid_error = h.euclidean_error(hybrid.center, sample.gt_center)
        self.assertIsNotNone(ncc_error)
        self.assertIsNotNone(hybrid_error)
        self.assertGreater(ncc_error, 20.0)
        self.assertLess(hybrid_error, 5.0)

    def test_invalid_input_fails_cleanly(self) -> None:
        reference = np.zeros((100, 100), np.uint8)
        search = np.zeros((200, 200), np.uint8)
        prediction = h.hybrid_localize(reference, search)
        self.assertIsNone(prediction.center)
        self.assertIn("no_candidate", prediction.status)


class MetricTests(unittest.TestCase):
    def test_polygon_iou_identity(self) -> None:
        poly = np.array([[10, 10], [40, 10], [40, 40], [10, 40]], dtype=float)
        self.assertAlmostEqual(h.polygon_iou(poly, poly), 1.0)

    def test_failure_categories(self) -> None:
        self.assertEqual(h.categorize_failure(None, None, None), h.FailureMode.MISSED_DETECTION)
        self.assertEqual(h.categorize_failure(30.0, 0.0, 0.0), h.FailureMode.FALSE_POSITIVE)
        self.assertEqual(h.categorize_failure(7.0, 0.0, 0.0), h.FailureMode.LOCALIZATION_DRIFT)
        self.assertEqual(h.categorize_failure(2.0, 30.0, 0.0), h.FailureMode.SCALE_ORIENTATION_ERROR)
        self.assertEqual(h.categorize_failure(2.0, 0.0, 0.05), h.FailureMode.SUCCESS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
