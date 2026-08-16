# Technical Review Verdict

## Architecture decision

The final technical direction is a two-stage late-fusion system:

**multi-scale gradient NCC proposal → local ORB/RANSAC verification → confidence fusion → center tie-break**.

## Why this direction was chosen

A single NCC maximum is insufficient on repeating semiconductor patterns. Global feature matching alone is also unreliable because repeated cells can form plausible geometric matches. Restricting feature matching to dense image-similarity proposals keeps both approaches in complementary roles:

- NCC answers **where might the target be?**
- local ORB/RANSAC answers **does this candidate have the right geometry?**

The hybrid therefore avoids putting all responsibility on either modality.

## Generator validity

The local generator preserves the key competition geometry, explicitly models edge brightening, supports continuous rotation and a configurable scale range, and derives ground-truth coordinates from an exact affine transform. It is an algorithm-validation generator, not a replacement for the official Hugging Face generator.

## Completion criterion for this phase

This hybrid component is considered technically complete when:

- all unit tests pass;
- the CLI produces predictions;
- the manifest evaluator works;
- ablation and stress outputs are generated;
- failure cases are explicitly recorded;
- the official benchmark can be fed through the manifest evaluator without algorithmic code changes.

The current local validation satisfies the first five conditions. Official-data benchmarking remains a separate evidence step.
