# Drift-Sense
## Hybrid Localization of Semiconductor SEM Patterns

A computer-vision solution for localizing a high-resolution semiconductor SEM reference pattern inside a lower-magnification search image.

---

## 1. Project Overview

Drift-Sense is a semiconductor image-localization system developed for the Drift-Sense challenge.

The task is to locate a known high-resolution reference image inside a lower-magnification search image and return the center coordinates `(x, y)` of the corresponding region in search-image coordinates.

### Imaging relationship

- Reference image: `1000 × 1000 px` at `1 nm/px`
- Search image: `1000 × 1000 px` at `10 nm/px`
- Approximate reference footprint in the search image: `100 × 100 px`

The main challenge is that semiconductor layouts such as DRAM and FinFET contain highly repetitive structures. Simple template matching can therefore produce strong false matches at incorrect repeated locations.

---

## 2. Solution

The final implementation uses a hybrid computer-vision pipeline:

1. Multi-scale gradient-based Normalized Cross-Correlation (NCC)
2. Candidate location generation
3. ORB feature matching
4. RANSAC-based geometric verification
5. Late fusion of appearance and geometric evidence
6. Center-of-image tie handling
7. Final `(x, y)` localization output

### Why a hybrid approach?

NCC provides dense structural similarity and is effective for candidate generation.

ORB/RANSAC provides complementary geometric evidence and is more tolerant of moderate scale and orientation variation.

Combining the two reduces the risk of selecting a visually similar periodic structure as the final match.

---

## 3. Synthetic Data

The repository includes a standalone synthetic-data generator supporting challenge-style semiconductor imagery.

Supported structure families include:

- DRAM
- FinFET

The generator supports:

- controlled edge brightening
- blur
- independent noise
- speckle
- salt-and-pepper corruption
- charging-like streaks
- rotation
- scale variation
- deterministic random seeds
- transformation-aware ground truth

The generated manifest records the sample information and ground-truth localization coordinates.

---

## 4. Repository Structure

```text
Drift_Sense_Hackathon/
│
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
│
├── src/
│   └── hybrid_drift_sense.py
│
├── scripts/
│   ├── generate_dataset.py
│   ├── infer.py
│   ├── evaluate_manifest.py
│   └── run_ablation.py
│
├── tests/
│   ├── test_hybrid.py
│   └── test_submission_interface.py
│
├── demo/
│   ├── reference.png
│   ├── search.png
│   ├── localization_overlay.png
│   └── demo_result.json
│
├── results/
│   ├── metrics_summary.json
│   ├── ablation_summary.json
│   ├── all_evaluation_rows.csv
│   └── figures/
│
└── docs/
    ├── TECHNICAL_REPORT.md
    ├── ARCHITECTURE.md
    ├── TEST_STRATEGY.md
    ├── TRANSFORMS_AND_GROUND_TRUTH.md
    ├── GENERATOR_AND_STRESS_TESTS.md
    └── REFERENCES.md
