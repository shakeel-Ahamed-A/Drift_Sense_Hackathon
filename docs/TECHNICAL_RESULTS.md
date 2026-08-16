# Hybrid Pipeline Experimental Results

## Scope of the executed experiment

The reported numbers below are from the **self-contained challenge-style generator in this component**, not from the official Hugging Face benchmark. The experiment is intended to validate the algorithm, its robustness, and its failure modes before official-data benchmarking.

### Dataset geometry

- 1000×1000 reference at 1 nm/px.
- 1000×1000 search at 10 nm/px.
- DRAM and FinFET architectures.
- Continuous 0–360° rotation support.
- Default 0.75×–1.25× scale variation.
- Stress sweep extended to 0.5×–2.0×.
- Independent reference/search sensor degradation.
- Edge brightening.

### Main ablation set

Three independent seeds were used with one DRAM and one FinFET sample per seed (six paired test cases per method). Additional parameter-sweep and combined-stress cases are included in the matrix.

## Pooled ablation results

| Method | N | Acc@1px | Acc@3px | Acc@5px | Acc@10px | Mean error | Mean IoU | Mean runtime |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NCC | 6 | 0.0% | 0.0% | 16.7% | 16.7% | 37.49 px | 0.301 | 53.0 ms |
| ORB-RANSAC | 6 | 0.0% | 0.0% | 0.0% | 0.0% | — | — | 46.3 ms |
| HYBRID-EQUAL | 6 | 66.7% | 100.0% | 100.0% | 100.0% | 0.64 px | 0.776 | 283.0 ms |
| **HYBRID-CONFIDENCE** | **6** | **66.7%** | **100.0%** | **100.0%** | **100.0%** | **0.64 px** | **0.776** | **283.6 ms** |

The small matrix is deliberately conservative; it is not a claim of final competition accuracy.

## Statistical comparison

Paired comparison used the same six generated cases for each method pair.

### Hybrid vs NCC

- Paired cases: 6
- Mean error difference (hybrid − NCC): **−36.84 px**
- 95% paired bootstrap CI: **[−62.82, −16.79] px**
- Wilcoxon signed-rank p-value: **0.03125**

The hybrid therefore shows a statistically significant reduction in localization error on this controlled development matrix at the 5% level.

### Hybrid confidence weighting vs equal weighting

- Paired cases: 6
- Mean error difference: **0.00 px**
- 95% bootstrap CI: **[0.00, 0.00] px**
- Wilcoxon p-value: **1.0**

On this matrix, confidence weighting is not measurably better than equal weighting. The confidence-weighted form is retained because it provides a principled mechanism for weak/strong geometric evidence and is no worse in the measured tests.

## Parameter sensitivity

### Rotation

Tested at 0°, 30°, 90°, 180°, and 270°. The hybrid maintained 100% accuracy within 5 px across the executed one-sample-per-architecture sweep at these levels.

Raw orientation error can be close to 90° for symmetric layout motifs even when center localization is excellent. This metric is therefore diagnostic rather than a competition objective: the challenge requires center coordinates, not orientation estimates.

### Scale

Tested at:

`0.5×, 0.75×, 0.9×, 1.0×, 1.1×, 1.25×, 1.5×, 2.0×`

The hybrid achieved 100% within 5 px through 1.5× in the executed sweep. At 2.0× it dropped to **50%** within 5 px, identifying an adversarial boundary where the local feature stage becomes less reliable.

### Edge brightening

Tested at 0.0, 0.1, 0.2, 0.4 and 0.6. The hybrid remained strong through most of the range. At edge strength 0.4, one of the two architecture cases failed badly in the executed sweep; this is retained as a known robustness boundary rather than hidden.

### Noise

The executed sweep included:

- reference/search Gaussian sigma (0, 0)
- (2, 5)
- (5, 10)
- (10, 20)

The hybrid retained 100% accuracy within 5 px in the tested noise-only cases.

## Combined worst-case

The executed combined stress case used:

- rotation = 137°
- scale = 0.75×
- edge brightening = 0.40
- reference noise sigma = 10
- search noise sigma = 20
- elevated search speckle
- elevated impulse noise

Results:

| Method | Acc@5px | Mean error | Mean IoU | Failure rate |
|---|---:|---:|---:|---:|
| NCC | 0% | 189.28 px | 0.138 | 100% false positives |
| ORB-RANSAC | 0% | — | — | 100% missed detections |
| HYBRID-EQUAL | 100% | 1.51 px | 0.928 | 0% |
| **HYBRID-CONFIDENCE** | **100%** | **1.51 px** | **0.928** | **0%** |

## Failure modes found

The most useful adversarial findings are:

1. **Very large scale changes (2.0×)** can make the local geometric verifier produce implausible scale hypotheses.
2. **Strong edge brightening (0.4)** can change the dense structural appearance enough to create misleading proposals in some cases.
3. **Global ORB-RANSAC** alone is not sufficiently reliable on the periodic layouts used here.
4. **Raw/NCC-only matching** remains vulnerable to periodic false positives even though the dense stage is fast.

These failure cases informed the final scale prior, feature-score threshold, and proposal-to-refinement consistency rule.

## Runtime trade-off

The hybrid is approximately 5× slower than the NCC-only baseline in this development environment, but the extra cost is spent only on a small candidate set rather than on an exhaustive feature search over the entire image.

The observed trade-off is therefore:

- NCC: ~53 ms, weak ambiguity handling.
- ORB-RANSAC global: ~46 ms, but frequent failure to establish a reliable global transform.
- Hybrid: ~284 ms, but substantially better localization robustness in the controlled matrix.

## Final configuration selected

**HYBRID-CONFIDENCE** with:

- proposal image: 500×500
- NCC proposal scales: 0.75×, 1.00×, 1.25×
- top 5 spatially separated NCC proposals per scale
- local ORB feature canvas: 256×256
- ORB features: 1800
- Lowe-style ratio threshold: 0.80
- RANSAC reprojection threshold: 4 px
- feature inlier threshold: ≥4
- center refinement jump rejection: 80 px
- feature confidence activation threshold: 0.10
- soft target-scale prior: 0.35–2.5 with strongest support in 0.5–2.0
- center tie tolerance: 0.01 fused-score units

The equal-weight version is statistically indistinguishable on the current matrix, but confidence weighting remains the recommended production configuration because it explicitly adapts the fusion to feature reliability.
