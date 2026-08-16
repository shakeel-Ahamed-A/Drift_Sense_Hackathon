# Drift-Sense — Final Technical Report

## 1. Executive Summary

This project addresses the Drift-Sense navigation-error recovery problem: given a high-resolution reference SEM image and a lower-magnification search SEM image containing the same semiconductor pattern, estimate the center `(x, y)` of the matching region in the search image.

The finalized technical solution is a hybrid classical computer-vision pipeline. A coarse multi-scale gradient-NCC stage generates candidate locations; a local ORB + RANSAC stage verifies geometric consistency and refines the candidate; late fusion combines appearance and geometry confidence; the search-image-center rule is used only when final candidates are effectively tied.

The project also contains a challenge-style synthetic generator with DRAM and FinFET structures, independent reference/search degradations, edge brightening, rotation and scale variation, and transform-aware ground truth. The public Hugging Face generator remains the authoritative source for challenge-aligned benchmarking.

**Important benchmark qualification:** the public Hugging Face Space is a generator rather than a frozen public benchmark dataset, and the hidden Applied Materials Phase 2 test set is not public. Therefore the quantitative results included in `results/` are local development-generator results, not official Applied Materials benchmark scores. This distinction is explicit throughout the package.

## 2. Problem Definition

The challenge requires locating a known reference pattern inside a search image. The reference is specified at 1 nm/px and the search image at 10 nm/px, so the reference footprint is approximately 100 x 100 pixels in search coordinates. Both DRAM-style and FinFET-style repeating structures are relevant.

The central difficulty is periodic ambiguity: many regions can look nearly identical. The task therefore requires more than selecting a visually strong local match. Noise, blur, edge artifacts, geometric variation and repeated device structures must be handled robustly.

The required output is the center `(x, y)` in search-image pixel coordinates. When multiple final candidates are effectively indistinguishable, the candidate nearest the search-image center is selected.

## 3. Design Requirements

The implementation is designed around the following requirements:

1. 1000 x 1000 reference at nominal 1 nm/px.
2. 1000 x 1000 search at nominal 10 nm/px.
3. DRAM-like and FinFET-like periodic structures.
4. Independent reference/search imaging degradations.
5. Edge brightening.
6. Blur and noise variation.
7. Rotation and scale variation.
8. Deterministic transformation-aware ground truth.
9. Batch evaluation with localization-error metrics.
10. Explicit failure reporting instead of silent false predictions.

The public hackathon page confirms the requirement to generate synthetic data, retain exact ground truth, use independent sensor noise, include edge brightening and realistic blur/rotation/scale variation, and evaluate at least 30 randomized pairs. It also states that Applied Materials will evaluate a separate hidden Phase 2 set. See the official source link recorded in this repository.

## 4. Final Architecture

### 4.1 Coarse proposal stage

The reference is represented at the expected lower search-image scale. Gradient magnitude is used rather than raw intensity so matching is more robust to moderate contrast and illumination differences. Multi-scale normalized cross-correlation is evaluated at 0.75x, 1.00x and 1.25x of the nominal search footprint. The best spatially separated candidates are retained.

### 4.2 Local geometric verification

Each candidate is converted into a local ROI. ORB descriptors are extracted from the reference and ROI on a common feature canvas. Descriptor matches are filtered with a nearest-neighbor ratio test. RANSAC estimates a partial-affine transform. The estimated transform provides a geometric consistency check and refined center, scale and orientation estimates.

### 4.3 Late fusion

The pipeline combines two complementary evidence sources:

- **NCC confidence:** dense appearance similarity.
- **RANSAC confidence:** local geometric consistency and inlier support.

The hybrid confidence mode uses these signals to rank candidates while rejecting clearly implausible transformations. Equal-weight fusion remains available as an ablation baseline.

### 4.4 Tie resolution

The image-center rule is deliberately applied only after fused scoring and only to genuinely near-equal candidates. A clearly superior candidate is not discarded merely because it is farther from the image center.

## 5. Synthetic Data Generator

The challenge-style generator supports:

- DRAM and FinFET structures.
- Nominal 10x scale relation.
- Independent reference/search Gaussian noise.
- Speckle noise.
- Salt-and-pepper corruption.
- Blur.
- Charging-like streak artifacts.
- Controlled edge brightening near structure boundaries.
- Continuous in-plane rotation over 0–360 degrees.
- Default scale variation of 0.75x–1.25x and a stress range of 0.5x–2.0x.

### 5.1 Ground-truth transformation

The generator uses an explicit affine transformation representation. For a reference point `p_r`, the corresponding search point is computed through the same matrix used to render the transformed sample. Ground truth is therefore transformation-aware rather than inferred from a rounded bounding box.

The exact mapping is documented in `TRANSFORMS_AND_GROUND_TRUTH.md`.

## 6. Why a Hybrid Method Was Selected

Fixed-scale NCC is inexpensive and interpretable but can fail on periodic layouts and geometric variation. Feature matching handles scale and rotation better but can become ambiguous on highly repetitive structures. The hybrid design therefore assigns each method a different job instead of requiring one method to solve every source of ambiguity.

The design trade-off is:

- higher runtime than NCC alone;
- significantly better robustness in the local stress matrix;
- no model-training dependency;
- deterministic and reproducible inference;
- straightforward failure diagnosis.

A learned Siamese approach remains a future direction rather than an implemented claim because there is no trained model, weights, or official benchmark evidence for such a method in this package.

## 7. Local Quantitative Results

The checked-in `results/` directory contains the executed local development ablation matrix.

### 7.1 Core comparison

| Method | Accuracy @5 px | Mean error | Mean IoU | Mean runtime |
|---|---:|---:|---:|---:|
| NCC | 16.7% | 37.49 px | 0.301 | ~53 ms |
| ORB-RANSAC | 0% | failed on evaluated cases | — | ~46 ms |
| HYBRID-EQUAL | 100% | 0.64 px | 0.776 | ~283 ms |
| HYBRID-CONFIDENCE | 100% | 0.64 px | 0.776 | ~284 ms |

These values are development-generator results only.

### 7.2 Statistical comparison

For the executed paired development comparison of the hybrid against NCC:

- mean error difference: approximately -36.84 px;
- paired bootstrap 95% interval: approximately -62.82 to -16.79 px;
- Wilcoxon signed-rank p-value: 0.03125.

The confidence-weighted and equal-weight hybrid variants did not differ materially on the small executed matrix; this supports retaining confidence weighting for interpretability while avoiding claims that it independently improves accuracy until a larger official-source benchmark is available.

### 7.3 Stress-test observations

The local tests showed that the hybrid is substantially more robust than NCC under combined perturbations, but very large scale changes and aggressive edge-brightening can still produce failures. These are useful engineering boundaries, not official benchmark statistics.

## 8. Testing and Validation

The repository includes 14 automated tests covering:

- reproducible generation;
- DRAM/FinFET generation;
- exact transform reprojection;
- inverse-transform stability;
- edge-brightening activation;
- nominal localization;
- rotation + scale localization;
- NCC failure versus hybrid recovery;
- invalid-input handling;
- IoU computation;
- failure categorization.

A clean extracted-package test run completed with:

```text
14 passed
```

The package also exposes standalone inference and manifest evaluation entry points.

## 9. Public Hugging Face Benchmark Status

The public Drift-Sense Hugging Face Space is confirmed as running, but it is a generator rather than a fixed public benchmark dataset. Its generator source creates the reference/search pairs and a manifest containing ground-truth coordinates.

The public hackathon specification explicitly states that Applied Materials will later use a separate Phase 2 test set with hidden placement/noise parameters. Therefore the local results in this package must not be presented as official challenge scores.

The exact benchmark limitation and reproduction procedure are documented in `OFFICIAL_BENCHMARK_STATUS.md`.

## 10. Reproducibility

Primary inference:

```bash
python infer.py --reference reference.png --search search.png
```

Manifest evaluation:

```bash
python evaluate_manifest.py metadata.csv --output predictions.csv
```

Test suite:

```bash
python -m unittest discover -s tests -v
```

The package records dependencies in `requirements.txt` and contains deterministic seed handling for the local generator.

## 11. Security and Operational Considerations

The implementation does not require a database, credentials, remote service calls, or privileged operations. Input validation rejects unsupported or excessive image sizes, unreadable inputs and invalid parameters. External image paths are treated as data paths; no shell commands are constructed from user input.

Runtime and memory measurements should be recorded on the same hardware when comparing methods. The current checked-in runtime results are local measurements and are not comparable to the hidden evaluator's hardware unless explicitly noted.

## 12. Limitations

The principal limitation is benchmark access. The local generator is a challenge-style approximation, not Applied Materials' hidden Phase 2 set.

The second limitation is that very large geometric deviations can exceed the current candidate-search range. The current default proposal scales are deliberately conservative because they balance robustness and runtime. Extending that range should be justified by official-source failures rather than added speculatively.

The third limitation is that feature-based verification can fail when there are insufficient distinctive local features. The code reports these failures explicitly.

## 13. Final Technical Recommendation

The recommended configuration is **HYBRID-CONFIDENCE**:

```text
multi-scale gradient NCC
        ↓
coarse candidates
        ↓
ORB + RANSAC local verification
        ↓
appearance + geometry fusion
        ↓
center tie-break
```

This is the strongest defensible solution currently supported by the evidence in this package.

No change to the core algorithm should be made solely from local-generator observations. The next justified technical change is only an official-source benchmark run followed by targeted modification if that benchmark reveals a reproducible failure mode.

## 14. Source Material and References

- Drift-Sense public generator: https://huggingface.co/spaces/aayushraina21/drift-sense-synthetic-data
- SEMICON India Hackathon 2026 problem page: https://i4c.in/hackathon-2026/
- OpenCV template matching documentation: https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html
- OpenCV SIFT documentation: https://docs.opencv.org/4.x/da/df5/tutorial_py_sift_intro.html

The original project notes and source documents used during development are retained under `docs/source_materials/`.

## 15. Completion Status

**Technical package status: complete for review.**

**Submission package status: not final yet.**

Before claiming first-round completion, the official-source generator should be executed in a network-enabled environment and its resulting manifest evaluated with the unchanged hybrid configuration. No GitHub repository or PowerPoint is included in this package because those were intentionally deferred until the official-source benchmark is available.
