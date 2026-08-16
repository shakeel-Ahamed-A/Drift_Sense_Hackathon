# Drift-Sense: Hybrid Localization for Navigation-Error Recovery in Wafer Inspection

## Abstract

Drift-Sense is a wafer-inspection localization problem in which a high-resolution reference SEM image must be localized within a lower-magnification search image containing the same semiconductor pattern. The nominal acquisition relationship is 1 nm/pixel for the 1000 x 1000-pixel reference and 10 nm/pixel for the 1000 x 1000-pixel search, so the reference occupies an approximately 100 x 100-pixel footprint in search coordinates. The principal challenge is periodic ambiguity: DRAM and FinFET layouts contain repeated structures that can produce strong but incorrect matches.

This work develops a hybrid, training-free classical computer-vision pipeline. Multi-scale gradient normalized cross-correlation (NCC) generates spatially separated candidates; local ORB matching with RANSAC then verifies geometric consistency and estimates a refined center. Appearance and geometry evidence are fused at the candidate level, followed by the required search-image-center tie-break when candidates are effectively indistinguishable. A challenge-style synthetic generator supplies DRAM and FinFET structures with independent reference/search degradation, controlled edge brightening, rotation, scale variation, and transformation-aware ground truth.

On the executed local development matrix (n = 6 for the headline ablation), the hybrid achieved 100.0% accuracy within 5 pixels, compared with 16.7% for NCC and 0% for ORB-RANSAC alone. Mean localization error was 0.64 pixels for both hybrid variants versus 37.49 pixels for NCC. These figures are development results only. The public Hugging Face resource is a generator rather than a frozen benchmark dataset, while the Applied Materials Phase 2 test set is separate and hidden; therefore no official benchmark score is claimed. The implementation is technically complete for review, with the remaining substantive validation step being execution against the official-source generator in a network-enabled environment.

## 1. Problem Definition

### 1.1 Task

Given a high-resolution reference image and a lower-magnification search image of the same semiconductor structure, estimate the center `(x, y)` of the region in the search image corresponding to the reference. The nominal scale relation is 10:1, so a 1000 x 1000-pixel reference maps to an approximately 100 x 100-pixel footprint in the search image. The required output is the center of the recovered location, expressed in search-image pixels.

### 1.2 Why the task is difficult

The dominant failure mode is periodic ambiguity. DRAM arrays and FinFET structures contain repeated motifs, so a visually strong local match is not necessarily the correct occurrence. The acquisition process also introduces independent noise, blur, drift, intensity variation, and other imaging artifacts. The public challenge specification requires realistic synthetic variation, including independent sensor noise, edge brightening, blur, rotation, scaling variation, known ground truth, and at least 30 randomized self-evaluation pairs. [1]

### 1.3 Decision rule

The localization system must return the best supported center. The image-center preference is a tie-break, not a blanket prior: it is applied only after the fused evidence identifies effectively equivalent candidates. This prevents a clearly superior match from being rejected merely because it is farther from the search-image center.

## 2. Design Objectives

The solution was designed to satisfy five objectives:

1. **Geometric robustness:** tolerate moderate scale and in-plane rotation changes.
2. **Appearance robustness:** reduce sensitivity to contrast and noise differences between reference and search images.
3. **Periodic-pattern resilience:** retain multiple plausible candidates instead of committing to the first correlation maximum.
4. **Deterministic inference:** avoid training-data or model-weight dependencies in the final classical pipeline.
5. **Reproducible evaluation:** record exact parameters, seeds, coordinates, predictions, errors, and failure states.

## 3. Hybrid Localization Architecture

### 3.1 Stage A: multi-scale gradient-NCC proposal generation

The reference is represented at the search-image scale and converted to a gradient-magnitude representation. Gaussian smoothing suppresses high-frequency sensor noise, while Sobel gradients emphasize structural boundaries. Normalized cross-correlation is evaluated at three proposal scales: 0.75x, 1.00x, and 1.25x of the nominal search footprint. The strongest spatially separated candidates are retained rather than selecting a single global maximum.

This stage is inexpensive and dense: every valid search position receives an appearance score. Its weakness is that correlation alone cannot reliably distinguish repeated structures under geometric variation; it therefore serves as a proposal mechanism rather than the sole decision rule.

### 3.2 Stage B: local ORB + RANSAC verification

Each NCC candidate defines a local search region. ORB features are extracted from the reference and candidate region. Descriptor matches are filtered by a nearest-neighbor ratio test, and a partial-affine transform is estimated with RANSAC. The resulting inlier count and geometric residual provide evidence that the candidate represents a coherent geometric correspondence rather than a coincidental correlation peak.

A partial-affine model is sufficient for the intended local geometry and is less permissive than an unconstrained homography. The transform also provides estimates of translation, scale and orientation for diagnostics and refinement.

### 3.3 Late fusion and tie resolution

The two stages provide complementary evidence:

