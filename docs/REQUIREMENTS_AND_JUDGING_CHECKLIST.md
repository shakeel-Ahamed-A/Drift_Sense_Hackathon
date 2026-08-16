# Drift-Sense First-Round Technical Compliance Checklist

Source: official SEMICON India Hackathon 2026 Drift-Sense requirements.

## Technical repository requirements

- [x] README with setup and execution instructions.
- [x] Standalone dataset generator: `generate_dataset.py`.
- [x] Generator accepts architecture, number of pairs, and output directory.
- [x] Generator records ground-truth center coordinates.
- [x] Standalone localization inference: `infer.py`.
- [x] Inference accepts reference and search image paths.
- [x] Inference stdout is a single `x y` coordinate pair by default.
- [x] Optional diagnostics are isolated to stderr with `--verbose`.
- [x] No deep-learning weights claimed or required.
- [x] Reproducible dependency manifest: `requirements.txt` and `requirements.lock.txt`.
- [x] Citation/supporting-reference documentation.

## Dataset-generation requirements

- [x] DRAM-style architecture.
- [x] FinFET-style architecture.
- [x] Independent reference/search noise streams.
- [x] Edge brightening.
- [x] Blur.
- [x] Rotation variation.
- [x] Scale variation.
- [x] Exact transformation-aware ground truth.
- [x] Minimum 30-pair self-evaluation capability.

## Evaluation requirements

- [x] Localization error metrics.
- [x] Accuracy thresholds.
- [x] Runtime measurement.
- [x] Failure categorization.
- [x] Stress/ablation analysis.
- [x] Development results explicitly separated from official Applied Materials scores.

## External submission materials still requiring user-specific completion

- [ ] Fill the official i4C Idea Submission Template with team/member/contact details.
- [ ] Add the final working GitHub repository URL to the slide deck/form.
- [ ] Include citation references used in the final presentation.
- [ ] Upload the final PPT/PDF using the official template.

## Important benchmark qualification

Applied Materials uses a separate Phase 2 test set with hidden placement/noise parameters.
Therefore local generated results are evidence of self-evaluation, not official Phase 2 scores.
