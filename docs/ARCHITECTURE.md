# Hybrid Localization Architecture

## 1. Interaction model

The pipeline uses **late fusion with iterative refinement**.

### Stage 1: dense proposal generation

Gradient-normalized NCC is used as a broad spatial search. It is deliberately coarse because the next stage provides full-resolution geometric verification.

### Stage 2: local geometric verification

Each NCC proposal is converted into a small ROI. ORB descriptors are matched between the reference and that ROI. RANSAC estimates a partial-affine transform.

The local verifier returns:

- refined center,
- feature confidence,
- inlier count,
- estimated reference-to-search orientation,
- estimated footprint scale.

### Stage 3: confidence fusion

For each candidate:

- dense confidence = normalized NCC score among proposals;
- geometric confidence = inlier ratio + inlier-support score;
- implausible scale is strongly penalized;
- excessive geometric displacement from the NCC proposal is rejected;
- feature confidence receives 55–80% of the final score depending on reliability;
- candidates with no trustworthy geometric verification receive only 18% of their normalized NCC confidence as a conservative fallback score.

This avoids a weak feature hypothesis or a raw correlation peak from dominating the final decision.

## Why this hybrid is superior to fixed-scale NCC

Fixed-scale NCC assumes the target orientation and footprint are known. The challenge permits rotation and scale variation and is intentionally repetitive. NCC is therefore retained as a proposal generator, while ORB/RANSAC resolves the local geometric ambiguity.

## Why the pipeline does not use global feature matching as the primary stage

Global feature matching is vulnerable to repeated semiconductor structures. A repeated cell can create a plausible geometric transform with a non-trivial inlier count. Running feature matching only in NCC-proposed ROIs reduces that global ambiguity and makes the geometric model a verifier rather than an unconstrained locator.

## Complexity

If `K` proposals are evaluated, the hybrid is roughly:

`dense NCC proposal cost + K × local feature verification cost`.

The current default uses three scales and five proposals per scale; the 500×500 proposal image substantially reduces the dense-search cost.