- **NCC confidence** measures dense structural similarity.
- **RANSAC confidence** measures local geometric consistency.

The final candidate score combines these signals. Candidates that fail geometric sanity checks are rejected. If the remaining candidates are effectively tied, the candidate whose center is closest to the search-image center is selected. This is late fusion: proposal generation and geometric verification remain independent, and their outputs are combined only after candidate formation.

## 4. Challenge-Style Synthetic Generator

### 4.1 Architecture classes

Two synthetic architecture families are supported:

- **DRAM-like:** periodic horizontal word-lines, vertical bit-lines, and contact-like intersections.
- **FinFET-like:** dense parallel fins with horizontal gate structures and local process variation.

### 4.2 Imaging model

The generator maintains the nominal acquisition relation of a 1000 x 1000 reference at 1 nm/pixel and a 1000 x 1000 search image at 10 nm/pixel. Reference and search images are degraded independently. The supported perturbations include Gaussian blur, Gaussian detector noise, speckle, salt-and-pepper corruption, charging-like streaks, controlled edge brightening, continuous in-plane rotation over 0–360 degrees, and multiplicative scale variation.

The default scale range is 0.75x–1.25x. A broader 0.5x–2.0x range is available for stress testing. The wider range is treated as a stress condition rather than a default because it materially increases the search space and is not required by the core task definition.

### 4.3 Transformation-aware ground truth

Ground truth is derived from the exact transformation used to construct each sample. If `p_r` is a point in the reference coordinate system, the corresponding search coordinate is obtained by applying the same affine transformation used during rendering, followed by the known 10x scale mapping. The transformed reference corners are reprojected through the full matrix rather than inferred from a rounded bounding box. This preserves sub-pixel coordinate consistency.

The forward transform is the authoritative mapping; inverse projection is used only for diagnostics and numerical checks. The generator records the parameters required to reproduce each sample.

## 5. Experimental Methodology

### 5.1 Ablation conditions

The executed local matrix compares:

- NCC alone;
- ORB-RANSAC alone;
- HYBRID-EQUAL;
- HYBRID-CONFIDENCE.

The ablation also sweeps rotation, scale, edge brightening, noise, and combined stress conditions across multiple seeds.

### 5.2 Metrics

The primary metric is localization accuracy within a pixel-error tolerance. The package records accuracy at 1, 3, 5 and 10 pixels, mean and median localization error, IoU, runtime, failure rate, confidence margin, and failure category. PR curves and diagnostic distributions are also generated. Orientation and scale errors are treated as diagnostic metrics because the challenge's required output is the center coordinate rather than pose.

### 5.3 Statistical reporting

The headline ablation contains six paired development cases, so percentages should be interpreted as descriptive rather than population-level performance estimates. The recorded Wilcoxon signed-rank comparison is therefore reported as an exploratory paired test, not as evidence of broad statistical generalization. The official benchmark remains necessary for any claim beyond the local development matrix.

## 6. Results

### 6.1 Headline development ablation

**Table 1. Headline localization results on the executed local development matrix (n = 6).**

| Method | Accuracy <=5 px | Mean error | Mean IoU | Mean runtime |
|---|---:|---:|---:|---:|
| NCC | 16.7% | 37.49 px | 0.301 | 53.0 ms |
| ORB-RANSAC | 0.0% | not defined; all cases failed | not defined | 46.3 ms |
| HYBRID-EQUAL | **100.0%** | **0.64 px** | **0.776** | 283.0 ms |
| HYBRID-CONFIDENCE | **100.0%** | **0.64 px** | **0.776** | 283.6 ms |

The hybrid substantially outperformed both individual components on this matrix. NCC retained useful proposal information but was vulnerable to periodic false matches. ORB-RANSAC alone failed to obtain sufficient geometric consensus in the evaluated cases. The hybrid combined the strengths of dense correlation and local geometry.

### 6.2 Architecture breakdown

**Table 2. Accuracy within 5 pixels by architecture on the same development matrix.**

| Method | DRAM (n=3) | FinFET (n=3) |
|---|---:|---:|
| NCC | 0.0% | 33.3% |
| ORB-RANSAC | 0.0% | 0.0% |
| HYBRID-EQUAL | **100.0%** | **100.0%** |
| HYBRID-CONFIDENCE | **100.0%** | **100.0%** |

### 6.3 Statistical comparison

For the paired development comparison of the hybrid against NCC, the mean localization-error difference was approximately -36.84 pixels. A paired bootstrap 95% interval was approximately [-62.82, -16.79] pixels, and the Wilcoxon signed-rank test returned `p = 0.03125`. Because `n = 6`, this result should be treated as exploratory evidence rather than a definitive population-level significance claim.

HYBRID-EQUAL and HYBRID-CONFIDENCE produced identical localization error and accuracy on the headline matrix. Their measured runtime differed only marginally. Therefore the evidence does **not** establish that confidence weighting improves localization accuracy; HYBRID-CONFIDENCE is retained because it provides explicit evidence weighting and a clearer extension point for future benchmarking.

### 6.4 Stress-test boundaries

The stress matrix identified two concrete limits of the current configuration:

- At a 2.0x scale ratio, accuracy within 5 pixels fell to 50.0%, with mean error of 9.85 pixels.
- At an edge-brightening level of 0.4, accuracy within 5 pixels fell to 50.0%, with mean error of 41.47 pixels.

These are useful engineering boundaries, not official benchmark scores. They indicate that extreme geometric or appearance perturbations can exceed the current candidate-search range or distort the structural representation enough to produce incorrect hypotheses.

## 7. Validation and Reproducibility

The package contains 14 automated tests covering reproducible generation, DRAM/FinFET generation, transform reprojection, inverse-transform stability, edge-brightening activation, nominal and transformed localization, NCC-versus-hybrid behavior, invalid inputs, IoU computation, and explicit failure categorization. A clean extracted-package run completed with all 14 tests passing.

The primary local commands are:

```bash
python infer.py --reference reference.png --search search.png
python evaluate_manifest.py metadata.csv --output predictions.csv
python -m unittest discover -s tests -v
```

The source package records its Python dependencies in `requirements.txt` and preserves deterministic seeds for local synthetic-data generation.

## 8. Official Benchmark Status

The public Hugging Face Drift-Sense resource is a running synthetic-data generator rather than a frozen public benchmark set. [2] The official challenge page states that participants must generate their own synthetic data for self-evaluation and that Applied Materials will use a separate Phase 2 test set with hidden placement and noise parameters. [1]

Accordingly, the results in this report are explicitly labeled **local development-generator results**. No official Applied Materials accuracy is claimed.

The next evidence-gathering step is to execute the unchanged hybrid implementation against a reproducible split generated by the public Hugging Face source in a network-enabled environment, then compare those results with the local development matrix. No algorithmic modification should be made unless that benchmark reveals a reproducible failure mode.

## 9. Limitations and Author Decisions

The following issues require empirical validation or author judgment rather than editorial repair:

1. **Official benchmark access:** the hidden Applied Materials test set is not public. Final competitive performance cannot therefore be established from the present package alone.
2. **Headline sample size:** the main ablation uses `n = 6`. It is appropriate for an engineering ablation but insufficient for a strong generalization claim. A larger self-evaluation set should be reported before any final performance claim.
3. **Extreme transformations:** the stress results show degradation at very large scale changes and aggressive edge brightening. Extending the search range may improve robustness but will increase runtime and should be driven by official-source evidence.
4. **Fusion choice:** HYBRID-CONFIDENCE and HYBRID-EQUAL were tied on the current matrix. Retaining confidence weighting is a design choice, not an experimentally proven accuracy improvement.

## 10. Conclusion

The finalized technical contribution is a deterministic hybrid localization pipeline that uses multi-scale gradient NCC to generate plausible locations and local ORB-RANSAC geometry to reject or refine ambiguous candidates. The design directly targets the defining difficulty of Drift-Sense—periodic semiconductor structure—without requiring a training pipeline or learned model weights.

On the executed development matrix, the hybrid reached 100.0% accuracy within 5 pixels and reduced mean localization error from 37.49 pixels for NCC to 0.64 pixels. These results demonstrate the value of combining dense appearance similarity with local geometric verification, while the documented stress failures prevent overclaiming robustness beyond the tested operating range.

The technical package is therefore ready for final **review**, but not yet for a claim of official benchmark performance. The remaining validation task is narrowly defined: run the unchanged implementation on a reproducible split generated from the public Drift-Sense source, report the resulting metrics without post-hoc tuning, and make any subsequent algorithmic change only if that benchmark exposes a concrete and reproducible failure mode.

## References

[1] i4C, *SEMICON India Hackathon 2026 — Drift-Sense: AI-Powered Navigation-Error Recovery for Wafer Inspection Tools*. Available at: https://i4c.in/hackathon-2026/ (accessed 16 Aug 2026).

[2] Aayush Raina, *Drift-Sense Synthetic Dataset Generator*, Hugging Face Spaces. Available at: https://huggingface.co/spaces/aayushraina21/drift-sense-synthetic-data (accessed 16 Aug 2026).

[3] OpenCV, *Template Matching*. OpenCV documentation. Available at: https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html (accessed 16 Aug 2026).

[4] OpenCV, *SIFT: Introduction*. OpenCV documentation. Available at: https://docs.opencv.org/4.x/da/df5/tutorial_py_sift_intro.html (accessed 16 Aug 2026).

## Appendix A. Package Contents

The technical package contains the hybrid implementation, standalone inference and manifest-evaluation scripts, ablation runner, tests, figures, experiment records, and supporting technical documentation. The original problem description and earlier project notes are retained under `docs/source_materials/` for traceability.
